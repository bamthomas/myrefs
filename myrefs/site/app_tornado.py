from functools import partial
import json
import feedparser
from feeds_repository import RssFeedsRepository
import os
from tornado.httpclient import AsyncHTTPClient
import tornado.web
from tornado.ioloop import IOLoop
from tornado.web import asynchronous
from tornado.gen import coroutine
from utils import json_encode


class RssFeedsHandler(tornado.web.RequestHandler):
    def initialize(self, rss_feeds):
        self.rss_feeds = rss_feeds

    def get(self):
        rssfeeds = self.rss_feeds.get_feeds('bruno')
        self.set_header('Content-Type', 'application/json; charset=utf-8')
        self.write(json.dumps(rssfeeds))

    @asynchronous
    def post(self, *args, **kwargs):
        rss_feed_url = json.loads(self.request.body)['url']
        AsyncHTTPClient().fetch(rss_feed_url, callback=partial(self.handle_feed_insert, rss_feed_url))

    def handle_feed_insert(self, rss_feed_url, response):
        rss = feedparser.parse(response.body)
        self.rss_feeds.insert_feed('bruno', {'url': rss_feed_url, 'main_url': rss.feed.link, 'title': rss.feed.title})


class CheckRssFeedsHandlder(tornado.web.RequestHandler):
    def initialize(self, rss_feeds):
        self.rss_feeds = rss_feeds
        self.set_header('Content-Type', 'text/event-stream')
        self.set_header('Cache-Control', 'no-cache')

    @coroutine
    def get(self):
        rssfeeds = self.rss_feeds.get_feeds('bruno')
        yield [AsyncHTTPClient().fetch(feed['url'], callback=partial(self.handle_feed_check, feed)) for feed in rssfeeds]
        self.write('event: close\ndata:\n\n')

    def handle_feed_check(self, rss_feed, response):
        rss = feedparser.parse(response.body)
        self.write('data: %s' % json.dumps({'url': rss_feed['main_url'], 'entries': json_encode(rss.entries)}))
        self.write('\n\n')
        self.flush()

application = tornado.web.Application([
    (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': os.path.join(os.getcwd() + '/static')}),
    (r'/rssfeeds', RssFeedsHandler, {'rss_feeds': RssFeedsRepository()}),
    (r'/updatefeeds', CheckRssFeedsHandlder, {'rss_feeds': RssFeedsRepository()}),
])

if __name__ == "__main__":
    application.listen(8888)
    IOLoop.instance().start()
