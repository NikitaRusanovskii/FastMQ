import logging
from pathlib import Path
from .configurator import Config


cfg = Config(Path('config.ini'))

logger_dir = Path('logs')
if not logger_dir.exists():
    logger_dir.mkdir()

logger_levels = {
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG,
    'ERROR': logging.ERROR,
    'FATAL': logging.FATAL,
    'CRITICAL': logging.CRITICAL,
    'WARNING': logging.WARNING
}


def instance_logger(logger: logging.Logger, name: str) -> logging.Logger:
    logger.setLevel(logger_levels[cfg.get_element('LOGGER_INFO', 'level')])
    log_path = Path('logs', f'{name}.log')
    file_handler = logging.FileHandler(log_path, mode='a')
    formatter = logging.Formatter(
        fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger
