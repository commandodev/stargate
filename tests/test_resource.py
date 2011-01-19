from eventlet.green import socket
from eventlet.websocket import WebSocket
from nose.tools import *
from stargate.resource import WebSocketAwareResource
from unittest import TestCase
import mock

class Traverser(WebSocketAwareResource):

    def __init__(self):
        self._router = dict()

    def __getitem__(self, key):
        return self._router[key]

class BrokenWebSocket(WebSocket):

    def send(self, msg):
        exc = socket.error()
        exc.errno = 32 #EPIPE
        raise exc

class TestWebSocketAwareContext(TestCase):

    def setUp(self):
        self.ctx = WebSocketAwareResource()
        self.mock_socket = s = mock.Mock()
        self.environ = env = dict(HTTP_ORIGIN='http://localhost', HTTP_WEBSOCKET_PROTOCOL='ws',
                                  PATH_INFO='test')

        self.test_ws = WebSocket(s, env)

#    def tearDown(self):
#        pass

    def test_context_has_listeners_property(self):
        eq_(self.ctx.listeners, set())

    def test_context_add_listeners(self):
        ws = self.test_ws
        OTHER_WS = WebSocket(self.mock_socket, self.environ)
        ctx = self.ctx
        eq_(ctx.listeners, set())
        ctx.add_listener(ws)
        eq_(ctx.listeners, set([ws]))
        ctx.add_listener(ws)
        eq_(ctx.listeners, set([ws]))
        ctx.remove_listener(OTHER_WS)
        eq_(ctx.listeners, set([ws]))
        ctx.remove_listener(ws)
        eq_(ctx.listeners, set())

    def test_context_add_2_listeners(self):
        ws = self.test_ws
        OTHER_WS = WebSocket(self.mock_socket, self.environ)
        ctx = self.ctx
        ctx.add_listener(ws)
        ctx.add_listener(OTHER_WS)
        eq_(len(ctx.listeners), 2)

    def test_context_send_to_ws(self):
        ctx = self.ctx
        ws = self.test_ws
        ctx.add_listener(ws)
        ctx.send('hello')
        ok_(ws.socket.sendall.called_with("\x00hello\xFF"))

    def test_model_path(self):
        root = Traverser()
        child = Traverser()
        child.__parent__ = root
        child.__name__ = 'child'
        eq_(child.path, '/child')
        eq_(str(child), 'Node: child (/child)')

    def test_context_remove_broken_pipe(self):
        ws = self.test_ws
        OTHER_WS = BrokenWebSocket(self.mock_socket, self.environ)
        ctx = self.ctx
        eq_(ctx.listeners, set())
        ctx.add_listener(ws)
        ctx.add_listener(OTHER_WS)
        ctx.send('hello')
        ok_(ws.socket.sendall.called_with("\x00hello\xFF"))
        # The broken socket should have been removed
        eq_(ctx.listeners, set([ws]))

