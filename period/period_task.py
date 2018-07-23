# -*- coding:utf-8 -*-
from flask_restful import Resource, reqparse, request
from flask import g
from common.log import loggers
from common.audit_log import audit_log
from common.db import DB
from common.utility import uuid_prefix
from common.sso import access_required
from common.const import role_dict
from tasks.tasks import job
from tasks.worker import insert_period_audit
from common.const import period_status, period_audit
from common.utility import utc_to_local
import json
import time
from scheduler.period_scheduler import *

logger = loggers()

parser = reqparse.RequestParser()
parser.add_argument("product_id", type=str, required=True, trim=True)
parser.add_argument("name", type=str, required=True, trim=True)
parser.add_argument("description", type=str, required=True, trim=True)
parser.add_argument("concurrent", type=int, default=0, trim=True)
parser.add_argument("interval", type=int, default=60, trim=True)
parser.add_argument("scheduler", type=str, default="period", trim=True)
parser.add_argument("once", type=dict, default={"type": "once", "date": "", "time": ""})
parser.add_argument("period", type=dict, default={"type": "", "interval": 1})
parser.add_argument("crontab", type=dict, default={"type": "", "second": 0, "minute": 0, "hour": 0, "day": 0, "week": 0})
parser.add_argument("execute", type=str, default="", trim=True)
parser.add_argument("sls", type=str, default="", trim=True)
parser.add_argument("shell", type=str, default="", trim=True)
parser.add_argument("module", type=str, default="", trim=True)
parser.add_argument("action", type=str, default="play", trim=True)
parser.add_argument("executed_minion", type=str, action="append")
parser.add_argument("target", type=str, required=True, action="append")


