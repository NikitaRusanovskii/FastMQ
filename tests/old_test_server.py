import websockets
import asyncio
import json
from core.main import main


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


async def test_main():
    stask = asyncio.create_task(main())
    ptask = asyncio.create_task(test_producer())
    ctask = asyncio.create_task(test_consumer())

    await asyncio.gather(
        stask,
        ptask,
        ctask
    )


if __name__ == '__main__':
    asyncio.run(test_main())