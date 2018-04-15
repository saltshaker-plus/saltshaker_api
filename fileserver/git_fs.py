# -*- coding:utf-8 -*-
import gitlab
from common.db import DB


# GitLab >= 9.0 api_version 请填 4 否则请填 3
def gitlab_project(product_id, project_type):
    db = DB()
    status, result = db.select_by_id("product", product_id)
    db.close_mysql()
    if status is True:
        if result:
            product = eval(result[0][0])
        else:
            return {"status": False, "message": "%s does not exist" % product_id}
    else:
        return {"status": False, "message": result}
    try:
        if product.get("file_server") == "gitfs":
            gl = gitlab.Gitlab(url=product.get("gitlab_url"),
                               private_token=None if product.get("private_token") is "" else product.get("private_token"),
                               oauth_token=None if product.get("oauth_token") is "" else product.get("oauth_token"),
                               email=None if product.get("email") is "" else product.get("email"),
                               password=None if product.get("password") is "" else product.get("password"),
                               ssl_verify=True,
                               http_username=None if product.get("http_username") is "" else product.get("http_username"),
                               http_password=None if product.get("http_password") is "" else product.get("http_password"),
                               timeout=120,
                               api_version=None if product.get("api_version") is "" else product.get("api_version")
                               )

            project = gl.projects.get(product.get(project_type))
            return project, product.get(project_type)
        else:
            return {"status": False, "message": "File server is not gitfs"}, ""
    except Exception as e:
        return {"status": False, "message": str(e)}
