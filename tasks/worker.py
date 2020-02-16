# -*- coding:utf-8 -*-
from common.log import loggers
from common.audit_log import audit_log
from common.const import period_status, period_audit
import time
import json
import sseclient
import re
from common.db import DB
from common.utility import salt_api_for_product, utc_to_local
import ast

logger = loggers()


def grains_worker(minion_list, product_id):
    salt_api = salt_api_for_product(product_id)
    if isinstance(salt_api, dict):
        return salt_api, 500
    db = DB()
    for minion in minion_list:
        select_status, select_result = db.select("grains", "where data -> '$.id'='%s' and data -> "
                                                           "'$.product_id'='%s'" % (minion, product_id))
        print(minion)
        grains = salt_api.grains(minion)
        if grains.get("status"):
            if grains.get("data").get(minion):
                grains["data"][minion].update({"product_id": product_id})
                if select_status is True:
                    if len(select_result) > 1:
                        for m in select_result:
                            db.delete_by_id("grains", m["id"])
                        insert_status, insert_result = db.insert("grains", json.dumps(grains["data"][minion],
                                                                                      ensure_ascii=False))
                        if insert_status is not True:
                            logger.error("Add Grains error: %s" % insert_result)
                    elif len(select_result) == 1:
                        update_status, update_result = db.update_by_id("grains", json.dumps(grains["data"][minion],
                                                                                            ensure_ascii=False),
                                                                       select_result[0]["id"])
                        if update_status is not True:
                            logger.error("Update Grains error: %s" % update_result)
                    else:
                        insert_status, insert_result = db.insert("grains", json.dumps(grains["data"][minion],
                                                                                      ensure_ascii=False))
                        if insert_status is not True:
                            logger.error("Add Grains error: %s" % insert_result)
        else:
            continue
    db.close_mysql()


def sse_worker(product):
    # job_pattern = re.compile('salt/job/\d+/ret/')
    mine_pattern = re.compile(r'"fun": "mine.update"')
    saltutil_pattern = re.compile(r'"fun": "saltutil.find_job"')
    running_pattern = re.compile(r'"fun": "saltutil.running"')
    lookup_pattern = re.compile(r'"fun": "runner.jobs.lookup_jid"')
    event_pattern = re.compile(r'"tag": "salt/event/new_client"')
    event_audit = re.compile(r'"tag": "salt/auth"')
    whell_pattern = re.compile(r'"fun": "wheel.key.list_all"')
    salt_api = salt_api_for_product(product)
    event_response = salt_api.events()
    client = sseclient.SSEClient(event_response)
    for event in client.events():
        if mine_pattern.search(event.data):
            pass
        elif saltutil_pattern.search(event.data):
            pass
        elif running_pattern.search(event.data):
            pass
        elif lookup_pattern.search(event.data):
            pass
        elif event_pattern.search(event.data):
            pass
        elif event_audit.search(event.data):
            pass
        elif whell_pattern.search(event.data):
            pass
        else:
            event_dict = ast.literal_eval(event.data.replace('true', 'True').replace('false', 'False').
                                          replace('null', '""'))
            event_dict['data']['_stamp'] = utc_to_local(event_dict['data']['_stamp'] + "Z")
            event_dict['data']['product_id'] = product
            db = DB()
            db.insert("event", json.dumps(event_dict, ensure_ascii=False))
            db.close_mysql()


def job_worker(period_id, product_id, user):
    period_result, minion_list, salt_api = get_period(period_id, product_id)
    concurrent = int(period_result["concurrent"])
    # 非并行的job
    if concurrent == 0:
        no_concurrent(period_result, period_id, minion_list, salt_api, user, period_id)
    # 并行分组执行
    if concurrent > 0:
        grouping(concurrent, period_result, period_id, minion_list, salt_api, user, period_id)


