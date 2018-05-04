# -*- coding:utf-8 -*-
from flask_restful import Resource, reqparse, request
from common.log import loggers
from common.audit_log import audit_log
from common.utility import salt_api_for_product
from common.sso import access_required
from common.db import DB
from common.const import role_dict
from flask import g
import json
import time

logger = loggers()

parser = reqparse.RequestParser()
parser.add_argument("product_id", type=str, required=True, trim=True)
parser.add_argument("minion_id", type=str, required=True, trim=True, action="append")
parser.add_argument("command", type=str, default="", trim=True)
parser.add_argument("item", type=str, default=[], trim=True, action="append")


class PillarItems(Resource):
    @access_required(role_dict["common_user"])
    def post(self):
        args = parser.parse_args()
        minion_id = args["minion_id"]
        salt_api = salt_api_for_product(args["product_id"])
        user_info = g.user_info
        audit_log(user_info["username"], minion_id, args["product_id"], "minion", "pillar")
        if isinstance(salt_api, dict):
            return salt_api, 500
        result = salt_api.pillar_items(minion_id, args["item"])
        db = DB()
        cmd_history = {
            "user_id": user_info["id"],
            "product_id": args["product_id"],
            "command": "pillar.items",
            "type": "pillar",
            "minion_id": minion_id,
            "result": result,
            "time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        }
        db.insert("cmd_history", json.dumps(cmd_history, ensure_ascii=False))
        db.close_mysql()
        audit_log(user_info["username"], minion_id, args["product_id"], "minion", "sls")

        minion_count = str(len(minion_id))
        cmd_succeed = str(len(result))
        cmd_failure = str(len(minion_id) - len(result))
        succeed_minion = []
        for i in result:
            succeed_minion.append(i)
        failure_minion = ','.join(
            list(set(minion_id).difference(set(succeed_minion))))
        if result.get("status") is False:
            status = False
            message = result.get("message")
        else:
            status = True
            message = ""
        return {"data": {"result": result,
                         "command": "pillar.items",
                         "total": minion_count,
                         "succeed": cmd_succeed,
                         "failure": cmd_failure,
                         "failure_minion": failure_minion}, "status": status, "message": message}, 200
