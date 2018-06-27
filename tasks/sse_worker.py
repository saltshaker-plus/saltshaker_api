import json
import sseclient
import re
from common.db import DB
from common.utility import salt_api_for_product
import ast


def see_worker(product):
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
