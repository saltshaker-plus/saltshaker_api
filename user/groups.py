# -*- coding:utf-8 -*-
from flask_restful import Resource, reqparse, request
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
parser.add_argument("product_id", type=str, required=True, trim=True)
# 不必填写的字段一定要指定默认值为""，否则无法转换成字典
parser.add_argument("description", type=str, default="")


class Groups(Resource):
    @access_required(role_dict["product"])
    def get(self, groups_id):
        db = DB()
        status, result = db.select_by_id("groups", groups_id)
        db.close_mysql()
        if status is True:
            if result:
                try:
                    groups = eval(result[0][0])
                except Exception as e:
                    return {"status": False, "message": str(e)}, 500
            else:
                return {"status": False, "message": "%s does not exist" % groups_id}, 404
        else:
            return {"status": False, "message": result}, 500
        return {"groups": groups}, 200

    @access_required(role_dict["product"])
    def delete(self, groups_id):
        user = g.user_info["username"]
        db = DB()
        status, result = db.delete_by_id("groups", groups_id)
        db.close_mysql()
        if status is not True:
            logger.error("Delete groups error: %s" % result)
            return {"status": False, "message": result}, 500
        if result is 0:
            return {"status": False, "message": "%s does not exist" % groups_id}, 404
        audit_log(user, groups_id, "", "groups", "delete")
        info = update_user_privilege("groups", groups_id)
        if info["status"] is False:
            return {"status": False, "message": info["message"]}, 500
        return {"status": True, "message": ""}, 204

    @access_required(role_dict["product"])
    def put(self, groups_id):
        user = g.user_info["username"]
        args = parser.parse_args()
        args["id"] = groups_id
        groups = args
        db = DB()
        status, result = db.select("groups", "where data -> '$.name'='%s'" % args["name"])
        if status is True:
            if len(result) != 0:
                info = eval(result[0][0])
                if groups_id != info.get("id"):
                    return {"status": False, "message": "The groups name already exists"}, 200
        status, result = db.update_by_id("groups", json.dumps(groups, ensure_ascii=False), groups_id)
        db.close_mysql()
        if status is not True:
            logger.error("Modify groups error: %s" % result)
            return {"status": False, "message": result}, 500
        audit_log(user, groups_id, "", "groups", "edit")
        return {"status": True, "message": ""}, 200


class GroupsList(Resource):
    @access_required(role_dict["product"])
    def get(self):
        product_id = request.args.get("product_id")
        db = DB()
        status, result = db.select("groups", "where data -> '$.product_id'='%s'" % product_id)
        db.close_mysql()
        groups_list = []
        if status is True:
            if result:
                for i in result:
                    try:
                        groups_list.append(eval(i[0]))
                    except Exception as e:
                        return {"status": False, "message": str(e)}, 500
            else:
                return {"status": False, "message": "Group does not exist"}, 404
        else:
            return {"status": False, "message": result}, 500
        return {"groups": {"groups": groups_list}}, 200

    @access_required(role_dict["product"])
    def post(self):
        args = parser.parse_args()
        args["id"] = uuid_prefix("g")
        user = g.user_info["username"]
        groups = args
        db = DB()
        status, result = db.select("groups", "where data -> '$.name'='%s'" % args["name"])
        if status is True:
            if len(result) == 0:
                insert_status, insert_result = db.insert("groups", json.dumps(groups, ensure_ascii=False))
                db.close_mysql()
                if insert_status is not True:
                    logger.error("Add groups error: %s" % insert_result)
                    return {"status": False, "message": insert_result}, 500
                audit_log(user, args["id"], "", "groups", "add")
                return {"status": True, "message": ""}, 201
            else:
                return {"status": False, "message": "The groups name already exists"}, 200
        else:
            logger.error("Select groups name error: %s" % result)
            return {"status": False, "message": result}, 500
