# -*- coding:utf-8 -*-
from flask_restful import Resource, reqparse, request
from fileserver.git_fs import gitlab_project
from common.const import role_dict
from common.log import loggers
from common.sso import access_required
from common.audit_log import audit_log
from flask import g
from resources.sls import delete_sls
import base64

logger = loggers()

parser = reqparse.RequestParser()
parser.add_argument("product_id", type=str, required=True, trim=True)
parser.add_argument("branch", type=str, default="master", trim=True)
parser.add_argument("path", type=str, default="", trim=True)
parser.add_argument("project_type", type=str, required=True, trim=True)
parser.add_argument("action", type=str, default="", trim=True)
parser.add_argument("content", type=str, default="", trim=True)


# 获取所有分支
class BranchList(Resource):
    @access_required(role_dict["common_user"])
    def get(self):
        args = parser.parse_args()
        project, _ = gitlab_project(args["product_id"], args["project_type"])
        if isinstance(project, dict):
            return project, 500
        else:
            branch_list = []
            try:
                branch = project.branches.list()
                for b in branch:
                    branch_list.append(b.name)
            except Exception as e:
                logger.error("Get branch error: %s" % e)
                return {"status": False, "message": str(e)}, 500
            return {"data": branch_list, "status": True, "message": ""}, 200


# 获取目录结构
class FilesList(Resource):
    @access_required(role_dict["common_user"])
    def get(self):
        args = parser.parse_args()
        project, product_name = gitlab_project(args["product_id"], args["project_type"])
        if isinstance(project, dict):
            return project, 500
        else:
            file_list = []
            try:
                items = project.repository_tree(path=args["path"], ref_name=args["branch"], all=True)
            except Exception as e:
                logger.error("Get file list error: %s" % e)
                return {"status": False, "message": str(e)}, 404

        if args["path"] == "/" or args["path"] is "":
            for i in items:
                if i["type"] == "tree":
                    file_list.append({"title": i["name"],
                                      "type": i["type"],
                                      "path": i["name"],
                                      "loading": False,
                                      "children": []
                                      })
                else:
                    file_list.append({"title": i["name"],
                                      "type": i["type"],
                                      "path": i["name"],
                                      })
            return {"data": [{
                    "title": product_name,
                    "expand": True,
                    "children": file_list,
                    "type": "tree",
                    }], "status": True, "message": ""}, 200
        else:
            for i in items:
                if i["type"] == "tree":
                    file_list.append({"title": i["name"],
                                      "type": i["type"],
                                      "path": args["path"] + "/" + i["name"],
                                      "loading": False,
                                      "children": []
                                      })
                else:
                    file_list.append({"title": i["name"],
                                      "type": i["type"],
                                      "path": args["path"] + "/" + i["name"],
                                      })
            return {"data": file_list, "status": True, "message": ""}, 200


# 获取文件内容
class FileContent(Resource):
    @access_required(role_dict["common_user"])
    def get(self):
        args = parser.parse_args()
        project, _ = gitlab_project(args["product_id"], args["project_type"])
        if isinstance(project, dict):
            return project, 500
        else:
            try:
                content = project.files.get(file_path=args["path"], ref=args["branch"])
                content_decode = content.decode().decode("utf-8")
            except Exception as e:
                logger.error("Get file content: %s" % e)
                return {"status": False, "message": str(e)}, 404
            return {"data": content_decode, "status": True, "message": ""}, 200


# 创建修改提交文件
class Commit(Resource):
    @access_required(role_dict["common_user"])
    def post(self):
        args = parser.parse_args()
        user = g.user_info["username"]
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
                # 假如删除，删除数据库中封装的SLS信息
                if args["action"] == "delete":
                    delete_sls(args["path"])
                audit_log(user, args["path"], args["product_id"], "sls", args["action"])
            except Exception as e:
                logger.error("Commit file: %s" % e)
                return {"status": False, "message": str(e)}, 500
            return {"status": True, "message": ""}, 200


# 上传文件
class Upload(Resource):
    @access_required(role_dict["common_user"])
    def post(self):
        args = parser.parse_args()
        user = g.user_info["username"]
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
                audit_log(user, file_path, args["product_id"], "sls", "upload")
            except Exception as e:
                logger.error("Upload file: %s" % e)
                return {"status": False, "message": str(e)}, 500
            return {"status": True, "message": ""}, 200
