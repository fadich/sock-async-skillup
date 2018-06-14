import log

import aiohttp
import asyncio
import json
import traceback
import threading
import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk
from typing import Any


HOST_URL = 'ws://127.0.0.1:4242'
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480


logger = log.get_logger('Client')


class AsyncThread(threading.Thread):
    loop: asyncio.BaseEventLoop = None

    def __init__(self, *args, **kwargs):
        self.loop = asyncio.new_event_loop()

        super().__init__(*args, **kwargs)

        task = self.loop.create_task(
            self._target(*self._args, **self._kwargs), )
        wait_tasks = asyncio.wait([task])

        self._target = self.loop.run_until_complete
        self._args = (wait_tasks, )


class Client(object):
    host: str = ''
    loop: asyncio.BaseEventLoop = None
    session: aiohttp.ClientSession = None
    ws: aiohttp.ClientWebSocketResponse = None

    def __init__(self, host: str):
        self.host = host
        self.loop = asyncio.new_event_loop()

    async def connect(self, handle_msg: callable, on_connected: callable = None,
                      autoreconnect: bool = True):
        self.session = aiohttp.ClientSession()

        while True:
            try:
                logger.info('Connecting to <{}>...'.format(self.host))
                self.ws = await self.session.ws_connect(self.host)
                logger.info('Connected')

                if on_connected:
                    on_connected(self.session, self.ws)

                async for msg in self.ws:
                    await asyncio.sleep(0)
                    handle_msg(msg)

            except aiohttp.client_exceptions.ClientConnectorError:
                if not autoreconnect:
                    break
                logger.info('Reconnecting...')
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(e)
                logger.warning(traceback.format_exc())
                break

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

        if self.ws and not self.ws.closed:
            await self.ws.close()

    async def send_command(self, command: str, data: Any = None):
        await self.ws.send_json({
            'c': command,
            'd': data
        })


class Window(Gtk.ApplicationWindow):
    scrolled: Gtk.ScrolledWindow = None
    grid: Gtk.Grid = None
    client: Client = None
    event_loop: asyncio.BaseEventLoop = None
    client_thread: threading.Thread = None

    clients = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.scrolled = Gtk.ScrolledWindow()
        self.grid = Gtk.Grid()

        self.scrolled.add(self.grid)
        self.add(self.scrolled)

        self.client = Client(HOST_URL)
        self.loop = asyncio.new_event_loop()

        self.connect('destroy', Gtk.main_quit)
        self.connect('destroy', self.close)

    def build(self):
        self.set_default_size(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.show()

        self.set_title('SimpleChat')

        self.client_thread = AsyncThread(
            target=self.client.connect,
            args=(self.msg_handler, self.on_connected, ),)
        client_thread.start()

        Gtk.main()

        # import time
        #
        # time.sleep(1)
        # self.send_profile('My name')
        #
        # while True:
        #     time.sleep(1)
        #     self.send_msg('Hi!')

    def close(self, window):
        client_thread.stop()
        # pass
        # self.client.loop.run_until_complete(self.client.close())

        # if self.client_thread and self.client_thread.is_alive():
        #     self.client_thread.join()

    def on_connected(self, session: aiohttp.ClientSession,
                     ws: aiohttp.ClientWebSocketResponse):

        # self.send_profile('My name')
        pass

    def send_msg(self, msg: str):
        self.client.loop.run_until_complete(
            self.client.send_command('msg', msg))

    def send_profile(self, name: str):
        self.client.loop.run_until_complete(
            self.client.send_command('profile', {
                'name': name,
            }))

    def send_user_list(self):
        self.client.loop.run_until_complete(
            self.client.send_command('user_list'))

    def msg_handler(self, message):
        if message.type != aiohttp.WSMsgType.TEXT:
            return

        msg = json.loads(message.data)
        command = msg.get('c')
        data = msg.get('d')

        # print('Command: {}'.format(command))
        # print('Data: {}'.format(data))

        if command == 'user_list':
            self.clients = data
        elif command == 'msg':
            user_id = data.get('user_id')
            body = data.get('body')

            logger.info('Message from <{} ({})>: {}'.format(
                self.clients[user_id].get('name', '-- noname --'),
                user_id,
                body
            ))


if __name__ == '__main__':
    Window().build()
