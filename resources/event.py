# -*- coding:utf-8 -*-
from flask_restful import Resource, reqparse
from common.log import loggers
from common.sso import access_required
from common.db import DB
from common.const import role_dict


logger = loggers()

parser = reqparse.RequestParser()
parser.add_argument("product_id", type=str, required=True, trim=True)


class Event(Resource):
    @access_required(role_dict["common_user"])
    def get(self, job_id):
        db = DB()
        args = parser.parse_args()
        status, result = db.select("event", "where data -> '$.data.product_id'='%s' and data -> '$.data.jid'='%s'"
                                   % (args["product_id"], job_id))
        db.close_mysql()
        if status is True:
            if result:
                return {"event": result, "status": True, "message": ""}, 200
            else:
                return {"status": False, "message": "%s does not exist" % job_id}, 404
        else:
            return {"status": False, "message": result}, 500


class EventList(Resource):
    @access_required(role_dict["common_user"])
    def get(self):
        db = DB()
        args = parser.parse_args()
        status, result = db.select("event", "where data -> '$.data.product_id'='%s'" % args["product_id"])
        db.close_mysql()
        if status is True:
            if result:
                return {"events": {"event": result}, "status": True, "message": ""}, 200
            else:
                return {"status": False, "message": "Even does not exist"}, 404
        else:
            return {"status": False, "message": result}, 500
