# -*- coding:utf-8 -*-
from extensions import celery
from tasks.worker import sse_worker, once_shell_worker


@celery.task
def event_to_mysql(product):
    sse_worker(product)


@celery.task
def once_shell(period_id, product_id, user, target, command, period_task):
    once_shell_worker(period_id, product_id, user, target, command, period_task)