class Period(Resource):
    @access_required(role_dict["common_user"])
    def get(self, period_id):
        db = DB()
        status, result = db.select_by_id("period_task", period_id)
        if status is True:
            if result:
                targets = result.get("target")
                result["target"] = []
                for target in targets:
                    group_status, group_result = db.select_by_id("groups", target)
                    if group_status is True and group_result:
                        result["target"].append({
                            "name": group_result.get("name"),
                            "id": target
                        })
                    else:
                        db.close_mysql()
                        return {"status": False, "message": group_result}, 500
                product_status, product_result = db.select_by_id("product", result.get("product_id"))
                if product_status is True and product_result:
                    result["product_id"] = product_result.get("name")
                count_status, count_result = db.select_count_by_id("period_result", result["id"])
                if count_result is False:
                    return {"status": False, "message": count_result}, 500
                # 数量小于15的时候避免等于负数
                if int(count_result) < 15:
                    count_result = 15
                # 获取最后15条数据
                period_result_status, period_result_result = db.select(
                    "period_result", "where data -> '$.id'='%s' limit %s,%s"
                                     % (result["id"], int(count_result) - 15, 15))
                if period_result_status is True:
                    for r in period_result_result:
                        result["result"].append(r.get("result"))
                period_audit_status, period_audit_result = db.select(
                    "period_audit", "where data -> '$.id'='%s'" % result["id"])
                if period_audit_status is True:
                    for a in period_audit_result:
                        result["audit"].append(a.get("result"))
                db.close_mysql()
                # 周期性Job审计信息超过10条后显示前10条及最后两条
                if result["scheduler"] != "once":
                    if len(result["audit"]) > 10:
                        result_limit = result["audit"][0:10]
                        result_limit.append({'user': '', 'option': '', 'timestamp': ''})
                        result_limit.extend(result["audit"][-2:])
                        result["audit"] = result_limit
                return {"data": result, "status": True, "message": ""}, 200
            else:
                db.close_mysql()
                return {"status": False, "message": "%s does not exist" % period_id}, 404
        else:
            db.close_mysql()
            return {"status": False, "message": result}, 500

    @access_required(role_dict["common_user"])
    def delete(self, period_id):
        user = g.user_info["username"]
        db = DB()
        select_status, select_result = db.select_by_id("period_task", period_id)
        if select_status is not True:
            db.close_mysql()
            logger.error("Modify period_task error: %s" % select_result)
            return {"status": False, "message": select_result}, 500
        # 删除定期任务的时候删除对应的调度
        if select_result["scheduler"] == "period":
            scheduler_result = scheduler_delete(period_id)
            if scheduler_result.get("status") is not True:
                # 假如不是job不存在，才返回
                if "'No job" not in scheduler_result.get("message"):
                    return {"status": False, "message": scheduler_result.get("message")}, 500
        status, result = db.delete_by_id("period_task", period_id)
        if status is not True:
            logger.error("Delete period_task error: %s" % result)
            return {"status": False, "message": result}, 500
        if result is 0:
            return {"status": False, "message": "%s does not exist" % period_id}, 404
        period_result_status, period_result_result = db.delete_by_id("period_result",  period_id)
        if period_result_status is not True:
            logger.error("Delete period_result error: %s" % period_result_result)
            return {"status": False, "message": result}, 500
        period_audit_status, period_audit_result = db.delete_by_id("period_audit", period_id)
        if period_audit_status is not True:
            logger.error("Delete period_result error: %s" % period_audit_result)
            return {"status": False, "message": result}, 500
        db.close_mysql()
        audit_log(user, period_id, "", "period_task", "delete")
        return {"status": True, "message": ""}, 200

    @access_required(role_dict["common_user"])
    def put(self, period_id):
        user = g.user_info["username"]
        args = parser.parse_args()
        args["id"] = period_id
        period_task = args
        db = DB()
        # 判断是否存在
        select_status, select_result = db.select_by_id("period_task", period_id)
        if select_status is not True:
            db.close_mysql()
            logger.error("Modify period_task error: %s" % select_result)
            return {"status": False, "message": select_result}, 500
        if not select_result:
            db.close_mysql()
            return {"status": False, "message": "%s does not exist" % period_id}, 404
        # 判断名字否已经存在
        status, result = db.select("period_task", "where data -> '$.name'='%s' and data -> '$.product_id'='%s'"
                                   % (args["name"], args["product_id"]))
        if status is True and result:
            if period_id != result[0].get("id"):
                db.close_mysql()
                return {"status": False, "message": "The period_task name already exists"}, 200
        period_task["result"] = select_result["result"]
        period_task["timestamp"] = select_result["timestamp"]
        period_task["status"] = select_result["status"]
        period_task["action"] = select_result["action"]
        period_task["executed_minion"] = select_result["executed_minion"]
        period_task["count"] = select_result["count"]
        period_task["step"] = select_result["step"]
        period_task["audit"] = select_result["audit"]
        if args["once"]["date"]:
            args["once"]["date"] = utc_to_local(args["once"]["date"])
        status, result = db.update_by_id("period_task", json.dumps(period_task, ensure_ascii=False), period_id)
        db.close_mysql()
        # 修改调度任务
        if args["scheduler"] == "once" and args["once"]["type"] == "timing":
            run_date = args["once"]["date"].split(" ")[0] + " " + args["once"]["time"]
            scheduler_timing_modify(args["id"], args["product_id"], user, run_date)
        if args["scheduler"] == "period":
            scheduler_interval_modify(args["id"], args["product_id"], user,  args["period"]["interval"],
                                      args["period"]["type"])
        if status is not True:
            logger.error("Modify period_task error: %s" % result)
            return {"status": False, "message": result}, 500
        audit_log(user, period_id, "", "period_task", "edit")
        return {"status": True, "message": ""}, 200


