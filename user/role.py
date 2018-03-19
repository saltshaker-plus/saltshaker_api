# -*- coding:utf-8 -*-
from flask_restful import Resource, reqparse
from flask import g
from common.log import Logger
from common.audit_log import audit_log
from common.db import DB
from common.utility import uuid_prefix
from common.sso import login_required
import json

logger = Logger()

parser = reqparse.RequestParser()
parser.add_argument("name", type=str, required=True, trim=True)
parser.add_argument("description", type=str, required=True, trim=True)


class Role(Resource):
    @login_required
    def get(self, role_id):
        db = DB()
        status, result = db.select_by_id("role", role_id)
        db.close_mysql()
        if status is True:
            if result:
                try:
                    role = eval(result[0][0])
                except Exception as e:
                    return {"status": False, "message": str(e)}, 200
            else:
                return {"status": False, "message": "%s does not exist" % role_id}, 200
        else:
            return {"status": False, "message": result}, 200
        return {"role": role}, 200

    @login_required
    def delete(self, role_id):
        user = g.user
        db = DB()
        status, result = db.delete_by_id("role", role_id)
        db.close_mysql()
        if status is not True:
            logger.error("Delete role error: %s" % result)
            return {"status": False, "message": result}, 200
        if result is 0:
            return {"status": False, "message": "%s does not exist" % role_id}, 200
        audit_log(user, role_id, "", "role", "delete")
        return {"status": True, "message": ""}, 201

    @login_required
    def put(self, role_id):
        user = g.user
        args = parser.parse_args()
        args["id"] = role_id
        role = args
        db = DB()
        status, result = db.select("role", "where data -> '$.name'='%s'" % args["name"])
        if status is True:
            if len(result) != 0:
                info = eval(result[0][0])
                if role_id != info.get("id"):
                    return {"status": False, "message": "The role name already exists"}, 200
        status, result = db.update_by_id("role", json.dumps(role, ensure_ascii=False), role_id)
        db.close_mysql()
        if status is not True:
            logger.error("Modify role error: %s" % result)
            return {"status": False, "message": result}, 200
        audit_log(user, role_id, "", "role", "edit")
        return {"status": True, "message": ""}, 201


class RoleList(Resource):
    @login_required
    def get(self):
        db = DB()
        status, result = db.select("role", "")
        db.close_mysql()
        role_list = []
        if status is True:
            if result:
                for i in result:
                    try:
                        role_list.append(eval(i[0]))
                    except Exception as e:
                        return {"status": False, "message": str(e)}, 200
        else:
            return {"status": False, "message": result}, 200
        return {"roles": {"role": role_list}}, 200

    @login_required
    def post(self):
        args = parser.parse_args()
        args["id"] = uuid_prefix("r")
        user = g.user
        role = args
        db = DB()
        status, result = db.select("role", "where data -> '$.name'='%s'" % args["name"])
        if status is True:
            if len(result) == 0:
                insert_status, insert_result = db.insert("role", json.dumps(role, ensure_ascii=False))
                db.close_mysql()
                if insert_status is not True:
                    logger.error("Add role error: %s" % insert_result)
                    return {"status": False, "message": insert_result}, 200
                audit_log(user, args["id"], "", "role", "add")
                return {"status": True, "message": ""}, 201
            else:
                return {"status": False, "message": "The role name already exists"}, 200
        else:
            logger.error("Select role name error: %s" % result)
            return {"status": False, "message": result}, 200
