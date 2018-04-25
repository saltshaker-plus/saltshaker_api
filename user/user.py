# -*- coding:utf-8 -*-
from flask_restful import Resource, reqparse
from common.log import loggers
from common.db import DB
from flask import g
from passlib.apps import custom_app_context
from common.utility import uuid_prefix
from common.sso import access_required
from common.audit_log import audit_log
import json
from common.const import role_dict


logger = loggers()

parser = reqparse.RequestParser()
parser.add_argument("username", type=str, required=True, trim=True)
parser.add_argument("password", type=str, required=True, trim=True)
parser.add_argument("product", type=str, default=[], action="append")
parser.add_argument("groups", type=str, default=[], action="append")
parser.add_argument("role", type=str, default=[], action="append")
parser.add_argument("acl", type=str, default=[], action="append")


class User(Resource):
    # 查看指定用户
    @access_required(role_dict["user"])
    def get(self, user_id):
        db = DB()
        status, result = db.select_by_id("user", user_id)
        db.close_mysql()
        if status is True:
            if result:
                try:
                    user = eval(result[0][0])
                    user.pop("password")
                except Exception as e:
                    return {"status": False, "message": str(e)}, 500
            else:
                return {"status": False, "message": "%s does not exist" % user_id}, 404
        else:
            return {"status": False, "message": result}, 500
        return {"data": user, "status": True, "message": ""}, 200

    # 删除指定用户
    @access_required(role_dict["user"])
    def delete(self, user_id):
        user = g.user_info["username"]
        db = DB()
        status, result = db.delete_by_id("user", user_id)
        db.close_mysql()
        if status is not True:
            logger.error("Delete user error: %s" % result)
            return {"status": False, "message": result}, 500
        if result is 0:
            return {"status": False, "message": "%s does not exist" % user_id}, 404
        audit_log(user, user_id, "", "user", "delete")
        return {"status": True, "message": ""}, 200

    # 修改指定用户
    @access_required(role_dict["user"])
    def put(self, user_id):
        user = g.user_info["username"]
        args = parser.parse_args()
        args["id"] = user_id
        db = DB()
        # 判断是否存在
        select_status, select_result = db.select_by_id("user", user_id)
        if select_status is not True:
            db.close_mysql()
            logger.error("Modify user error: %s" % select_result)
            return {"status": False, "message": select_result}, 500
        if not select_result:
            db.close_mysql()
            return {"status": False, "message": "%s does not exist" % user_id}, 404
        # 判断名字否已经存在
        status, result = db.select("user", "where data -> '$.username'='%s'" % args["username"])
        if status is True:
            if len(result) != 0:
                info = eval(result[0][0])
                if user_id != info.get("id"):
                    db.close_mysql()
                    return {"status": False, "message": "The user name already exists"}, 200
        # 获取之前的加密密码
        status, result = db.select_by_id("user", user_id)
        if status is True:
            if result:
                try:
                    user_info = eval(result[0][0])
                    args["password"] = user_info.get("password")
                except Exception as e:
                    db.close_mysql()
                    return {"status": False, "message": str(e)}, 500
            else:
                db.close_mysql()
                return {"status": False, "message": "%s does not exist" % user_id}, 404
        else:
            db.close_mysql()
            return {"status": False, "message": result}, 500
        # 更新用户信息
        users = args
        status, result = db.update_by_id("user", json.dumps(users, ensure_ascii=False), user_id)
        db.close_mysql()
        if status is not True:
            logger.error("Modify user error: %s" % result)
            return {"status": False, "message": result}, 500
        audit_log(user, user_id, "", "user", "edit")
        return {"status": True, "message": ""}, 200


