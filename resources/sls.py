# -*- coding:utf-8 -*-
from flask_restful import Resource, reqparse, request
from flask import g
from fileserver.git_fs import gitlab_project
from common.const import role_dict
from common.log import loggers
from common.sso import access_required
from common.db import DB
from common.parse_yaml import ParseYaml
import json
from common.audit_log import audit_log
from common.utility import uuid_prefix
import yaml

logger = loggers()

parser = reqparse.RequestParser()
parser.add_argument("product_id", type=str, required=True, trim=True)
parser.add_argument("branch", type=str, default="master", trim=True)
parser.add_argument("path", type=str, default="", trim=True)
parser.add_argument("project_type", type=str, trim=True)
parser.add_argument("action", type=str, default="", trim=True)
parser.add_argument("file_managed", type=dict, default={
    "name": "",
    "destination": "",
    "source": "",
    "user": "",
    "group": "",
    "template": "",
    "mode": 644,
    "attrs": ""
}, action="append")
parser.add_argument("file_directory", type=dict, action="append")
parser.add_argument("cmd_run", type=dict, action="append")
parser.add_argument("pkg_installed", type=dict, action="append")


# 封装SLS文件
class SLSCreate(Resource):
    @access_required(role_dict["common_user"])
    def post(self):
        args = parser.parse_args()
        args["id"] = uuid_prefix("s")
        user = g.user_info["username"]
        db = DB()
        print(args)
        print(args['file_managed'])
        yaml = ""
        status, result = db.select("sls", "where data -> '$.path'='%s'" % args["path"])
        if status is True:
            if len(result) == 0:
                insert_status, insert_result = db.insert("sls", json.dumps(args, ensure_ascii=False))
                db.close_mysql()
                if insert_status is not True:
                    logger.error("Add sls error: %s" % insert_result)
                    return {"status": False, "message": insert_result}, 500
                # 获取YAML文件格式
                for file_managed in args['file_managed']:
                    file = ParseYaml.file_managed(name=file_managed["name"],
                                                  destination=file_managed["destination"],
                                                  source=file_managed["source"],
                                                  user=file_managed["user"],
                                                  group=file_managed["group"],
                                                  template=file_managed["template"],
                                                  mode=file_managed["mode"],
                                                  attrs=file_managed["attrs"], )
                    yaml += file
                print(yaml)
                project, _ = gitlab_project(args["product_id"], args["project_type"])
                data = {
                    'branch': args["branch"],
                    'commit_message': args["action"] + " " + args["path"],
                    'actions': [
                        {
                            'action': args["action"],
                            'file_path': args["path"],
                            'content': yaml
                        }
                    ]
                }
                if isinstance(project, dict):
                    return project, 500
                else:
                    try:
                        project.commits.create(data)
                    except Exception as e:
                        logger.error("Commit file: %s" % e)
                        return {"status": False, "message": str(e)}, 500
                audit_log(user, args["id"], args["product_id"], "sls", "add")
                return {"status": True, "message": ""}, 201
            else:
                db.close_mysql()
                return {"status": False, "message": "The sls name already exists"}, 200
        else:
            db.close_mysql()
            logger.error("Select sls name error: %s" % result)
            return {"status": False, "message": result}, 500



# 创建修改提交文件
class Commit(Resource):
    @access_required(role_dict["common_user"])
    def post(self):
        args = parser.parse_args()
        project, _ = gitlab_project(args["product_id"], args["project_type"])
        # 支持的action create, delete, move, update
        data = {
            'branch': args["branch"],
            'commit_message': args["action"] + " " + args["path"],
            'actions': [
                {
                    'action': args["action"],
                    'file_path': args["path"],
                    'content': args["content"]
                }
            ]
        }
        if isinstance(project, dict):
            return project, 500
        else:
            try:
                project.commits.create(data)
            except Exception as e:
                logger.error("Commit file: %s" % e)
                return {"status": False, "message": str(e)}, 500
            return {"status": True, "message": ""}, 200


# 创建修改删除文件
class Upload(Resource):
    @access_required(role_dict["common_user"])
    def post(self):
        args = parser.parse_args()
        project, _ = gitlab_project(args["product_id"], args["project_type"])
        file = request.files['file']
        if args["path"]:
            file_path = args["path"] + "/" + file.filename
        content = file.read()
        try:
            content_decode = content.decode()
            actions = [
                {
                    'action': 'create',
                    'file_path': file_path,
                    'content': content_decode
                }
            ]
        except Exception as e:
            return {"status": False, "message": str(e)}, 500
        # try:
        #     content_decode = content.decode()
        #     actions = [
        #         {
        #             'action': args["action"],
        #             'file_path': file_path,
        #             'content': base64.b64encode(content_decode),
        #             'encoding': 'base64',
        #         }
        #     ]
        # except Exception as e:
        #     print(e)
        data = {
            'branch': args["branch"],
            'commit_message': args["action"] + " " + args["path"],
            'actions': actions
        }
        if isinstance(project, dict):
            return project, 500
        else:
            try:
                project.commits.create(data)
            except Exception as e:
                logger.error("Upload file: %s" % e)
                return {"status": False, "message": str(e)}, 500
            return {"status": True, "message": ""}, 200
