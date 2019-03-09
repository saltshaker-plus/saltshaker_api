# -*- coding:utf-8 -*-
import flask_restful
from resources.minions import MinionsKeys, MinionsStatus, MinionsGrains, MinionsGrainsList
from resources.job import Job, JobList, JobManager
from resources.event import Event, EventList
from system.product import ProductList, Product, ProductCheck
from system.role import RoleList, Role
from system.user import UserList, User, Register, ResetPassword, ResetPasswordByOwner, ChangeUserInfo
from system.login import Login
from system.acl import ACLList, ACL
from system.groups import GroupsList, Groups
from system.host import HostList, Host
from resources.log import LogList
from resources.cherry_stats import CherryStats
from resources.execute import ExecuteShell, ExecuteSLS, ExecuteGroups
from resources.gitfs import BranchList, FilesList, FileContent, Commit, Upload
from resources.dashboard import GrainsStatistics, TitleInfo, Minion, ServiceStatus
from kit.tools import HostSync, GrainsSync
from resources.command import HistoryList
from resources.pillar import PillarItems
from resources.rsa_encrypt import RSA
from resources.sse import SSE, SSEStatus
from webhook.salt_hook import Hook
from period.period_task import *
from common.utility import custom_abort
from resources.sls import SLSCreate


api = flask_restful.Api(catch_all_404s=True)

# 重新定义flask restful 400错误
flask_restful.abort = custom_abort

# login
api.add_resource(Login, "/saltshaker/api/v1.0/login")

# sse
api.add_resource(SSE, "/saltshaker/api/v1.0/sse")
api.add_resource(SSEStatus, "/saltshaker/api/v1.0/sse/status")

# product
api.add_resource(ProductList, "/saltshaker/api/v1.0/product")
api.add_resource(Product, "/saltshaker/api/v1.0/product/<string:product_id>")
api.add_resource(ProductCheck, "/saltshaker/api/v1.0/product/check/<string:name>")

# role
api.add_resource(RoleList, "/saltshaker/api/v1.0/role")
api.add_resource(Role, "/saltshaker/api/v1.0/role/<string:role_id>")

# acl
api.add_resource(ACLList, "/saltshaker/api/v1.0/acl")
api.add_resource(ACL, "/saltshaker/api/v1.0/acl/<string:acl_id>")

# user
api.add_resource(UserList, "/saltshaker/api/v1.0/user")
api.add_resource(User, "/saltshaker/api/v1.0/user/<string:user_id>")
api.add_resource(Register, "/saltshaker/api/v1.0/user/register")
api.add_resource(ResetPassword, "/saltshaker/api/v1.0/user/reset/<string:user_id>")
api.add_resource(ResetPasswordByOwner, "/saltshaker/api/v1.0/user/reset/owner/<string:user_id>")
api.add_resource(ChangeUserInfo, "/saltshaker/api/v1.0/user/change/<string:user_id>")

# groups
api.add_resource(GroupsList, "/saltshaker/api/v1.0/groups")
api.add_resource(Groups, "/saltshaker/api/v1.0/groups/<string:groups_id>")

# host
api.add_resource(HostList, "/saltshaker/api/v1.0/host")
api.add_resource(Host, "/saltshaker/api/v1.0/host/<string:host_id>")

# minions
api.add_resource(MinionsStatus, "/saltshaker/api/v1.0/minions/status")
api.add_resource(MinionsKeys, "/saltshaker/api/v1.0/minions/key")
api.add_resource(MinionsGrains, "/saltshaker/api/v1.0/minions/grain")
api.add_resource(MinionsGrainsList, "/saltshaker/api/v1.0/minions/grains")

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
# api.add_resource(ExecuteModule, "/saltshaker/api/v1.0/execute/module")

# gitlab
api.add_resource(BranchList, "/saltshaker/api/v1.0/gitlab/branch")
api.add_resource(FilesList, "/saltshaker/api/v1.0/gitlab/file")
api.add_resource(FileContent, "/saltshaker/api/v1.0/gitlab/content")
api.add_resource(Commit, "/saltshaker/api/v1.0/gitlab/commit")
api.add_resource(Upload, "/saltshaker/api/v1.0/gitlab/upload")

# audit log
api.add_resource(LogList, "/saltshaker/api/v1.0/log")

# period task
api.add_resource(PeriodList, "/saltshaker/api/v1.0/period")
api.add_resource(Period, "/saltshaker/api/v1.0/period/<string:period_id>")
api.add_resource(Reopen, "/saltshaker/api/v1.0/period/reopen/<string:period_id>")
api.add_resource(ConcurrentPause, "/saltshaker/api/v1.0/period/concurrent/pause/<string:period_id>")
api.add_resource(ConcurrentPlay, "/saltshaker/api/v1.0/period/concurrent/play/<string:period_id>")
api.add_resource(SchedulerPause, "/saltshaker/api/v1.0/period/scheduler/pause/<string:period_id>")
api.add_resource(SchedulerResume, "/saltshaker/api/v1.0/period/scheduler/resume/<string:period_id>")

# command log
api.add_resource(HistoryList, "/saltshaker/api/v1.0/history")

# CherryPy server stats
api.add_resource(CherryStats, "/saltshaker/api/v1.0/cherry/stats")

# hook
api.add_resource(Hook, "/saltshaker/api/v1.0/hook")

# pillar
api.add_resource(PillarItems, "/saltshaker/api/v1.0/pillar")

# rsa
api.add_resource(RSA, "/saltshaker/api/v1.0/rsa")

# kit
api.add_resource(HostSync, "/saltshaker/api/v1.0/host/sync")
api.add_resource(GrainsSync, "/saltshaker/api/v1.0/grains/sync")

# dashboard
api.add_resource(GrainsStatistics, "/saltshaker/api/v1.0/dashboard/grains/<string:item>")
api.add_resource(TitleInfo, "/saltshaker/api/v1.0/dashboard/title")
api.add_resource(Minion, "/saltshaker/api/v1.0/dashboard/minion")
api.add_resource(ServiceStatus, "/saltshaker/api/v1.0/dashboard/status")

# sls
api.add_resource(SLSCreate, "/saltshaker/api/v1.0/sls/create")
