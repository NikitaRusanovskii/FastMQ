import websockets
import asyncio
import json
from core.source import Server


async def test_producer():
    message = {
        'IDs': [0],
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


async def main():
    server = Server()
    stask = asyncio.create_task(server.start_server())
    ptask = asyncio.create_task(test_producer())
    ctask = asyncio.create_task(test_consumer())

    await asyncio.gather(
        stask,
        ptask,
        ctask
    )


if __name__ == '__main__':
    asyncio.run(main())
