from extensions import celery
from tasks.sse_worker import see_worker


@celery.task
def event_to_mysql(product):
    see_worker(product)
