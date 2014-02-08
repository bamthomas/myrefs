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

        agent = Agent(reactor)
        d = agent.request('GET', rss_feed_url.encode('utf-8'), Headers({'User-Agent': ['MyRefs']}), None)

        def response_received(rss_response):
            finished = Deferred()
            rss_response.deliverBody(RssParserProtocol(finished, self.rss_feeds, rss_feed_url))
            return finished

        def finish_request(_):
            add_feed_request.finish()

        d.addCallback(response_received)
        d.addErrback(error)
        d.addCallback(finish_request)
        d.addErrback(error)

        return NOT_DONE_YET


class RssParserProtocol(Protocol):
    def __init__(self, finished, rss_feed_repository, rss_feed_url):
        self.finished = finished
        self.buffer = StringIO()
        self.rss_feed_repository = rss_feed_repository
        self.rss_feed_url = rss_feed_url

        finished.addCallback(self.parse_feed)
        finished.addErrback(error)
        finished.addCallback(self.store_feed_info)
        finished.addErrback(error)

    def dataReceived(self, data):
        self.buffer.write(data)

    def connectionLost(self, reason=connectionDone):
        print "connection lost"
        self.finished.callback(self.buffer.getvalue())

    def parse_feed(self, xmlfeed):
        print "parse feed"
        return feedparser.parse(xmlfeed)

    def store_feed_info(self, rss):
        print "store feed"
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