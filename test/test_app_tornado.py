# coding=utf-8
from Queue import Queue
from app_tornado import CheckRssFeedsHandlder, ArticleHandler
import tornado
from tornado.httpserver import HTTPServer
from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application


class MemoryFeedsRepository(object):
    def __init__(self, get_feed_return_value):
        self.feeds = get_feed_return_value
        self.articles = []

    def get_feeds(self, _):
        return self.feeds

    def insert_fetched_article(self, user, article_as_dict):
        self.articles.append(article_as_dict['url'])

    def get_feed_read_articles(self, user, feed_id):
        return self.articles


class MockRequestHandler(tornado.web.RequestHandler):
    def initialize(self, requests_queue, response_queue):
        self.requests = requests_queue
        self.responses = response_queue

    def get(self, path):
        self.requests.put(path)
        self.write(self.responses.get(0))


class TestCheckRssFeedsHandlder(AsyncHTTPTestCase):
    def setUp(self):
        super(TestCheckRssFeedsHandlder, self).setUp()
        self.requests_queue = Queue()
        self.response_queue = Queue()
        self.feed_provider = HTTPServer(Application([(r'/(.*)', MockRequestHandler,
                          {'requests_queue': self.requests_queue, 'response_queue': self.response_queue})]), io_loop=self.io_loop)
        self.feed_provider.listen(12345)

    def get_app(self):
        feeds_repository = MemoryFeedsRepository([{'id': 'md5', 'url': 'http://localhost:12345/feeds', 'main_url': 'main_url'}])
        return Application([
            (r'/updatefeeds', CheckRssFeedsHandlder, {'rss_feeds': feeds_repository}),
            (r'/article', ArticleHandler, {'rss_feeds': feeds_repository})])

    def test_feeds_checked_with_get(self):
        self.response_queue.put(FEED_HEADER + '<item><link>my_article_url</link></item>' + FEED_FOOTER)

        response = self.fetch('/updatefeeds')

        self.assertEquals(1, self.requests_queue.qsize())
        self.assertEquals('feeds', self.requests_queue.get())
        self.assertIn("my_article_url", response.body)

    def test_feeds_checked_with_get__read_article_is_not_sent(self):
        self.response_queue.put(FEED_HEADER + '<item><link>my_article_url</link></item>' + FEED_FOOTER)

        self.fetch('/article', method='PUT', body='{"feed_id": "id", "url": "my_article_url"}')

        self.assertNotIn("my_article_url", (self.fetch('/updatefeeds')).body)


FEED_HEADER = """
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:wfw="http://wellformedweb.org/CommentAPI/"
     xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:atom="http://www.w3.org/2005/Atom"
     xmlns:sy="http://purl.org/rss/1.0/modules/syndication/" xmlns:slash="http://purl.org/rss/1.0/modules/slash/">
    <channel><title>Feed Title</title>
        <atom:link href="http://feed_url" rel="self" type="application/rss+xml"/>
        <link>http://blog_url</link>
        <description>feed description</description>
"""

FEED_FOOTER = """
</channel>
</rss>
"""