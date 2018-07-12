# -*- coding:utf-8 -*-
from flask_restful import Resource, reqparse
from flask import g
from common.log import loggers
from common.db import DB
from common.sso import access_required
from system.host import Hosts
from common.utility import salt_api_for_product
from common.const import role_dict
from resources.minions import Grains

logger = loggers()

parser = reqparse.RequestParser()
parser.add_argument("product_id", type=str, required=True, trim=True)


class HostSync(Resource):
    @access_required(role_dict["common_user"])
    def get(self):
        user = g.user_info["username"]
        args = parser.parse_args()
        salt_api = salt_api_for_product(args["product_id"])
        minions = []
        minions_mysql = []
        if isinstance(salt_api, dict):
            return salt_api, 500
        else:
            result = salt_api.list_all_key()
            if result:
                if result.get("status") is False:
                    return result, 500
                for minion in result.get("minions"):
                    minions.append(minion)
        # 根据已经同意的minion添加host
        Hosts.add_host(minions, args["product_id"], user)
        db = DB()
        status, result = db.select("host", "where data -> '$.product_id'='%s'" % args["product_id"])
        db.close_mysql()
        if status is True and result:
            for i in result:
                minions_mysql.append(i.get("minion_id"))
        # 对比数据库中的minion与已经同意的minion的不同，删掉数据库中多余的minion
        diff = list(set(minions_mysql).difference(minions))
        Hosts.delete_host(diff, args["product_id"], user)
        return {"status": True, "message": ""}, 200


class GrainsSync(Resource):
    @access_required(role_dict["common_user"])
    def get(self):
        user = g.user_info["username"]
        args = parser.parse_args()
        salt_api = salt_api_for_product(args["product_id"])
        minions = []
        minions_mysql = []
        if isinstance(salt_api, dict):
            return salt_api, 500
        else:
            result = salt_api.list_all_key()
            if result:
                if result.get("status") is False:
                    return result, 500
                for minion in result.get("minions"):
                    minions.append(minion)
        # 同步产品线下的Grains
        Grains.create_grains(minions, args["product_id"], user)
        db = DB()
        status, result = db.select("grains", "where data -> '$.product_id'='%s'" % args["product_id"])
        db.close_mysql()
        if status is True and result:
            for i in result:
                minions_mysql.append(i.get("id"))
        # 对比数据库中的minion与已经同意的minion的不同，删掉数据库中多余的minion
        diff = list(set(minions_mysql).difference(minions))
        Grains.delete_grains(diff, args["product_id"], user)
        return {"status": True, "message": ""}, 200
