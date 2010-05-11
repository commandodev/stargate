import eventlet
from eventlet import wsgi


def server_factory(global_conf, host, port):
    port = int(port)
    def serve(app):
        listener = eventlet.listen((host, port))
        wsgi.server(listener, app)
    return serve