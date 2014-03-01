from functools import partial
import json
import feedparser
import os
from pymongo import MongoClient
from tornado.httpclient import AsyncHTTPClient
import tornado.web
from tornado.ioloop import IOLoop
from tornado.web import asynchronous


class RssFeedsRepository(object):
    def __init__(self):
        self.client = MongoClient()
        db = self.client.myrefs
        self.userfeeds = db.userfeeds

    def get_feeds(self, user):
        return self.userfeeds.find_one({'user': user})['rssfeeds']

    def insert_feed(self, user, feed_as_dict):
        self.userfeeds.update({'user': user}, {'$push': {'rssfeeds': feed_as_dict}})


class RssFeedsHandler(tornado.web.RequestHandler):
    def initialize(self, rss_feeds):
        self.rss_feeds = rss_feeds

    def get(self):
        rssfeeds = self.rss_feeds.get_feeds('bruno')
        self.set_header('Content-Type', 'application/json; charset=utf-8')
        return self.write(json.dumps(rssfeeds))

    @asynchronous
    def post(self, *args, **kwargs):
        rss_feed_url = json.loads(self.request.body)['url']
        client = AsyncHTTPClient()
        client.fetch(rss_feed_url, callback=partial(self.handle_feed, rss_feed_url))

    def handle_feed(self, rss_feed_url, response):
        rss = feedparser.parse(response.body)
        self.rss_feeds.insert_feed('bruno', {'url': rss_feed_url, 'main_url': rss.feed.link, 'title': rss.feed.title})


application = tornado.web.Application([
    (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': os.path.join(os.getcwd() + '/static')}),
    (r'/rssfeeds', RssFeedsHandler, {'rss_feeds': RssFeedsRepository()}),
])

if __name__ == "__main__":
    application.listen(8888)
    IOLoop.instance().start()
