# -*- coding:utf-8 -*-
from flask_restful import Resource
from common.utility import generate_key_pair
from common.redis import RedisTool


class RSA(Resource):
    def get(self):
        try:
            public_key = RedisTool.get("public_key")
            if not public_key:
                generate_key_pair()
                public_key = RedisTool.get("public_key")
            return {"data": public_key, "status": True, "message": ""}, 200
        except Exception as e:
            return {"status": False, "message": str(e)}, 200
