import time
from nose.tools import eq_
from utils import json_encode, get_not_read_entries


class TestJsonEncoder(object):
    def test_encode_time_struct(self):
        data = {'title': 'title', 'publish_date': time.struct_time((2014, 3, 7, 10, 44, 30, 4, 66, 0))}
        actual = json_encode(data)
        eq_('{"publish_date": "2014-03-07T10:44:30", "title": "title"}', actual)


class TestFeedFiltering(object):
    def test_unread_entries__when_no_articles_is_read(self):
        eq_([], get_not_read_entries([], []))
        eq_([{'url': 'article1'}], get_not_read_entries([{'url': 'article1'}], []))

    def test_unread_entries(self):
        eq_([], get_not_read_entries([{'url': 'article1'}], [{'url': 'article1'}]))
        eq_([{'url': 'article2'}], get_not_read_entries([{'url': 'article1'}, {'url': 'article2'}], [{'url': 'article1'}]))