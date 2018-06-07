import asyncio


async def target(n: int):
    for i in range(5):
        print('Entered to {}'.format(n))
        await asyncio.sleep(1)
        print('Leaving {}'.format(n))


if __name__ == '__main__':
    tasks = []
    loop = asyncio.get_event_loop()  # type: asyncio.BaseEventLoop

    tasks.append(loop.create_task(target(1)))
    tasks.append(loop.create_task(target(2)))
    tasks.append(loop.create_task(target(3)))

    wait_tasks = asyncio.wait(tasks)
    loop.run_until_complete(wait_tasks)

    loop.close()
