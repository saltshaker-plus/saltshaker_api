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
parser.add_argument("allow", type=str, default="", trim=True)
parser.add_argument("deny", type=str, default="", trim=True)
parser.add_argument("description", type=str, default="", trim=True)


class ACL(Resource):
    @login_required
    def get(self, acl_id):
        db = DB()
        status, result = db.select_by_id("acl", acl_id)
        db.close_mysql()
        if status is True:
            if result:
                try:
                    acl = eval(result[0][0])
                except Exception as e:
                    return {"status": False, "message": str(e)}, 200
            else:
                return {"status": False, "message": "%s does not exist" % acl_id}, 200
        else:
            return {"status": False, "message": result}, 200
        return {"acl": acl}, 200

    @login_required
    def delete(self, acl_id):
        user = g.user
        db = DB()
        status, result = db.delete_by_id("acl", acl_id)
        db.close_mysql()
        if status is not True:
            logger.error("Delete acl error: %s" % result)
            return {"status": False, "message": result}, 200
        if result is 0:
            return {"status": False, "message": "%s does not exist" % acl_id}, 200
        audit_log(user, acl_id, "", "acl", "delete")
        return {"status": True, "message": ""}, 201

    @login_required
    def put(self, acl_id):
        user = g.user
        args = parser.parse_args()
        args["id"] = acl_id
        acl = args
        db = DB()
        status, result = db.select("acl", "where data -> '$.name'='%s'" % args["name"])
        if status is True:
            if len(result) != 0:
                info = eval(result[0][0])
                if acl_id != info.get("id"):
                    return {"status": False, "message": "The acl name already exists"}, 200
        status, result = db.update_by_id("acl", json.dumps(acl, ensure_ascii=False), acl_id)
        db.close_mysql()
        if status is not True:
            logger.error("Modify acl error: %s" % result)
            return {"status": False, "message": result}, 200
        audit_log(user, acl_id, "", "acl", "edit")
        return {"status": True, "message": ""}, 201


class ACLList(Resource):
    @login_required
    def get(self):
        db = DB()
        status, result = db.select("acl", "")
        db.close_mysql()
        acl_list = []
        if status is True:
            if result:
                for i in result:
                    try:
                        acl_list.append(eval(i[0]))
                    except Exception as e:
                        return {"status": False, "message": str(e)}, 200
        else:
            return {"status": False, "message": result}, 200
        return {"acls": {"acl": acl_list}}, 200

    @login_required
    def post(self):
        args = parser.parse_args()
        args["id"] = uuid_prefix("a")
        user = g.user
        acl = args
        db = DB()
        status, result = db.select("acl", "where data -> '$.name'='%s'" % args["name"])
        if status is True:
            if len(result) == 0:
                insert_status, insert_result = db.insert("acl", json.dumps(acl, ensure_ascii=False))
                db.close_mysql()
                if insert_status is not True:
                    logger.error("Add acl error: %s" % insert_result)
                    return {"status": False, "message": insert_result}, 200
                audit_log(user, args["id"], "", "acl", "add")
                return {"status": True, "message": ""}, 201
            else:
                return {"status": False, "message": "The acl name already exists"}, 200
        else:
            logger.error("Select acl name error: %s" % result)
            return {"status": False, "message": result}, 200
