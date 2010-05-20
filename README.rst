Introduction
============

rpz.websocket is a package for adding WebSockets_ support to
repoze.bfg applications using the excellent eventlet library for long running
connections

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

Normally the websocket communication in a web app is implemented as a stand alone
server (perhaps running on a different port). rpz.websocket allows you to connect
persistent connection directly to the same objects that serve your HTML.

Documentation
=============

Documentation is maintained at http://boothead.github.com/rpz.websocket

References
==========

.. [WebSockets] http://en.wikipedia.org/wiki/Web_Sockets
.. [spec] http://tools.ietf.org/html/draft-hixie-thewebsocketprotocol-76