class UserList(Resource):
    # 查看所有用户
    @access_required(role_dict["user"])
    def get(self):
        db = DB()
        status, result = db.select("user", "")
        user_list = []
        if status is True:
            if result:
                for i in result:
                    try:
                        info = eval(i[0])
                        info.pop("password")
                        user_list.append(info)
                    except Exception as e:
                        return {"status": False, "message": str(e)}, 500
        else:
            return {"status": False, "message": result}, 500
        for item in user_list:
            for attr in item.keys():
                if attr not in ["id", "username"]:
                    if item[attr]:
                        tmp = []
                        status, result = db.select_by_list(attr, "id", item[attr])
                        if status is True:
                            for i in result:
                                try:
                                    info = eval(i[0])
                                    tmp.append({"id": info["id"], "name": info["name"]})
                                except Exception as e:
                                    db.close_mysql()
                                    return {"status": False, "message": str(e)}, 500
                            item[attr] = tmp
                        else:
                            db.close_mysql()
                            return {"status": False, "message": result}, 500
        db.close_mysql()
        return {"data": user_list, "status": True, "message": ""}, 200

    # 添加用户
    @access_required(role_dict["user"])
    def post(self):
        user = g.user_info["username"]
        args = parser.parse_args()
        args["id"] = uuid_prefix("u")
        db = DB()
        status, result = db.select("user", "where data -> '$.username'='%s'" % args["username"])
        if status is True:
            if len(result) == 0:
                password_hash = custom_app_context.encrypt(args["password"])
                args["password"] = password_hash
                users = args
                # 默认新添加的用户都是默认用户
                role_id = get_common_user()
                if isinstance(role_id, dict):
                    return role_id
                users["role"].append(role_id)
                insert_status, insert_result = db.insert("user", json.dumps(users, ensure_ascii=False))
                db.close_mysql()
                if insert_status is not True:
                    logger.error("Add user error: %s" % insert_result)
                    return {"status": False, "message": insert_result}, 500
                audit_log(user, args["id"], "", "user", "add")
                return {"status": True, "message": ""}, 201
            else:
                db.close_mysql()
                return {"status": False, "message": "The user name already exists"}, 200
        else:
            db.close_mysql()
            logger.error("Select user error: %s" % result)
            return {"status": False, "message": result}, 500


# 获取普通用户的id
def get_common_user():
    db = DB()
    status, result = db.select("role", "where data -> '$.tag'=%s" % role_dict["common_user"])
    db.close_mysql()
    if status is True:
        if result:
            try:
                role = eval(result[0][0])
                return role["id"]
            except Exception as e:
                return {"status": False, "message": str(e)}
        else:
            return {"status": False, "message": "Common user does not exist"}
    return {"status": False, "message": result}


# 当删除acl, role, group等数据时,更新用户权限信息
def update_user_privilege(table, privilege):
    db = DB()
    status, result = db.select("user", "")
    if status is True:
        if result:
            for i in result:
                try:
                    info = eval(i[0])
                    if table in info:
                        if privilege in info[table]:
                            info[table].remove(privilege)
                            db.update_by_id("user", json.dumps(info, ensure_ascii=False), info["id"])
                except Exception as e:
                    db.close_mysql()
                    logger.error("Update user privilege error: %s" % str(e))
                    return {"status": False, "message": str(e)}
            db.close_mysql()
            return {"status": True, "message": ""}
        else:
            db.close_mysql()
            return {"status": False, "message": "User does not exist"}
    else:
        db.close_mysql()
        logger.error("Update user privilege error: %s" % result)
        return {"status": False, "message": result}


# 默认创建完产品线后该产品线属于创建者
def update_user_product(user_id, product_id):
    db = DB()
    status, result = db.select_by_id("user", user_id)
    if status is True:
        if result:
            for i in result:
                try:
                    info = eval(i[0])
                    info["product"].append(product_id)
                    db.update_by_id("user", json.dumps(info, ensure_ascii=False), user_id)
                except Exception as e:
                    db.close_mysql()
                    logger.error("Update user product error: %s" % str(e))
                    return {"status": False, "message": str(e)}
            db.close_mysql()
            return {"status": True, "message": ""}
        else:
            db.close_mysql()
            return {"status": False, "message": "User does not exist"}
    else:
        db.close_mysql()
        logger.error("Update user product error: %s" % result)
        return {"status": False, "message": result}
