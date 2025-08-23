from configparser import ConfigParser
from pathlib import Path
from typing import Any


def default_parser():
    cfg_parser = ConfigParser()
    cfg_parser['SERVER_INFO'] = {
        'server_ip': '0.0.0.0',
        'server_port': '25565'
    }
    cfg_parser['UNIT_INFO'] = {
        'start_consumer_id': '0',
        'start_producer_id': '100'
    }
    return cfg_parser


class Config:
    def __init__(self, path: Path, cfg: ConfigParser):
        self.config_parser = cfg
        self.path = path
        self.save_config()

    def get_element(self, section: str, element: str) -> Any:
        return self.config_parser[section][element]

    def reset_config(self):
        self.config_parser = default_parser()
        with open(self.path, 'w') as cfg:
            self.config_parser.write(cfg)

    def save_config(self):
        with open(self.path, 'w') as cfg:
            self.config_parser.write(cfg)


path = Path('config.ini')
if not path.exists():
    path.touch()
cfg = Config(path, default_parser())


def instance_config():
    return cfg
