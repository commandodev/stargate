import eventlet
from eventlet import debug, hubs, Timeout, spawn_n, greenthread, wsgi, patcher
from eventlet.green import urllib2
from eventlet.websocket import WebSocket
from nose.tools import ok_, eq_, set_trace, raises
from paste import deploy
from repoze.bfg.events import NewRequest
from repoze.bfg.interfaces import IRequest
from repoze.bfg.configuration import Configurator
from repoze.bfg.threadlocal import get_current_request, get_current_registry
from repoze.bfg import testing
from StringIO import StringIO
from zope.event import notify
from zope.interface import implements
from unittest import TestCase

from rpz.websocket.factory import server_factory
from rpz.websocket import WebSocketView

#from repoze.debug.responselogger import ResponseLoggingMiddleware
from logging import getLogger

import logging
import mock
import random

httplib2 = patcher.import_patched('httplib2')


class StubWebsocket(WebSocketView):

    def handle_websocket(self, ws):
        self._ws = ws
        return super(StubWebsocket, self).handle_websocket(ws)

    def handler(self, ws):
        self.ws.close()

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

##### Borrowed from the eventlet tests package

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
        config = testing.setUp()
        config_logger = getLogger("config")
        config_logger.setLevel(logging.INFO)
        config.add_route('ec', '/ec', EchoWebsocket)
        config.add_route('stub', '/stub', StubWebsocket)
        config.add_route('range', '/range', RangeWebsocket)
        config.end()
        self.config = config
        self.logfile = StringIO()
        self.killer = None
        self.spawn_server()
        eventlet.sleep(0.5)
        self.set_timeout(self.TEST_TIMEOUT)

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

        Kills any previously-running server."""
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

    def tearDown(self):
#        self.timer.cancel()
        greenthread.kill(self.killer)
        eventlet.sleep(0)
        if self.timer:
            self.timer.cancel()
            #greenthread.kill(self.timer)
        try:
            hub = hubs.get_hub()
            num_readers = len(hub.get_readers())
            num_writers = len(hub.get_writers())
            assert num_readers == num_writers == 0
        except AssertionError, e:
#            set_trace()
            print "ERROR: Hub not empty"
            print debug.format_hub_timers()
            print debug.format_hub_listeners()

        eventlet.sleep(0)

    @raises(urllib2.HTTPError)
    def test_incorrect_headers(self):
        try:
            urllib2.urlopen("http://localhost:%s/stub" % self.port)
        except urllib2.HTTPError, e:
            eq_(e.code, 400)
            raise

    def test_incomplete_headers(self):
        headers = dict(kv.split(': ') for kv in [
                "Upgrade: WebSocket",
                #"Connection: Upgrade", Without this should trigger the HTTPServerError
                "Host: localhost:%s" % self.port,
                "Origin: http://localhost:%s" % self.port,
                "WebSocket-Protocol: ws",
                ])
        http = httplib2.Http()
        resp, content = http.request("http://localhost:%s/stub" % self.port, headers=headers)

        eq_(resp['status'], '400')
        eq_(resp['connection'], 'Close')
        ok_(content.startswith('Bad:'))

    def test_correct_upgrade_request(self):
        connect = [
                "GET /ec HTTP/1.1",
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
                                 'WebSocket-Location: ws://localhost:%s/ec\r\n\r\n' % self.port]))

    def test_sending_messages_to_websocket(self):
        connect = [
                "GET /ec HTTP/1.1",
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



