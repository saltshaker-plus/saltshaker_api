# -*- coding:utf-8 -*-
from flask_restful import Resource, reqparse
from fileserver.git_fs import gitlab_project
from common.const import role_dict
from common.log import Logger
from common.sso import access_required

logger = Logger()

parser = reqparse.RequestParser()
parser.add_argument("product_id", type=str, required=True, trim=True)
parser.add_argument("branch", type=str, default="master", trim=True)
parser.add_argument("path", type=str, default="", trim=True)


# 获取所有分支
class BranchList(Resource):
    @access_required(role_dict["common_user"])
    def get(self):
        args = parser.parse_args()
        project = gitlab_project(args["product_id"])
        if isinstance(project, dict):
            return project, 200
        else:
            branch_list = []
            branch = project.branches.list()
            for b in branch:
                branch_list.append(b.name)
            return {"branchs": {"branch": branch_list}, "status": True, "message": ""}, 200


# 获取目录结构
class FilesList(Resource):
    @access_required(role_dict["common_user"])
    def get(self):
        args = parser.parse_args()
        project = gitlab_project(args["product_id"])
        if isinstance(project, dict):
            return project, 200
        else:
            file_list = []
            try:
                items = project.repository_tree(path=args["path"], ref_name=args["branch"])
            except Exception as e:
                return {"status": False, "message": str(e)}, 200
            for i in items:
                file_list.append({"name": i["name"], "type": i["type"]})
            return {"files": {"file": file_list}, "status": True, "message": ""}, 200


# 获取文件内容
class FileContent(Resource):
    @access_required(role_dict["common_user"])
    def get(self):
        args = parser.parse_args()
        project = gitlab_project(args["product_id"])
        if isinstance(project, dict):
            return project, 200
        else:
            try:
                content = project.files.get(file_path=args["path"], ref=args["branch"])
            except Exception as e:
                return {"status": False, "message": str(e)}, 200
            return {"content": content.decode().decode("utf-8"), "status": True, "message": ""}, 200
