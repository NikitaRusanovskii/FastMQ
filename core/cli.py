import inspect
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Callable, Any


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("CLI-logger")


class IConsole(ABC):
    @abstractmethod
    def on_command(self):
        pass


class Console(IConsole):
    def __init__(self):
        self.commands = {}

    def convert_args(self, value: str,
                     expected_type: int | str) -> int | str:
        try:
            if expected_type is int:
                return int(value)
            return value
        except Exception as ex:
            logger.error(f'Error {ex}.')

    def parse_args(self, function: Callable, raw_args: list[str]) -> list[Any]:
        sign = inspect.signature(function)
        annotations = list(sign.parameters.values())
        args = []
        ann_id = 0
        for param in raw_args:
            args.append(self.convert_args(param,
                                          annotations[ann_id].annotation))
            ann_id += 1
        logger.info((f'Arguments for {function.__name__} has been parsed.\n'
                     f'Args: {args}'))
        return args

    async def on_command(self):
        while True:
            command = await asyncio.to_thread(input, 'Input command > ')
            if not command:
                logger.info('Input empty command.')
                continue
            split_com = command.split()
            name = split_com[0]
            if not name:
                logger.warning('Input unknown command.')
                continue
            func = self.commands[name]
            if len(split_com) == 1:
                func()
                continue
            str_args = split_com[1:]
            args = self.parse_args(func, str_args)
            try:
                func(*args)
            except Exception as ex:
                logger.error(f'Error {ex}.')
