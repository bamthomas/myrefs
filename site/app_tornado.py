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
from utils import json_encode, get_unread_entries


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


class ArticleHandler(tornado.web.RequestHandler):
    def initialize(self, rss_feeds):
        self.rss_feeds = rss_feeds

    def put(self, *args, **kwargs):
        article = json.loads(self.request.body)
        self.rss_feeds.insert_fetched_article('bruno', article)


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
        read_articles = self.rss_feeds.get_feed_read_articles('bruno', rss_feed['id'])
        entries = get_unread_entries(rss.entries, read_articles)
        self.write('data: %s' % json.dumps({'id': rss_feed['id'], 'url': rss_feed['main_url'], 'entries': json_encode(entries)}))
        self.write('\n\n')
        self.flush()

if __name__ == "__main__":
    rss_feeds_repository = RssFeedsRepository()
    application = tornado.web.Application([
        (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': os.path.join(os.getcwd() + '/static')}),
        (r'/rssfeeds', RssFeedsHandler, {'rss_feeds': rss_feeds_repository}),
        (r'/updatefeeds', CheckRssFeedsHandlder, {'rss_feeds': rss_feeds_repository}),
    ])
    application.listen(8888)
    IOLoop.instance().start()
