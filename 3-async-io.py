import sys
import asyncio


async def target_out():
    for i in range(9, -1, -1):
        print('Message: {}'.format(i))
        await asyncio.sleep(1.5)


async def target_in():
    for i in range(9, -1, -1):
        line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
        print('({}) Got line: {}'.format(i, line))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    tasks = [
        loop.create_task(target_out()),
        loop.create_task(target_in()),
    ]

    wait_tasks = asyncio.wait(tasks)
    loop.run_until_complete(wait_tasks)

    loop.close()
