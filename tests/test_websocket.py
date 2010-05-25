import eventlet
from eventlet import debug, hubs, greenthread, wsgi
from eventlet.green import urllib2, httplib
from nose.tools import ok_, eq_, set_trace, raises
from repoze.bfg.exceptions import NotFound
from repoze.bfg import testing
from StringIO import StringIO
from unittest import TestCase
from webob.exc import HTTPNotFound
from rpz.websocket.factory import server_factory
from rpz.websocket import WebSocketView, is_websocket

from logging import getLogger

import logging
import mock
import random


class EchoWebsocket(WebSocketView):

    def handle_websocket(self, ws):
        self._ws = ws
        return super(EchoWebsocket, self).handle_websocket(ws)

    def handler(self, ws):
        while True:
            m = ws.wait()
#            import ipdb; ipdb.set_trace()
            if m is None:
                break
            ws.send('%s says %s' % (ws.origin, m))

class RangeWebsocket(WebSocketView):

    def handle_websocket(self, ws):
        self._ws = ws
        return super(RangeWebsocket, self).handle_websocket(ws)

    def handler(self, ws):
        for i in xrange(10):
            ws.send("msg %d" % i)
            eventlet.sleep(0.1)

serve = server_factory({}, 'localhost', 6544)

class Root(object):
    pass

def get_root(request):
    return Root()

def not_found(context, request):
    assert(isinstance(context, NotFound))
    return HTTPNotFound('404')

##### Borrowed from the eventlet tests package

class Fixture(object):

    def setUp(self, module):
        config = testing.setUp()
        config._set_root_factory(get_root)
        config_logger = getLogger("config")
        config_logger.setLevel(logging.INFO)
        config.add_route('echo', '/echo', EchoWebsocket)
        config.add_route('range', '/range', RangeWebsocket)
        config.add_view(name='traversal_echo', context=Root,
                        view=EchoWebsocket, custom_predicates=[is_websocket])
        # Add a not found view as setup_registry won't have been called
        config.add_view(view=not_found, context=NotFound)
        config.end()
        self.config = config
        self.logfile = StringIO()
        self.killer = None
        self.spawn_server()
        eventlet.sleep(0.3)


    def set_timeout(self, new_timeout):
        """Changes the timeout duration; only has effect during one test case"""
        if self.timer:
            self.timer.cancel()
        self.timer = eventlet.Timeout(new_timeout,
                                      TestIsTakingTooLong(new_timeout))

    def spawn_server(self, **kwargs):
        """Spawns a new wsgi server with the given arguments.
        Sets self.port to the port of the server, and self.killer is the greenlet
        running it.

        Kills any previously-running server.
        """
        if self.killer:
            greenthread.kill(self.killer)
            eventlet.sleep(0)
        app = self.config.make_wsgi_app()
        new_kwargs = dict(max_size=128,
                          log=self.logfile)
        new_kwargs.update(kwargs)

        sock = eventlet.listen(('localhost', 0))

        self.port = sock.getsockname()[1]
        self.killer = eventlet.spawn_n(wsgi.server, sock, app, **new_kwargs)

    def tearDown(self, module):
        greenthread.kill(self.killer)
        eventlet.sleep(0)
        if self.timer:
            self.timer.cancel()
        try:
            hub = hubs.get_hub()
            num_readers = len(hub.get_readers())
            num_writers = len(hub.get_writers())
            assert num_readers == num_writers == 0
        except AssertionError:
            print "ERROR: Hub not empty"
            print debug.format_hub_timers()
            print debug.format_hub_listeners()

        eventlet.sleep(0)

class TestIsTakingTooLong(Exception):
    """ Custom exception class to be raised when a test's runtime exceeds a limit. """
    pass

