.. _websocket_ref:

What are WebSockets?
####################

From `wikipedia <http://en.wikipedia.org/wiki/Web_Sockets>`_::

    WebSockets is a technology providing for bi-directional, full-duplex
    communications channels, over a single TCP socket

The WebSocket protocol provides a persistent low latency, low complexity way to
achieve two way communication from the browser to server.

From a client point of view using WebSocket is very simple:

.. code-block:: javascript

    var ws = new WebSocket('ws://somehost/some/url');
    ws.onopen = function(msg){
        //do some cool setup
    }
    ws.onmessage = function(msg){
        //do something cool
    }
    ws.onclose = function(msg){
        //do some clean up... stay cool
    }

    // later:
    ws.send('How cool am I?!');

That's pretty much all there is to it.


How do they work?
=================

The socket connection that WebSocket uses is negotiated with an HTTP request/response
between the client and the server

On the server side things are slightly more complex. The server must:

 * Perform a handshake with the client
 * Keep hold of the persistent connection
 * Receive messages from the client
 * Route messages to the client

The following refers to the hybi version 10 websocket spec [hybi10]_

Handshake
---------

From the browser::

    GET /ws HTTP/1.1
    Host: pmx
    Upgrade: websocket
    Connection: Upgrade
    Sec-WebSocket-Version: 6
    Sec-WebSocket-Origin: http://pmx
    Sec-WebSocket-Extensions: deflate-stream
    Sec-WebSocket-Key: x3JJHMbDL1EzLkh9GBhXDw==

The server sends back::

    HTTP/1.1 101 Switching Protocols
    Upgrade: websocket
    Connection: Upgrade
    Sec-WebSocket-Accept: HSmrc0sMlYUkAGmm5OPpG2HaGWk=

.. note:: There are also mechanisms for sub-protocols and extension. These haven't been implemented yet

See the [WebSockets] Wikipedia page for more details.

The part of the protocol that deals with framing is much more extensive than the older versions. Framing is handled by
the ws4py library.

Older Versions
==============

.. note:: The following is included for historical reasons only - as I understand it these have been disabled by default
    for security reasons in most browsers.

Handshake
---------

The handshake version of the WebSocket protocol underwent a major revision at version 76 [ws76]_.
As of version 0.2, Stargate supports both this and the older [ws75]_. Examples of both are below:


Version 76
~~~~~~~~~~

From the browser::

    GET /demo HTTP/1.1
    Host: example.com
    Connection: Upgrade
    Sec-WebSocket-Key2: 12998 5 Y3 1  .P00
    Sec-WebSocket-Protocol: sample
    Upgrade: WebSocket
    Sec-WebSocket-Key1: 4 @1  46546xW%0l 1 5
    Origin: http://example.com

    ^n:ds[4U

The server would send back::

    HTTP/1.1 101 WebSocket Protocol Handshake
    Upgrade: WebSocket
    Connection: Upgrade
    Sec-WebSocket-Origin: http://example.com
    Sec-WebSocket-Location: ws://example.com/demo
    Sec-WebSocket-Protocol: sample

    8jKS'y:G*Co,Wxa-


Version 75 and older
~~~~~~~~~~~~~~~~~~~~

Client::

    GET /demo HTTP/1.1
    Host: example.com
    Connection: Upgrade
    Upgrade: WebSocket
    Origin: http://example.com

Server::

    HTTP/1.1 101 WebSocket Protocol Handshake
    Upgrade: WebSocket
    Connection: Upgrade
    WebSocket-Origin: http://example.com
    WebSocket-Location: ws://example.com/demo


The implementation of the handshake can be found in :mod:`stargate.handshake`

Connection
----------

Once the handshake has been successfully negotiated there is a persistent bi-directional
websocket connection from the client to the server. This is a pretty thin wrapper
around a socket that sends text messages packed in the ``\x00`` and ``\xFF`` bytes.


.. [WebSockets] http://en.wikipedia.org/wiki/Web_Sockets
.. [hybi10] http://tools.ietf.org/html/draft-ietf-hybi-thewebsocketprotocol-10
.. [ws76] http://tools.ietf.org/html/draft-hixie-thewebsocketprotocol-76
.. [ws75] http://tools.ietf.org/html/draft-hixie-thewebsocketprotocol-75

