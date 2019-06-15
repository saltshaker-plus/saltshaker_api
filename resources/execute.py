# -*- coding:utf-8 -*-
from flask_restful import Resource, reqparse, request
from common.log import loggers
from common.audit_log import audit_log
from common.utility import salt_api_for_product
from common.sso import access_required
from common.db import DB
from common.const import role_dict
from flask import g
import re
import json
import time

logger = loggers()

parser = reqparse.RequestParser()
parser.add_argument("product_id", type=str, required=True, trim=True)
parser.add_argument("minion_id", type=str, required=True, trim=True, action="append")
parser.add_argument("command", type=str, default="", trim=True)
parser.add_argument("sls", type=str, default="", trim=True)


class ExecuteShell(Resource):
    @access_required(role_dict["common_user"])
    def post(self):
        args = parser.parse_args()
        command = args["command"]
        if not command:
            return {"status": False,
                    "message": "The specified command parameter does not exist"}, 400
        minion_id = args["minion_id"]
        salt_api = salt_api_for_product(args["product_id"])
        user_info = g.user_info
        if isinstance(salt_api, dict):
            return salt_api, 500
        acl_list = user_info["acl"]
        # 验证 acl
        status = verify_acl(acl_list, command)
        # acl deny 验证完成后执行命令
        if status["status"]:
            result = salt_api.shell_remote_execution(minion_id, command)
            # 记录历史命令
            db = DB()
            cmd_history = {
                "user_id": user_info["id"],
                "product_id": args["product_id"],
                "command": command,
                "type": "shell",
                "minion_id": minion_id,
                "result": result,
                "time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            }
            db.insert("cmd_history", json.dumps(cmd_history, ensure_ascii=False))
            db.close_mysql()
            audit_log(user_info["username"], minion_id, args["product_id"], "minion", "shell")

            minion_count = str(len(minion_id))
            result_len = len(result)
            for k, v in result.items():
                if not v:
                    result_len -= 1
            cmd_succeed = str(result_len)
            cmd_failure = str(len(minion_id) - result_len)
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
                             "command": command,
                             "total": minion_count,
                             "succeed": cmd_succeed,
                             "failure": cmd_failure,
                             "failure_minion": failure_minion}, "status": status, "message": message}, 200
        else:
            return status, 500


class ExecuteSLS(Resource):
    @access_required(role_dict["common_user"])
    def post(self):
        args = parser.parse_args()
        sls = args["sls"]
        if not sls:
            return {"status": False,
                    "message": "The specified sls parameter does not exist"}, 400
        # 去掉后缀
        sls = sls.replace(".sls", "")
        minion_id = args["minion_id"]
        salt_api = salt_api_for_product(args["product_id"])
        user_info = g.user_info
        audit_log(user_info["username"], minion_id, args["product_id"], "minion", "sls")
        if isinstance(salt_api, dict):
            return salt_api, 500
        result = salt_api.target_deploy(minion_id, sls)
        db = DB()
        cmd_history = {
            "user_id": user_info["id"],
            "product_id": args["product_id"],
            "command": args["sls"],
            "type": "sls",
            "minion_id": minion_id,
            "result": result,
            "time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        }
        db.insert("cmd_history", json.dumps(cmd_history, ensure_ascii=False))
        db.close_mysql()
        audit_log(user_info["username"], minion_id, args["product_id"], "minion", "sls")

        minion_count = str(len(minion_id))
        result_len = len(result)
        for k, v in result.items():
            if not v:
                result_len -= 1
        cmd_succeed = str(result_len)
        cmd_failure = str(len(minion_id) - result_len)
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
                         "command": args["sls"],
                         "total": minion_count,
                         "succeed": cmd_succeed,
                         "failure": cmd_failure,
                         "failure_minion": failure_minion}, "status": status, "message": message}, 200


# 执行页面显示的组
class ExecuteGroups(Resource):
    @access_required(role_dict["common_user"])
    def get(self):
        product_id = request.args.get("product_id")
        db = DB()
        user_info = g.user_info
        sql_list = []
        groups_list = []
        if user_info["groups"]:
            for group in user_info["groups"]:
                sql_list.append("data -> '$.id'='%s' and data -> '$.product_id'='%s'" % (group, product_id))
            sql = " or ".join(sql_list)
            status, result = db.select("groups", "where %s" % sql)
            db.close_mysql()
            if status is True:
                if result:
                    groups_list = result
                    return {"data": groups_list, "status": True, "message": ""}, 200
                else:
                    return {"status": False, "message": "Group does not exist"}, 404
            else:
                return {"status": False, "message": result}, 500
        else:
            return {"data": groups_list, "status": True, "message": ""}, 200


def verify_acl(acl_list, command):
    if acl_list:
        db = DB()
        sql_list = []
        for acl_id in acl_list:
            sql_list.append("data -> '$.id'='%s'" % acl_id)
        sql = " or ".join(sql_list)
        status, result = db.select("acl", "where %s" % sql)
        db.close_mysql()
        if status is True:
            if result:
                for acl in result:
                    for deny in acl["deny"]:
                        deny_pattern = re.compile(deny)
                        if deny_pattern.search(command):
                            return {"status": False,
                                    "message": "Deny Warning : You don't have permission run [ %s ]" % command}
                return {"status": True, "message": ""}
            else:
                return {"status": False, "message": "acl does not exist"}
        else:
            return {"status": False, "message": result}
    else:
        return {"status": True, "message": ""}