class LimitedTestCase(TestCase):
    """ Unittest subclass that adds a timeout to all tests.  Subclasses must
    be sure to call the LimitedTestCase setUp and tearDown methods.  The default
    timeout is 1 second, change it by setting self.TEST_TIMEOUT to the desired
    quantity."""

    TEST_TIMEOUT = 2
    SERVE = server_factory({}, 'localhost', 6544)

    def setUp(self):
        self.timer = None
        self.port = fixture.port
        self.set_timeout(self.TEST_TIMEOUT)

    def tearDown(self):
        eventlet.sleep(0)
        if self.timer:
            self.timer.cancel()


    def set_timeout(self, new_timeout):
        """Changes the timeout duration; only has effect during one test case"""
        if self.timer:
            self.timer.cancel()
        self.timer = eventlet.Timeout(new_timeout,
                                      TestIsTakingTooLong(new_timeout))

    @raises(urllib2.HTTPError)
    def test_incorrect_headers(self):
        try:
            urllib2.urlopen("http://localhost:%s/echo" % self.port)
        except urllib2.HTTPError, e:
            eq_(e.code, 400)
            raise

    @raises(urllib2.HTTPError)
    def test_traversal_view_lookup(self):
        try:
            urllib2.urlopen("http://localhost:%s/traversal_echo" % self.port)
        except urllib2.HTTPError, e:
            eq_(e.code, 404)
            raise

    def test_incomplete_headers(self):
        headers = dict(kv.split(': ') for kv in [
                "Upgrade: WebSocket",
                # NOTE: intentionally no connection header
                "Host: localhost:%s" % self.port,
                "Origin: http://localhost:%s" % self.port,
                "WebSocket-Protocol: ws",
                ])
        http = httplib.HTTPConnection('localhost', self.port)
        http.request("GET", "/echo", headers=headers)
        resp = http.getresponse()

        self.assertEqual(resp.status, 400)
        self.assertEqual(resp.getheader('connection'), 'Close')
        self.assert_(resp.read().startswith('Upgrade negotiation failed:'))

    def test_correct_upgrade_request(self):
        connect = [
                "GET /echo HTTP/1.1",
                "Upgrade: WebSocket",
                "Connection: Upgrade",
                "Host: localhost:%s" % self.port,
                "Origin: http://localhost:%s" % self.port,
                "WebSocket-Protocol: ws",
                ]
        sock = eventlet.connect(
            ('localhost', self.port))

        fd = sock.makefile('rw', close=True)
        fd.write('\r\n'.join(connect) + '\r\n\r\n')
        fd.flush()
        result = sock.recv(1024)
        fd.close()
        ## The server responds the correct Websocket handshake
        eq_(result, '\r\n'.join(['HTTP/1.1 101 Web Socket Protocol Handshake',
                                 'Upgrade: WebSocket',
                                 'Connection: Upgrade',
                                 'WebSocket-Origin: http://localhost:%s' % self.port,
                                 'WebSocket-Location: ws://localhost:%s/echo\r\n\r\n' % self.port]))

    def test_correct_traversal_upgrade_request(self):
        connect = [
                "GET /traversal_echo HTTP/1.1",
                "Upgrade: WebSocket",
                "Connection: Upgrade",
                "Host: localhost:%s" % self.port,
                "Origin: http://localhost:%s" % self.port,
                "WebSocket-Protocol: ws",
                ]
        sock = eventlet.connect(
            ('localhost', self.port))

        fd = sock.makefile('rw', close=True)
        fd.write('\r\n'.join(connect) + '\r\n\r\n')
        fd.flush()
        result = sock.recv(1024)
        fd.close()
        ## The server responds the correct Websocket handshake
        eq_(result, '\r\n'.join(['HTTP/1.1 101 Web Socket Protocol Handshake',
                                 'Upgrade: WebSocket',
                                 'Connection: Upgrade',
                                 'WebSocket-Origin: http://localhost:%s' % self.port,
                                 'WebSocket-Location: ws://localhost:%s/traversal_echo\r\n\r\n' % self.port]))

    def test_sending_messages_to_websocket(self):
        connect = [
                "GET /echo HTTP/1.1",
                "Upgrade: WebSocket",
                "Connection: Upgrade",
                "Host: localhost:%s" % self.port,
                "Origin: http://localhost:%s" % self.port,
                "WebSocket-Protocol: ws",
                ]
        sock = eventlet.connect(
            ('localhost', self.port))

        fd = sock.makefile('rw', close=True)
        fd.write('\r\n'.join(connect) + '\r\n\r\n')
        fd.flush()
        first_resp = sock.recv(1024)
        fd.write('\x00hello\xFF')
        fd.flush()
        result = sock.recv(1024)
        eq_(result, '\x00http://localhost:%s says hello\xff' % self.port)
        fd.write('\x00start')
        fd.flush()
        fd.write(' end\xff')
        fd.flush()
        result = sock.recv(1024)
        eq_(result, '\x00http://localhost:%s says start end\xff' % self.port)
        fd.write('')
        fd.flush()



    def test_getting_messages_from_websocket(self):
        connect = [
                "GET /range HTTP/1.1",
                "Upgrade: WebSocket",
                "Connection: Upgrade",
                "Host: localhost:%s" % self.port,
                "Origin: http://localhost:%s" % self.port,
                "WebSocket-Protocol: ws",
                ]
        sock = eventlet.connect(
            ('localhost', self.port))

        fd = sock.makefile('rw', close=True)
        fd.write('\r\n'.join(connect) + '\r\n\r\n')
        fd.flush()
        resp = sock.recv(1024)
        headers, result = resp.split('\r\n\r\n')
        msgs = [result.strip('\x00\xff')]
        cnt = 10
        while cnt:
            msgs.append(sock.recv(20).strip('\x00\xff'))
            cnt -= 1
        # Last item in msgs is an empty string
        eq_(msgs[:-1], ['msg %d' % i for i in range(10)])

    def test_closing_websocket(self):
        connect = [
                "GET /range HTTP/1.1",
                "Upgrade: WebSocket",
                "Connection: Upgrade",
                "Host: localhost:%s" % self.port,
                "Origin: http://localhost:%s" % self.port,
                "WebSocket-Protocol: ws",
                ]
        sock = eventlet.connect(
            ('localhost', self.port))

        fd = sock.makefile('rw', close=True)
        fd.write('\r\n'.join(connect) + '\r\n\r\n')
        fd.flush()
        sock.close()

fixture = Fixture()
setup_module = fixture.setUp
teardown_modulw = fixture.tearDown

