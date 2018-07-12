# -*- coding:utf-8 -*-
from flask import Flask
from common.cli import initialize
import click
from flask_cors import CORS
from tasks.tasks_conf import CELERY_BROKER_URL
from extensions import celery, Config, scheduler, aps_listener
from router import api
from common.redis import RedisTool
import time

app = Flask(__name__)
# 跨域访问
CORS(app, supports_credentials=True, resources={r"*": {"origins": "*"}})

# flask_restful init
api.init_app(app)
# celery init
app.config['CELERY_BROKER_URL'] = CELERY_BROKER_URL
celery.init_app(app)

# APScheduler
# 全局锁避免使用gunicorn多进程导致的计划任务多次运行
try:
    status = RedisTool.setnx("gunicorn.lock", time.time())
except Exception as e:
    raise
if status:
    app.config.from_object(Config())
    scheduler.init_app(app)
    scheduler.add_listener(aps_listener)
    scheduler.start()
# 设置过期时间3秒
try:
    RedisTool.pexpire("gunicorn.lock", 3000)
except Exception as e:
    raise


@app.cli.command()
@click.option('--username', prompt='Enter the initial administrators username', default='admin',
              help="Enter the initial username")
@click.option('--password', prompt='Enter the initial Administrators password', hide_input=True,
              confirmation_prompt=True, help="Enter the initial password")
def init(username, password):
    """Initialize the saltshaker_plus."""
    initialize(username, password)


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
