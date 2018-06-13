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


class Client(object):
    host: str = ''
    loop: asyncio.BaseEventLoop = None
    session: aiohttp.ClientSession = None
    ws: aiohttp.ClientWebSocketResponse = None

    def __init__(self, host: str):
        self.host = host
        self.loop = asyncio.new_event_loop()

    async def connect(self, msg_handler: callable):
        self.session = aiohttp.ClientSession()

        try:
            while True:
                try:
                    logger.info('Connecting to <{}>...'.format(self.host))
                    async with self.session.ws_connect(self.host) as self.ws:
                        logger.info('Connected')

                        async for msg in self.ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                msg_handler(msg)
                except aiohttp.client_exceptions.ClientConnectorError:
                    pass
        except Exception as e:
            logger.error(e)
            logger.warning(traceback.format_exc())
        finally:
            if self.ws and not self.ws.closed:
                await self.ws.close()

        await self.session.close()

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

        thread = threading.Thread(target=self.loop.run_until_complete,
                                  args=(self.client.connect(self.msg_handler),))
        thread.start()
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
        pass
        # self.client.loop.run_until_complete(self.client.close())

        # if self.client_thread and self.client_thread.is_alive():
        #     self.client_thread.join()

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

            print('Message from <{} ({})>: {}'.format(
                self.clients[user_id].get('name', '-- noname --'),
                user_id,
                body
            ))


if __name__ == '__main__':
    Window().build()
