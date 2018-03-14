# -*- coding:utf-8 -*-
from flask_restful import Resource, reqparse
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth, MultiAuth
from common.log import Logger
from common.db import DB
from common.utility import verify_password, verify_token
from flask import make_response, jsonify, g


logger = Logger()
basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth(scheme='Bearer')
multi_auth = MultiAuth(basic_auth, token_auth)


parser = reqparse.RequestParser()
parser.add_argument("product_id", type=str, required=True, trim=True)


# 错误提示重新定义
@basic_auth.error_handler
def unauthorized():
    return make_response(jsonify({"status": False, "message": "Unauthorized access"}), 401)


@token_auth.error_handler
def unauthorized():
    return make_response(jsonify({"status": False, "message": "Token error or expiration"}), 401)


# 验证密码
@basic_auth.verify_password
def auth_password(username, password):
    return verify_password(username, password)


# 验证Token
@token_auth.verify_token
def auth_token(token):
    return verify_token(token)


class LogList(Resource):
    @multi_auth.login_required
    def get(self):
        print(g.user)
        args = parser.parse_args()
        db = DB()
        status, result = db.select_by_id("audit_log", args["product_id"])
        log_list = []
        if status is True:
            if result:
                for i in result:
                    log_list.append(eval(i[0]))
        else:
            return {"status": False, "message": result}, 200
        return {"audit_logs": {"audit_log": log_list}}




