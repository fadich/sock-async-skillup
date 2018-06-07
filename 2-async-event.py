import asyncio


async def target(n, wait_event: asyncio.Event, set_event: asyncio.Event):
    for i in range(3):
        print('[{}] Entered to'.format(n))

        print('[{}] Waiting for event'.format(n))
        await wait_event.wait()
        print('[{}] Sleeping'.format(n))
        await asyncio.sleep(1)

        print('[{}] Setting event'.format(n))
        set_event.set()
        print('[{}] Leaving'.format(n))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    e1 = asyncio.Event()
    e2 = asyncio.Event()

    e1.set()

    tasks = [
        loop.create_task(target(1, e1, e2)),
        loop.create_task(target(2, e2, e1))
    ]

    wait_tasks = asyncio.wait(tasks)
    loop.run_until_complete(wait_tasks)

    loop.close()
