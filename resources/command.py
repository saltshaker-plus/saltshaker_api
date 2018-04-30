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
        user_list = []
        user_status, user_result = db.select("user", "")
        if user_status is True and user_result:
            for i in user_result:
                try:
                    user_list.append(eval(i[0]))
                except Exception as e:
                    db.close_mysql()
                    return {"status": False, "message": str(e)}, 500
        db.close_mysql()
        print(user_list)
        if status is True:
            if result:
                for i in result:
                    history_dict = eval(i[0].replace('true', '"true"').replace('false', '"false"').replace('null', '""'))
                    for user in user_list:
                        if history_dict["user_id"] == user["id"]:
                            history_dict["username"] = user["username"]
                    history_list.append(history_dict)
        else:
            return {"status": False, "message": result}, 500
        return {"data": history_list, "status": True, "message": ""}, 200



