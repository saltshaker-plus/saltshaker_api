# -*- coding:utf-8 -*-
from flask_restful import Resource, reqparse
from common.log import loggers
from common.db import DB
from common.sso import access_required
from common.const import role_dict

logger = loggers()

parser = reqparse.RequestParser()
parser.add_argument("product_id", type=str, required=True, trim=True)
parser.add_argument("type", type=str, required=True, trim=True)


class HistoryList(Resource):
    @access_required(role_dict["common_user"])
    def get(self):
        args = parser.parse_args()
        db = DB()
        status, result = db.select("cmd_history", "where data -> '$.product_id'='%s' and "
                                                  "data -> '$.type'='%s' "
                                                  "order by data -> '$.time' desc" % (args["product_id"], args["type"]))
        history_list = []
        user_status, user_result = db.select("user", "")
        if user_status is True and user_result:
            user_list = user_result
        else:
            return {"status": False, "message": user_result}, 500
        db.close_mysql()
        if status is True:
            if result:
                for history in result:
                    for user in user_list:
                        if history["user_id"] == user["id"]:
                            history["username"] = user["username"]
                    history_list.append(history)
        else:
            return {"status": False, "message": result}, 500
        return {"data": history_list, "status": True, "message": ""}, 200



