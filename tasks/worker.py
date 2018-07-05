# -*- coding:utf-8 -*-
from common.log import loggers
from common.audit_log import audit_log
from common.const import period_status, period_audit
import time
import json
import sseclient
import re
from common.db import DB
from common.utility import salt_api_for_product
import ast

logger = loggers()


def sse_worker(product):
    # job_pattern = re.compile('salt/job/\d+/ret/')
    mine_pattern = re.compile(r'"fun": "mine.update"')
    saltutil_pattern = re.compile(r'"fun": "saltutil.find_job"')
    running_pattern = re.compile(r'"fun": "saltutil.running"')
    lookup_pattern = re.compile(r'"fun": "runner.jobs.lookup_jid"')
    event_pattern = re.compile(r'"tag": "salt/event/new_client"')
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
        else:
            print(event.data)
            event_dict = ast.literal_eval(event.data.replace('true', 'True').replace('false', 'False').
                                          replace('null', '""'))
            event_dict['data']['product_id'] = product
            db = DB()
            db.insert("event", json.dumps(event_dict, ensure_ascii=False))
            db.close_mysql()


def once_worker(period_id, product_id, user):
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
        concurrent = int(period_result["concurrent"])
        # 全部一次执行
        if concurrent == 0:
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
                "time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                "result": result,
                "option": period_audit.get(9)
            }
            period_result["status"] = {
                "id": 3,
                "name": period_status.get(3)
            }
            period_result["audit"].append({
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                "user": "机器人",
                "option": period_audit.get(3)
            })
            insert_period_result(period_id, results)
            # period_task["results"].append(results)
            db.update_by_id("period_task", json.dumps(period_result, ensure_ascii=False), period_id)
            db.close_mysql()
            audit_log(user, minion_list, product_id, "minion", "shell")
        # 并行分组执行
        if concurrent > 0:
            # 假如并行数大于minion的总数,range步长为minion长度，即一次全部运行
            for m in period_result["executed_minion"]:
                minion_list.remove(m)
            if concurrent > len(minion_list):
                concurrent = len(minion_list)
            count = 1
            for i in range(0, len(minion_list), concurrent):
                db = DB()
                p_status, p_result = db.select_by_id("period_task", period_id)
                if p_status is True and p_result:
                    if p_result.get("action") == "play":
                        # 记录状态为第N组运行中
                        p_result["status"] = {
                            "id": 7,
                            "name": period_status.get(7) % count
                        }
                        p_result["audit"].append({
                            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                            "user": "机器人",
                            "option": period_audit.get(7) % count
                        })
                        db.update_by_id("period_task", json.dumps(p_result, ensure_ascii=False), period_id)
                        # 根据并行数，对minion进行切分
                        minion = minion_list[i:i+concurrent]
                        if period_result.get("execute") == "shell":
                            result = salt_api.shell_remote_execution(minion, period_result.get("shell"))
                        elif period_result.get("execute") == "sls":
                            result = salt_api.target_deploy(minion, period_result.get("sls"))
                        results = {
                            "time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                            "result": result,
                            "option": period_audit.get(7) % count
                        }
                        insert_period_result(period_id, results)
                        # 执行完命令更新状态
                        p_result["status"] = {
                            "id": 8,
                            "name": period_status.get(8) % count
                        }
                        p_result["audit"].append({
                            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                            "user": "机器人",
                            "option": period_audit.get(8) % count
                        })
                        p_result["executed_minion"].extend(minion)
                        db.update_by_id("period_task", json.dumps(p_result, ensure_ascii=False), period_id)
                        # 并行间隔时间，最后一次不等待
                        if concurrent < len(minion_list):
                            if i != list(range(0, len(minion_list), concurrent))[-1]:
                                time.sleep(int(p_result["interval"]))
                                count += 1
                        db.close_mysql()
                        # audit_log(user, minion, product_id, "minion", "shell")
            # 更新状态为完成
            p_result["status"] = {
                "id": 3,
                "name": period_status.get(3)
            }
            p_result["audit"].append({
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                "user": "机器人",
                "option": period_audit.get(3)
            })
            db = DB()
            db.update_by_id("period_task", json.dumps(p_result, ensure_ascii=False), period_id)
            db.close_mysql()


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