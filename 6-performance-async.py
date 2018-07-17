import asyncio
import time

from random import uniform


async def target(n: int, verbose: bool = True):
    verbose and print('Entered to {}...'.format(n))
    await asyncio.sleep(uniform(4.0, 5.0))
    verbose and print('Leaving {}...'.format(n))


if __name__ == '__main__':
    start_time = time.time()
    tasks = []
    loop = asyncio.get_event_loop()  # type: asyncio.BaseEventLoop

    print('Creating tasks...')

    for i in range(100_000):
        tasks.append(loop.create_task(target(i, False)))

    print('Starting tasks...')

    wait_tasks = asyncio.wait(tasks)
    loop.run_until_complete(wait_tasks)

    loop.close()

    print('Tasks done...')

    print('Work time: {}'.format(time.time() - start_time))
