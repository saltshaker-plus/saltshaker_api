# -*- coding:utf-8 -*-
from common.db import DB, Logger
import time
import json


objects = {
    "product": "产品",
    "minion":  "minion",
}

types = {
    "edit": "编辑",
    "add": "添加",
    "delete": "删除",
    "accept": "同意",
    "reject": "拒绝",
}


def audit_log(user, id, product_id, action_object, action_type):
    db = DB()
    log = {
        "time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
        "user": user,
        "id": id,
        "product_id": product_id,
        "action_object": objects.get(action_object),
        "action_type": types.get(action_type)
    }
    status, result = db.insert("audit_log", json.dumps(log, ensure_ascii=False))
    logger = Logger()
    if status is not True:
        logger.error("Add action log error: %s" % result)
