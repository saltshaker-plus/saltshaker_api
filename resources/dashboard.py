# -*- coding:utf-8 -*-
from flask_restful import Resource, reqparse
from common.log import loggers
from common.sso import access_required
from common.db import DB
from common.const import role_dict
from collections import Counter
from common.utility import salt_api_for_product


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
        host_status, host_result = db.select("host", "where data -> '$.product_id'='%s'" % args["product_id"])
        event_status, event_result = db.select("event", "where data -> '$.data.product_id'='%s'" % args["product_id"])
        period_status, period_result = db.select("period_task", "where data -> '$.product_id'='%s'" % args["product_id"])
        log_status, log_result = db.select("period_task", "where data -> '$.product_id'='%s'" % args["product_id"])
        db.close_mysql()
        data["minion"] = len(host_result)
        data["period"] = len(period_result)
        data["event"] = len(event_result)
        data["log"] = len(log_result)
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
                "title": ["Accepted", "Up", "Down", "Rejected", "Unaccepted"],
                "series": [
                    {"value": len(key_result.get("minions")), "name": 'Accepted',
                     "itemStyle": {"normal": {"color": '#f0e334'}}},
                    {"value": 400, "name": 'Up', "itemStyle":
                        {"normal": {"color": '#64d572'}}},
                    {"value": 0, "name": 'Down', "itemStyle":
                        {"normal": {"color": '#f25e43'}}},
                    {"value": len(key_result.get("minions_rejected")), "name": 'Rejected',
                     "itemStyle": {"normal": {"color": '#ffd572'}}},
                    {"value": len(key_result.get("minions_pre")), "name": 'Unaccepted',
                     "itemStyle": {"normal": {"color": '#2d8cf0'}}}
                ],
            }
            return {"data": data, "status": True, "message": ""}, 200
