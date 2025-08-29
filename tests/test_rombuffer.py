import asyncio
from core.buffer import ROMBuffer


async def main():
    buffer = ROMBuffer()
    await buffer.initialize()

    await buffer.add('hello, my friend!')
    print(await buffer.get(1))
    await buffer.pop(1)

    print(await buffer.get(1))


if __name__ == '__main__':
    asyncio.run(main())
