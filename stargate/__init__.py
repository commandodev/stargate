"""WebSocket support for pyramid is implemented as a :class:`view <WebSocketView>`
which handles the upgrade request and a
:class:`resource <stargate.resource.WebSocketAwareResource>` which manages the
persistent connected clients. Both should be subclassed to provide send and receive
functionality desired
"""

from stargate.handshake import websocket_handshake, HandShakeFailed
from stargate.resource import WebSocketAwareResource
from stargate.view import IncorrectlyConfigured, WebSocketView


def is_websocket(context, request):
    """Custom predicate to denote a websocket handshake

    See [predicate_arguments]_
    and the ``custom_predicate`` key word argument to
    :meth:`repoze.bfg.configuration.Configurator.add_view`
    """
    try:
        return (request.headers['Upgrade'].lower() == 'websocket') and \
               (request.headers['Connection'] == 'Upgrade')
    except KeyError:
        return False
