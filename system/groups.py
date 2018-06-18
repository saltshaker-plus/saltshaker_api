# -*- coding:utf-8 -*-
from flask_restful import Resource, reqparse, request
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
parser.add_argument("product_id", type=str, required=True, trim=True)
# 不必填写的字段一定要指定默认值为""，否则无法转换成字典
parser.add_argument("description", type=str, default="", trim=True)
parser.add_argument("minion", type=str, default=[], action="append")


class Groups(Resource):
    @access_required(role_dict["product"])
    def get(self, groups_id):
        db = DB()
        status, result = db.select_by_id("groups", groups_id)
        db.close_mysql()
        if status is True:
            if result:
                return {"data": result, "status": True, "message": ""}, 200
            else:
                return {"status": False, "message": "%s does not exist" % groups_id}, 404
        else:
            return {"status": False, "message": result}, 500

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
        return {"status": True, "message": ""}, 200

    @access_required(role_dict["product"])
    def put(self, groups_id):
        user = g.user_info["username"]
        args = parser.parse_args()
        args["id"] = groups_id
        groups = args
        db = DB()
        # 判断产品线是否存在
        status, result = db.select_by_id("product", args["product_id"])
        if status is True:
            if not result:
                db.close_mysql()
                return {"status": False, "message": "%s does not exist" % args["product_id"]}, 404
        else:
            return {"status": False, "message": result}, 500
        # 判断是否存在
        select_status, select_result = db.select_by_id("groups", groups_id)
        if select_status is not True:
            db.close_mysql()
            logger.error("Modify groups error: %s" % select_result)
            return {"status": False, "message": select_result}, 500
        if not select_result:
            db.close_mysql()
            return {"status": False, "message": "%s does not exist" % groups_id}, 404
        # 判断名字否已经存在
        status, result = db.select("groups", "where data -> '$.name'='%s' and  data -> '$.product_id'='%s'"
                                   % (args["name"], args["product_id"]))
        if status is True and result:
            if groups_id != result[0].get("id"):
                db.close_mysql()
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
        if status is True:
            return {"data": result, "status": True, "message": ""}, 200
        else:
            return {"status": False, "message": result}, 500

    @access_required(role_dict["product"])
    def post(self):
        args = parser.parse_args()
        args["id"] = uuid_prefix("g")
        user = g.user_info["username"]
        groups = args
        db = DB()
        status, result = db.select_by_id("product", args["product_id"])
        if status is True:
            if not result:
                db.close_mysql()
                return {"status": False, "message": "%s does not exist" % args["product_id"]}, 404
        else:
            return {"status": False, "message": result}, 500
        status, result = db.select("groups", "where data -> '$.name'='%s' and data -> '$.product_id'='%s'"
                                   % (args["name"], args["product_id"]))
        if status is True:
            if len(result) == 0:
                insert_status, insert_result = db.insert("groups", json.dumps(groups, ensure_ascii=False))
                db.close_mysql()
                if insert_status is not True:
                    logger.error("Add groups error: %s" % insert_result)
                    return {"status": False, "message": insert_result}, 500
                audit_log(user, args["id"], "", "groups", "add")
                group_to_user(args["id"], g.user_info["id"])
                return {"status": True, "message": ""}, 201
            else:
                db.close_mysql()
                return {"status": False, "message": "The groups name already exists"}, 200
        else:
            db.close_mysql()
            logger.error("Select groups name error: %s" % result)
            return {"status": False, "message": result}, 500


def group_to_user(gid, uid):
    db = DB()
    select_status, select_result = db.select_by_id("user", uid)
    if select_status is True and select_result:
        select_result["groups"].append(gid)
    else:
        return {"status": False, "message": select_result}
    status, result = db.update_by_id("user", json.dumps(select_result, ensure_ascii=False), uid)
    db.close_mysql()
    if status is True:
        return {"status": True, "message": ""}
    else:
        logger.error("Group to user error: %s" % result)
        return {"status": False, "message": result}
