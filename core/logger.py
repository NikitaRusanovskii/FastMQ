import logging


def instance_logger(logger: logging.Logger) -> logging.Logger:
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler(f'logs\\{__name__}.log', mode='a')
    formatter = logging.Formatter(
        fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger
