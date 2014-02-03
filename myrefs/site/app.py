import json
from twisted.python.syslog import startLogging
from twisted.web import server, resource
from twisted.internet import reactor
from pymongo.mongo_client import MongoClient
from twisted.web.resource import Resource
from twisted.web.static import File


class RssFeeds(object):
    def __init__(self):
        self.client = MongoClient()
        db = self.client.myrefs
        self.userfeeds = db.userfeeds

    def get_feeds(self, user):
        return self.userfeeds.find_one({'user': user})['rssfeeds']

    def insert_feed(self, user, feed_as_dict):
        self.userfeeds.update({'user': user}, {'$push': {'rssfeeds': feed_as_dict}})


class RssFeedsResource(resource.Resource):
    isLeaf = True

    def __init__(self, rss_feeds):
        resource.Resource.__init__(self)
        self.rss_feeds = rss_feeds

    def render_GET(self, request):
        rssfeeds = self.rss_feeds.get_feeds('bruno')
        request.setHeader('Content-Type', 'application/json; charset=utf-8')
        return json.dumps(rssfeeds)

    def render_POST(self, request):
        rss_feed = json.loads(request.content.getvalue())
        self.rss_feeds.insert_feed('bruno', rss_feed)
        request.setResponseCode(200)
        return ''


startLogging(prefix='myrefs')
rss_feeds = RssFeeds()
root = Resource()
root.putChild('rssfeeds', RssFeedsResource(rss_feeds))
root.putChild('', File('static'))
reactor.listenTCP(8080, server.Site(root))
reactor.run()