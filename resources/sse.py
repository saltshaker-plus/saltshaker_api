# -*- coding:utf-8 -*-
from flask_restful import Resource, reqparse
from common.db import DB
from flask import g
from tasks.tasks import event_to_mysql

parser = reqparse.RequestParser()
parser.add_argument("action", type=str, required=True, trim=True)


class SSE(Resource):
    def get(self):
        db = DB()
        status, result = db.select("product", "")
        db.close_mysql()
        if status is True:
            if result:
                for product in result:
                    event_to_mysql.delay(product['id'])
                return {"data": "", "status": True, "message": ""}, 200
            else:
                return {"data": "", "status": False, "message": "Product does not exist"}, 404
        else:
            return {"data": "", "status": False, "message": result}, 500
