"""WebSocket support for repoze is implemented as a view which handles the
upgrade request and which can be subclassed to provide send and recieve
functionalitly
"""

import errno
import sys
from eventlet import wsgi
from eventlet.support import get_errno
from eventlet.green import socket
from eventlet.websocket import WebSocket
from webob import Response
from webob.exc import HTTPBadRequest

from stargate.handshake import websocket_handshake, HandShakeFailed

class IncorrectlyConfigured(Exception):
    """Exception to use in place of an assertion error"""

def is_websocket(context, request):
    """Custom predicate to denote a websocket handshake

    See [predicate_arguments]_
    and the ``custom_predicate`` key word argument to
    :meth:`repoze.bfg.configuration.Configurator.add_view`
    """
    try:
        return (request.headers['Upgrade'] == 'WebSocket') and \
               (request.headers['Connection'] == 'Upgrade')
    except KeyError:
        return False


class WebSocketView(object):
    """A view for handling websockets

    This view handles both the upgrade request and the ongoing socket
    communiction.
    """

    def __init__(self, request):
        self.request = request
        self.environ = request.environ
        self.sock = self.environ['eventlet.input'].get_socket()

    def __call__(self):
        return self.handle_upgrade()

    def handler(self, websocket): #pragma NO COVER
        """Handles the interaction with the websocket after being set up

        This is the method to override in subclasses to receive and send
        messages over the websocket connection

        :param websocket: A :class:`WebSocket <eventlet.websocket.WebSocket>`
        """
        raise NotImplementedError

    def handle_websocket(self, websocket):
        """Handles the connection after setup and after the socket is closed

        Hands off to :meth:`handler` until the socket is closed and then
        ensures a correct :class:`webob.Response` is returned

        :param websocket: A :class:`WebSocket <eventlet.websocket.Websocket>`
        """
        try:
            self.handler(websocket)
        except socket.error, e: #pragma NO COVER
            if get_errno(e) != errno.EPIPE:
                raise
        # use this undocumented feature of eventlet.wsgi to close the
        # connection properly
        resp = Response()
        resp.app_iter = wsgi.ALREADY_HANDLED
        return resp

    def handle_upgrade(self):
        """Completes the upgrade request sent by the browser

        Sends the headers required to set up to websocket connection back to
        the browser and then hands off to :meth:`handle_websocket`.

        See [websocket_protocol]_

        :returns: :exc:`webob.exc.HTTPBadRequest` if handshake fails
        """
        try:
            handshake_reply = websocket_handshake(self.request.headers,
                                                  self.request.path_info)
        except HandShakeFailed:
            _, val, _ = sys.exc_info()
            response = HTTPBadRequest(headers=dict(Connection='Close'))
            response.body = 'Upgrade negotiation failed:\n\t%s\n%s' % \
                            (val, self.request.headers)
            return response
        sock = self.environ['eventlet.input'].get_socket()
        sock.sendall(handshake_reply)
        return self.handle_websocket(WebSocket(self.sock, self.environ))
