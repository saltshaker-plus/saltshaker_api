# -*- coding:utf-8 -*-
from flask_restful import Resource, reqparse
from common.log import Logger
from common.db import DB
from flask import g
from passlib.apps import custom_app_context
from common.utility import uuid_prefix
from common.sso import login_required
from common.audit_log import audit_log
import json


logger = Logger()

parser = reqparse.RequestParser()
parser.add_argument("username", type=str, required=True, trim=True)
parser.add_argument("password", type=str, required=True, trim=True)


class User(Resource):
    # 查看指定用户
    @login_required
    def get(self, user_id):
        db = DB()
        status, result = db.select_by_id("user", user_id)
        db.close_mysql()
        if status is True:
            if result:
                user = eval(result[0][0])
                user.pop("password")
            else:
                return {"status": False, "message": "%s does not exist" % user_id}, 200
        else:
            return {"status": False, "message": result}, 200
        return {"user": user}, 200

    # 删除指定用户
    @login_required
    def delete(self, user_id):
        user = g.user
        db = DB()
        status, result = db.delete_by_id("user", user_id)
        db.close_mysql()
        if status is not True:
            logger.error("Delete user error: %s" % result)
            return {"status": False, "message": result}, 200
        if result is 0:
            return {"status": False, "message": "%s does not exist" % user_id}, 200
        audit_log(user, user_id, "", "user", "delete")
        return {"status": True, "message": ""}, 201

    # 修改指定用户
    @login_required
    def put(self, user_id):
        user = g.user
        args = parser.parse_args()
        args["id"] = user_id
        users = args
        db = DB()
        status, result = db.update_by_id("user", json.dumps(users, ensure_ascii=False), user_id)
        db.close_mysql()
        if status is not True:
            logger.error("Modify user error: %s" % result)
            return {"status": False, "message": result}, 200
        audit_log(user, user_id, "", "user", "edit")
        return {"status": True, "message": ""}, 201


class UserList(Resource):
    # 查看所有用户
    @login_required
    def get(self):
        db = DB()
        status, result = db.select("user", "")
        db.close_mysql()
        user_list = []
        if status is True:
            if result:
                for i in result:
                    info = eval(i[0])
                    info.pop("password")
                    user_list.append(info)
        else:
            return {"status": False, "message": result}, 200
        return {"users": {"user": user_list}}, 200

    # 添加用户
    @login_required
    def post(self):
        user = g.user
        args = parser.parse_args()
        args["id"] = uuid_prefix("u")
        db = DB()
        status, result = db.select("user", "where data -> '$.username'='%s'" % args["username"])
        if status is True:
            if len(result) == 0:
                password_hash = custom_app_context.encrypt(args["password"])
                users = {"id": args["id"],
                         "username": args["username"],
                         "password": password_hash}
                insert_status, insert_result = db.insert("user", json.dumps(users, ensure_ascii=False))
                db.close_mysql()
                if insert_status is not True:
                    logger.error("Add user error: %s" % insert_result)
                    return {"status": False, "message": insert_result}, 200
                audit_log(user, args["id"], "", "user", "add")
                return {"status": True, "message": ""}, 201
            else:
                return {"status": False, "message": "The user name already exists"}, 200
        else:
            logger.error("Select user error: %s" % result)
            return {"status": False, "message": result}, 200
