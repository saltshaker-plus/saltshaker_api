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
parser.add_argument("description", type=str)
parser.add_argument("salt_master_url", type=str, required=True, trim=True)
parser.add_argument("salt_master_user", type=str, required=True, trim=True)
parser.add_argument("salt_master_password", type=str, required=True, trim=True)


class Product(Resource):
    @login_required
    def get(self, product_id):
        db = DB()
        status, result = db.select_by_id("product", product_id)
        db.close_mysql()
        if status is True:
            if result:
                try:
                    product = eval(result[0][0])
                except Exception as e:
                    return {"status": False, "message": str(e)}, 200
            else:
                return {"status": False, "message": "%s does not exist" % product_id}, 200
        else:
            return {"status": False, "message": result}, 200
        return {"product": product}, 200

    @login_required
    def delete(self, product_id):
        user = g.user
        db = DB()
        status, result = db.delete_by_id("product", product_id)
        db.close_mysql()
        if status is not True:
            logger.error("Delete product error: %s" % result)
            return {"status": False, "message": result}, 200
        if result is 0:
            return {"status": False, "message": "%s does not exist" % product_id}, 200
        audit_log(user, product_id, product_id, "product", "delete")
        return {"status": True, "message": ""}, 201

    @login_required
    def put(self, product_id):
        user = g.user
        args = parser.parse_args()
        args["id"] = product_id
        product = args
        db = DB()
        status, result = db.update_by_id("product", json.dumps(product, ensure_ascii=False), product_id)
        db.close_mysql()
        if status is not True:
            logger.error("Modify product error: %s" % result)
            return {"status": False, "message": result}, 200
        audit_log(user, args["id"], product_id, "product", "edit")
        return {"status": True, "message": ""}, 201


class ProductList(Resource):
    @login_required
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
                        return {"status": False, "message": str(e)}, 200
        else:
            return {"status": False, "message": result}, 200
        return {"products": {"product": product_list}}, 200

    @login_required
    def post(self):
        args = parser.parse_args()
        args["id"] = uuid_prefix("p")
        user = g.user
        product = args
        db = DB()
        status, result = db.select("product", "where data -> '$.name'='%s'" % args["name"])
        if status is True:
            if len(result) == 0:
                insert_status, insert_result = db.insert("product", json.dumps(product, ensure_ascii=False))
                db.close_mysql()
                if insert_status is not True:
                    logger.error("Add product error: %s" % insert_result)
                    return {"status": False, "message": insert_result}, 200
                audit_log(user, args["id"], "", "product", "add")
                return {"status": True, "message": ""}, 201
            else:
                return {"status": False, "message": "The product name already exists"}, 200
        else:
            logger.error("Select product name error: %s" % result)
            return {"status": False, "message": result}, 200
