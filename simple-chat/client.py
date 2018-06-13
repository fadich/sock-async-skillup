import aiohttp
import asyncio
import json
import logging
import traceback
import threading
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


HOST_URL = 'ws://0.0.0.0:4242'
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480


logger = logging.getLogger()


class Client(object):
    host: str = ''
    msg_handler: callable = None
    loop: asyncio.BaseEventLoop = None
    session: aiohttp.ClientSession = None
    ws: aiohttp.ClientWebSocketResponse = None

    def __init__(self, host: str, msg_handler: callable):
        self.host = host
        self.msg_handler = msg_handler
        self.loop = asyncio.new_event_loop()

    async def connect(self):
        self.session = aiohttp.ClientSession()
        try:
            async with self.session.ws_connect(self.host) as self.ws:

                async for msg in self.ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        self.msg_handler(msg)

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


class Window(Gtk.ApplicationWindow):
    scrolled: Gtk.ScrolledWindow = None
    grid: Gtk.Grid = None
    client: Client = None
    event_loop: asyncio.BaseEventLoop = None
    client_thread: threading.Thread = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.scrolled = Gtk.ScrolledWindow()
        self.grid = Gtk.Grid()

        self.scrolled.add(self.grid)
        self.add(self.scrolled)

        self.client = Client(HOST_URL, self.msg_handler)
        self.loop = asyncio.new_event_loop()

        self.connect('destroy', Gtk.main_quit)
        self.connect('destroy', self.close)

    def build(self):
        self.set_default_size(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.show()

        self.set_title('SimpleChat')

        thread = threading.Thread(target=self.loop.run_until_complete,
                                  args=(self.client.connect(),))
        thread.start()

        Gtk.main()

    def close(self, window):
        # self.client.loop.run_until_complete(self.client.close())

        if self.client_thread and self.client_thread.is_alive():
            self.client_thread.join()

    def msg_handler(self, *args, **kwargs):
        print(locals())


if __name__ == '__main__':
    Window().build()
