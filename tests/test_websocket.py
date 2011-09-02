import eventlet
from eventlet.green import urllib2, httplib
from nose.tools import eq_, raises
from unittest import TestCase
from stargate.test_utils import Fixture, Root
from stargate import WebSocketView, is_websocket


class EchoWebsocket(WebSocketView):

    def handle_websocket(self, ws):
        self._ws = ws
        return super(EchoWebsocket, self).handle_websocket(ws)

    def handler(self, ws):
        while True:
            m = ws.wait()
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


class TestIsTakingTooLong(Exception):
    """ Custom exception class to be raised when a test's runtime exceeds a limit. """
    pass

class LimitedTestCase(TestCase):
    """ Unittest subclass that adds a timeout to all tests.  Subclasses must
    be sure to call the LimitedTestCase setUp and tearDown methods.  The default
    timeout is 1 second, change it by setting self.TEST_TIMEOUT to the desired
    quantity."""

    TEST_TIMEOUT = 2

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
            urllib2.urlopen("http://127.0.0.1:%s/echo" % self.port)
        except urllib2.HTTPError, e:
            eq_(e.code, 400)
            raise

    @raises(urllib2.HTTPError)
    def test_traversal_view_lookup(self):
        try:
            urllib2.urlopen("http://127.0.0.1:%s/traversal_echo" % self.port)
        except urllib2.HTTPError, e:
            eq_(e.code, 404)
            raise

    def test_incomplete_headers(self):
        headers = dict(kv.split(': ') for kv in [
                "Upgrade: WebSocket",
                # NOTE: intentionally no connection header
                "Host: 127.0.0.1:%s" % self.port,
                "Origin: http://127.0.0.1:%s" % self.port,
                "WebSocket-Protocol: ws",
                ])
        http = httplib.HTTPConnection('127.0.0.1', self.port)
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
                "Host: 127.0.0.1:%s" % self.port,
                "Origin: http://127.0.0.1:%s" % self.port,
                "WebSocket-Protocol: ws",
                ]
        sock = eventlet.connect(
            ('127.0.0.1', self.port))

        fd = sock.makefile('rw', close=True)
        fd.write('\r\n'.join(connect) + '\r\n\r\n')
        fd.flush()
        result = sock.recv(1024)
        fd.close()
        ## The server responds the correct Websocket handshake
        eq_(result, '\r\n'.join(['HTTP/1.1 101 Web Socket Protocol Handshake',
                                 'Upgrade: WebSocket',
                                 'Connection: Upgrade',
                                 'WebSocket-Origin: http://127.0.0.1:%s' % self.port,
                                 'WebSocket-Location: ws://127.0.0.1:%s/echo\r\n\r\n' % self.port]))

    def test_correct_traversal_upgrade_request(self):
        connect = [
                "GET /traversal_echo HTTP/1.1",
                "Upgrade: WebSocket",
                "Connection: Upgrade",
                "Host: 127.0.0.1:%s" % self.port,
                "Origin: http://127.0.0.1:%s" % self.port,
                "WebSocket-Protocol: ws",
                ]
        sock = eventlet.connect(
            ('127.0.0.1', self.port))

        fd = sock.makefile('rw', close=True)
        fd.write('\r\n'.join(connect) + '\r\n\r\n')
        fd.flush()
        result = sock.recv(1024)
        fd.close()
        ## The server responds the correct Websocket handshake
        eq_(result, '\r\n'.join(['HTTP/1.1 101 Web Socket Protocol Handshake',
                                 'Upgrade: WebSocket',
                                 'Connection: Upgrade',
                                 'WebSocket-Origin: http://127.0.0.1:%s' % self.port,
                                 'WebSocket-Location: ws://127.0.0.1:%s/traversal_echo\r\n\r\n' % self.port]))

    def test_sending_messages_to_websocket(self):
        connect = [
                "GET /echo HTTP/1.1",
                "Upgrade: WebSocket",
                "Connection: Upgrade",
                "Host: 127.0.0.1:%s" % self.port,
                "Origin: http://127.0.0.1:%s" % self.port,
                "WebSocket-Protocol: ws",
                ]
        sock = eventlet.connect(
            ('127.0.0.1', self.port))

        fd = sock.makefile('rw', close=True)
        fd.write('\r\n'.join(connect) + '\r\n\r\n')
        fd.flush()
        first_resp = sock.recv(1024)
        fd.write('\x00hello\xFF')
        fd.flush()
        result = sock.recv(1024)
        eq_(result, '\x00http://127.0.0.1:%s says hello\xff' % self.port)
        fd.write('\x00start')
        fd.flush()
        fd.write(' end\xff')
        fd.flush()
        result = sock.recv(1024)
        eq_(result, '\x00http://127.0.0.1:%s says start end\xff' % self.port)
        fd.write('')
        fd.flush()



    def test_getting_messages_from_websocket(self):
        connect = [
                "GET /range HTTP/1.1",
                "Upgrade: WebSocket",
                "Connection: Upgrade",
                "Host: 127.0.0.1:%s" % self.port,
                "Origin: http://127.0.0.1:%s" % self.port,
                "WebSocket-Protocol: ws",
                ]
        sock = eventlet.connect(
            ('127.0.0.1', self.port))

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
                "Host: 127.0.0.1:%s" % self.port,
                "Origin: http://127.0.0.1:%s" % self.port,
                "WebSocket-Protocol: ws",
                ]
        sock = eventlet.connect(
            ('127.0.0.1', self.port))

        fd = sock.makefile('rw', close=True)
        fd.write('\r\n'.join(connect) + '\r\n\r\n')
        fd.flush()
        sock.close()

fixture = Fixture(routes=[('echo', '/echo', dict(view=EchoWebsocket)),
                          ('range', '/range', dict(view=RangeWebsocket))],
                  views=[dict(name='traversal_echo', context=Root,
                              view=EchoWebsocket,
                              custom_predicates=[is_websocket])])
setup_module = fixture.start_server
teardown_modulw = fixture.clear_up

