# -*- coding:utf-8 -*-
from flask import g
from flask_restful import Resource, reqparse
from common.log import Logger
from common.db import DB
from common.sso import login_required

logger = Logger()

parser = reqparse.RequestParser()
parser.add_argument("product_id", type=str, required=True, trim=True)


class LogList(Resource):
    @login_required
    def get(self):
        args = parser.parse_args()
        db = DB()
        status, result = db.select_by_id("audit_log", args["product_id"])
        log_list = []
        if status is True:
            if result:
                for i in result:
                    log_list.append(eval(i[0]))
        else:
            return {"status": False, "message": result}, 200
        return {"audit_logs": {"audit_log": log_list}}



