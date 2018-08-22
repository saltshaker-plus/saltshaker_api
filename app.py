# -*- coding:utf-8 -*-
from flask import Flask
from common.cli import initialize
import click
from flask_cors import CORS
from tasks.tasks_conf import CELERY_BROKER_URL
from extensions import celery, scheduler, aps_listener
from router import api

app = Flask(__name__)
# 跨域访问
CORS(app, supports_credentials=True, resources={r"*": {"origins": "*"}})

# flask_restful init
api.init_app(app)
# celery init
app.config['CELERY_BROKER_URL'] = CELERY_BROKER_URL
celery.init_app(app)


# app.config.from_object(Config())
# scheduler.init_app(app)
scheduler.add_listener(aps_listener)
scheduler.start()


@app.cli.command()
@click.option('--username', prompt='Enter the initial administrators username', default='admin',
              help="Enter the initial username")
@click.option('--password', prompt='Enter the initial Administrators password', hide_input=True,
              confirmation_prompt=True, help="Enter the initial password")
def init(username, password):
    """Initialize the saltshaker_plus."""
    initialize(username, password)


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=9000)
