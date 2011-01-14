.. stargate documentation master file, created by
   sphinx-quickstart on Wed May 19 05:44:16 2010.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to stargate's documentation!
=========================================

stargate is a package for adding [WebSockets]_ support to
`pyramid <http://docs.pylonsproject.org/projects/pyramid/dev/>`_ applications using the excellent
`eventlet <http://eventlet.net/doc/>`_ library to handle long running connections inside a non blocking WSGI server.

Advantages
----------

Most existing implementations of a WebSocket capable server run stand alone from
your web app, usually on a different port or host. ``stargate`` allows you
to connect persistent connection directly to the same objects that comprise your
application. The advantages of this approach will become apparent in the examples
section.


Contents:

.. toctree::
   :maxdepth: 2

   websockets
   examples
   api



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

