# -*- coding:utf-8 -*-
from common.db import DB
from common.saltstack_api import SaltAPI
import uuid


def uuid_prefix(prefix):
    str_uuid = str(uuid.uuid1())
    s_uuid = ''.join(str_uuid.split("-"))
    return prefix + "-" + s_uuid


def salt_api_for_product(product_id):
    db = DB()
    status, result = db.select_by_id("product", product_id)
    db.close_mysql()
    if status is True:
        if result:
            product = eval(result[0][0])
        else:
            return {"status": False, "message": "%s does not exist" % product_id}
    else:
        return {"status": False, "message": result}
    salt_api = SaltAPI(
        url=product.get("salt_master_url"),
        user=product.get("salt_master_user"),
        passwd=product.get("salt_master_password")
    )
    return salt_api



