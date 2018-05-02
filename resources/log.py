# -*- coding:utf-8 -*-
from flask_restful import Resource, reqparse
from common.log import loggers
from common.db import DB
from common.sso import access_required
from common.const import role_dict

logger = loggers()

parser = reqparse.RequestParser()
parser.add_argument("product_id", type=str, required=True, trim=True)


class LogList(Resource):
    @access_required(role_dict["common_user"])
    def get(self):
        args = parser.parse_args()
        db = DB()
        status, result = db.select("audit_log", "where data -> '$.product_id'='%s' order by data -> '$.time' desc"
                                   % args["product_id"])
        db.close_mysql()
        if status is True:
            return {"data": result, "status": True, "message": ""}, 200
        else:
            return {"status": False, "message": result}, 500

