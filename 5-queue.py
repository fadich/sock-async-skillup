import asyncio


async def worker(q: asyncio.Queue, se: asyncio.Event):
    print('[WORKER] Starting worker...')

    while True:
        print('[WORKER] Waiting for task...')
        task: str = await q.get()

        complexity = len(task)
        print('[WORKER] Processing task <{}>...'
              'Complexity: {}'.format(task, complexity))
        await asyncio.sleep(complexity)
        print('[WORKER] Task <{}> done...'.format(task))

        if se.is_set() and not q.qsize():
            print('[WORKER] Stopping...'.format(task))
            break


async def generator(q: asyncio.Queue, se: asyncio.Event):
    print('[GENERATOR] Running generator...')

    while True:
        """The synchronous input() like this:
            ```
            task = input('Type a task command: ')
            ```
        Will never allow the worker() task to be run.
        """

        task: str = await asyncio.get_event_loop().run_in_executor(
            None, input, 'Type a task command: ')
        await q.put(task)
        print('[GENERATOR] Task put...')

        if task.lower() in ['exit', 'stop', 'break', 'quit']:
            print('[GENERATOR] Stopping...')
            se.set()
            break


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    queue = asyncio.Queue()
    stop_event = asyncio.Event()

    tasks = [
        loop.create_task(generator(queue, stop_event)),
        loop.create_task(worker(queue, stop_event)),
    ]

    wait_tasks = asyncio.wait(tasks)
    loop.run_until_complete(wait_tasks)

    loop.close()
