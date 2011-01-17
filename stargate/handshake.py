"""The handshake module contains implementations of different websocket spec
versions' handshakes.

The WebSocket spec had a major revision at version 76 [ws76]_  on May 6th 2010. This
module is an attempt to insulate downstream application programmers from those
changes
"""
import string
import struct
from mercurial.keepalive import md5

class HandShakeFailed(Exception):
    """Raised when the handshake fails"""

class InvalidOrigin(Exception):
    """Raised when the websocket request doesn't have a valid origin"""

BASE_RESPONSE = ("HTTP/1.1 101 Web Socket Protocol Handshake\r\n"
                 "Upgrade: WebSocket\r\n"
                 "Connection: Upgrade\r\n")

def websocket_handshake(headers, path, allowed_origins=None):
    """Perform the websocket handshake

    This function does the part of the handshake that is common across spec
    versions and then hands off to the spec specific implementations.

    See: :func:`handshake_pre76`

    :param headers: The websocket upgrade request headers
    :type headers: A dict like object - e.g. headers from :class:`webob.Request`
    :param path: The full url path to this resource
    :raises: :exc:`HandShakeFailed`, :exc:`InvalidOrigin`
    :returns: A string to send back to the client
    """
    if not ((headers.get('Upgrade') == 'WebSocket')
                and
            (headers.get('Connection') == 'Upgrade')
                and
            ('Origin' in headers)):
        raise HandShakeFailed('Not valid upgrade headers: %s' % headers)
    origin = headers['Origin']
    if allowed_origins and origin not in allowed_origins:
        raise InvalidOrigin('Origin %s not allowed' % origin)
    # The following 3 lines are sent regardless of spec version
    if any([k.startswith('Sec-Websocket') for k in headers]):
        return handshake_v76(headers, BASE_RESPONSE, path)
    return handshake_pre76(headers, BASE_RESPONSE, path)
    
def build_location_url(headers):
    environ = headers.environ
    scheme = 'ws'
    if environ.get('wsgi.url_scheme') == 'https':
        scheme = 'wss'
    location = '%s://%s%s%s' % (
        scheme,
        environ.get('HTTP_HOST'),
        environ.get('SCRIPT_NAME'),
        environ.get('PATH_INFO')
    )
    qs = environ.get('QUERY_STRING')
    if qs:
        location += '?' + qs
    return location

def handshake_pre76(headers, base_response, path):
    """The websocket handshake as described in version 75 of the spec [ws75]_

    :param headers: The request headers from :func:`websocket_handshake`
    :param base_response: The headers common accross different spec versions
    :param path: The full url path to this resource

    .. note:: ``base_response`` and ``path`` are provided by
        :func:`websocket_handshake`
    """
    try:
        base_response += ("WebSocket-Origin: %s\r\n"
                          "WebSocket-Location: %s\r\n\r\n" \
                                % (headers['Origin'], build_location_url(headers)))
    except KeyError:
        raise HandShakeFailed("'Host' not in headers")
    return base_response

def _extract_number(value):
        """
        Utility function which, given a string like 'g98sd  5[]221@1', will
        return 9852211. Used to parse the Sec-WebSocket-Key headers.
        """
        out = ""
        spaces = 0
        for char in value:
            if char in string.digits:
                out += char
            elif char == " ":
                spaces += 1
        return int(out) / spaces


def handshake_v76(headers, base_response, path):
    """The websocket handshake as described in version 76 of the spec [ws76]_ 

    .. warning:: Not implemented yet

    :param headers: The request headers from :func:`websocket_handshake`
    :param base_response: The headers common across different spec versions
    :param path: The full url path to this resource

    .. note:: ``base_response`` and ``path`` are provided by
        :func:`websocket_handshake`
    """
    #import pdb; pdb.set_trace()
    #import pprint; pprint.pprint(headers)
    key1 = _extract_number(headers['Sec-Websocket-Key1'])
    key2 = _extract_number(headers['Sec-Websocket-Key2'])
    # There's no content-length header in the request, but it has 8
    # bytes of data.
    headers.environ['wsgi.input'].content_length = 8
    key3 = headers.environ['wsgi.input'].read(8)
    key = struct.pack(">II", key1, key2) + key3
    response = md5(key).digest()
    try:
        base_response += ("Sec-WebSocket-Origin: %s\r\n"
                          "Sec-WebSocket-Protocol: %s\r\n"
                          "Sec-WebSocket-Location: %s\r\n"
                          "\r\n%s" % (
                                headers.get('Origin'),
                                headers.get('Sec-WebSocket-Protocol', 'default'),
                                build_location_url(headers),
                                response))
    except KeyError:
        raise HandShakeFailed('WTF')
    print base_response
    return base_response