# -*- coding:utf-8 -*-
from flask_restful import Resource, reqparse
from common.log import loggers
from common.sso import access_required
from common.db import DB
from common.const import role_dict
from collections import Counter


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
        args = parser.parse_args()
        status, result = db.select("event", "where data -> '$.data.product_id'='%s'" % args["product_id"])
        db.close_mysql()
        if status is True:
            if result:
                return {"events": {"event": result}, "status": True, "message": ""}, 200
            else:
                return {"status": False, "message": "Even does not exist"}, 404
        else:
            return {"status": False, "message": result}, 500
