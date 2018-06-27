# -*- coding:utf-8 -*-
from flask_restful import Resource
from common.db import DB
from tasks.tasks import event_to_mysql


class SSE(Resource):
    def get(self):
        db = DB()
        status, result = db.select("product", "")
        db.close_mysql()
        if status is True and result:
            for product in result:
                event_to_mysql.delay(product['id'])
        return {"data": "", "status": True, "message": ""}
