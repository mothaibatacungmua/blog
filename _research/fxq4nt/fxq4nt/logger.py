import logging


def create_logger(name, level='info'):
    logger = logging.getLogger(name)

    if level == 'info':
        logger.setLevel(logging.INFO)
    elif level == 'warning':
        logger.setLevel(logging.WARNING)
    else:
        logger.setLevel(logging.DEBUG)

    return logger