# 并行的job
def grouping(concurrent, period_result, period_id, minion_list, salt_api, user, product_id):
    # 假如并行数大于minion的总数,range步长为minion长度，即一次全部运行
    # for m in period_result["executed_minion"]:
    #     minion_list.remove(m)
    if concurrent > len(minion_list):
        concurrent = len(minion_list)

    count = period_result["count"] if period_result["count"] != 0 else 1
    step = period_result["step"] if period_result["step"] != 0 else 0
    for i in range(step, len(minion_list), concurrent):
        db = DB()
        p_status, p_result = db.select_by_id("period_task", period_id)
        if p_status is True and p_result:
            if p_result.get("action") == "concurrent_play" or p_result.get("action") == "scheduler_resume":
                # 记录状态为第N组运行中
                p_result["status"] = {
                    "id": 7,
                    "name": period_status.get(7) % count
                }
                audits = {
                    "timestamp": int(time.time()),
                    "user": "机器人",
                    "option": period_audit.get(7) % count
                }
                insert_period_audit(period_id, audits)
                db.update_by_id("period_task", json.dumps(p_result, ensure_ascii=False), period_id)
                # 根据并行数，对minion进行切分
                minion = minion_list[i:i + concurrent]
                if period_result.get("execute") == "shell":
                    result = salt_api.shell_remote_execution(minion, period_result.get("shell"))
                elif period_result.get("execute") == "sls":
                    result = salt_api.target_deploy(minion, period_result.get("sls").replace(".sls", ""))
                # 执行结果写入到period_result表
                results = {
                    "time": int(time.time()),
                    "result": result,
                    "option": period_audit.get(7) % count
                }
                insert_period_result(period_id, results)
                # 执行完命令更新状态
                p_result["status"] = {
                    "id": 8,
                    "name": period_status.get(8) % count
                }
                # 执行审计写入到period_audit表
                audits = {
                    "timestamp": int(time.time()),
                    "user": "机器人",
                    "option": period_audit.get(8) % count
                }
                insert_period_audit(period_id, audits)
                p_result["count"] = count + 1
                p_result["step"] = step + concurrent
                # 并行间隔时间，最后一次不等待
                if concurrent < len(minion_list):
                    if i != list(range(0, len(minion_list), concurrent))[-1]:
                        time.sleep(int(p_result["interval"]))
                        count += 1
                    elif i == list(range(0, len(minion_list), concurrent))[-1]:
                        # 正常循环最后一次对计数几步长初始化
                        p_result["count"] = 0
                        p_result["step"] = 0
                db.update_by_id("period_task", json.dumps(p_result, ensure_ascii=False), period_id)
                db.close_mysql()
                # audit_log(user, minion, product_id, "minion", "shell")
    # 不同调度方式使用不同的状态显示
    if p_result["scheduler"] == "period":
        p_result["status"] = {
            "id": 9,
            "name": period_status.get(9)
        }
    elif p_result["scheduler"] == "crontab":
        p_result["status"] = {
            "id": 10,
            "name": period_status.get(10)
        }
    elif p_result.get("action") != "concurrent_pause":
        p_result["status"] = {
            "id": 3,
            "name": period_status.get(3)
        }
    if p_result.get("action") != "concurrent_pause":
        audits = {
            "timestamp": int(time.time()),
            "user": "机器人",
            "option": period_audit.get(3)
        }
        insert_period_audit(period_id, audits)
    db = DB()
    db.update_by_id("period_task", json.dumps(p_result, ensure_ascii=False), period_id)
    db.close_mysql()


# 非并行的job
def no_concurrent(period_result, period_id, minion_list, salt_api, user, product_id):
    db = DB()
    period_result["status"] = {
        "id": 2,
        "name": period_status.get(2)
    }
    db.update_by_id("period_task", json.dumps(period_result, ensure_ascii=False), period_id)
    if period_result.get("execute") == "shell":
        result = salt_api.shell_remote_execution(minion_list, period_result.get("shell"))
    elif period_result.get("execute") == "sls":
        # 去掉后缀
        sls = period_result.get("sls").replace(".sls", "")
        result = salt_api.target_deploy(minion_list, sls)
    results = {
        "time": int(time.time()),
        "result": result,
        "option": period_audit.get(9)
    }
    insert_period_result(period_id, results)
    # 不同调度方式使用不同的状态显示
    if period_result["scheduler"] == "period":
        period_result["status"] = {
            "id": 9,
            "name": period_status.get(9)
        }
    elif period_result["scheduler"] == "crontab":
        period_result["status"] = {
            "id": 10,
            "name": period_status.get(10)
        }
    else:
        period_result["status"] = {
            "id": 3,
            "name": period_status.get(3)
        }
    # 执行审计写入到period_audit表
    audits = {
        "timestamp": int(time.time()),
        "user": "机器人",
        "option": period_audit.get(3)
    }
    insert_period_audit(period_id, audits)
    db.update_by_id("period_task", json.dumps(period_result, ensure_ascii=False), period_id)
    db.close_mysql()
    audit_log(user, minion_list, product_id, "minion", "shell")


# 获取period和minion
def get_period(period_id, product_id):
    db = DB()
    status, period_result = db.select_by_id("period_task", period_id)
    if status is True and period_result:
        minions = []
        for group in period_result.get("target"):
            status, result = db.select_by_id("groups", group)
            if status is True and result:
                minions.extend(result.get("minion"))
        minion_list = list(set(minions))
        salt_api = salt_api_for_product(product_id)
        if isinstance(salt_api, dict):
            period_result["status"] = {
                "id": 4,
                "name": period_status.get(4)
            }
            db.update_by_id("period_task", json.dumps(period_result, ensure_ascii=False), period_id)
            return salt_api, 500
        return period_result, minion_list, salt_api
    else:
        logger.error("Get period and minion error: %s" % period_result)


# 结果信息放到period_result表
def insert_period_result(period_id, period_result):
    db = DB()
    results = {
        "id": period_id,
        "result": period_result
    }
    status, result = db.insert("period_result", json.dumps(results, ensure_ascii=False))
    if status is False:
        db.close_mysql()
        logger.error("Insert period result error: %s" % result)


# 审计信息放到period_audit表
def insert_period_audit(period_id, period_audits):
    db = DB()
    results = {
        "id": period_id,
        "result": period_audits
    }
    status, result = db.insert("period_audit", json.dumps(results, ensure_ascii=False))
    if status is False:
        db.close_mysql()
        logger.error("Insert period audit error: %s" % result)
