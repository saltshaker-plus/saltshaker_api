# -*- coding:utf-8 -*-
from flask_restful import Resource, reqparse
from common.log import loggers
from common.utility import salt_api_for_product
from common.sso import access_required
from common.const import role_dict

logger = loggers()

parser = reqparse.RequestParser()
parser.add_argument("product_id", type=str, required=True, trim=True)
parser.add_argument("tag", type=str, default="gitfs/update", trim=True)


class Hook(Resource):
    @access_required(role_dict["common_user"])
    def post(self):
        args = parser.parse_args()
        salt_api = salt_api_for_product(args["product_id"])
        if isinstance(salt_api, dict):
            return salt_api, 500
        else:
            result = salt_api.hook(args["tag"])
            if isinstance(result, dict):
                if result.get("success") is True:
                    return {"data": result, "status": True, "message": ""}, 200
                else:
                    return {"data": result, "status": False, "message": result}, 500
            else:
                return {"status": False, "message": result}, 500
