from configparser import ConfigParser
from pathlib import Path
from typing import Any


class Config:
    def __init__(self, path: Path):
        self.config_parser = ConfigParser()
        self.path = path
        if not self.path.exists():
            self.reset_config()
        else:
            self.config_parser.read(self.path)

    def get_element(self, section: str, element: str) -> Any:
        return self.config_parser[section][element]

    def get_int_element(self, section: str, element: str) -> int:
        return int(self.get_element(section, element))

    def get_float_element(self, section: str, element: str) -> float:
        return float(self.get_element(section, element))

    def reset_config(self):
        self.config_parser['SERVER_INFO'] = {
            'server_ip': '0.0.0.0',
            'server_port': '25565'
            }
        self.config_parser['UNIT_INFO'] = {
            'start_consumer_id': '0',
            'start_producer_id': '100'
            }
        self.config_parser['QUEUE_INFO'] = {
            'attempts_count': '5',
            'time_sleep': '5',
            'queue_pause': '5',
            'timeout': '10'
        }
        self.config_parser['LOGGER_INFO'] = {
            'level': 'INFO'
        }
        self.save()

    def save(self):
        with open(self.path, 'w') as cfg:
            self.config_parser.write(cfg)
