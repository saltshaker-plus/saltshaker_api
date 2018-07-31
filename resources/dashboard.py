# -*- coding:utf-8 -*-
from flask_restful import Resource, reqparse
from common.log import loggers
from common.sso import access_required
from common.db import DB
from common.const import role_dict
from collections import Counter
from common.utility import salt_api_for_product
import os

logger = loggers()

parser = reqparse.RequestParser()
parser.add_argument("product_id", type=str, required=True, trim=True)


class GrainsStatistics(Resource):
    @access_required(role_dict["common_user"])
    def get(self, item):
        db = DB()
        args = parser.parse_args()
        status, result = db.select("grains", "where data -> '$.product_id'='%s'" % args["product_id"])
        db.close_mysql()
        info = []
        legend_data = []
        series_data = []
        data = {
            "legendData": legend_data,
            "seriesData": series_data
        }
        if status is True and result:
            if item == "os":
                for grains in result:
                    info.append("%s %s" % (grains.get("os"), grains.get("osrelease")))
                    statistics = Counter(info)
            elif item == "saltversion":
                for grains in result:
                    info.append(grains.get("saltversion"))
                    statistics = Counter(info)
            elif item == "kernelrelease":
                for grains in result:
                    info.append(grains.get("kernelrelease"))
                    statistics = Counter(info)
            elif item == "manufacturer":
                for grains in result:
                    info.append(grains.get("manufacturer"))
                    statistics = Counter(info)
            elif item == "productname":
                for grains in result:
                    info.append(grains.get("productname"))
                    statistics = Counter(info)
            elif item == "num_cpus":
                for grains in result:
                    info.append(grains.get("num_cpus"))
                    statistics = Counter(info)
            elif item == "cpu_model":
                for grains in result:
                    info.append(grains.get("cpu_model"))
                    statistics = Counter(info)
            elif item == "mem_total":
                for grains in result:
                    info.append(grains.get("mem_total"))
                    statistics = Counter(info)
            else:
                return {"status": False, "message": "The specified item parameter is null "
                                                    "or not incorrect parameters"}, 500
            for k, v in statistics.items():
                legend_data.append(k)
                series_data.append({"name": k, "value": v})
            data = {
                "legendData": legend_data,
                "seriesData": series_data
            }
            return {"data": data, "status": True, "message": ""}, 200
        elif status is False:
            return {"status": False, "message": result}, 500
        else:
            return {"data": data, "status": True, "message": ""}, 200


class TitleInfo(Resource):
    @access_required(role_dict["common_user"])
    def get(self):
        db = DB()
        data = {
            "minion": None,
            "period": None,
            "event": None,
            "log": None
        }
        args = parser.parse_args()
        host_status, host_result = db.select_count("host", "product_id", args["product_id"])
        event_status, event_result = db.select_count("event", "data.product_id", args["product_id"])
        period_status, period_result = db.select("period_task",
                                                 "where data -> '$.product_id'='%s' and "
                                                 "data -> '$.scheduler'!='once'" % args["product_id"])
        log_status, log_result = db.select_count("audit_log", "product_id", args["product_id"])
        db.close_mysql()
        data["minion"] = host_result
        data["period"] = len(period_result)
        data["event"] = event_result
        data["log"] = log_result
        return {"data": data, "status": True, "message": ""}, 200


class Minion(Resource):
    @access_required(role_dict["common_user"])
    def get(self):
        args = parser.parse_args()
        salt_api = salt_api_for_product(args["product_id"])
        if isinstance(salt_api, dict):
            return salt_api, 500
        else:
            key_result = salt_api.list_all_key()
            if key_result:
                if key_result.get("status") is False:
                    return key_result, 500
            # status_result = salt_api.runner_status("status")
            # if status_result:
            #     if status_result.get("status") is False:
            #         return status_result, 500
            data = {
                "title": ["Accepted", "Rejected", "Unaccepted"],
                "series": [
                    {"value": len(key_result.get("minions")), "name": 'Accepted',
                     "itemStyle": {"normal": {"color": '#f0e334'}}},
                    # {"value": 40, "name": 'Up', "itemStyle":
                    #     {"normal": {"color": '#64d572'}}},
                    # {"value": 0, "name": 'Down', "itemStyle":
                    #     {"normal": {"color": '#f25e43'}}},
                    {"value": len(key_result.get("minions_rejected")), "name": 'Rejected',
                     "itemStyle": {"normal": {"color": '#ffd572'}}},
                    {"value": len(key_result.get("minions_pre")), "name": 'Unaccepted',
                     "itemStyle": {"normal": {"color": '#2d8cf0'}}}
                ],
            }
            return {"data": data, "status": True, "message": ""}, 200


class ServiceStatus(Resource):
    @access_required(role_dict["common_user"])
    def get(self):
        status = []
        args = parser.parse_args()
        salt_api = salt_api_for_product(args["product_id"])
        if isinstance(salt_api, dict):
            return salt_api, 500
        else:
            cherry_result = salt_api.stats()
            if isinstance(cherry_result, dict):
                if cherry_result.get("CherryPy Applications").get("Enabled") is True:
                    status.append({
                        "name": "Cherry",
                        "status": "UP"
                    })
            else:
                status.append({
                    "name": "Cherry",
                    "status": "Down"
                })
            master_status = salt_api.list_all_key()
            if master_status.get("status") is not False:
                status.append({
                    "name": "Master",
                    "status": "UP"
                })
            else:
                status.append({
                    "name": "Master",
                    "status": "Down"
                })
        echo = os.popen("ps aux|grep app.celery|grep -v grep |wc -l")
        try:
            num = int(echo.readline().split('\n')[0])
            if num == 0:
                status.append({
                    "name": "Celery",
                    "status": "Down"
                })
            else:
                status.append({
                    "name": "Celery",
                    "status": "Up"
                })
        except Exception as e:
            status.append({
                "name": "Celery",
                "status": "Down"
            })
            logger.error("Get celery error: %s" % e)
        return {"data": status, "status": True, "message": ""}, 200
