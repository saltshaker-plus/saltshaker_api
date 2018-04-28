# -*- coding:utf-8 -*-
from flask_restful import Resource, reqparse
from common.log import loggers
from common.db import DB
from common.sso import access_required
from common.const import role_dict

logger = loggers()

parser = reqparse.RequestParser()
parser.add_argument("product_id", type=str, required=True, trim=True)


class ShellList(Resource):
    @access_required(role_dict["common_user"])
    def get(self):
        args = parser.parse_args()
        db = DB()
        status, result = db.select("cmd_history", "where data -> '$.product_id'='%s' order by data -> '$.time' desc"
                                   % args["product_id"])
        history_list = []
        if status is True:
            if result:
                for i in result:
                    history_dict = eval(i[0].replace('true', '"true"').replace('false', '"false"').replace('null', '""'))
                    user_status, user_result = db.select_by_id("user", history_dict["user_id"])
                    if user_status is True and user_result:
                        history_dict["username"] = eval(user_result[0][0])["username"]
                    history_list.append(history_dict)
        else:
            db.close_mysql()
            return {"status": False, "message": result}, 500
        db.close_mysql()
        return {"data": history_list, "status": True, "message": ""}, 200



