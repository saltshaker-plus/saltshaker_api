# -*- coding:utf-8 -*-
from common.db import DB
from common.utility import uuid_prefix
from common.const import role_dict
from passlib.apps import custom_app_context
import json
import click
import os
import time


def initialize(username, password):
    # 创建日志路径
    log_path = "/var/log/saltshaker_plus"
    if not os.path.exists(log_path):
        os.mkdir(log_path)
        click.echo("Create [%s] log path is successful" % log_path)
    db = DB()
    # 创建数据库表
    tables = [
        "user",
        "role",
        "acl",
        "groups",
        "product",
        "audit_log",
        "event",
        "cmd_history",
        "host",
        "grains",
        "period_task",
        "period_result",
        "period_audit",
        "sls"
    ]
    for t in tables:
        status, result = db.create_table(t)
        if status is True:
            click.echo("Create %s table is successful" % t)
        else:
            click.echo("Create %s table is false: %s" % (t, result))
    # 添加角色
    role = [
        {
            "id": uuid_prefix("r"),
            "name": "超级管理员",
            "description": "所有权限",
            "tag": role_dict["superuser"]
        },
        {
            "id": uuid_prefix("r"),
            "name": "普通用户",
            "description": "默认普通用户",
            "tag": role_dict["common_user"]
        },
        {
            "id": uuid_prefix("r"),
            "name": "产品管理员",
            "description": "管理产品权限",
            "tag": role_dict["product"]
        },
        {
            "id": uuid_prefix("r"),
            "name": "用户管理员",
            "description": "管理用户权限",
            "tag": role_dict["user"]
        },
        {
            "id": uuid_prefix("r"),
            "name": "访问控制管理员",
            "description": "管理访问控制列权限",
            "tag": role_dict["acl"]
        },
            ]
    for i in range(5):
        # 避免生成的uuid过于相似
        time.sleep(1)
        status, result = db.select("role", "where data -> '$.tag'=%s" % i)
        if status is True:
            if len(result) == 0:
                insert_status, insert_result = db.insert("role", json.dumps(role[i], ensure_ascii=False))
                if insert_status is not True:
                    click.echo("Init role error: %s" % insert_result)
                    return
                if i == role_dict["superuser"]:
                    role_id = role[i]["id"]
                click.echo("Init %s role successful" % role[i]["name"])
            else:
                click.echo("%s role already exists" % role[i]["name"])
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
                "role": [role_id],
                "acl": [],
                "groups": [],
                "product": [],
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
