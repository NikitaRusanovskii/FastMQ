import logging
from .imanagers import IFiltersManager
from abc import ABC
from pydantic import BaseModel, Field
from enum import Enum
from .logger import instance_logger


logger = logging.Logger(__name__)
logger = instance_logger(logger, __name__)


class CommandType(str, Enum):
    ADD_FILTER = 'add_filter'
    REMOVE_FILTER = 'remove_filter'


class CommandSchema (BaseModel):
    command_name: CommandType
    argument: str = Field(min_length=1, max_length=16)


class IHttpApi(ABC):
    pass


class HttpApi(IHttpApi):
    def __init__(self,
                 filters_manager: IFiltersManager):
        self.filters_manager = filters_manager
        self.commands = {
            'add_filter': self.filters_manager.add,
            'remove_filter': self.filters_manager.remove,
        }

    async def on_command(self, command: str, filter_name: str) -> None:
        command_schema = CommandSchema(command, filter_name)
        func = self.commands[command_schema.command_name]
        try:
            await func(command_schema.argument)
            logger.info('command executed')
        except Exception as ex:
            logger.error(f'Error in HttpApi.on_command: {ex}')
