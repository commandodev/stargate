from nose.tools import assert_raises, eq_
from stargate import handshake as hs

PATH = '/path'

CORRECT_PRE76_RESPONSE = hs.BASE_RESPONSE + ("WebSocket-Origin: http://localhost\r\n"
                                             "WebSocket-Location: ws://localhost%s\r\n\r\n") \
                                                % PATH

def raises(headers, path):
    assert_raises(hs.HandShakeFailed, hs.websocket_handshake, headers, path)

def equals(headers, path, expected):
    eq_(hs.websocket_handshake(headers, path), expected)

def test_upgrade_header():
    headers = {
        #"Upgrade": "WebSocket",
        "Connection": "Upgrade",
        "Host": "localhost",
        "Origin": "http://localhost",
        #"WebSocket-Protocol": "ws",
    }
    raises.description = 'No Upgrade header raises HandShakeFailed'
    yield raises, headers, PATH
    headers['Upgrade'] = 'Not WebSocket'
    raises.description = "Upgrade header != 'WebSocket' raises HandShakeFailed"
    yield raises, headers, PATH
    headers['Upgrade'] = 'WebSocket'
    equals.description = 'Correct Upgrade header returns a headers string'
    yield equals, headers, PATH, CORRECT_PRE76_RESPONSE
    headers.pop('Origin')
    raises.description = 'No "Origin" with correct "Upgrade" raises HandShakeFailed'
    yield raises, headers, PATH
    raises.description = ''
    equals.description = ''



def test_conneciton_header():
    headers = {
        "Upgrade": "WebSocket",
        #"Connection": "Upgrade",
        "Host": "localhost",
        "Origin": "http://localhost",
        #"WebSocket-Protocol": "ws",
    }
    raises.description = 'No Connection header raises HandShakeFailed'
    yield raises, headers, PATH
    headers['Connection'] = 'Not Upgrade'
    raises.description = "Connection header != 'Upgrade' raises HandShakeFailed"
    yield raises, headers, PATH
    headers['Connection'] = 'Upgrade'
    equals.description = 'Correct Connection header returns a headers string'
    yield equals, headers, PATH, CORRECT_PRE76_RESPONSE
    headers.pop('Origin')
    raises.description = 'No "Origin" with correct "Connection" raises HandShakeFailed'
    yield raises, headers, PATH
    raises.description = ''
    equals.description = ''

def test_host_not_in_headers():
    headers = {
        "Upgrade": "WebSocket",
        "Connection": "Upgrade",
        #"Host": "localhost",
        "Origin": "http://localhost",
        #"WebSocket-Protocol": "ws",
    }
    raises.description = 'No "Host" header raises HandShakeFailed'
    yield raises, headers, PATH
    raises.description = ''

def test_version76_handshake_called():
    headers = {
        "Upgrade": "WebSocket",
        "Connection": "Upgrade",
        "Host": "localhost",
        "Origin": "http://localhost",
        "Sec-WebSocket-Protocol": "ws",
    }
    assert_raises(NotImplementedError, hs.websocket_handshake, headers, PATH)

def test_origins():
    headers = {
        "Upgrade": "WebSocket",
        "Connection": "Upgrade",
        "Host": "localhost",
        "Origin": "http://localhost",
        "Sec-WebSocket-Protocol": "ws",
    }
    assert_raises(hs.InvalidOrigin, hs.websocket_handshake, headers, PATH,
                  ['some.origins.com'])