# -*- coding:utf-8 -*-
from flask_restful import Resource, reqparse
from common.log import Logger
from common.db import DB
from passlib.apps import custom_app_context
from common.utility import uuid_prefix
import json


logger = Logger()

parser = reqparse.RequestParser()
parser.add_argument("username", type=str, required=True, trim=True)
parser.add_argument("password", type=str, required=True, trim=True)


class User(Resource):
    def post(self):
        args = parser.parse_args()
        db = DB()
        status, result = db.select("user", "where data -> '$.username'='%s'" % args["username"])
        if status:
            if len(result) == 0:
                password_hash = custom_app_context.encrypt(args["password"])
                user = {"id": uuid_prefix("u"),
                        "username": args["username"],
                        "password": password_hash}
                db.insert("user", json.dumps(user, ensure_ascii=False))
                db.close_mysql()
                return {"status": True, "message": ""}, 200
            else:
                return {"status": False, "message": "The user name already exists"}, 200
        else:
            return {"status": False, "message": result}, 200

