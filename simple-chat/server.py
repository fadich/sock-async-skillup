from aiohttp import web
from asyncio import CancelledError

import uuid


clients = {}


async def handler(request):
    ws = web.WebSocketResponse()
    client_id = uuid.uuid4().hex

    print('New client <{}>'.format(client_id))

    await ws.prepare(request)

    # Append client.
    clients[client_id] = ws

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                for client, ws in clients.items():
                    if client != client_id:
                        await ws.send_str(msg.data)

    except CancelledError:
        pass

    del clients[client_id]
    print('Disconnected <{}>'.format(client_id))

    return ws


app = web.Application()
app.router.add_get('/', handler)

if __name__ == '__main__':
    web.run_app(app, port=4242)
