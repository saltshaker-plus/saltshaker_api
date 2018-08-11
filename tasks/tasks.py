# -*- coding:utf-8 -*-
from extensions import celery
from tasks.worker import sse_worker, job_worker, grains_worker


@celery.task
def event_to_mysql(product):
    sse_worker(product)


@celery.task
def job(period_id, product_id, user):
    job_worker(period_id, product_id, user)


@celery.task
def grains(minion_list, product_id):
    grains_worker(minion_list, product_id)
