import log

import aiohttp
import asyncio
import json
import traceback
import threading
import gi
import sys

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gdk
from typing import Any


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
    history: Gtk.Grid = None
    toolbar: Gtk.Grid = None
    entry: Gtk.Entry = None
    client: Client = None
    event_loop: asyncio.BaseEventLoop = None
    client_thread: AsyncThread = None

    client_id: str = None
    clients: dict = {}
    profile: dict = {}

    i = 25

    def __init__(self, host: str, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.grid = Gtk.Grid()
        self.scrolled = Gtk.ScrolledWindow()
        self.toolbar = Gtk.Grid()
        self.entry = Gtk.Entry()
        self.history = Gtk.Grid()

        self.client = Client('ws://{}:4242'.format(host))
        self.loop = asyncio.new_event_loop()

        self.history.override_background_color(Gtk.StateFlags.NORMAL,
                                               Gdk.RGBA())

        self.entry.connect('key-release-event', self.on_entry_key_event)

        self.toolbar.attach(Gtk.Label('User list:'), 0, 0, 10, 10)
        self.toolbar.attach(Gtk.Label('---\n---\n---\n---\n'), 0, 10, 50, 50)

        self.scrolled.add(self.history)

        self.grid.attach(self.scrolled, 0, 0, int(WINDOW_HEIGHT * .8),
                         int(WINDOW_WIDTH * .85))
        self.grid.attach(self.toolbar, int(WINDOW_WIDTH * .85), 0,
                         int(WINDOW_HEIGHT * .6), int(WINDOW_WIDTH * .15))
        self.grid.attach(self.entry, 0, WINDOW_HEIGHT * 2, WINDOW_WIDTH, 60)

        self.add(self.grid)

        self.connect('destroy', Gtk.main_quit)
        self.connect('destroy', self.close)

    def build(self):
        self.scrolled.set_min_content_height(int(WINDOW_HEIGHT * .8))
        self.scrolled.set_min_content_width(int(WINDOW_WIDTH * .85))
        # self.scrolled.set_max_content_width(int(WINDOW_WIDTH * .85))

        self.set_default_size(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.show_all()

        self.set_title('SimpleChat')

        self.client_thread = AsyncThread(
            target=self.client.connect,
            args=(self.msg_handler, self.on_connected, ),)
        self.client_thread.start()

        Gtk.main()

    def on_entry_key_event(self, entry, ev, data=None):
        if ev.keyval == Gdk.KEY_Return:
            self.send_msg(entry.get_text())
            self.append_history(self.profile.get('name'),
                                entry.get_text(), False)

            entry.set_text('')

    def close(self, window):
        pass

    def append_history(self, user: str, msg: str, left: bool = True):
        self.i += 25

        label = Gtk.Label(label='{}:\n{}\n'.format(
            '{}{}'.format(user, (' (me)', '')[left]), msg))
        label.show()
        # label.set_xalign(500)
        self.history.attach(label, 100, self.i, 1000, 10)

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

            self.append_history(
                self.clients.get(user_id, {}).get('name', user_id),
                body)

            logger.info('Message from <{} ({})>: {}'.format(
                self.clients[user_id].get('name', '-- noname --'),
                user_id,
                body
            ))

    def _exec_command(self, coro: callable):
        asyncio.run_coroutine_threadsafe(coro, self.client_thread.loop)


def main(host: str = '127.0.0.1'):
    builder = Gtk.Builder()
    builder.add_from_file('client.glade')

    history = builder.get_object('history')

    msg = Gtk.Label('The guy')
    msg.set_line_wrap(True)
    msg.set_alignment(0, 0)
    msg.set_margin_left(10)
    history.add(msg)
    msg = Gtk.Label('Hello!')
    msg.set_line_wrap(True)
    msg.set_alignment(0, 0)
    msg.set_margin_left(20)
    msg.set_margin_bottom(10)
    history.add(msg)

    msg = Gtk.Label('The guy')
    msg.set_line_wrap(True)
    msg.set_alignment(0, 0)
    msg.set_margin_left(10)
    history.add(msg)
    msg = Gtk.Label('Whats up?')
    msg.set_line_wrap(True)
    msg.set_alignment(0, 0)
    msg.set_margin_left(20)
    msg.set_margin_bottom(10)
    history.add(msg)

    msg = Gtk.Label('Me')
    msg.set_line_wrap(True)
    msg.set_alignment(1, 0)
    msg.set_margin_right(10)
    history.add(msg)
    msg = Gtk.Label('Hi, fine!')
    msg.set_line_wrap(True)
    msg.set_alignment(1, 0)
    msg.set_margin_right(10)
    msg.set_margin_bottom(10)
    history.add(msg)

    msg = Gtk.Label('Me')
    msg.set_line_wrap(True)
    msg.set_alignment(1, 0)
    msg.set_margin_right(10)
    history.add(msg)
    msg = Gtk.Label('Very long message... ' * 10)
    msg.set_line_wrap(True)
    msg.set_alignment(1, 0)
    msg.set_margin_right(10)
    msg.set_margin_bottom(10)
    history.add(msg)

    appwin = builder.get_object('appwin')
    appwin.set_title('SimpleChat')
    appwin.show_all()
    appwin.connect('destroy', Gtk.main_quit)

    try:
        Gtk.main()
    except KeyboardInterrupt:
        pass
    finally:
        pass
        # window.client_thread.task.cancel()


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))
