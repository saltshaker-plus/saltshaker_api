# -*- coding:utf-8 -*-
from extensions import scheduler
import time


# 添加一次性定时执行
def scheduler_timing_add(period_id, product_id, user, run_date):
    # run_date="2018-07-04 14:01:00"
    scheduler.add_job(func="tasks.tasks:once_now", trigger='date', run_date=run_date,
                      args=[period_id, product_id, user], id=period_id)


# 修改一次性定时执行
def scheduler_timing_modify(period_id, product_id, user, run_date):
    # run_date="2018-07-04 14:01:00"
    try:
        scheduler.modify_job(func="tasks.tasks:once_now", trigger='date', run_date=run_date,
                             args=[period_id, product_id, user], id=period_id)
    except Exception as e:
        # 如果之前的scheduler已经不存在，重新添加定时任务
        scheduler_timing_add(period_id, product_id, user, run_date)
        print(e)


# 删除定时任务
def scheduler_delete(period_id):
    try:
        scheduler.delete_job(id=period_id)
    except Exception as e:
        print(e)


def my_job():
    print("bbbb" + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))


def my_job1():
    times = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    with open(r'/tmp/rs.txt', 'a') as f:
        f.write(str(times) + '\n')
    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))


def test():
    scheduler.add_job(func="app:my_job1", id="ddddkkkkkk", trigger='interval', seconds=5)

def test1():
    scheduler.delete_job(id="erere")
    #scheduler.add_job(func="scheduler.period_scheduler:my_job", id="dfdfdf", trigger='interval', seconds=5)

def test2():
    scheduler.add_job(func="scheduler.period_scheduler:my_job", id="time", trigger='date', run_date="2018-07-04 14:01:00")

if __name__=="__main__":
    from common.utility import local_to_utc
    print(local_to_utc("2018-07-04 00:00:00"))