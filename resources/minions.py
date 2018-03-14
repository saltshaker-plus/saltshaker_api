# -*- coding:utf-8 -*-
from flask_restful import Resource, reqparse
from flask_httpauth import HTTPBasicAuth
from flask import make_response, jsonify, g
from common.log import Logger
from common.audit_log import audit_log
from common.utility import salt_api_for_product, verify_password

logger = Logger()
auth = HTTPBasicAuth()

parser = reqparse.RequestParser()
parser.add_argument("product_id", type=str, required=True, trim=True)
parser.add_argument("action", type=str, trim=True)
parser.add_argument("minion_id", type=str, trim=True, action="append")


# 错误提示重新定义
@auth.error_handler
def unauthorized():
    return make_response(jsonify({"status": False, "message": "Unauthorized access"}), 401)


# 验证密码
@auth.verify_password
def auth_password(username, password):
    return verify_password(username, password)


class MinionsStatus(Resource):
    @auth.login_required
    def get(self):
        args = parser.parse_args()
        salt_api = salt_api_for_product(args["product_id"])
        if isinstance(salt_api, dict):
            return salt_api
        else:
            result = salt_api.runner_status("status")
            return result


class MinionsKeys(Resource):
    @auth.login_required
    def get(self):
        args = parser.parse_args()
        salt_api = salt_api_for_product(args["product_id"])
        if isinstance(salt_api, dict):
            return salt_api
        else:
            result = salt_api.list_all_key()
            return result

    @auth.login_required
    def post(self):
        args = parser.parse_args()
        salt_api = salt_api_for_product(args["product_id"])
        user = g.user
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
                    return {"status": result_list, "message": ""}
                if args["action"] == "reject":
                    for minion in args["minion_id"]:
                        result = salt_api.reject_key(minion)
                        result_list.append({minion: result})
                        audit_log(user, minion, args["product_id"], "minion", "reject")
                    return {"status": result_list, "message": ""}
                if args["action"] == "delete":
                    for minion in args["minion_id"]:
                        result = salt_api.delete_key(minion)
                        result_list.append({minion: result})
                        audit_log(user, minion, args["product_id"], "minion", "delete")
                    return {"status": result_list, "message": ""}
            else:
                return {"status": False,
                        "message": "Missing required parameter in the JSON body or the post body or the query string"}
