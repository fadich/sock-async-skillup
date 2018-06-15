import log

import aiohttp
import asyncio
import json
import traceback
import threading
import gi
import sys

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk
from typing import Any


HOST_URL = 'ws://127.0.0.1:4242'
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 768


logger = log.get_logger('Client')


class AsyncThread(threading.Thread):
    loop: asyncio.BaseEventLoop = None
    task: asyncio.Task = None

    def __init__(self, *args, **kwargs):
        self.loop = asyncio.new_event_loop()

        super().__init__(*args, **kwargs)

        self.task = self.loop.create_task(
            self._target(*self._args, **self._kwargs), )
        wait_tasks = asyncio.wait([self.task])

        self._target = self.loop.run_until_complete
        self._args = (wait_tasks, )


class Client(object):
    host: str = ''
    session: aiohttp.ClientSession = None
    ws: aiohttp.ClientWebSocketResponse = None

    def __init__(self, host: str):
        self.host = host

    async def connect(self, handle_msg: callable, on_connected: callable = None,
                      autoreconnect: bool = True):
        self.session = aiohttp.ClientSession()

        try:

            while True:
                try:
                    logger.info('Connecting to <{}>...'.format(self.host))
                    self.ws = await self.session.ws_connect(self.host)
                    logger.info('Connected')

                    if on_connected:
                        on_connected(self.session, self.ws)

                    while True:
                        try:
                            msg = await self.ws.receive(timeout=0.01)

                            if msg.type in (aiohttp.WSMsgType.CLOSED, ):
                                break

                            handle_msg(msg)
                        except asyncio.TimeoutError:
                            pass
                        finally:
                            await asyncio.sleep(0)
                except aiohttp.client_exceptions.ClientConnectorError:
                    logger.warning('Connection error.')
                    if not autoreconnect:
                        break

                    logger.info('Reconnecting...')
                    await asyncio.sleep(1.5)

        except asyncio.CancelledError:
            logger.info('Connection aborted.')
        except Exception as e:
            logger.error(e)
            logger.warning(traceback.format_exc())
        finally:
            await self.close()

    async def close(self):

        if self.ws and not self.ws.closed:
            logger.debug('Closing ws...')
            await self.ws.close()

        if self.session and not self.session.closed:
            logger.debug('Closing session...')
            await self.session.close()

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
    client_thread: AsyncThread = None

    client_id: str = None
    clients: dict = {}
    profile: dict = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.grid = Gtk.Grid()
        self.scrolled = Gtk.ScrolledWindow()

        history = Gtk.Grid()
        for i in range(50):
            history.attach(Gtk.Label(label='123213'), 0, i * 50, 700, 50)

        print(dir(self.scrolled))
        self.scrolled.add(history)
        # self.grid.attach(Gtk.Label(label='1231231'), 100, 500, 100, 100)
        # self.grid.attach(Gtk.Label(label='1231231'), 200, 500, 100, 100)
        # self.grid.attach(Gtk.Label(label='1231231'), 300, 500, 100, 100)
        # self.grid.attach(Gtk.Label(label='1231231'), 400, 500, 100, 100)

        self.grid.add(self.scrolled)
        self.grid.add(Gtk.Label(label='123'))
        self.add(self.grid)

        self.client = Client(HOST_URL)
        self.loop = asyncio.new_event_loop()

        self.connect('destroy', Gtk.main_quit)
        self.connect('destroy', self.close)

    def build(self):
        self.set_default_size(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.show_all()

        self.set_title('SimpleChat')

        self.client_thread = AsyncThread(
            target=self.client.connect,
            args=(self.msg_handler, self.on_connected, ),)
        self.client_thread.start()

        Gtk.main()

    def close(self, window):
        pass

    def on_connected(self, session: aiohttp.ClientSession,
                     ws: aiohttp.ClientWebSocketResponse):

        self.send_profile('My name')

    def send_msg(self, msg: str):
        self._exec_command(self.client.send_command('msg', msg))

    def send_profile(self, name: str):
        self._exec_command(self.client.send_command('profile', {'name': name}))

    def send_user_list(self):
        self._exec_command(self.client.send_command('user_list'))

    def msg_handler(self, message):
        if message.type != aiohttp.WSMsgType.TEXT:
            return

        msg = json.loads(message.data)
        command = msg.get('c')
        data = msg.get('d')

        if command == 'user_list':
            self.clients = data
            logger.info('Clients: {}'.format(self.clients))

        if command == 'profile':
            self.profile = data
            logger.info('Profile: {}'.format(self.profile))

        if command == 'client_id':
            self.client_id = data
            logger.info('Client ID: {}'.format(self.client_id))

        elif command == 'msg':
            user_id = data.get('user_id')
            body = data.get('body')

            logger.info('Message from <{} ({})>: {}'.format(
                self.clients[user_id].get('name', '-- noname --'),
                user_id,
                body
            ))

    def _exec_command(self, coro: callable):
        asyncio.run_coroutine_threadsafe(coro, self.client_thread.loop)


def main():
    window = Window()

    try:
        window.build()
    except KeyboardInterrupt:
        pass
    finally:
        window.client_thread.task.cancel()


if __name__ == '__main__':
    sys.exit(main())
