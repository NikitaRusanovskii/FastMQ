import websockets
import asyncio
import json
from core.source import Server


async def test_producer():
    message = {
        'filters': ['test'],
        'message': 'hello my friend'
    }
    async with websockets.connect('ws://localhost:25565/producer') as con:
        await asyncio.sleep(3)
        await con.send(json.dumps(message))


async def test_consumer():
    async with websockets.connect('ws://localhost:25565/consumer') as con:
        await asyncio.sleep(2)
        msg = await con.recv()
        print(msg)


async def test_server():
    server = Server()
    await server.filters_manager.add('test')
    await server.filters_manager.add('removed_test')
    await server.filters_manager.subscribe_on('test', 0)
    await server.filters_manager.remove('removed_test')
    await server.start_server()


async def main():
    stask = asyncio.create_task(test_server())
    ptask = asyncio.create_task(test_producer())
    ctask = asyncio.create_task(test_consumer())

    await asyncio.gather(
        stask,
        ptask,
        ctask
    )


if __name__ == '__main__':
    asyncio.run(main())
