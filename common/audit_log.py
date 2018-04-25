# -*- coding:utf-8 -*-
from common.db import DB, loggers
import time
import json


def audit_log(user, id, product_id, action_object, action_type):
    db = DB()
    log = {
        "time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
        "user": user,
        "id": id,
        "product_id": product_id,
        "action_object": action_object,
        "action_type": action_type
    }
    status, result = db.insert("audit_log", json.dumps(log, ensure_ascii=False))
    db.close_mysql()
    logger = loggers()
    if status is not True:
        logger.error("Add audit log error: %s" % result)
