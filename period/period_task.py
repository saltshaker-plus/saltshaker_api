# -*- coding:utf-8 -*-
from flask_restful import Resource, reqparse, request
from flask import g
from common.log import loggers
from common.audit_log import audit_log
from common.db import DB
from common.utility import uuid_prefix
from common.sso import access_required
from common.const import role_dict
from tasks.tasks import once
from common.const import period_status, period_audit
from common.utility import utc_to_local
import json
import time
from scheduler.period_scheduler import scheduler_timing_add, scheduler_timing_modify, scheduler_delete

logger = loggers()

parser = reqparse.RequestParser()
parser.add_argument("product_id", type=str, required=True, trim=True)
parser.add_argument("name", type=str, required=True, trim=True)
parser.add_argument("description", type=str, required=True, trim=True)
parser.add_argument("concurrent", type=int, default=0, trim=True)
parser.add_argument("interval", type=int, default=60, trim=True)
parser.add_argument("period", type=str, default="once", trim=True)
parser.add_argument("time_type", type=str, default="now", trim=True)
parser.add_argument("time", type=str, default="", trim=True)
parser.add_argument("date", type=str, default="", trim=True)
parser.add_argument("cron", type=str, default="", trim=True)
parser.add_argument("type", type=str, default="", trim=True)
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
                period_result_status, period_result_result = db.select("period_result",
                                                                       "where data -> '$.id'='%s'" % result["id"])
                if period_result_status is True:
                    for r in period_result_result:
                        result["result"].append(r.get("result"))
                db.close_mysql()
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
        status, result = db.delete_by_id("period_task", period_id)
        if status is not True:
            logger.error("Delete period_task error: %s" % result)
            return {"status": False, "message": result}, 500
        if result is 0:
            return {"status": False, "message": "%s does not exist" % period_id}, 404
        period_result_status, period_result_result = db.delete_by_id("period_result",  period_id)
        if period_result_status is not True:
            logger.error("Delete period_result error: %s" % result)
            return {"status": False, "message": result}, 500
        db.close_mysql()
        # 删除定期任务的时候删除对应的调度
        scheduler_delete(period_id)
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
        period_task["audit"] = select_result["audit"]
        args["date"] = utc_to_local(args["date"])
        status, result = db.update_by_id("period_task", json.dumps(period_task, ensure_ascii=False), period_id)
        db.close_mysql()
        if args["period"] == "once" and args["time_type"] == "timing":
            run_date = args["date"].split(" ")[0] + " " + args["time"]
            scheduler_timing_modify(args["id"], args["product_id"], user, run_date)
        if status is not True:
            logger.error("Modify period_task error: %s" % result)
            return {"status": False, "message": result}, 500
        audit_log(user, period_id, "", "period_task", "edit")
        return {"status": True, "message": ""}, 200


class PeriodList(Resource):
    @access_required(role_dict["common_user"])
    def get(self):
        product_id = request.args.get("product_id")
        db = DB()
        task = []
        status, result = db.select("period_task", "where data -> '$.product_id'='%s' "
                                                  "order by data -> '$.timestamp' desc" % product_id)
        if status is True:
            for period in result:
                target = []
                for group_id in period.get("target"):
                    group_status, group_result = db.select_by_id("groups", group_id)
                    if group_status is True:
                        target.append({"id": group_id, "name": group_result.get("name")})
                period["target"] = target
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
        period_task["timestamp"] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        period_task["result"] = []
        period_task["status"] = {
            "id": 0,
            "name": period_status.get(0)
        }
        period_task["executed_minion"] = []
        period_task["audit"] = [{
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
            "user": user,
            "option": period_audit.get(0)
        }]
        args["date"] = utc_to_local(args["date"])
        db = DB()
        status, result = db.select("period_task", "where data -> '$.name'='%s' and data -> '$.product_id'='%s'"
                                   % (args["name"], args["product_id"]))
        if status is True:
            if len(result) == 0:
                insert_status, insert_result = db.insert("period_task", json.dumps(period_task, ensure_ascii=False))
                db.close_mysql()
                if insert_status is not True:
                    logger.error("Add period_task error: %s" % insert_result)
                    return {"status": False, "message": insert_result}, 500
                audit_log(user, args["id"], "", "period_task", "add")
                # 一次立即执行的直接扔给celery
                if args["period"] == "once" and args["time_type"] == "now":
                    once.delay(args["id"], args["product_id"], user)
                # 一次定时执行的扔给APScheduler,进行定时处理
                if args["period"] == "once" and args["time_type"] == "timing":
                    run_date = args["date"].split(" ")[0] + " " + args["time"]
                    scheduler_timing_add(args["id"], args["product_id"], user, run_date)
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
                if result["period"] == "once" and result["time_type"] == "now":
                    # 重开之前清空已经执行过的minion
                    result["executed_minion"] = []
                    result["audit"].append({
                        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                        "user": user,
                        "option": period_audit.get(1)
                    })
                    update_status, update_result = db.update_by_id("period_task",
                                                                   json.dumps(result, ensure_ascii=False),
                                                                   period_id)
                    if update_status is not True:
                        logger.error("Reopen period_task error: %s" % update_result)
                        db.close_mysql()
                        return {"status": False, "message": update_result}, 500

                    audit_log(user, period_id, "", "period_task", "reopen")
                    once.delay(period_id, product_id, user)
                    db.close_mysql()
                    return {"status": True, "message": ""}, 200
            else:
                db.close_mysql()
                return {"status": False, "message": "The period_task does not exist"}, 404
        else:
            db.close_mysql()
            return {"status": False, "message": result}, 500


class Pause(Resource):
    @access_required(role_dict["common_user"])
    def put(self, period_id):
        user = g.user_info["username"]
        db = DB()
        status, result = db.select_by_id("period_task", period_id)
        if status is True:
            result["action"] = "pause"
            result["audit"].append({
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                "user": user,
                "option": period_audit.get(5)
            })
            update_status, update_result = db.update_by_id("period_task", json.dumps(result, ensure_ascii=False),
                                                           period_id)
            if update_status is not True:
                logger.error("Pause period_task error: %s" % update_result)
                db.close_mysql()
                return {"status": False, "message": update_result}, 500
            audit_log(user, period_id, "", "period_task", "pause")
            return {"status": True, "message": ""}, 200
        else:
            db.close_mysql()
            return {"status": False, "message": result}, 500


class Play(Resource):
    @access_required(role_dict["common_user"])
    def put(self, period_id):
        product_id = request.args.get("product_id")
        user = g.user_info["username"]
        db = DB()
        status, result = db.select_by_id("period_task", period_id)
        if status is True:
            result["action"] = "play"
            result["audit"].append({
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                "user": user,
                "option": period_audit.get(2)
            })
            update_status, update_result = db.update_by_id("period_task", json.dumps(result, ensure_ascii=False),
                                                           period_id)
            if update_status is not True:
                logger.error("Pause period_task error: %s" % update_result)
                db.close_mysql()
                return {"status": False, "message": update_result}, 500
            if result["period"] == "once" and result["time_type"] == "now":
                once.delay(period_id, product_id, user)
            audit_log(user, period_id, "", "period_task", "pause")
            return {"status": True, "message": ""}, 200
        else:
            db.close_mysql()
            return {"status": False, "message": result}, 500
