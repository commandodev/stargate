Introduction
============

rpz.websocket is a package for adding WebSocket WebSockets_ support to
repoze.bfg applications.

What is a WebSocket?
====================

From wikipedia::

    WebSockets is a technology providing for bi-directional, full-duplex
    communications channels, over a single TCP socket

The WebSocket protocol provides a persistent low latency, low complexity way to
achieve two way communication from the browser to server.

From a client point of view using websocket is very simple::

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

What about the server side?
===========================

On the server side things are slightly more complex. The server must:

 * Perform a handshake with the client
 * Keep hold of the persistent connection
 * Receive messages from the client
 * Route messages to the client

Handshake
---------

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

The ``Sec-*`` headers can be ignored for now (these are only the very latest
draft of the websocket spec_. They will be implemented in a later version of
rpz.websocket. So the headers that matter right now are:

Client:

    GET /demo HTTP/1.1
    Host: example.com
    Connection: Upgrade
    Upgrade: WebSocket
    Origin: http://example.com

Server:

    HTTP/1.1 101 WebSocket Protocol Handshake
    Upgrade: WebSocket
    Connection: Upgrade
    WebSocket-Origin: http://example.com
    WebSocket-Location: ws://example.com/demo


Connection
----------

Once the handshake has been successfully negotiated there is a persistent bi-directional
websocket connection from the client to the server


.. [WebSockets] http://en.wikipedia.org/wiki/Web_Sockets
.. [spec] http://tools.ietf.org/html/draft-hixie-thewebsocketprotocol-76
