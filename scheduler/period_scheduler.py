# -*- coding:utf-8 -*-
from common.log import loggers
from extensions import scheduler
import time

logger = loggers()


# 添加一次性定时执行
def scheduler_timing_add(period_id, product_id, user, run_date):
    # run_date="2018-07-04 14:01:00"
    try:
        scheduler.add_job(func="tasks.tasks:job", trigger='date', run_date=run_date,
                          args=[period_id, product_id, user], id=period_id)
        return {"status": True, "message": ""}
    except Exception as e:
        logger.error("Add timing scheduler error: %s" % e)
        return {"status": False, "message": str(e)}


# 修改一次性定时执行
def scheduler_timing_modify(period_id, product_id, user, run_date):
    # run_date="2018-07-04 14:01:00"
    try:
        scheduler.modify_job(func="tasks.tasks:job", trigger='date', run_date=run_date,
                             args=[period_id, product_id, user], id=period_id)
        return {"status": True, "message": ""}
    except Exception as e:
        logger.error("Modify timing scheduler error: %s" % e)
        # 如果之前的scheduler已经不存在，重新添加定时任务
        scheduler_result = scheduler_timing_add(period_id, product_id, user, run_date)
        if scheduler_result.get("status") is not True:
            return {"status": False, "message": scheduler_result.get("message")}
        else:
            return {"status": True, "message": ""}


# 添加周期间隔任务
def scheduler_interval_add(period_id, product_id, user, run_interval, interval):
    if interval == "second":
        try:
            scheduler.add_job(func="tasks.tasks:job", trigger='interval', seconds=run_interval,
                              args=[period_id, product_id, user], id=period_id)
            return {"status": True, "message": ""}
        except Exception as e:
            logger.error("Add second period scheduler error: %s" % e)
            return {"status": False, "message": str(e)}
    elif interval == "minute":
        try:
            scheduler.add_job(func="tasks.tasks:job", trigger='interval', minutes=run_interval,
                              args=[period_id, product_id, user], id=period_id)
            return {"status": True, "message": ""}
        except Exception as e:
            logger.error("Add minute period scheduler error: %s" % e)
            return {"status": False, "message": str(e)}
    elif interval == "hour":
        try:
            scheduler.add_job(func="tasks.tasks:job", trigger='interval', hours=run_interval,
                              args=[period_id, product_id, user], id=period_id)
            return {"status": True, "message": ""}
        except Exception as e:
            logger.error("Add hour period scheduler error: %s" % e)
            return {"status": False, "message": str(e)}
    elif interval == "day":
        try:
            scheduler.add_job(func="tasks.tasks:job", trigger='interval', days=run_interval,
                              args=[period_id, product_id, user], id=period_id)
            return {"status": True, "message": ""}
        except Exception as e:
            logger.error("Add day period scheduler error: %s" % e)
            return {"status": False, "message": str(e)}
    elif interval == "week":
        try:
            scheduler.add_job(func="tasks.tasks:job", trigger='interval', weeks=run_interval,
                              args=[period_id, product_id, user], id=period_id)
            return {"status": True, "message": ""}
        except Exception as e:
            logger.error("Add week period scheduler error: %s" % e)
            return {"status": False, "message": str(e)}
    else:
        return {"status": False, "message": "No interval specified"}


# 修改周期间隔任务
def scheduler_interval_modify(period_id, product_id, user, run_interval, interval):
    if interval == "second":
        try:
            scheduler.modify_job(func="tasks.tasks:job", trigger='interval', seconds=run_interval,
                                 args=[period_id, product_id, user], id=period_id)
            return {"status": True, "message": ""}
        except Exception as e:
            logger.error("Modify second period scheduler error: %s" % e)
            scheduler_result = scheduler_interval_add(period_id, product_id, user, run_interval, interval)
            if scheduler_result.get("status") is not True:
                return {"status": False, "message": scheduler_result.get("message")}
            else:
                return {"status": True, "message": ""}
    elif interval == "minute":
        try:
            scheduler.modify_job(func="tasks.tasks:job", trigger='interval', minutes=run_interval,
                                 args=[period_id, product_id, user], id=period_id)
            return {"status": True, "message": ""}
        except Exception as e:
            logger.error("Modify minute period scheduler error: %s" % e)
            scheduler_result = scheduler_interval_add(period_id, product_id, user, run_interval, interval)
            if scheduler_result.get("status") is not True:
                return {"status": False, "message": scheduler_result.get("message")}
            else:
                return {"status": True, "message": ""}
    elif interval == "hour":
        try:
            scheduler.modify_job(func="tasks.tasks:job", trigger='interval', hours=run_interval,
                                 args=[period_id, product_id, user], id=period_id)
            return {"status": True, "message": ""}
        except Exception as e:
            logger.error("Modify hour period scheduler error: %s" % e)
            scheduler_result = scheduler_interval_add(period_id, product_id, user, run_interval, interval)
            if scheduler_result.get("status") is not True:
                return {"status": False, "message": scheduler_result.get("message")}
            else:
                return {"status": True, "message": ""}
    elif interval == "day":
        try:
            scheduler.modify_job(func="tasks.tasks:job", trigger='interval', days=run_interval,
                                 args=[period_id, product_id, user], id=period_id)
            return {"status": True, "message": ""}
        except Exception as e:
            logger.error("Modify day period scheduler error: %s" % e)
            scheduler_result = scheduler_interval_add(period_id, product_id, user, run_interval, interval)
            if scheduler_result.get("status") is not True:
                return {"status": False, "message": scheduler_result.get("message")}
            else:
                return {"status": True, "message": ""}
    elif interval == "week":
        try:
            scheduler.modify_job(func="tasks.tasks:job", trigger='interval', weeks=run_interval,
                                 args=[period_id, product_id, user], id=period_id)
            return {"status": True, "message": ""}
        except Exception as e:
            logger.error("Modify week period scheduler error: %s" % e)
            scheduler_result = scheduler_interval_add(period_id, product_id, user, run_interval, interval)
            if scheduler_result.get("status") is not True:
                return {"status": False, "message": scheduler_result.get("message")}
            else:
                return {"status": True, "message": ""}
    else:
        return {"status": False, "message": "No interval specified"}


# 删除任务
def scheduler_delete(period_id):
    try:
        scheduler.delete_job(id=period_id)
        return {"status": True, "message": ""}
    except Exception as e:
        logger.error("Delete period scheduler error: %s" % e)
        return {"status": False, "message": str(e)}


# 暂停任务
def scheduler_pause(period_id):
    try:
        scheduler.pause_job(id=period_id)
        return {"status": True, "message": ""}
    except Exception as e:
        logger.error("Pause period scheduler error: %s" % e)
        return {"status": False, "message": str(e)}


# 恢复任务
def scheduler_resume(period_id):
    try:
        scheduler.resume_job(id=period_id)
        return {"status": True, "message": ""}
    except Exception as e:
        logger.error("Resume period scheduler error: %s" % e)
        return {"status": False, "message": str(e)}