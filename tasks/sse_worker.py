import json
import sseclient
import re
from common.db import DB
from common.utility import salt_api_for_product


def see_worker():
    db = DB()
    status, result = db.select("product", "")
    db.close_mysql()
    if status is True and result:
        for i in result:
            product = eval(i[0])
            #job_pattern = re.compile('salt/job/\d+/ret/')
            salt_api = salt_api_for_product(product["id"])
            event_response = salt_api.events()
            client = sseclient.SSEClient(event_response)
            for event in client.events():
                print(event.data)
                # if job_pattern.search(event.data):
                event_dict = eval(event.data.replace('true', '"true"').replace('false', '"false"').replace('null', '""'))
                event_dict['data']['product_id'] = product["id"]
                db = DB()
                db.insert("event", json.dumps(event_dict, ensure_ascii=False))
                db.close_mysql()
