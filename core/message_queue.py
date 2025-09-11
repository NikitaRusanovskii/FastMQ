import asyncio
import logging

from .ibuffer import IBuffer
from .imanagers import IRegistry
from .imessage_queue import IMessageQueue
from .logger import instance_logger
from .units import Consumer

# logging
logger = logging.getLogger(__name__)
logger = instance_logger(logger, __name__)


class MessageQueue(IMessageQueue):
    def __init__(
        self,
        buffer: IBuffer,
        registry: IRegistry,
        attempts_count: int,
        time_sleep: int,
        queue_pause: int,
        timeout: float,
    ):
        self.registry = registry
        self.buffer = buffer
        self.attempts_count = attempts_count
        self.time_sleep = time_sleep
        self.queue_pause = queue_pause
        self.timeout = timeout

    async def publish(self, message: str, consumer_ids: list[int]):
        try:
            await self.buffer.add(message=message, consumer_ids=consumer_ids)
            logger.info(f"Public message {message} succesful.")
        except Exception as ex:
            logger.error(f"Error in publish {ex}.")

    async def send_to(self, message: str, consumer: Consumer) -> bool:
        for attempt in range(self.attempts_count):
            try:
                await consumer.websocket.send(message)
                logger.info("Message sended.")
                return True
            except Exception as ex:
                logger.error(f"Error in send_to {ex}")
                continue
        return False

    async def loop(self):
        while True:
            tasks = []
            element = await self.buffer.pop_oldest()
            if not element:
                logger.info("Element in empty.")
                await asyncio.sleep(self.queue_pause)
                continue
            msg = element[2]
            consumer_ids = element[1]
            logger.info(f"Message: {element}")
            if (not msg) or (not consumer_ids):
                await asyncio.sleep(self.queue_pause)
                continue
            try:
                for id in consumer_ids:
                    ws = await self.registry.get_consumer_by_id(id)
                    tasks.append(self.send_to(msg, ws))
            except Exception as ex:
                logger.error(f"Error in loop {ex}")
            await asyncio.gather(*tasks)
