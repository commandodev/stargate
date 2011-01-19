"""This module supplies a class which can be subclassed or mixed in and used in
conjunction with :class:`~stargate.WebSocketView`. It provides
functionality for adding and removing
:class:`websockets <eventlet.websocket.WebSocket>` as listeners for events
"""

from eventlet.green import socket
from eventlet.support import get_errno
from pyramid.traversal import resource_path
import errno

class ListenersDescriptor(object):

    def __get__(self, obj, klass=None):
        if obj:
            if not hasattr(obj, '_registered'):
                obj._registered = set()
            return obj._registered


class WebSocketAwareResource(object):
    """An object in a :term:`pyramid:traversal` graph that handles websockets

    It is designed to be persistent and to route messages to attached clients
    """

    #: A set of attached :class:`websockets <eventlet.websocket.WebSocket>`
    listeners = ListenersDescriptor()

    __name__ = ''
    __parent__ = None

    def __str__(self):
        return u"Node: %s (%s)" % (self.__name__ if self.__name__ else 'ROOT',
                                 self.path)

    @property
    def path(self):
        return resource_path(self)

    def add_listener(self, ws):
        """Adds a :class:`eventlet.websocket.WebSocket` the the set of listeners"""
        self.listeners.add(ws)

    def remove_listener(self, ws):
        """Removes ws from the set of listeners"""
        self.listeners.discard(ws)

    def send(self, message):
        """Sends ``message`` to all sockets in the set of :attr:`listeners`

        It will clear up any websockets that are no longer connected
        """
        remove = []
        for ws in self.listeners:
            try:
                ws.send(message)
            except socket.error, e: #pragma NO COVER
                if get_errno(e) != errno.EPIPE:
                    raise
                remove.append(ws)
        for ws in remove:
            self.remove_listener(ws)