class PeriodList(Resource):
    @access_required(role_dict["common_user"])
    def get(self):
        product_id = request.args.get("product_id")
        scheduler_type = request.args.get("scheduler_type")
        db = DB()
        task = []
        if scheduler_type:
            sql = "where data -> '$.product_id'='%s' and data -> '$.scheduler'!='%s' " \
                  "order by data -> '$.timestamp' desc" % (product_id, scheduler_type)
        else:
            sql = "where data -> '$.product_id'='%s' order by data -> '$.timestamp' desc" % product_id
        status, result = db.select("period_task", sql)
        if status is True:
            for period in result:
                target = []
                for group_id in period.get("target"):
                    group_status, group_result = db.select_by_id("groups", group_id)
                    if group_status is True:
                        target.append({"id": group_id, "name": group_result.get("name")})
                period["target"] = target
                period_audit_status, period_audit_result = db.select(
                    "period_audit", "where data -> '$.id'='%s' order by data -> '$.result.timestamp' desc limit 1" %
                                    period["id"])
                period["audit"].extend(period_audit_result)
                task.append(period)
            db.close_mysql()
            return {"data": task, "status": True, "message": ""}, 200
        else:
            return {"status": False, "message": task}, 500

    @access_required(role_dict["common_user"])
    def post(self):
        args = parser.parse_args()
        args["id"] = uuid_prefix("t")
        user = g.user_info["username"]
        period_task = args
        period_task["timestamp"] = int(time.time())
        period_task["result"] = []
        period_task["audit"] = []
        period_task["status"] = {
            "id": 1,
            "name": period_status.get(1)
        }
        period_task["count"] = 0
        period_task["step"] = 0
        audit = {
            "timestamp": int(time.time()),
            "user": user,
            "option": period_audit.get(0)
        }
        insert_period_audit(args["id"], audit)
        if args["once"]["date"]:
            args["once"]["date"] = utc_to_local(args["once"]["date"])
        db = DB()
        status, result = db.select("period_task", "where data -> '$.name'='%s' and data -> '$.product_id'='%s'"
                                   % (args["name"], args["product_id"]))
        if status is True:
            if len(result) == 0:
                audit_log(user, args["id"], "", "period_task", "add")
                # 一次立即执行的直接扔给celery
                if args["scheduler"] == "once" and args["once"]["type"] == "now":
                    period_task["action"] = "concurrent_play"
                    job.delay(args["id"], args["product_id"], user)
                # 一次定时执行的扔给APScheduler,进行定时处理
                if args["scheduler"] == "once" and args["once"]["type"] == "timing":
                    period_task["action"] = "scheduler_resume"
                    run_date = args["once"]["date"].split(" ")[0] + " " + args["once"]["time"]
                    scheduler_result = scheduler_timing_add(args["id"], args["product_id"], user, run_date)
                    if scheduler_result.get("status") is not True:
                        return {"status": False, "message": scheduler_result.get("message")}, 500
                # 周期性的扔给APScheduler,进行定时处理
                if args["scheduler"] == "period":
                    period_task["action"] = "scheduler_resume"
                    scheduler_result = scheduler_interval_add(args["id"], args["product_id"],
                                                              user, args["period"]["interval"], args["period"]["type"])
                    if scheduler_result.get("status") is not True:
                        return {"status": False, "message": scheduler_result.get("message")}, 500
                insert_status, insert_result = db.insert("period_task", json.dumps(period_task, ensure_ascii=False))
                db.close_mysql()
                if insert_status is not True:
                    logger.error("Add period_task error: %s" % insert_result)
                    return {"status": False, "message": insert_result}, 500
                return {"status": True, "message": ""}, 201
            else:
                db.close_mysql()
                return {"status": False, "message": "The period_task name already exists"}, 200
        else:
            db.close_mysql()
            logger.error("Select period_task name error: %s" % result)
            return {"status": False, "message": result}, 500


class Reopen(Resource):
    @access_required(role_dict["common_user"])
    def put(self, period_id):
        product_id = request.args.get("product_id")
        user = g.user_info["username"]
        db = DB()
        status, result = db.select_by_id("period_task", period_id)
        if status is True:
            if result:
                if result["scheduler"] == "once" and result["once"]["type"] == "now":
                    # 重开之前清空已经执行过的minion
                    result["count"] = 0
                    result["step"] = 0
                    audit = {
                        "timestamp": int(time.time()),
                        "user": user,
                        "option": period_audit.get(1)
                    }
                    insert_period_audit(period_id, audit)
                    update_status, update_result = db.update_by_id("period_task",
                                                                   json.dumps(result, ensure_ascii=False),
                                                                   period_id)
                    if update_status is not True:
                        logger.error("Reopen period_task error: %s" % update_result)
                        db.close_mysql()
                        return {"status": False, "message": update_result}, 500

                    audit_log(user, period_id, product_id, "period_task", "reopen")
                    job.delay(period_id, product_id, user)
                    db.close_mysql()
                    return {"status": True, "message": ""}, 200
            else:
                db.close_mysql()
                return {"status": False, "message": "The period_task does not exist"}, 404
        else:
            db.close_mysql()
            return {"status": False, "message": result}, 500


