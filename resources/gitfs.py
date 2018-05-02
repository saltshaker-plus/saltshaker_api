# -*- coding:utf-8 -*-
from flask_restful import Resource, reqparse
from fileserver.git_fs import gitlab_project
from common.const import role_dict
from common.log import loggers
from common.sso import access_required

logger = loggers()

parser = reqparse.RequestParser()
parser.add_argument("product_id", type=str, required=True, trim=True)
parser.add_argument("branch", type=str, default="master", trim=True)
parser.add_argument("path", type=str, default="", trim=True)
parser.add_argument("project_type", type=str, required=True, trim=True)


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
                items = project.repository_tree(path=args["path"], ref_name=args["branch"])
            except Exception as e:
                logger.error("Get file list error: %s" % e)
                return {"status": False, "message": str(e)}, 404
            for i in items:
                if i["type"] == "tree":
                    file_list.append({"title": i["name"],
                                      "type": i["type"],
                                      "expand": False,
                                      "children": [{'title':"test"}]
                                      })
                else:
                    file_list.append({"title": i["name"], "type": i["type"], "expand": True, "path": "/" + i["name"]})
            return {"data": [{
                    "title": product_name,
                    "expand": True,
                    "children": file_list
                    }], "status": True, "message": ""}, 200


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
            except Exception as e:
                logger.error("Get file content: %s" % e)
                return {"status": False, "message": str(e)}, 404
            return {"data": content.decode().decode("utf-8"), "status": True, "message": ""}, 200
