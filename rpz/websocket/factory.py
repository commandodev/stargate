"""This module provides a paste [server_factory]_ to run repoze.bfg inside an
eventlet wsgi server

See `Paste Deploy <http://pythonpaste.org/deploy/#paste-server-factory>`_
for more details.
"""

import eventlet
from eventlet import wsgi


def server_factory(global_conf, host, port):
    """Implements the [server_factory]_ api to provide an eventlet wsgi server"""
    port = int(port)
    def serve(app):
        listener = eventlet.listen((host, port))
        wsgi.server(listener, app)
    return serve