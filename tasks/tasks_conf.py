# -*- coding:utf-8 -*-
import configparser
import os

config = configparser.ConfigParser()
conf_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
config.read(conf_path + "/saltshaker.conf")
broker_host = config.get("Broker", "Broker_HOST")
broker_port = config.get("Broker", "Broker_PORT")
broker_user = config.get("Broker", "BROKER_USER")
broker_password = config.get("Broker", "BROKER_PASSWORD")
broker_vhost = config.get("Broker", "BROKER_VHOST")
# amqp://saltshaker:saltshaker@127.0.0.1:5672/
CELERY_BROKER_URL = "amqp://%s:%s@%s:%s%s" % (broker_user, broker_password, broker_host, broker_port, broker_vhost)

