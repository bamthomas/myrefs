from Queue import Queue
from app_tornado import CheckRssFeedsHandlder
import tornado
from tornado.httpserver import HTTPServer
from tornado.testing import AsyncHTTPTestCase, IOLoop
from tornado.web import Application


class MockFeedsRepository(object):
    def __init__(self, get_feed_return_value):
        self.get_feed_return_value = get_feed_return_value

    def get_feeds(self, _):
        return self.get_feed_return_value


class MockRequestHandler(tornado.web.RequestHandler):
    def initialize(self, requests_queue):
        self.requests = requests_queue

    def get(self, path):
        self.requests.put(path)


class TestCheckRssFeedsHandlder(AsyncHTTPTestCase):
    def setUp(self):
        super(TestCheckRssFeedsHandlder, self).setUp()
        self.requests_queue = Queue()
        self.feed_provider = HTTPServer(Application([(r'/(.*)', MockRequestHandler, {'requests_queue': self.requests_queue})]), io_loop=self.io_loop)
        self.feed_provider.listen(12345)

    def get_app(self):
        return Application([
            (r'/updatefeeds', CheckRssFeedsHandlder, {'rss_feeds': MockFeedsRepository(
                [{'id': 'md5', 'url': 'http://localhost:12345/feeds', 'main_url': 'main_url'}])})])

    def test_feeds_checked_with_get(self):
        self.http_client.fetch(self.get_url('/updatefeeds'), self.stop)
        self.wait()
        self.assertEquals(1, self.requests_queue.qsize())
        self.assertEquals('feeds', self.requests_queue.get())