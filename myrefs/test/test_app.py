import time
from app_tornado import json_encode
from nose.tools import eq_


class TestJsonEncoder(object):
    def test_encode_time_struct(self):
        data = {'title': 'title',
                'publish_date': time.struct_time((2014, 3, 7, 10, 44, 30, 4, 66, 0))}
        actual = json_encode(data)
        eq_('{"publish_date": "2014-03-07T10:44:30", "title": "title"}', actual)