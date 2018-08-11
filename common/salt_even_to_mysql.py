#!/bin/env python
import json
import salt.utils.event
from common.db import DB

opts = salt.config.client_config('/etc/salt/master')

# Listen Salt Master Event System
event = salt.utils.event.MasterEvent(opts['sock_dir'])
for event_info in event.iter_events(full=True):
    ret = event_info['data']
    if "salt/job/" in event_info['tag']:
        # Return Event
        if 'id' in ret and 'return' in ret:
            # Ignore saltutil.find_job event
            if ret['fun'] == "saltutil.find_job":
                continue
            db = DB()
            db.insert("salt_return", json.dumps(ret, ensure_ascii=False))
            db.close_mysql()
    # Other Event
    else:
        pass




