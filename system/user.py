# -*- coding:utf-8 -*-
from flask_restful import Resource, reqparse
from common.log import loggers
from common.db import DB
from flask import g
from passlib.apps import custom_app_context
from common.utility import uuid_prefix
from common.sso import access_required, verify_password
from common.audit_log import audit_log
import json
from common.const import role_dict
from common.utility import rsa_decrypt
import random
import string
from common.send_mail import send_mail


logger = loggers()

parser = reqparse.RequestParser()
parser.add_argument("username", type=str, required=True, trim=True)
parser.add_argument("password", type=str, trim=True)
parser.add_argument("product", type=str, default=[], action="append")
parser.add_argument("groups", type=str, default=[], action="append")
parser.add_argument("role", type=str, default=[], action="append")
parser.add_argument("acl", type=str, default=[], action="append")
parser.add_argument("mail", type=str, trim=True)
parser.add_argument("old_password", type=str, trim=True)
parser.add_argument("new_password", type=str, trim=True)


class User(Resource):
    # 查看指定用户
    @access_required(role_dict["common_user"])
    def get(self, user_id):
        db = DB()
        status, result = db.select_by_id("user", user_id)
        db.close_mysql()
        if status is True:
            if result:
                result.pop("password")
                return {"data": result, "status": True, "message": ""}, 200
            else:
                return {"status": False, "message": "%s does not exist" % user_id}, 404
        else:
            return {"status": False, "message": result}, 500

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
            if result:
                if user_id != result[0].get("id"):
                    db.close_mysql()
                    return {"status": False, "message": "The user name already exists"}, 200
        # 获取之前的加密密码
        if args["password"]:
            # 基于RSA加密算法获取密码
            password = rsa_decrypt(args["password"])
            if password is False:
                return {"status": False, "message": "Decrypt is failure "}, 500
            password_hash = custom_app_context.encrypt(password)
            args["password"] = password_hash
        else:
            status, result = db.select_by_id("user", user_id)
            if status is True:
                if result:
                    args["password"] = result.get("password")
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
        user_info = g.user_info
        role_sql = []
        if user_info["role"]:
            for role in user_info["role"]:
                role_sql.append("data -> '$.id'='%s'" % role)
            sql = " or ".join(role_sql)
            role_status, role_result = db.select("role", "where %s" % sql)
            if role_status and role_result:
                for role in role_result:
                    user_list = []
                    if role["tag"] == 0:
                        status, result = db.select("user", "")
                    else:
                        status, result = db.select_by_list_list("user", "product", user_info["product"])
                    if status is True:
                        if result:
                            for user in result:
                                user.pop("password")
                                user_list.append(user)
                        else:
                            return {"data": user_list, "status": True, "message": ""}, 200
                    else:
                        return {"status": False, "message": result}, 500

        for item in user_list:
            for attr in item.keys():
                if attr not in ["id", "username", "mail"]:
                    if item[attr]:
                        tmp = []
                        status, result = db.select_by_list(attr, "id", item[attr])
                        if status is True:
                            for info in result:
                                tmp.append({"id": info["id"], "name": info["name"]})
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
                # 默认新添加的用户都是默认用户
                role_id = get_common_user()
                if isinstance(role_id, dict):
                    return role_id
                    args["role"].append(role_id)
                insert_status, insert_result = db.insert("user", json.dumps(args, ensure_ascii=False))
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


class Register(Resource):
    # 注册用户
    def post(self):
        args = parser.parse_args()
        args["id"] = uuid_prefix("u")
        db = DB()
        status, result = db.select("user", "where data -> '$.username'='%s'" % args["username"])
        if status is True:
            if len(result) == 0:
                # 基于RSA加密算法获取密码
                password = rsa_decrypt(args["password"])
                if password is False:
                    return {"status": False, "message": "Decrypt is failure "}, 500
                password_hash = custom_app_context.encrypt(password)
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
                return {"status": True, "message": ""}, 201
            else:
                db.close_mysql()
                return {"status": False, "message": "The user name already exists"}, 200
        else:
            db.close_mysql()
            logger.error("Select user error: %s" % result)
            return {"status": False, "message": result}, 500


