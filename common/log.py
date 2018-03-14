# -*- coding:utf-8 -*-
import logging.config
import os


class Logger:
    def __init__(self):
        logging.config.fileConfig(os.path.dirname(os.path.realpath(__file__)) + "/logger.conf")
        self.logger = logging.getLogger("flask_api")

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)
