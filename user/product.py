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
from fileserver.rsync_fs import rsync_config

logger = Logger()

parser = reqparse.RequestParser()
parser.add_argument("name", type=str, required=True, trim=True)
parser.add_argument("description", type=str)
parser.add_argument("salt_master_id", type=str, required=True, trim=True)
parser.add_argument("salt_master_url", type=str, required=True, trim=True)
parser.add_argument("salt_master_user", type=str, required=True, trim=True)
parser.add_argument("salt_master_password", type=str, required=True, trim=True)
parser.add_argument("file_server", type=str, required=True, trim=True)

# GitLab 设置
parser.add_argument("gitlab_url", type=str, default="", trim=True)
parser.add_argument("private_token", type=str, default="", trim=True)
parser.add_argument("oauth_token", type=str, default="", trim=True)
parser.add_argument("email", type=str, default="", trim=True)
parser.add_argument("password", type=str, default="", trim=True)
parser.add_argument("http_username", type=str, default="", trim=True)
parser.add_argument("http_password", type=str, default="", trim=True)
parser.add_argument("api_version", type=str, default="", trim=True)
parser.add_argument("project", type=str, default="", trim=True)


class Product(Resource):
    @access_required(role_dict["product"])
    def get(self, product_id):
        db = DB()
        status, result = db.select_by_id("product", product_id)
        db.close_mysql()
        if status is True:
            if result:
                try:
                    product = eval(result[0][0])
                except Exception as e:
                    return {"status": False, "message": str(e)}, 500
            else:
                return {"status": False, "message": "%s does not exist" % product_id}, 404
        else:
            return {"status": False, "message": result}, 500
        return {"product": product}, 200

    @access_required(role_dict["product"])
    def delete(self, product_id):
        user = g.user_info["username"]
        db = DB()
        status, result = db.delete_by_id("product", product_id)
        db.close_mysql()
        if status is not True:
            logger.error("Delete product error: %s" % result)
            return {"status": False, "message": result}, 500
        if result is 0:
            return {"status": False, "message": "%s does not exist" % product_id}, 404
        audit_log(user, product_id, product_id, "product", "delete")
        info = update_user_privilege("product", product_id)
        if info["status"] is False:
            return {"status": False, "message": info["message"]}, 500
        # 更新Rsync配置
        rsync_config()
        return {"status": True, "message": ""}, 200

    @access_required(role_dict["product"])
    def put(self, product_id):
        user = g.user_info["username"]
        args = parser.parse_args()
        args["id"] = product_id
        product = args
        db = DB()
        # 判断是否存在
        select_status, select_result = db.select_by_id("product", product_id)
        if select_status is not True:
            db.close_mysql()
            logger.error("Modify product error: %s" % select_result)
            return {"status": False, "message": select_result}, 500
        if not select_result:
            db.close_mysql()
            return {"status": False, "message": "%s does not exist" % product_id}, 404
        # 判断名字是否重复
        status, result = db.select("product", "where data -> '$.name'='%s'" % args["name"])
        if status is True:
            if len(result) != 0:
                info = eval(result[0][0])
                if product_id != info.get("id"):
                    db.close_mysql()
                    return {"status": False, "message": "The product name already exists"}, 200
        status, result = db.update_by_id("product", json.dumps(product, ensure_ascii=False), product_id)
        db.close_mysql()
        if status is not True:
            logger.error("Modify product error: %s" % result)
            return {"status": False, "message": result}, 500
        audit_log(user, args["id"], product_id, "product", "edit")
        # 更新Rsync配置
        rsync_config()
        return {"status": True, "message": ""}, 200


class ProductList(Resource):
    @access_required(role_dict["product"])
    def get(self):
        db = DB()
        status, result = db.select("product", "")
        db.close_mysql()
        product_list = []
        if status is True:
            if result:
                for i in result:
                    try:
                        product_list.append(eval(i[0]))
                    except Exception as e:
                        return {"status": False, "message": str(e)}, 500
            else:
                return {"status": False, "message": "Product does not exist"}, 404
        else:
            return {"status": False, "message": result}, 500
        return {"products": {"product": product_list}}, 200

    @access_required(role_dict["product"])
    def post(self):
        args = parser.parse_args()
        args["id"] = uuid_prefix("p")
        user = g.user_info["username"]
        product = args
        db = DB()
        status, result = db.select("product", "where data -> '$.name'='%s'" % args["name"])
        if status is True:
            if len(result) == 0:
                insert_status, insert_result = db.insert("product", json.dumps(product, ensure_ascii=False))
                db.close_mysql()
                if insert_status is not True:
                    logger.error("Add product error: %s" % insert_result)
                    return {"status": False, "message": insert_result}, 500
                audit_log(user, args["id"], "", "product", "add")
                # 更新Rsync配置
                if args["file_server"] == "rsync":
                    rsync_config()
                return {"status": True, "message": ""}, 201
            else:
                db.close_mysql()
                return {"status": False, "message": "The product name already exists"}, 200
        else:
            db.close_mysql()
            logger.error("Select product name error: %s" % result)
            return {"status": False, "message": result}, 500



