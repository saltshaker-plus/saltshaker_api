# -*- coding:utf-8 -*-
import logging.config
import os


def loggers():
    logging.config.fileConfig(os.path.dirname(os.path.realpath(__file__)) + "/logger.conf")
    logger = logging.getLogger("flask_api")
    return logger
