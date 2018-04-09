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
from user.host import HostList, Host, DifferenceHost
from resources.log import LogList
from resources.cherry_stats import CherryStats
from resources.execute import ExecuteShell, ExecuteSLS, ExecuteGroups
from resources.gitfs import BranchList, FilesList, FileContent
from common.cli import initialize
from common.sso import create_token, verify_password
import os
import click
import configparser
from flask_cors import CORS


config = configparser.ConfigParser()
conf_path = os.path.dirname(os.path.realpath(__file__))
config.read(conf_path + "/saltshaker.conf")
expires_in = int(config.get("Token", "EXPIRES_IN"))


app = Flask(__name__)
CORS(app, supports_credentials=True, resources={r"*": {"origins": "*"}})
api = Api(app, catch_all_404s=True)

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

# groups
api.add_resource(GroupsList, "/saltshaker/api/v1.0/groups")
api.add_resource(Groups, "/saltshaker/api/v1.0/groups/<string:groups_id>")

# host
api.add_resource(HostList, "/saltshaker/api/v1.0/host")
api.add_resource(DifferenceHost, "/saltshaker/api/v1.0/host_diff")
api.add_resource(Host, "/saltshaker/api/v1.0/host/<string:host_id>")

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

# execute
api.add_resource(ExecuteShell, "/saltshaker/api/v1.0/execute/shell")
api.add_resource(ExecuteSLS, "/saltshaker/api/v1.0/execute/sls")
api.add_resource(ExecuteGroups, "/saltshaker/api/v1.0/execute/groups")
#api.add_resource(ExecuteModule, "/saltshaker/api/v1.0/execute/module")

# gitlab
api.add_resource(BranchList, "/saltshaker/api/v1.0/gitlab/branch")
api.add_resource(FilesList, "/saltshaker/api/v1.0/gitlab/file")
api.add_resource(FileContent, "/saltshaker/api/v1.0/gitlab/content")

# audit log
api.add_resource(LogList, "/saltshaker/api/v1.0/log")

# CherryPy server stats
api.add_resource(CherryStats, "/saltshaker/api/v1.0/cherry/stats")


@app.cli.command()
@click.option('--username', prompt='Enter the initial administrators username', default='admin',
              help="Enter the initial username")
@click.option('--password', prompt='Enter the initial Administrators password', hide_input=True,
              confirmation_prompt=True, help="Enter the initial password")
def init(username, password):
    """Initialize the saltshaker_plus."""
    initialize(username, password)


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
                                     '<a href=/saltshaker/api/v1.0/groups?product_id='
                                     'p-b4aaef1e322611e8ab56000c298454d8>Groups</a></br>'
                                     '<a href=/saltshaker/api/v1.0/execute/groups>Execute Groups</a></br>'
                                     '<a href=/saltshaker/api/v1.0/event?product_id=p-c5008b0421d611e894b0000c298454d8>'
                                     'event</a></br>'
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