import asyncio
import json

import websockets

from core.main import main


async def test_producer():
    message = {"filters": ["test"], "message": "hello my friend"}
    async with websockets.connect("ws://localhost:25565/producer") as con:
        await asyncio.sleep(3)
        await con.send(json.dumps(message))


async def test_consumer():
    async with websockets.connect("ws://localhost:25565/consumer") as con:
        await asyncio.sleep(2)
        await con.send("/subscribe_on test")
        msg = await con.recv()
        print(msg)


async def producer(filters: list[str], messages: list[str]):
    msgs = [f"{filters: {filters}}" for msg in messages]
    async with websockets.connect("ws://localhost:25565/producer") as con:
        await asyncio.sleep(8)
        for m in msgs:
            await con.send(json.dumps(m))
            await asyncio.sleep(1)


async def consumer(filters: list[str], consumer_name: str):
    async with websockets.connect("ws://localhost:25565/consumer") as con:
        await asyncio.sleep(6)
        for filt in filters:
            await con.send(f"/subscribe_on {filt}")
        while True:
            msg = await con.recv()
            print(f"---\nCONSUMER_NAME: {consumer_name}\nMESSAGE: {msg}\n---")


async def test_main():
    stask = asyncio.create_task(main())
    ptask = asyncio.create_task(test_producer())
    ctask = asyncio.create_task(test_consumer())

    await asyncio.gather(stask, ptask, ctask)


if __name__ == "__main__":
    asyncio.run(test_main())
