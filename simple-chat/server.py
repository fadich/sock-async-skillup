from aiohttp import web
from asyncio import CancelledError, get_event_loop, run_coroutine_threadsafe
from typing import Any

import uuid
import json
import log


logger = log.get_logger('Server')

clients = {}
profiles = {}


def response(command: str, data: Any = None):
    return {
        'c': command,
        'd': data
    }


async def handler(request):
    async def broadcast_profiles():
        for _ws in clients.values():
            run_coroutine_threadsafe(
                _ws.send_json(response('user_list', profiles)),
                get_event_loop())

    ws = web.WebSocketResponse()
    client_id = uuid.uuid4().hex

    logger.info('New client <{}>'.format(client_id))

    await ws.prepare(request)

    # Append client.
    clients[client_id] = ws
    profiles[client_id] = {}

    try:
        await ws.send_json(response('client_id', client_id))
        await broadcast_profiles()

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

                elif cmd == 'client_id':
                    await ws.send_json(response('client_id', client_id))

                elif cmd == 'user_list':
                    await ws.send_json(response('user_list', profiles))

                elif cmd == 'profile':
                    if isinstance(cmd_data, dict):
                        profiles[client_id] = cmd_data
                        await broadcast_profiles()

                    profile = profiles.get(client_id)

                    await ws.send_json(response('profile', profile))

                elif cmd == 'msg':
                    for client, _ws in clients.items():
                        if client != client_id:
                            run_coroutine_threadsafe(
                                _ws.send_json(response('msg', {
                                    'user_id': client_id,
                                    'body': cmd_data
                                })), get_event_loop())

                else:
                    await ws.send_json(
                        response('error', 'Unknown command <{}>'.format(cmd)))

    except CancelledError:
        pass

    del clients[client_id]
    del profiles[client_id]
    logger.info('Disconnected <{}>'.format(client_id))

    await broadcast_profiles()

    return ws


app = web.Application()
app.router.add_get('/', handler)

if __name__ == '__main__':
    web.run_app(app, host='127.0.0.1', port=4242)
