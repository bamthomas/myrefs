from datetime import datetime
import json
import time


def json_encode(data):
    class JsonEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, time.struct_time):
                return datetime.fromtimestamp(time.mktime(o)).isoformat()
            return json.JSONEncoder.default(self, o)
    return json.dumps(data, cls=JsonEncoder)
