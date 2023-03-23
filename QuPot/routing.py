from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from apps.runtime.urls import websocket_url



application = ProtocolTypeRouter(
    {
        'websocket': AuthMiddlewareStack(
            URLRouter(
                websocket_url
            )
        )
    }
)


