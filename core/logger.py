import logging
from pathlib import Path

logger_dir = Path('logs')
if not logger_dir.exists():
    logger_dir.mkdir()


def instance_logger(logger: logging.Logger, name: str) -> logging.Logger:
    logger.setLevel(logging.INFO)
    log_path = Path('logs', f'{name}.log')
    file_handler = logging.FileHandler(log_path, mode='a')
    formatter = logging.Formatter(
        fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger
