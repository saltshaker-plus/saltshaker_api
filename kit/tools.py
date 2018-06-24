# -*- coding:utf-8 -*-
from flask_restful import Resource, reqparse, request
from flask import g
from common.log import loggers
from common.audit_log import audit_log
from common.db import DB
from common.sso import access_required
from system.host import Hosts
from common.utility import salt_api_for_product
import json
from common.const import role_dict
from resources.minions import create_grains

logger = loggers()

parser = reqparse.RequestParser()
parser.add_argument("product_id", type=str, required=True, trim=True)


class HostSync(Resource):
    @access_required(role_dict["common_user"])
    def get(self):
        user = g.user_info["username"]
        args = parser.parse_args()
        salt_api = salt_api_for_product(args["product_id"])
        minions = []
        if isinstance(salt_api, dict):
            return salt_api, 500
        else:
            result = salt_api.list_all_key()
            if result:
                if result.get("status") is False:
                    return result, 500
                for minion in result.get("minions"):
                    minions.append(minion)
        Hosts.add_host(minions, args["product_id"], user)
        return {"status": True, "message": ""}, 200


class GrainsSync(Resource):
    @access_required(role_dict["common_user"])
    def get(self):
        # user = g.user_info["username"]
        args = parser.parse_args()
        create_grains(args["product_id"])
        return {"status": True, "message": ""}, 200
