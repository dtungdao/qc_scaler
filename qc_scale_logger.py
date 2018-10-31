import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# create a file handler
handler = logging.FileHandler('log.txt')
handler.setLevel(logging.DEBUG)

# create a logging format
formatter = logging.Formatter('[%(asctime)s | %(name)s | %(levelname)s] %(message)s')
handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)