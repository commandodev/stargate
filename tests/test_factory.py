from paste.deploy.loadwsgi import loadserver
import os.path
import mock

INI_FILE = os.path.join(os.path.dirname(__file__), 'test.ini')

@mock.patch('eventlet.listen')
@mock.patch('eventlet.wsgi.server')
def test_loadserver(server_patch, listen_patch):
    server = loadserver('config:%s' % INI_FILE)
    listen_patch.return_value = mock.sentinel.SERVE
    server(mock.sentinel.APP)
    listen_patch.assert_called_with(('0.0.0.0', 6544))
    server_patch.assert_called_with(mock.sentinel.SERVE, mock.sentinel.APP)