# -*- coding:utf-8 -*-
from extensions import celery
from tasks.worker import sse_worker, once_worker


@celery.task
def event_to_mysql(product):
    sse_worker(product)


@celery.task
def once(period_id, product_id, user):
    once_worker(period_id, product_id, user)