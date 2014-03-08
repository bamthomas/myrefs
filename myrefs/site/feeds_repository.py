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
        self.user_feeds.update({'user': user}, {'$push': {'rssfeeds': feed_as_dict}})

    def insert_fetched_article(self, user, article_url):
        self.user_articles.insert({'user': user, 'article_url': article_url})
