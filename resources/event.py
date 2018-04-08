# -*- coding:utf-8 -*-
from flask_restful import Resource, reqparse
from common.log import Logger
from common.sso import access_required
from common.db import DB
from common.const import role_dict


logger = Logger()

parser = reqparse.RequestParser()
parser.add_argument("product_id", type=str, required=True, trim=True)


class Event(Resource):
    @access_required(role_dict["common_user"])
    def get(self):
        return True, 200


class EventList(Resource):
    @access_required(role_dict["common_user"])
    def get(self):
        db = DB()
        args = parser.parse_args()
        status, result = db.select("event", "where data -> '$.product_id'='%s'" % args["product_id"])
        db.close_mysql()
        event_list = []
        if status is True:
            if result:
                for i in result:
                    try:
                        event_list.append(eval(i[0]))
                    except Exception as e:
                        return {"status": False, "message": str(e)}, 200
            else:
                return {"status": False, "message": "Even does not exist"}, 200
        else:
            return {"status": False, "message": result}, 200
        return {"events": {"event": event_list}}, 200
