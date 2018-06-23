import asyncio

from threading import Thread
from typing import Optional


async def some(number):
    while True:
        await asyncio.sleep(0.25)
        print('[{}] Hello!'.format(number))


class AsyncThread(Thread):
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

    def join(self, timeout: Optional[float] = 0.0):
        self.task.cancel()
        super().join(timeout=timeout)


if __name__ == '__main__':
    th1 = AsyncThread(target=some, args=(1, ))
    th2 = AsyncThread(target=some, args=(2, ))
    th3 = AsyncThread(target=some, args=(3, ))
    th4 = AsyncThread(target=some, args=(4, ))

    th1.start()
    th2.start()
    th3.start()
    th4.start()

    try:
        while 1:
            pass
    except KeyboardInterrupt:
        th1.join()
        th2.join()
        th3.join()
        th4.join()
