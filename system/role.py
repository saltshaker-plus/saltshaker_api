# -*- coding:utf-8 -*-
from flask_restful import Resource, reqparse
from flask import g
from common.log import loggers
from common.audit_log import audit_log
from common.db import DB
from common.utility import uuid_prefix
from common.sso import access_required
import json
from system.user import update_user_privilege
from common.const import role_dict

logger = loggers()

parser = reqparse.RequestParser()
parser.add_argument("name", type=str, required=True, trim=True)
parser.add_argument("description", type=str, required=True, trim=True)
parser.add_argument("tag", type=int, required=True, trim=True)


class Role(Resource):
    @access_required(role_dict["product"])
    def get(self, role_id):
        db = DB()
        status, result = db.select_by_id("role", role_id)
        db.close_mysql()
        if status is True:
            if result:
                return {"data": result, "status": True, "message": ""}, 200
            else:
                return {"status": False, "message": "%s does not exist" % role_id}, 404
        else:
            return {"status": False, "message": result}, 500

    @access_required(role_dict["product"])
    def delete(self, role_id):
        user = g.user_info["username"]
        db = DB()
        status, result = db.delete_by_id("role", role_id)
        db.close_mysql()
        if status is not True:
            logger.error("Delete role error: %s" % result)
            return {"status": False, "message": result}, 500
        if result is 0:
            return {"status": False, "message": "%s does not exist" % role_id}, 404
        audit_log(user, role_id, "", "role", "delete")
        info = update_user_privilege("role", role_id)
        if info["status"] is False:
            return {"status": False, "message": info["message"]}, 500
        return {"status": True, "message": ""}, 200

    @access_required(role_dict["product"])
    def put(self, role_id):
        user = g.user_info["username"]
        args = parser.parse_args()
        args["id"] = role_id
        role = args
        db = DB()
        # 判断是否存在
        select_status, select_result = db.select_by_id("role", role_id)
        if select_status is not True:
            db.close_mysql()
            logger.error("Modify role error: %s" % select_result)
            return {"status": False, "message": select_result}, 500
        if not select_result:
            db.close_mysql()
            return {"status": False, "message": "%s does not exist" % role_id}, 404
        # 判断名字是否重复
        status, result = db.select("role", "where data -> '$.name'='%s'" % args["name"])
        if status is True:
            if result:
                if role_id != result[0].get("id"):
                    db.close_mysql()
                    return {"status": False, "message": "The role name already exists"}, 200
        status, result = db.update_by_id("role", json.dumps(role, ensure_ascii=False), role_id)
        db.close_mysql()
        if status is not True:
            logger.error("Modify role error: %s" % result)
            return {"status": False, "message": result}, 500
        audit_log(user, role_id, "", "role", "edit")
        return {"status": True, "message": ""}, 200


class RoleList(Resource):
    @access_required(role_dict["product"])
    def get(self):
        db = DB()
        status, result = db.select("role", "")
        db.close_mysql()
        if status is True:
            return {"data": result, "status": True, "message": ""}, 200
        else:
            return {"status": False, "message": result}, 500

    @access_required(role_dict["product"])
    def post(self):
        args = parser.parse_args()
        args["id"] = uuid_prefix("r")
        user = g.user_info["username"]
        role = args
        db = DB()
        status, result = db.select("role", "where data -> '$.name'='%s'" % args["name"])
        if status is True:
            if len(result) == 0:
                insert_status, insert_result = db.insert("role", json.dumps(role, ensure_ascii=False))
                db.close_mysql()
                if insert_status is not True:
                    logger.error("Add role error: %s" % insert_result)
                    return {"status": False, "message": insert_result}, 500
                audit_log(user, args["id"], "", "role", "add")
                return {"status": True, "message": ""}, 201
            else:
                db.close_mysql()
                return {"status": False, "message": "The role name already exists"}, 200
        else:
            db.close_mysql()
            logger.error("Select role name error: %s" % result)
            return {"status": False, "message": result}, 500
