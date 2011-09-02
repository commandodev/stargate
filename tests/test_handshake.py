from eventlet.wsgi import Input
from nose.tools import assert_raises, eq_
from stargate import handshake as hs
from StringIO import StringIO
from webob import Request

HOST = 'http://localhost'
PATH = '/path'

CORRECT_PRE76_RESPONSE = hs.BASE_RESPONSE + ("WebSocket-Origin: http://localhost\r\n"
                                             "WebSocket-Location: ws://localhost%s\r\n\r\n") \
                                                % PATH

CORRECT_V76_RESPONSE = hs.BASE_RESPONSE + ("Sec-WebSocket-Origin: http://localhost\r\n"
                                           "Sec-WebSocket-Protocol: ws\r\n"
                                           "Sec-WebSocket-Location: ws://localhost%s\r\n\r\n8jKS\'y:G*Co,Wxa-" % PATH)

def make_environ_headers(headers, body=None):
    #set_trace()
    req = Request.blank(HOST + PATH)
    req.headers.update(headers)
    if body:
        req.body_file = Input(StringIO(body), None)
    return req.headers

def raises(headers):
    assert_raises(hs.HandShakeFailed, hs.websocket_handshake, headers)

def equals(headers, expected):
    eq_(hs.websocket_handshake(headers), expected)

def test_environ_headers():
    headers = {
        #"Upgrade": "WebSocket",
        "Connection": "Upgrade",
        "Host": "localhost",
        "Origin": "http://localhost",
        #"WebSocket-Protocol": "ws",
    }
    #set_trace()
    env = make_environ_headers(headers)

def test_upgrade_header():
    headers = make_environ_headers({
        #"Upgrade": "WebSocket",
        "Connection": "Upgrade",
        "Host": "localhost",
        "Origin": "http://localhost",
        #"WebSocket-Protocol": "ws",
    })
    raises.description = 'No Upgrade header raises HandShakeFailed'
    yield raises, headers
    headers['Upgrade'] = 'Not WebSocket'
    raises.description = "Upgrade header != 'WebSocket' raises HandShakeFailed"
    yield raises, headers
    headers['Upgrade'] = 'WebSocket'
    equals.description = 'Correct Upgrade header returns a headers string'
    yield equals, headers, (0, CORRECT_PRE76_RESPONSE)
    headers.pop('Origin')
    raises.description = 'No "Origin" with correct "Upgrade" raises HandShakeFailed'
    yield raises, headers
    raises.description = ''
    equals.description = ''

def test_conneciton_header():
    headers = make_environ_headers({
        "Upgrade": "WebSocket",
        #"Connection": "Upgrade",
        "Host": "localhost",
        "Origin": "http://localhost",
        #"WebSocket-Protocol": "ws",
    })
    raises.description = 'No Connection header raises HandShakeFailed'
    yield raises, headers
    headers['Connection'] = 'Not Upgrade'
    raises.description = "Connection header != 'Upgrade' raises HandShakeFailed"
    yield raises, headers
    headers['Connection'] = 'Upgrade'
    equals.description = 'Correct Connection header returns a headers string'
    yield equals, headers, (0, CORRECT_PRE76_RESPONSE)
    headers.pop('Origin')
    raises.description = 'No "Origin" with correct "Connection" raises HandShakeFailed'
    yield raises, headers
    raises.description = ''
    equals.description = ''

def test_version76_handshake():
    headers = make_environ_headers({
        "Upgrade": "WebSocket",
        "Connection": "Upgrade",
        "Host": "localhost",
        "Origin": "http://localhost",
        "Sec-WebSocket-Protocol": "ws",
        "Sec-WebSocket-Key1": "4 @1  46546xW%0l 1 5",
        "Sec-WebSocket-Key2": "12998 5 Y3 1  .P00",
    }, body='^n:ds[4U')
    equals(headers, (1, CORRECT_V76_RESPONSE))

def test_origins():
    headers = make_environ_headers({
        "Upgrade": "WebSocket",
        "Connection": "Upgrade",
        "Host": "localhost",
        "Origin": "http://localhost",
        "Sec-WebSocket-Protocol": "ws",
    })
    assert_raises(hs.InvalidOrigin, hs.websocket_handshake, headers,
                  ['some.origins.com'])