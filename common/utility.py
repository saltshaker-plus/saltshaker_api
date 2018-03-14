# -*- coding:utf-8 -*-
from passlib.apps import custom_app_context
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import g
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


# 基于Pass lib 的离散哈希BasicAuth
def verify_password(username, password):
    db = DB()
    status, result = db.select("user", "where data -> '$.username'='%s'" % username)
    if status:
        if len(result) > 0:
            password_hash = eval(result[0][0]).get("password")
            if custom_app_context.verify(password, password_hash):
                # 保存在全局变量g中
                g.user = username
                return True
    else:
        return False


USER_LIST = {
    1: {'name': 'Michael'},
    2: {'name': 'Tom'},
}

for user_id in USER_LIST.keys():
    serializer = Serializer('saltshaker secret key', expires_in=1800)
    token = serializer.dumps({'id': user_id})
    print('Token for {}: {}\n'.format(USER_LIST[user_id]['name'], token))


def verify_token(token):
    g.user = None
    try:
        data = serializer.loads(token)
    except Exception as e:
        return False
    if 'id' in data:
        g.user = USER_LIST[data['id']]['name']
        return True
    return False
