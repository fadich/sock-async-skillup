from aiohttp import web
from asyncio import CancelledError
from typing import Any

import uuid
import json
import logging


logger = logging.getLogger()

clients = {}


def response(command: str, data: Any = None):
    return {
        'c': command,
        'd': data
    }


async def handler(request):
    ws = web.WebSocketResponse()
    client_id = uuid.uuid4().hex

    logger.info('New client <{}>'.format(client_id))

    await ws.prepare(request)

    # Append client.
    clients[client_id] = ws

    try:
        await ws.send_json(response('profile', {
            'client_id': client_id
        }))

        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    msg_data = json.loads(msg.data)
                except json.JSONDecodeError as e:
                    logger.warning('JSON Decoder error: {}'.format(e))
                    await ws.send_json(response('error', 'Invalid data format'))
                    continue

                cmd = isinstance(msg_data, dict) and msg_data.get('c')
                cmd_data = isinstance(msg_data, dict) and msg_data.get('d')

                if cmd == 'ping':
                    await ws.send_json(response('pong'))

                elif cmd == 'user_list':
                    await ws.send_json(response('user_list', list(clients.keys())))

                elif cmd == 'profile':
                    await ws.send_json(response('profile', {
                        'client_id': client_id
                    }))

                elif cmd == 'msg':
                    for client, ws in clients.items():
                        if client != client_id:
                            await ws.send_json(response('msg', {
                                'user_id': client_id,
                                'body': cmd_data
                            }))

                else:
                    await ws.send_json(response('error', 'Unknown command <{}>'.format(cmd)))

    except CancelledError:
        pass

    del clients[client_id]
    logger.info('Disconnected <{}>'.format(client_id))

    return ws


app = web.Application()
app.router.add_get('/', handler)

if __name__ == '__main__':
    web.run_app(app, port=4242)
