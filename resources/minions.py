# -*- coding:utf-8 -*-
from flask_restful import Resource, reqparse, request
from flask import g
from common.log import loggers
from common.audit_log import audit_log
from common.utility import salt_api_for_product
from common.sso import access_required
from common.const import role_dict
from system.host import Hosts
from common.db import DB
import json
from tasks.tasks import grains

logger = loggers()

parser = reqparse.RequestParser()
parser.add_argument("product_id", type=str, required=True, trim=True)
parser.add_argument("action", type=str, trim=True)
parser.add_argument("minion_id", type=str, trim=True, action="append")
parser.add_argument("minion", type=str, trim=True)
parser.add_argument("item", type=str, trim=True)


class MinionsStatus(Resource):
    @access_required(role_dict["common_user"])
    def get(self):
        args = parser.parse_args()
        salt_api = salt_api_for_product(args["product_id"])
        minion_status = []
        if isinstance(salt_api, dict):
            return salt_api, 500
        else:
            result = salt_api.runner_status("status")
            if isinstance(result, dict):
                if result.get("status") is False:
                    return result, 500
                for minion in result.get("up"):
                    minion_status.append({"status": "up", "minions_id": minion})
                for minion in result.get("down"):
                    minion_status.append({"status": "down", "minions_id": minion})
            else:
                logger.error("Get minion status error: %s" % result)
            return {"data": minion_status, "status": True, "message": ""}, 200


class MinionsKeys(Resource):
    @access_required(role_dict["common_user"])
    def get(self):
        args = parser.parse_args()
        salt_api = salt_api_for_product(args["product_id"])
        minion_key = []
        if isinstance(salt_api, dict):
            return salt_api, 500
        else:
            result = salt_api.list_all_key()
            if isinstance(result, dict):
                if result.get("status") is False:
                    return result, 500
                for minions_rejected in result.get("minions_rejected"):
                    minion_key.append({"minions_status": "Rejected", "minions_id": minions_rejected})
                for minions_denied in result.get("minions_denied"):
                    minion_key.append({"minions_status": "Denied", "minions_id": minions_denied})
                for minions in result.get("minions"):
                    minion_key.append({"minions_status": "Accepted", "minions_id": minions})
                for minions_pre in result.get("minions_pre"):
                    minion_key.append({"minions_status": "Unaccepted", "minions_id": minions_pre})
            else:
                logger.error("Get minion key error: %s" % result)
            return {"data": minion_key, "status": True, "message": ""}, 200

    @access_required(role_dict["common_user"])
    def post(self):
        args = parser.parse_args()
        salt_api = salt_api_for_product(args["product_id"])
        user = g.user_info["username"]
        if isinstance(salt_api, dict):
            return salt_api
        else:
            result_list = []
            if args["action"] and args["minion_id"]:
                if args["action"] == "accept":
                    for minion in args["minion_id"]:
                        result = salt_api.accept_key(minion)
                        result_list.append({minion: result})
                        audit_log(user, minion, args["product_id"], "minion", "accept")
                    # 添加host
                    Hosts.add_host(args["minion_id"], args["product_id"], user)
                    return {"status": True, "message": result_list}, 200
                if args["action"] == "reject":
                    for minion in args["minion_id"]:
                        result = salt_api.reject_key(minion)
                        result_list.append({minion: result})
                        audit_log(user, minion, args["product_id"], "minion", "reject")
                    # 拒绝host
                    # Hosts.reject_host(args["minion_id"], args["product_id"], user)
                    return {"status": True, "message": result_list}, 200
                if args["action"] == "delete":
                    for minion in args["minion_id"]:
                        result = salt_api.delete_key(minion)
                        result_list.append({minion: result})
                        audit_log(user, minion, args["product_id"], "minion", "delete")
                    # 删除host
                    Hosts.delete_host(args["minion_id"], args["product_id"], user)
                    return {"status": True, "message": result_list}, 200
            else:
                return {"status": False,
                        "message": "The specified action or minion_id parameter does not exist"}, 400


class MinionsGrains(Resource):
    @access_required(role_dict["common_user"])
    def get(self):
        args = parser.parse_args()
        salt_api = salt_api_for_product(args["product_id"])
        if isinstance(salt_api, dict):
            return salt_api, 500
        else:
            if args["minion"]:
                if args["item"]:
                    result = salt_api.grain(args["minion"], args["item"])
                    if result:
                        result.update({"status": True, "message": ""})
                        return result
                    return {"status": False, "message": "The specified minion does not exist"}, 404
                else:
                    result = salt_api.grains(args["minion"])
                    if result:
                        # create_grains(args["product_id"])
                        data = {"data": result, "status": True, "message": ""}
                        return data
                    return {"status": False, "message": "The specified minion does not exist"}, 404
            else:
                return {"status": False, "message": "The specified minion parameter does not exist"}, 400


class MinionsGrainsList(Resource):
    @access_required(role_dict["common_user"])
    def get(self):
        product_id = request.args.get("product_id")
        db = DB()
        status, result = db.select("grains", "where data -> '$.product_id'='%s'" % product_id)
        db.close_mysql()
        if status is True:
            return {"data": result, "status": True, "message": ""}, 200
        else:
            return {"status": False, "message": result}, 500


class Grains(object):
    @staticmethod
    def create_grains(minion_list, product_id, user):
        grains.delay(minion_list, product_id)
        audit_log(user, "", product_id, "grains", "update")

    @staticmethod
    def delete_grains(minion_list, product_id, user):
        db = DB()
        for minion in minion_list:
            db.delete_by_id("grains", minion)
            audit_log(user, minion, product_id, "grains", "delete")
        db.close_mysql()
