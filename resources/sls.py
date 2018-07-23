# -*- coding:utf-8 -*-
from flask_restful import Resource, reqparse
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

logger = loggers()

parser = reqparse.RequestParser()
parser.add_argument("product_id", type=str, required=True, trim=True)
parser.add_argument("branch", type=str, default="master", trim=True)
parser.add_argument("path", type=str, default="", trim=True)
parser.add_argument("project_type", type=str, trim=True)
parser.add_argument("action", type=str, default="", trim=True)
parser.add_argument("file_managed", type=dict, action="append")
parser.add_argument("file_directory", type=dict, action="append")
parser.add_argument("cmd_run", type=dict, action="append")
parser.add_argument("pkg_installed", type=dict, action="append")
parser.add_argument("steps", required=True, type=dict, action="append")


# 封装SLS文件
class SLSCreate(Resource):
    @access_required(role_dict["common_user"])
    def post(self):
        args = parser.parse_args()
        args["id"] = uuid_prefix("s")
        user = g.user_info["username"]
        db = DB()
        yaml = ""
        status, result = db.select("sls", "where data -> '$.path'='%s'" % args["path"])
        if status is True:
            if len(result) == 0:
                insert_status, insert_result = db.insert("sls", json.dumps(args, ensure_ascii=False))
                db.close_mysql()
                if insert_status is not True:
                    logger.error("Add sls error: %s" % insert_result)
                    return {"status": False, "message": insert_result}, 500
                # 根据步骤循环
                for step in args['steps']:
                    # 文件管理
                    if step.get("state_name") == "file_managed" and args.get("file_managed"):
                        for file_managed in args.get("file_managed"):
                            # 在文件管理找到对应的ID
                            if step["id"] == file_managed.get("name"):
                                # 获取YAML文件格式
                                file = ParseYaml.file_managed(name=file_managed.get("name"),
                                                              destination=file_managed.get("destination"),
                                                              source=file_managed.get("source"),
                                                              user=file_managed.get("user"),
                                                              group=file_managed.get("group"),
                                                              template=file_managed.get("template"),
                                                              mode=file_managed.get("mode"))
                                yaml += file
                    if step.get("state_name") == "cmd_run" and args.get("cmd_run"):
                        for cmd_run in args.get("cmd_run"):
                            if step["id"] == cmd_run.get("name"):
                                # 获取YAML文件格式
                                file = ParseYaml.cmd_run(name=cmd_run.get("name"),
                                                         cmd=cmd_run.get("cmd"),
                                                         env=cmd_run.get("env"),
                                                         unless=cmd_run.get("unless"),
                                                         require=cmd_run.get("require"))
                                yaml += file
                    if step.get("state_name") == "pkg_installed" and args.get("pkg_installed"):
                        for pkg_installed in args.get("pkg_installed"):
                            if step["id"] == pkg_installed.get("name"):
                                # 获取YAML文件格式
                                file = ParseYaml.pkg_installed(name=pkg_installed.get("name"),
                                                               pkgs=pkg_installed.get("pkgs"))
                                yaml += file
                    if step.get("state_name") == "file_directory" and args.get("file_directory"):
                        for file_directory in args.get("file_directory"):
                            if step["id"] == file_directory.get("name"):
                                # 获取YAML文件格式
                                file = ParseYaml.file_directory(name=file_directory.get("name"),
                                                                destination=file_directory.get("destination"),
                                                                user=file_directory.get("user"),
                                                                group=file_directory.get("group"),
                                                                mode=file_directory.get("mode"),
                                                                makedirs=file_directory.get("makedirs"))
                                yaml += file
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


def delete_sls(path):
    db = DB()
    status, result = db.select("sls", "where data -> '$.path'='%s'" % path)
    if status is True and result:
        for sls in result:
            db.delete_by_id("sls", sls.get("id"))
