# -*- coding:utf-8 -*-
from flask import Flask, request, make_response
from flask_restful import Api
from resources.minions import MinionsKeys, MinionsStatus, MinionsGrains
from resources.job import Job, JobList, JobManager
from resources.event import Event, EventList
from user.product import ProductList, Product
from user.role import RoleList, Role
from user.user import UserList, User
from user.acl import ACLList, ACL
from user.groups import GroupsList, Groups
from resources.log import LogList
from common.sso import create_token, verify_password
import os
import configparser


config = configparser.ConfigParser()
conf_path = os.path.dirname(os.path.realpath(__file__))
config.read(conf_path + "/saltshaker.conf")
expires_in = int(config.get("Token", "EXPIRES_IN"))


app = Flask(__name__)
api = Api(app)

# login
#api.add_resource(Login, "/login")

# product
api.add_resource(ProductList, "/saltshaker/api/v1.0/product")
api.add_resource(Product, "/saltshaker/api/v1.0/product/<string:product_id>")

# role
api.add_resource(RoleList, "/saltshaker/api/v1.0/role")
api.add_resource(Role, "/saltshaker/api/v1.0/role/<string:role_id>")

# acl
api.add_resource(ACLList, "/saltshaker/api/v1.0/acl")
api.add_resource(ACL, "/saltshaker/api/v1.0/acl/<string:acl_id>")

# user
api.add_resource(UserList, "/saltshaker/api/v1.0/user")
api.add_resource(User, "/saltshaker/api/v1.0/user/<string:user_id>")

# group
api.add_resource(GroupsList, "/saltshaker/api/v1.0/groups")
api.add_resource(Groups, "/saltshaker/api/v1.0/groups/<string:groups_id>")

# minions
api.add_resource(MinionsStatus, "/saltshaker/api/v1.0/minions/status")
api.add_resource(MinionsKeys, "/saltshaker/api/v1.0/minions/keys")
api.add_resource(MinionsGrains, "/saltshaker/api/v1.0/minions/grains")

# job
api.add_resource(JobList, "/saltshaker/api/v1.0/job")
api.add_resource(Job, "/saltshaker/api/v1.0/job/<string:job_id>")
api.add_resource(JobManager, "/saltshaker/api/v1.0/job/manager")

# event
api.add_resource(EventList, "/saltshaker/api/v1.0/event")
api.add_resource(Event, "/saltshaker/api/v1.0/event/<string:job_id>")

# audit log
api.add_resource(LogList, "/saltshaker/api/v1.0/log")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if verify_password(username, password):
            cookie_key, token = create_token(username)
            response = make_response('<a href=/saltshaker/api/v1.0/role>Role</a></br>'
                                     '<a href=/saltshaker/api/v1.0/product>Product</a></br>'
                                     '<a href=/saltshaker/api/v1.0/user>User</a></br>'
                                     '<a href=/saltshaker/api/v1.0/groups>Groups</a></br>'
                                     '<p>' + token.decode('utf-8') + '</p>'
                                     )
            response.set_cookie(cookie_key, token, expires_in)
            return response
        else:
            return "用户名或者密码错"

    return """
    <form action="" method="post">
        <p><input type=text name=username>
        <p><input type=text name=password>
        <p><input type=submit value=Login>
    </form>
    """


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
