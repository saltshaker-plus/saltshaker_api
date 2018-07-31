# -*- coding:utf-8 -*-
from flask_restful import Resource, reqparse
from common.db import DB
from flask import g
from tasks.tasks import event_to_mysql
import os
from common.log import loggers
import ast

logger = loggers()

parser = reqparse.RequestParser()
parser.add_argument("action", type=str, required=True, trim=True)


class SSE(Resource):
    def get(self):
        args = parser.parse_args()
        action = args["action"]
        if action == "start":
            db = DB()
            status, result = db.select("product", "")
            db.close_mysql()
            if status is True:
                if result:
                    for product in result:
                        event_to_mysql.delay(product['id'])
                    return {"data": "", "status": True, "message": ""}, 200
                else:
                    return {"data": "", "status": False, "message": "Product does not exist"}, 404
            else:
                return {"data": "", "status": False, "message": result}, 500
        if action == "stop":
            echo = os.popen("celery -A app.celery inspect active --json")
            info = echo.readline()
            try:
                result = eval(info.replace("true", "'true'").replace("false", "'false'"))
                for k, v in result.items():
                    for w in v:
                        os.popen("kill -9 %s" % w.get("worker_pid"))
                return {"data": "", "status": True, "message": ""}, 200
            except Exception as e:
                logger.error("Stop celery error: %s" % e)
                return {"data": "", "status": False, "message": "%s" % e}, 200


class SSEStatus(Resource):
    def get(self):
        db = DB()
        status, result = db.select("product", "")
        db.close_mysql()
        if status is True:
            product_count = len(result)
        else:
            return {"data": "", "status": False, "message": result}, 500
        status = []
        pid = []
        echo = os.popen("celery -A app.celery inspect active --json")
        info = echo.readline()
        if not info:
            status.append({
                "service": "Event",
                "status": "Down",
                "pid": []
            })
            logger.error("Get celery error: %s" % info)
            return {"data": status, "status": True, "message": "%s" % info}, 200
        try:
            result = eval(info.replace("true", "'true'").replace("false", "'false'"))
            for k, v in result.items():
                if len(v) == product_count:
                    for w in v:
                        pid.append(w.get("worker_pid"))
                    status.append({
                        "service": "Event",
                        "status": "Up",
                        "pid": pid
                    })
                    return {"data": status, "status": True, "message": ""}, 200
                elif len(v) < product_count:
                    for w in v:
                        pid.append(w.get("worker_pid"))
                    status.append({
                        "service": "Event",
                        "status": "Missing",
                        "pid": pid
                    })
                    return {"data": status, "status": True, "message": ""}, 200
                elif len(v) > product_count:
                    for w in v:
                        pid.append(w.get("worker_pid"))
                    status.append({
                        "service": "Event",
                        "status": "More",
                        "pid": pid
                    })
                    return {"data": status, "status": True, "message": ""}, 200
        except Exception as e:
            status.append({
                "service": "Event",
                "status": "Down",
                "pid": []
            })
            logger.error("Get celery error: %s" % e)
            return {"data": status, "status": False, "message": "%s" % e}, 200
