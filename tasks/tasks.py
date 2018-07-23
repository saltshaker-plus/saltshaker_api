# -*- coding:utf-8 -*-
from extensions import celery
from tasks.worker import sse_worker, job_worker


@celery.task
def event_to_mysql(product):
    sse_worker(product)


@celery.task
def job(period_id, product_id, user):
    job_worker(period_id, product_id, user)
