# -*- coding:utf-8 -*-
from flask_restful import Resource, reqparse
from flask import g
from common.log import loggers
from common.audit_log import audit_log
from common.utility import salt_api_for_product
from common.sso import access_required
from common.const import role_dict
from common.db import DB

logger = loggers()

parser = reqparse.RequestParser()
parser.add_argument("product_id", type=str, required=True, trim=True)
parser.add_argument("action", type=str, trim=True)
parser.add_argument("jid", type=str, trim=True)
parser.add_argument("minion", type=dict, trim=True, action="append")


class Job(Resource):
    @access_required(role_dict["common_user"])
    def get(self, job_id):
        args = parser.parse_args()
        salt_api = salt_api_for_product(args["product_id"])
        if isinstance(salt_api, dict):
            return salt_api, 500
        else:
            result = salt_api.jobs_info(job_id)
            return result, 200


class JobList(Resource):
    @access_required(role_dict["common_user"])
    def get(self):
        args = parser.parse_args()
        job_list = []
        db = DB()
        status, result = db.select("event", "where data -> '$.data.product_id'='%s' "
                                            "and data -> '$.data.jid'!='""' "
                                            "order by data -> '$.data._stamp' desc" % args["product_id"])
        db.close_mysql()
        if status is True:
            if result:
                for job in result:
                    job_list.append(job['data'])
        else:
            return {"status": False, "message": result}, 500
        return {"data": job_list, "status": True, "message": ""}, 200


class JobManager(Resource):
    @access_required(role_dict["common_user"])
    def get(self):
        args = parser.parse_args()
        salt_api = salt_api_for_product(args["product_id"])
        job_active_list = []
        if isinstance(salt_api, dict):
            return salt_api, 500
        else:
            result = salt_api.runner("jobs.active")
            if result:
                if result.get("status") is False:
                    return result, 500
                for jid, info in result.items():
                            # 不能直接把info放到append中
                            info.update({"Jid": jid})
                            job_active_list.append(info)
            return {"data": job_active_list, "status": True, "message": ""}, 200

    @access_required(role_dict["common_user"])
    def post(self):
        args = parser.parse_args()
        salt_api = salt_api_for_product(args["product_id"])
        user = g.user_info["username"]
        if isinstance(salt_api, dict):
            return salt_api, 500
        else:
            if args["action"] == "kill" and args["jid"] and args["minion"]:
                for minion in args["minion"]:
                    for minion_id, ppid in minion.items():
                        # 获取pgid 并杀掉
                        kill_ppid_pid = r'''ps -eo pid,pgid,ppid,comm |grep %s |grep salt-minion |
                                            awk '{print "kill -- -"$2}'|sh''' % ppid
                        try:
                            # kill_job = "salt %s saltutil.kill_job %s" % (minion_id, args["jid"])
                            # result = salt_api.shell_remote_execution(product.get("salt_master_id"), kill_job)
                            # audit_log(user, args["jid"], args["product_id"], "job id", "kill")
                            # logger.info("kill %s %s return: %s" % (minion, args["jid"], result))
                            audit_log(user, args["jid"], args["product_id"], "job id", "kill")
                            # 通过kill -- -pgid 删除salt 相关的父进程及子进程
                            pid_result = salt_api.shell_remote_execution(minion_id, kill_ppid_pid)
                            logger.info("kill %s %s return: %s" % (minion, kill_ppid_pid, pid_result))
                        except Exception as e:
                            logger.info("kill %s %s error: %s" % (minion, args["jid"], e))
                return {"status": True, "message": ""}, 200
            else:
                return {"status": False, "message": "The specified jid or action or minion_id "
                                                    "parameter does not exist"}, 400
