# -*- coding:utf-8 -*-
from common.db import DB
from common.utility import uuid_prefix
from passlib.apps import custom_app_context
import json
import click


def init_db(username, password):
    db = DB()
    # 创建数据库表
    tables = [
        "user",
        "role",
        "acl",
        "groups",
        "product",
        "audit_log",
        "event"
    ]
    for t in tables:
        status, result = db.create_table(t)
        if status is True:
            click.echo("Create %s table is successful" % t)
        else:
            click.echo("Create %s table is false: %s" % (t, result))
    # 添加角色
    status, result = db.select("role", "where data -> '$.tag'=%s" % 0)
    role_id = uuid_prefix("r")
    if status is True:
        if len(result) == 0:
            role = {
                "id": role_id,
                "name": "超级管理员",
                "description": "所有权限",
                "tag": 0
            }
            insert_status, insert_result = db.insert("role", json.dumps(role, ensure_ascii=False))
            if insert_status is not True:
                click.echo("Init role error: %s" % insert_result)
                return
        click.echo("Init role successful")
    else:
        click.echo("Init role error: %s" % result)
        return
    # 添加用户
    status, result = db.select("user", "where data -> '$.username'='%s'" % username)
    if status is True:
        if len(result) == 0:
            password_hash = custom_app_context.encrypt(password)
            users = {
                "id": uuid_prefix("u"),
                "username": username,
                "password": password_hash,
                "role": [role_id]
            }
            insert_status, insert_result = db.insert("user", json.dumps(users, ensure_ascii=False))
            db.close_mysql()
            if insert_status is not True:
                click.echo("Init user error: %s" % insert_result)
                return
            click.echo("Init user successful")
        else:
            click.echo("The user name already exists")
            return
    else:
        click.echo("Init user error: %s" % result)
        return
    click.echo("Successful")
