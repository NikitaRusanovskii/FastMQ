import asyncio
import logging
import aiosqlite
import json
from .ibuffer import IBuffer
from .logger import instance_logger


# logging
logger = logging.getLogger(__name__)
logger = instance_logger(logger, __name__)


class RAMBuffer(IBuffer):
    def __init__(self):
        self.storage = []
        self.lock = asyncio.Lock()

    async def get_old_element(self) -> tuple[list, str] | None:
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
            self.storage.append((consumer_ids, message))
            logger.info('message added')

    async def delete_old(self):
        async with self.lock:
            try:
                self.storage.pop(0)
                logger.info('message popped')
            except IndexError as ex:
                logger.error(f'message not popped. Error {ex}')

    async def pop_oldest(self) -> tuple[list, str] | None:
        async with self.lock:
            try:
                el = self.storage.pop(0)
                logger.info('message popped')
            except IndexError as ex:
                logger.error(f'message not popped. Error {ex}')
        return el if el else None


class ROMBuffer(IBuffer):
    def __init__(self):
        pass

    async def initialize(self):
        async with aiosqlite.connect('buffer.db') as con:
            cur = await con.cursor()
            await cur.execute("""
                              CREATE TABLE IF NOT EXISTS messages (
                              id INTEGER PRIMARY KEY AUTOINCREMENT,
                              consumer_ids TEXT NOT NULL,
                              message TEXT NOT NULL,
                              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                              )
                              """)
            await con.commit()

    async def get_old_element(self) -> tuple[list, str] | None:
        async with aiosqlite.connect('buffer.db') as con:
            cur = await con.cursor()
            await cur.execute("""SELECT * FROM messages
                              ORDER BY created_at ASC""")
            result = await cur.fetchone()
        if not result:
            return None
        consumer_ids = json.loads(result[1])
        message = result[2]
        return (consumer_ids, message)

    async def add(self, consumer_ids: list, message: str) -> None:
        async with aiosqlite.connect('buffer.db') as con:
            cur = await con.cursor()
            await cur.execute("INSERT INTO messages\
                              (consumer_ids, message) VALUES (?, ?)",
                              (json.dumps(consumer_ids), message,))
            await con.commit()

    async def delete_old(self):
        async with aiosqlite.connect('buffer.db') as con:
            cur = await con.cursor()
            await cur.execute("DELETE FROM messages\
                              WHERE id = \
                              (SELECT id FROM messages ORDER BY id ASC\
                              LIMIT 1)")
            await con.commit()

    async def pop_oldest(self) -> tuple[list, str] | None:
        async with aiosqlite.connect('buffer.db') as con:
            cur = await con.cursor()
            await cur.execute("DELETE FROM messages\
                              WHERE ID = (\
                              SELECT id FROM messages ORDER BY id ASC\
                              LIMIT 1)\
                              RETURNING *")
            result = await cur.fetchone()
            await con.commit()
        if not result:
            return None
        return (
            json.loads(result[1]),
            result[2]
        )