# 管理员重置其他人密码
class ResetPassword(Resource):
    @access_required(role_dict["user"])
    def get(self, user_id):
        user = g.user_info["username"]
        db = DB()
        status, result = db.select_by_id("user", user_id)
        if status is True and result:
            # 生成12位随机密码
            password = ''.join(random.sample(string.ascii_letters + string.digits, 12))
            send_mail(result["mail"], "Saltshaker 重置密码", "新密码：" + password)
            # 离散hash
            password_hash = custom_app_context.encrypt(password)
            result["password"] = password_hash
            insert_status, insert_result = db.update_by_id("user", json.dumps(result, ensure_ascii=False), user_id)
            db.close_mysql()
            if insert_status is not True:
                logger.error("Reset %s password error: %s" % (user_id, insert_result))
                return {"status": False, "message": insert_result}, 500
            audit_log(user, user_id, "", "user", "reset")
            return {"status": True, "message": ""}, 201
        else:
            db.close_mysql()
            logger.error("Select user error: %s" % result)
            return {"status": False, "message": result}, 500


# 用户自己修改密码
class ResetPasswordByOwner(Resource):
    @access_required(role_dict["common_user"])
    def post(self, user_id):
        args = parser.parse_args()
        user = g.user_info["username"]
        if not args["old_password"]:
            return {"status": False, "message": "The specified old_password parameter does not exist"}, 200
        if not args["new_password"]:
            return {"status": False, "message": "The specified now_password parameter does not exist"}, 200
        db = DB()
        status, result = db.select_by_id("user", user_id)
        if status is True and result:
            if not verify_password(result["username"], args["old_password"]):
                return {"status": False, "message": "Old password error"}, 200
            else:
                # 基于RSA加密算法获取密码
                password = rsa_decrypt(args["new_password"])
                if password is False:
                    return {"status": False, "message": "Decrypt is failure"}, 500
                # 加密新密码
                password_hash = custom_app_context.encrypt(password)
                result["password"] = password_hash
                update_status, update_result = db.update_by_id("user", json.dumps(result, ensure_ascii=False),
                                                               user_id)
                db.close_mysql()
                if update_status is not True:
                    logger.error("Reset %s password error: %s" % (user_id, update_result))
                    return {"status": False, "message": update_result}, 500
                audit_log(user, user_id, "", "user", "reset by owner")
                return {"status": True, "message": ""}, 201
        else:
            db.close_mysql()
            logger.error("Select user error: %s" % result)
            return {"status": False, "message": result}, 500


# 用自己修改用户信息
class ChangeUserInfo(Resource):
    @access_required(role_dict["common_user"])
    def put(self, user_id):
        args = parser.parse_args()
        user = g.user_info["username"]
        if not args["mail"]:
            return {"status": False, "message": "The specified mail parameter does not exist"}, 200
        db = DB()
        select_status, select_result = db.select("user", "where data -> '$.username'='%s'" % args["username"])
        if select_status is True and select_result:
            if select_result[0]["id"] != user_id:
                db.close_mysql()
                return {"status": False, "message": "The user name already exists"}, 200
        status, result = db.select_by_id("user", user_id)
        if status is True and result:
            result["username"] = args["username"]
            result["mail"] = args["mail"]
            update_status, update_result = db.update_by_id("user", json.dumps(result, ensure_ascii=False),
                                                           user_id)
            db.close_mysql()
            if update_status is not True:
                logger.error("Change %s user info error: %s" % (user_id, update_result))
                return {"status": False, "message": update_result}, 500
            audit_log(user, user_id, "", "user", "change user info")
            return {"status": True, "message": ""}, 201
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
            return result[0]['id']
        else:
            return {"status": False, "message": "Common user does not exist"}
    return {"status": False, "message": result}


# 当删除acl, role, group等数据时,更新用户权限信息
def update_user_privilege(table, privilege):
    db = DB()
    status, result = db.select("user", "")
    if status is True:
        if result:
            for info in result:
                if table in info:
                    if privilege in info[table]:
                        info[table].remove(privilege)
                        db.update_by_id("user", json.dumps(info, ensure_ascii=False), info["id"])
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
            result["product"].append(product_id)
            db.update_by_id("user", json.dumps(result, ensure_ascii=False), user_id)
            db.close_mysql()
            return {"status": True, "message": ""}
        else:
            db.close_mysql()
            return {"status": False, "message": "User does not exist"}
    else:
        db.close_mysql()
        logger.error("Update user product error: %s" % result)
        return {"status": False, "message": result}
