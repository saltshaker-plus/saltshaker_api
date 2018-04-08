# -*- coding:utf-8 -*-
from flask_restful import Resource, reqparse
from flask import g
from common.log import Logger
from common.audit_log import audit_log
from common.db import DB
from common.utility import uuid_prefix
from common.sso import access_required
import json
from user.user import update_user_privilege
from common.const import role_dict


logger = Logger()

parser = reqparse.RequestParser()
parser.add_argument("name", type=str, required=True, trim=True)
parser.add_argument("allow", type=str, default=[], action="append")
parser.add_argument("deny", type=str, default=[], action="append")
parser.add_argument("description", type=str, default="", trim=True)


class ACL(Resource):
    @access_required(role_dict["acl"])
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
        return {"acl": acl, "status": True, "message": ""}, 200

    @access_required(role_dict["acl"])
    def delete(self, acl_id):
        user = g.user_info["username"]
        db = DB()
        status, result = db.delete_by_id("acl", acl_id)
        db.close_mysql()
        if status is not True:
            logger.error("Delete acl error: %s" % result)
            return {"status": False, "message": result}, 200
        if result is 0:
            return {"status": False, "message": "%s does not exist" % acl_id}, 200
        audit_log(user, acl_id, "", "acl", "delete")
        info = update_user_privilege("acl", acl_id)
        if info["status"] is False:
            return {"status": False, "message": info["message"]}, 200
        return {"status": True, "message": ""}, 200

    @access_required(role_dict["acl"])
    def put(self, acl_id):
        user = g.user_info["username"]
        args = parser.parse_args()
        args["id"] = acl_id
        acl = args
        db = DB()
        # 判断是否存在
        select_status, select_result = db.select_by_id("acl", acl_id)
        if select_status is not True:
            db.close_mysql()
            logger.error("Modify acl error: %s" % select_result)
            return {"status": False, "message": select_result}, 200
        if not select_result:
            db.close_mysql()
            return {"status": False, "message": "%s does not exist" % acl_id}, 200
        # 判断名字否已经存在
        status, result = db.select("acl", "where data -> '$.name'='%s'" % args["name"])
        if status is True:
            if len(result) != 0:
                info = eval(result[0][0])
                if acl_id != info.get("id"):
                    db.close_mysql()
                    return {"status": False, "message": "The acl name already exists"}, 200
        status, result = db.update_by_id("acl", json.dumps(acl, ensure_ascii=False), acl_id)
        db.close_mysql()
        if status is not True:
            logger.error("Modify acl error: %s" % result)
            return {"status": False, "message": result}, 200
        audit_log(user, acl_id, "", "acl", "edit")
        return {"status": True, "message": ""}, 200


class ACLList(Resource):
    @access_required(role_dict["acl"])
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
                return {"status": False, "message": "Acl does not exist"}, 200
        else:
            return {"status": False, "message": result}, 200
        return {"acls": {"acl": acl_list}, "status": True, "message": ""}, 200

    @access_required(role_dict["acl"])
    def post(self):
        args = parser.parse_args()
        args["id"] = uuid_prefix("a")
        user = g.user_info["username"]
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
                db.close_mysql()
                return {"status": False, "message": "The acl name already exists"}, 200
        else:
            db.close_mysql()
            logger.error("Select acl name error: %s" % result)
            return {"status": False, "message": result}, 200
