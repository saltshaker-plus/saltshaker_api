# -*- coding:utf-8 -*-
from flask_restful import Resource, reqparse
from common.log import Logger
from common.audit_log import audit_log
from common.db import DB
from common.utility import uuid_prefix
import json

logger = Logger()

parser = reqparse.RequestParser()
parser.add_argument("name", type=str, required=True, trim=True)
parser.add_argument("description", type=str)
parser.add_argument("salt_master_url", type=str, required=True, trim=True)
parser.add_argument("salt_master_user", type=str, required=True, trim=True)
parser.add_argument("salt_master_password", type=str, required=True, trim=True)


class Product(Resource):
    def get(self, product_id):
        db = DB()
        status, result = db.select_by_id("product", product_id)
        if status is True:
            if result:
                product = eval(result[0][0])
            else:
                return {"status": False, "message": "%s does not exist" % product_id}, 200
        else:
            return {"status": False, "message": result}, 200
        return {"product": product}

    def delete(self, product_id):
        user = get_user(self)
        db = DB()
        status, result = db.delete_by_id("product", product_id)
        if status is not True:
            logger.error("Delete product error: %s" % result)
            return {"status": False, "message": result}, 200
        if result is 0:
            return {"status": False, "message": "%s does not exist" % product_id}, 200
        audit_log(user, product_id, product_id, "product", "delete")
        return {"status": True, "message": ""}, 201

    def put(self, product_id):
        user = get_user(self)
        args = parser.parse_args()
        args["id"] = product_id
        product = args
        db = DB()
        status, result = db.update_by_id("product", json.dumps(product, ensure_ascii=False), product_id)
        if status is not True:
            logger.error("Modify product error: %s" % result)
            return {"status": False, "message": result}, 200
        audit_log(user, args["id"], product_id, "product", "edit")
        return {"status": True, "message": ""}, 201


class ProductList(Resource):
    def get(self):
        db = DB()
        status, result = db.select("product", "")
        product_list = []
        if status is True:
            if result:
                for i in result:
                    product_list.append(eval(i[0]))
        else:
            return {"status": False, "message": result}, 200
        return {"products": {"product": product_list}}

    def post(self):
        args = parser.parse_args()
        args["id"] = uuid_prefix("p")
        user = get_user(self)
        product = args
        db = DB()
        status, result = db.insert("product", json.dumps(product, ensure_ascii=False))
        if status is not True:
            logger.error("Add product error: %s" % result)
            return {"status": False, "message": result}, 200
        audit_log(user, args["id"], args["id"], "product", "add")
        return {"status": True, "message": ""}, 201
