from StringIO import StringIO
import json
import feedparser
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol, connectionDone
from twisted.python.syslog import startLogging
from twisted.web import server, resource
from pymongo.mongo_client import MongoClient
from twisted.web.client import Agent
from twisted.web.http_headers import Headers
from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET
from twisted.web.static import File
from twisted.internet import reactor


class RssFeedsRepository(object):
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

    def render_POST(self, add_feed_request):
        rss_feed_url = json.loads(add_feed_request.content.getvalue())['url']

        def finish_request(_):
            add_feed_request.finish()

        d = RssParserProtocol(self.rss_feeds).run(rss_feed_url)
        d.addCallback(finish_request)
        d.addErrback(error)

        return NOT_DONE_YET


class RssParserProtocol(Protocol):
    def __init__(self, rss_feed_repository):
        self.agent = Agent(reactor)
        self.finished = Deferred()
        self.buffer = StringIO()
        self.rss_feed_repository = rss_feed_repository

        self.finished.addCallback(self.parse_feed)
        self.finished.addErrback(error)
        self.finished.addCallback(self.store_feed_info)
        self.finished.addErrback(error)

    def run(self, rss_feed_url):
        self.rss_feed_url = rss_feed_url
        deferred = self.agent.request('GET', rss_feed_url.encode('utf-8'),Headers({'User-Agent': ['MyRefs']}), None)
        deferred.addCallback(self.response_received)
        return deferred

    def dataReceived(self, data):
        self.buffer.write(data)

    def connectionLost(self, reason=connectionDone):
        self.finished.callback(self.buffer.getvalue())

    def response_received(self, rss_response):
        rss_response.deliverBody(self)
        return self.finished

    def parse_feed(self, xmlfeed):
        return feedparser.parse(xmlfeed)

    def store_feed_info(self, rss):
        self.rss_feed_repository.insert_feed('bruno', {'url': self.rss_feed_url, 'main_url': rss.feed.link,'title': rss.feed.title})
        return None


def error(traceback):
    print traceback

startLogging(prefix='myrefs')
rss_feeds = RssFeedsRepository()
root = Resource()
root.putChild('rssfeeds', RssFeedsResource(rss_feeds))
root.putChild('', File('static'))
reactor.listenTCP(8080, server.Site(root))
reactor.run()