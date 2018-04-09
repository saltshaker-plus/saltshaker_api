# -*- coding:utf-8 -*-
from flask_restful import Resource, reqparse
from common.log import Logger
from common.audit_log import audit_log
from common.utility import salt_api_for_product
from common.sso import access_required
from common.db import DB
from common.const import role_dict
from flask import g
import re
import json
import time

logger = Logger()

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
                    "message": "Missing required parameter in the JSON body or "
                    "the post body or the query string"}, 400
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
            host = ",".join(minion_id)
            result = salt_api.shell_remote_execution(host, command)
            # 记录历史命令
            db = DB()
            cmd_history = {
                "user_id": user_info["id"],
                "command": command,
                "minion_id": minion_id,
                "result": result,
                "time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            }
            db.insert("cmd_history", json.dumps(cmd_history, ensure_ascii=False))
            db.close_mysql()
            audit_log(user_info["username"], minion_id, args["product_id"], "minion", "shell")

            minion_count = 'Total: ' + str(len(minion_id))
            cmd_succeed = 'Succeed: ' + str(len(result))
            cmd_failure = 'Failure: ' + str(len(minion_id) - len(result))
            command = 'Command: ' + command
            succeed_minion = []
            for i in result:
                succeed_minion.append(i)
            failure_minion = 'Failure_Minion: ' + ','.join(
                list(set(minion_id).difference(set(succeed_minion))))
            return {'result': result,
                    'command': command,
                    'line': "#" * 50,
                    'minion_count': minion_count,
                    'cmd_succeed': cmd_succeed,
                    'cmd_failure': cmd_failure,
                    'failure_minion': failure_minion,
                    "status": True,
                    "message": ""
                    }, 200
        else:
            return status, 500


class ExecuteSLS(Resource):
    @access_required(role_dict["common_user"])
    def post(self):
        args = parser.parse_args()
        sls = args["sls"]
        if not sls:
            return {"status": False,
                    "message": "Missing required parameter in the JSON body or "
                    "the post body or the query string"}, 400
        minion_id = args["minion_id"]
        salt_api = salt_api_for_product(args["product_id"])
        user_info = g.user_info
        audit_log(user_info["username"], minion_id, args["product_id"], "minion", "sls")
        if isinstance(salt_api, dict):
            return salt_api, 500
        host = ",".join(minion_id)
        result = salt_api.target_deploy(host, sls)
        result.update({"status": True, "message": ""})
        return result, 200


# 执行页面显示的组
class ExecuteGroups(Resource):
    @access_required(role_dict["common_user"])
    def get(self):
        db = DB()
        user_info = g.user_info
        sql_list = []
        groups_list = []
        if user_info["groups"]:
            for group in user_info["groups"]:
                sql_list.append("data -> '$.id'='%s'" % group)
            sql = " or ".join(sql_list)
            status, result = db.select("groups", "where %s" % sql)
            db.close_mysql()
            if status is True:
                if result:
                    for i in result:
                        try:
                            groups_list.append(eval(i[0]))
                        except Exception as e:
                            return {"status": False, "message": str(e)}, 500
                    return {"groups": {"groups": groups_list}, "status": True, "message": ""}, 200
                else:
                    return {"status": False, "message": "Group does not exist"}, 404
            else:
                return {"status": False, "message": result}, 500
        else:
            return {"groups": {"groups": groups_list}, "status": True, "message": ""}, 200


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
                for i in result:
                    try:
                        acl = eval(i[0])
                        for deny in acl["deny"]:
                            deny_pattern = re.compile(deny)
                            if deny_pattern.search(command):
                                return {"status": False,
                                        "message": "Deny Warning : You don't have permission run [ %s ]"
                                                   % command}
                    except Exception as e:
                        return {"status": False, "message": str(e)}
                return {"status": True, "message": ""}
            else:
                return {"status": False, "message": "acl does not exist"}
        else:
            return {"status": False, "message": result}
    else:
        return {"status": True, "message": ""}
