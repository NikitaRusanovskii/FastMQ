import asyncio
import logging
import aiosqlite
import json
from itertools import count
from .ibuffer import IBuffer
from .logger import instance_logger


# logging
logger = logging.getLogger(__name__)
logger = instance_logger(logger, __name__)


class RAMBuffer(IBuffer):
    def __init__(self):
        self.message_id = count(0)
        self.storage = []
        self.lock = asyncio.Lock()

    async def get_old_element(self) -> tuple[int,
                                             list[int],
                                             str] | None:
        async with self.lock:
            try:
                message = self.storage[0]
                logger.info('message received')
                return message
            except Exception as ex:
                logger.error(f'message not received. Error {ex}')
                return None

    async def add(self, consumer_ids: list, message: str) -> None:
        async with self.lock:
            cur_id = next(self.message_id)
            self.storage.append((cur_id, consumer_ids, message))
            logger.info(f'message {message} added')

    async def delete_old(self):
        async with self.lock:
            try:
                m = self.storage.pop(0)
                logger.info(f'message {m} deleted')
            except IndexError as ex:
                logger.error(f'message not deleted. Error {ex}')

    async def pop_oldest(self) -> tuple[list, str] | None:
        async with self.lock:
            try:
                el = self.storage.pop(0)
                if el is None:
                    logger.warning('element is none')
                else:
                    logger.info(f'message {el} popped')
            except IndexError as ex:
                logger.error(f'message not popped. Error {ex}')
        return el if el else None


class ROMBuffer(IBuffer):
    def __init__(self, connection: aiosqlite.Connection):
        self.connection = connection

    async def initialize(self):
        cur = await self.connection.cursor()
        await cur.execute("""
                          CREATE TABLE IF NOT EXISTS messages (
                          id INTEGER PRIMARY KEY AUTOINCREMENT,
                          consumer_ids TEXT NOT NULL,
                          message TEXT NOT NULL,
                          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                          )
                          """)
        await self.connection.commit()
        logger.info('ROMBuffer initialized')

    async def get_old_element(self) -> tuple[int,
                                             list[int],
                                             str] | None:
        cur = await self.connection.cursor()
        await cur.execute("""SELECT * FROM messages
                          ORDER BY id ASC""")
        result = await cur.fetchone()
        if not result:
            logger.warning('old element is empty')
            return None
        logger.info(f'old element is {result}')
        return (
            result[0],
            json.loads(result[1]),
            result[2]
        )

    async def add(self, consumer_ids: list[int], message: str) -> None:
        list_consumer_ids = json.dumps(consumer_ids)
        cur = await self.connection.cursor()
        await cur.execute("INSERT INTO messages\
                          (consumer_ids, message) VALUES (?, ?)",
                          (list_consumer_ids, message,))
        logger.info(f"Element {list_consumer_ids}, {message} added")
        await self.connection.commit()

    async def delete_old(self):
        cur = await self.connection.cursor()
        await cur.execute("DELETE FROM messages\
                          WHERE id = \
                          (SELECT created_at FROM messages\
                          ORDER BY id ASC\
                          LIMIT 1)")
        await self.connection.commit()
        logger.info('old element deleted')

    async def pop_oldest(self) -> tuple[int, list[int], str] | None:
        cur = await self.connection.cursor()
        await cur.execute("DELETE FROM messages\
                          WHERE ID = (\
                          SELECT id FROM messages\
                          ORDER BY id ASC\
                          LIMIT 1)\
                          RETURNING *")
        result = await cur.fetchone()
        await self.connection.commit()
        if not result:
            logger.warning('old element is empty')
            return None
        logger.info(f'old element popped: {result}')
        return (
            result[0],
            json.loads(result[1]),
            result[2]
        )
