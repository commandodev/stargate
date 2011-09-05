import errno
import sys
import types
from eventlet import wsgi
from eventlet.semaphore import Semaphore
from eventlet.support import get_errno
from eventlet.green import socket
from eventlet.websocket import WebSocket as v76WebSocket
from webob import Response
from pyramid.httpexceptions import HTTPBadRequest
from ws4py.streaming import Stream

from stargate.handshake import websocket_handshake, HandShakeFailed

class WebSocket(object):
    def __init__(self, sock, environ, protocols=None, extensions=None):
        self.stream = Stream()

        self.protocols = protocols
        self.extensions = extensions
        self.environ = environ

        self.sock = sock
        self.sock.settimeout(30.0)

        self.client_terminated = False
        self.server_terminated = False

        self._lock = Semaphore()

    def close(self, code=1000, reason=''):
        """
        Call this method to initiate the websocket connection
        closing by sending a close frame to the connected peer.

        Once this method is called, the server_terminated
        attribute is set. Calling this method several times is
        safe as the closing frame will be sent only the first
        time.

        @param code: status code describing why the connection is closed
        @param reason: a human readable message describing why the connection is closed
        """
        if not self.server_terminated:
            self.server_terminated = True
            self.write_to_connection(self.stream.close(code=code, reason=reason))
        self.close_connection()

    @property
    def terminated(self):
        """
        Returns True if both the client and server have been
        marked as terminated.
        """
        return self.client_terminated is True and self.server_terminated is True

    def write_to_connection(self, bytes):
        """
        Writes the provided bytes to the underlying connection.

        @param bytes: data tio send out
        """
        return self.sock.sendall(bytes)

    def read_from_connection(self, amount):
        """
        Reads bytes from the underlying connection.

        @param amount: quantity to read (if possible)
        """
        return self.sock.recv(amount)

    def close_connection(self):
        """
        Shutdowns then closes the underlying connection.
        """
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        finally:
            self.sock.close()

    def send(self, payload, binary=False):
        """
        Sends the given payload out.

        If payload is some bytes or a bytearray,
        then it is sent as a single message not fragmented.

        If payload is a generator, each chunk is sent as part of
        fragmented message.

        @param payload: string, bytes, bytearray or a generator
        @param binary: if set, handles the payload as a binary message
        """
        if isinstance(payload, basestring) or isinstance(payload, bytearray):
            if not binary:
                self.write_to_connection(self.stream.text_message(payload).single())
            else:
                self.write_to_connection(self.stream.binary_message(payload).single())

        elif type(payload) == types.GeneratorType:
            bytes = payload.next()
            first = True
            for chunk in payload:
                if not binary:
                    self.write_to_connection(self.stream.text_message(bytes).fragment(first=first))
                else:
                    self.write_to_connection(self.stream.binary_message(payload).fragment(first=first))
                bytes = chunk
                first = False
            if not binary:
                self.write_to_connection(self.stream.text_message(bytes).fragment(last=True))
            else:
                self.write_to_connection(self.stream.text_message(bytes).fragment(last=True))

    def receive(self, message_obj=False):
        """
        Performs the operation of reading from the underlying
        connection in order to feed the stream of bytes.

        We start with a small size of two bytes to be read
        from the connection so that we can quickly parse an
        incoming frame header. Then the stream indicates
        whatever size must be read from the connection since
        it knows the frame payload length.

        Note that we perform some automatic opererations:

        * On a closing message, we respond with a closing
          message and finally close the connection
        * We respond to pings with pong messages.
        * Whenever an error is raised by the stream parsing,
          we initiate the closing of the connection with the
          appropriate error code.
        """
        next_size = 2
        #try:
        while not self.terminated:
            bytes = self.read_from_connection(next_size)
            if not bytes and next_size > 0:
                raise IOError()

            message = None
            with self._lock:
                s = self.stream
                next_size = s.parser.send(bytes)

                if s.closing is not None:
                    if not self.server_terminated:
                        next_size = 2
                        self.close(s.closing.code, s.closing.reason)
                    else:
                        self.client_terminated = True
                    raise IOError()

                elif s.errors:
                    errors = s.errors[:]
                    for error in s.errors:
                        self.close(error.code, error.reason)
                        s.errors.remove(error)
                    raise IOError()

                elif s.has_message:
                    if message_obj:
                        message = s.message
                        s.message = None
                    else:
                        message = str(s.message)
                        s.message.data = None
                        s.message = None

                for ping in s.pings:
                    self.write_to_connection(s.pong(str(ping.data)))
                s.pings = []
                s.pongs = []

                if message is not None:
                    return message


class IncorrectlyConfigured(Exception):
    """Exception to use in place of an assertion error"""

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
        """Handles the connection after setup and handshake is done

        Hands off to :meth:`handler` until the socket is closed and then
        ensures a correct :class:`webob.Response` is returned after the socket
        is closed

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
        #from nose.tools import set_trace; set_trace()
        try:
            v, handshake_reply = websocket_handshake(self.request.headers)
        except HandShakeFailed:
            _, val, _ = sys.exc_info()
            response = HTTPBadRequest(headers=dict(Connection='Close'),
                                      body='Upgrade negotiation failed:\n\t%s\n%s' % \
                                                (val, self.request.headers))
            return response
        sock = self.environ['eventlet.input'].get_socket()
        sock.sendall(handshake_reply)
        if v < 2:
            return self.handle_websocket(v76WebSocket(self.sock, self.environ))
        else:
            return self.handle_websocket(WebSocket(self.sock, self.environ))
  