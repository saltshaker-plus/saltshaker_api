# -*- coding:utf-8 -*-
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from passlib.apps import custom_app_context
import configparser
from common.redis import RedisTool
from common.const import role_dict
from common.db import DB
import os
from flask import request, g
from common.log import loggers
import ast
from common.utility import rsa_decrypt

logger = loggers()

config = configparser.ConfigParser()
conf_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
config.read(conf_path + "/saltshaker.conf")
secret_key = config.get("Token", "SECRET_KEY")
expires_in = int(config.get("Token", "EXPIRES_IN"))
cookie_key = config.get("Token", "COOKIE_KEY")


serializer = Serializer(secret_key, expires_in=expires_in)


# 登录认证token并更新token过期时间,同时验证访问权限
def access_required(tag):
    def login_required(func):
        def verify_token(*args, **kwargs):
            # 通过 Cookie Token 进行认证
            token = request.cookies.get(cookie_key)
            if token:
                try:
                    user_info = ast.literal_eval(RedisTool.get(token).replace('true', 'True').
                                                 replace('false', 'False').replace('null', '""'))
                    # 验证是否有权限访问
                    if not verify_role(user_info, tag):
                        return {"status": False, "message": "Access forbidden"}, 403
                    g.user_info = user_info
                except Exception as e:
                    logger.error("Verify token error: %s" % e)
                    return {"status": False, "message": "Unauthorized access"}, 401
                if RedisTool.get(token):
                    RedisTool.expire(token, expires_in)
                    return func(*args, **kwargs)
            # 通过 Bearer Token 进行认证
            elif 'Authorization' in request.headers:
                try:
                    scheme, cred = request.headers['Authorization'].split(None, 1)
                    user_info = ast.literal_eval(RedisTool.get(cred).replace('true', 'True').
                                                 replace('false', 'False').replace('null', '""'))
                    # 验证是否有权限访问
                    if not verify_role(user_info, tag):
                        return {"status": False, "message": "access forbidden"}, 403
                    g.user_info = user_info
                except Exception as e:
                    logger.error("Verify token error: %s" % e)
                    return {"status": False, "message": "Unauthorized access"}, 401
                else:
                    if scheme == 'Bearer' and RedisTool.get(cred):
                        RedisTool.expire(token, expires_in)
                        return func(*args, **kwargs)
                    else:
                        return {"status": False, "message": "Unauthorized access"}, 401
            # 通过 X-Gitlab-Token 进行认证
            elif 'X-Gitlab-Token' in request.headers:
                gitlab_token = request.headers['X-Gitlab-Token']
                try:
                    user_info = ast.literal_eval(RedisTool.get(gitlab_token).replace('true', 'True').
                                                 replace('false', 'False').replace('null', '""'))
                    # 验证是否有权限访问
                    if not verify_role(user_info, tag):
                        return {"status": False, "message": "access forbidden"}, 403
                    g.user_info = user_info
                except Exception as e:
                    logger.error("Verify token error: %s" % e)
                    return {"status": False, "message": "Unauthorized access"}, 401
                if RedisTool.get(gitlab_token):
                    RedisTool.expire(gitlab_token, expires_in)
                    return func(*args, **kwargs)
            else:
                return {"status": False, "message": "Unauthorized access"}, 401
        return verify_token
    return login_required


def verify_role(user_info, tag):
    for role in user_info["role"]:
        db = DB()
        status, result = db.select_by_id("role", role)
        db.close_mysql()
        if status is True and result:
            try:
                if result["tag"] == role_dict["superuser"] or result["tag"] == tag:
                    return True
            except KeyError as _:
                return False
        else:
            return False
    return False


def create_token(username):
    token = serializer.dumps({'username': username})
    db = DB()
    status, result = db.select("user", "where data -> '$.username'='%s'" % username)
    db.close_mysql()
    if status is True and result:
        try:
            RedisTool.setex(token, expires_in, result[0])
        except Exception as e:
            logger.error("Verify password error: %s" % e)
    return cookie_key, token


# 基于 Passlib 的离散哈希 BasicAuth
def verify_password(username, password_rsa):
    db = DB()
    status, result = db.select("user", "where data -> '$.username'='%s'" % username)
    db.close_mysql()
    if status is True and result:
        try:
            # 数据库中获取离散哈希数据
            password_hash = result[0].get("password")
            # 基于RSA加密算法获取密码
            password = rsa_decrypt(password_rsa)
            if password is False:
                return False
            # 基于离散哈希的密码认证
            status = custom_app_context.verify(password, password_hash)
            return status
        except Exception as e:
            logger.error("Verify password error: %s" % e)
            return False
    else:
        logger.error("Verify password error: %s" % result)
        return False
