# -*- coding:utf-8 -*-
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from passlib.apps import custom_app_context
import configparser
from common.redis import RedisTool
from common.db import DB
import os
from flask import request, g

config = configparser.ConfigParser()
conf_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
config.read(conf_path + "/saltshaker.conf")
secret_key = config.get("Token", "SECRET_KEY")
expires_in = int(config.get("Token", "EXPIRES_IN"))
cookie_key = config.get("Token", "COOKIE_KEY")


serializer = Serializer(secret_key, expires_in=expires_in)


# 登录认证token并更新token过期时间
def login_required(func):
    def verify_token(*args, **kwargs):
        # 通过 Cookie Token 进行认证
        token = request.cookies.get(cookie_key)
        try:
            g.user = RedisTool.get(token)
        except Exception as e:
            return {"status": False, "message": str(e)}, 500
        if RedisTool.get(token):
            RedisTool.expire(token, expires_in)
            return func(*args, **kwargs)
        # 通过 Bearer Token 进行认证
        elif 'Authorization' in request.headers:
            try:
                scheme, cred = request.headers['Authorization'].split(None, 1)
            except ValueError:
                # 不正确的 Authorization header
                pass
            else:
                g.user = RedisTool.get(cred)
                if scheme == 'Bearer' and RedisTool.get(cred):
                    RedisTool.expire(token, expires_in)
                    return func(*args, **kwargs)
                else:
                    return {"status": False, "message": "Unauthorized access"}, 401
        else:
            return {"status": False, "message": "Unauthorized access"}, 401
    return verify_token


def create_token(username):
    token = serializer.dumps({'username': username})
    RedisTool.setex(token, expires_in, username)
    return cookie_key, token


# 基于 Passlib 的离散哈希 BasicAuth
def verify_password(username, password):
    db = DB()
    status, result = db.select("user", "where data -> '$.username'='%s'" % username)
    db.close_mysql()
    if status:
        if len(result) > 0:
            password_hash = eval(result[0][0]).get("password")
            if custom_app_context.verify(password, password_hash):
                return True
    else:
        return False
