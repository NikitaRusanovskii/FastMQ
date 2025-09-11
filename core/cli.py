import asyncio
import inspect
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable

from .imanagers import IFiltersManager
from .logger import instance_logger

# logging
logger = logging.getLogger(__name__)
logger = instance_logger(logger, __name__)


# utils
def convert_args(value: str, expected_type: int | str) -> int | str | None:
    try:
        if expected_type is int:
            return int(value)
        return value
    except Exception as ex:
        logger.error(f"Error {ex}.")
    return None


def parse_args(function: Callable, raw_args: list[str]) -> list[Any]:
    sign = inspect.signature(function)
    annotations = list(sign.parameters.values())
    args = []
    ann_id = 0
    for param in raw_args:
        args.append(convert_args(param, annotations[ann_id].annotation))
        ann_id += 1
    logger.info(
        (f"Arguments for {function.__name__} \
         has been parsed. " f"Args: {args}")
    )
    return args


class IConsole(ABC):
    @abstractmethod
    def on_command(self):
        pass


class Console(IConsole):
    def __init__(self, fmanager: IFiltersManager):
        self.fmanager = fmanager
        self.commands = {"/add_filter": fmanager.add,
                         "/remove_filter": fmanager.remove}

    async def on_command(self):
        while True:
            command = await asyncio.to_thread(input, "Input command > ")
            if not command:
                logger.info("Input empty command.")
                continue
            split_com = command.split()
            name = split_com[0]
            if not self.commands.get(name):
                logger.warning("Input unknown command.")
                continue
            try:
                func = self.commands[name]
                if len(split_com) == 1:
                    await func()
                    continue
                str_args = split_com[1:]
                args = parse_args(func, str_args)
                try:
                    await func(*args)
                except Exception as ex:
                    logger.error(f"Error {ex}.")
            except Exception as ex:
                logger.error(f"Call function error: {ex}")
