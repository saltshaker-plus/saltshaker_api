# -*- coding:utf-8 -*-
from common.log import loggers
from common.audit_log import audit_log
from common.const import period_status
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


def once_shell_worker(period_id, product_id, user, target, command, period_task):
    db = DB()
    period_task["status"] = period_status.get(2)
    db.update_by_id("period_task", json.dumps(period_task, ensure_ascii=False), period_id)
    minions = []
    for group in target:
        status, result = db.select_by_id("groups", group)
        if status is True and result:
            minions.extend(result.get("minion"))
    minion_list = list(set(minions))
    salt_api = salt_api_for_product(product_id)
    if isinstance(salt_api, dict):
        period_task["status"] = period_status.get(4)
        db.update_by_id("period_task", json.dumps(period_task, ensure_ascii=False), period_id)
        return salt_api, 500
    result = salt_api.shell_remote_execution(minion_list, command)
    results = {
        "time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
        "result": result
    }
    period_task["status"] = period_status.get(3)
    period_task["results"].append(results)
    db.update_by_id("period_task", json.dumps(period_task, ensure_ascii=False), period_id)
    db.close_mysql()
    audit_log(user, minion_list, product_id, "minion", "shell")
