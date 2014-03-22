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


def get_unread_entries(entries, read_articles):
    articles_url_set = set([a['url'] for a in read_articles])
    return [e for e in entries if e['url'] not in articles_url_set]
