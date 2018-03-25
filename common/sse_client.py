import json
import sseclient
import re
from common.saltstack_api import SaltAPI
from common.db import DB


def salt_api_for_product(product_id):
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
    salt_api = SaltAPI(
        url=product.get("salt_master_url"),
        user=product.get("salt_master_user"),
        passwd=product.get("salt_master_password")
    )
    return salt_api


job_pattern = re.compile('salt/job/\d+/ret/')

salt_api = SaltAPI(url='http://127.0.0.1:8000', user='saltapi', passwd='saltapi')
event_response = salt_api.events()

client = sseclient.SSEClient(event_response)
for event in client.events():
    if job_pattern.search(event.data):
        event_dict = eval(event.data.replace('true', '"true"').replace('false', '"false"'))
        event_dict['data']['product_id'] = 'p-c5008b0421d611e894b0000c298454d8'
        db = DB()
        db.insert("salt_return", json.dumps(event_dict['data'], ensure_ascii=False))
        db.close_mysql()