class ConcurrentPause(Resource):
    @access_required(role_dict["common_user"])
    def put(self, period_id):
        product_id = request.args.get("product_id")
        user = g.user_info["username"]
        db = DB()
        status, result = db.select_by_id("period_task", period_id)
        if status is True:
            result["action"] = "concurrent_pause"
            audit = {
                "timestamp": int(time.time()),
                "user": user,
                "option": period_audit.get(5)
            }
            insert_period_audit(period_id, audit)
            update_status, update_result = db.update_by_id("period_task", json.dumps(result, ensure_ascii=False),
                                                           period_id)
            if update_status is not True:
                logger.error("Pause period_task error: %s" % update_result)
                db.close_mysql()
                return {"status": False, "message": update_result}, 500
            audit_log(user, period_id, product_id, "period_task", "pause")
            return {"status": True, "message": ""}, 200
        else:
            db.close_mysql()
            return {"status": False, "message": result}, 500


class ConcurrentPlay(Resource):
    @access_required(role_dict["common_user"])
    def put(self, period_id):
        product_id = request.args.get("product_id")
        user = g.user_info["username"]
        db = DB()
        status, result = db.select_by_id("period_task", period_id)
        if status is True:
            result["action"] = "concurrent_play"
            audit = {
                "timestamp": int(time.time()),
                "user": user,
                "option": period_audit.get(2)
            }
            insert_period_audit(period_id, audit)
            update_status, update_result = db.update_by_id("period_task", json.dumps(result, ensure_ascii=False),
                                                           period_id)
            if update_status is not True:
                logger.error("Pause period_task error: %s" % update_result)
                db.close_mysql()
                return {"status": False, "message": update_result}, 500
            if result["scheduler"] == "once" and result["once"]["type"] == "now":
                job.delay(period_id, product_id, user)
            audit_log(user, period_id, product_id, "period_task", "pause")
            return {"status": True, "message": ""}, 200
        else:
            db.close_mysql()
            return {"status": False, "message": result}, 500


class SchedulerPause(Resource):
    @access_required(role_dict["common_user"])
    def put(self, period_id):
        product_id = request.args.get("product_id")
        user = g.user_info["username"]
        db = DB()
        status, result = db.select_by_id("period_task", period_id)
        if status is True:
            result["action"] = "scheduler_pause"
            result["status"] = {
                "id": 11,
                "name": period_status.get(11)
            }
            audit = {
                "timestamp": int(time.time()),
                "user": user,
                "option": period_audit.get(11)
            }
            insert_period_audit(period_id, audit)
            update_status, update_result = db.update_by_id("period_task", json.dumps(result, ensure_ascii=False),
                                                           period_id)
            if update_status is not True:
                logger.error("Scheduler Pause period_task error: %s" % update_result)
                db.close_mysql()
                return {"status": False, "message": update_result}, 500
            scheduler_result = scheduler_pause(period_id)
            if scheduler_result.get("status") is not True:
                return {"status": False, "message": scheduler_result.get("message")}, 500
            audit_log(user, period_id, product_id, "period_task", "scheduler pause")
            return {"status": True, "message": ""}, 200
        else:
            db.close_mysql()
            return {"status": False, "message": result}, 500


class SchedulerResume(Resource):
    @access_required(role_dict["common_user"])
    def put(self, period_id):
        product_id = request.args.get("product_id")
        user = g.user_info["username"]
        db = DB()
        status, result = db.select_by_id("period_task", period_id)
        if status is True:
            result["action"] = "scheduler_resume"
            result["status"] = {
                "id": 9,
                "name": period_status.get(9)
            }
            audit = {
                "timestamp": int(time.time()),
                "user": user,
                "option": period_audit.get(10)
            }
            insert_period_audit(period_id, audit)
            update_status, update_result = db.update_by_id("period_task", json.dumps(result, ensure_ascii=False),
                                                           period_id)
            if update_status is not True:
                logger.error("Pause period_task error: %s" % update_result)
                db.close_mysql()
                return {"status": False, "message": update_result}, 500
            scheduler_result = scheduler_resume(period_id)
            if scheduler_result.get("status") is not True:
                return {"status": False, "message": scheduler_result.get("message")}, 500
            audit_log(user, period_id, product_id, "period_task", "scheduler resume")
            return {"status": True, "message": ""}, 200
        else:
            db.close_mysql()
            return {"status": False, "message": result}, 500

