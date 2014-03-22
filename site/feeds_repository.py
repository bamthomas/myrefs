import hashlib
from pymongo import MongoClient


class RssFeedsRepository(object):
    def __init__(self):
        self.client = MongoClient()
        db = self.client.myrefs
        self.user_feeds = db.user_feeds
        self.user_articles = db.user_articles

    def get_feeds(self, user):
        return self.user_feeds.find_one({'user': user})['rssfeeds']

    def insert_feed(self, user, feed_as_dict):
        feed_as_dict['id'] = hashlib.md5(feed_as_dict['url']).hexdigest()
        self.user_feeds.update({'user': user}, {'$push': {'rssfeeds': feed_as_dict}})

    def insert_fetched_article(self, user, feed_id, article_url):
        self.user_articles.insert({'user': user, 'feed_id': feed_id, 'url': article_url})

    def get_feed_read_articles(self, user, feed_id):
        return self.user_articles.find({'user': user, 'feed_id': feed_id})