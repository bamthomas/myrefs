from StringIO import StringIO
from functools import partial
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
        self.user_feeds = db.user_feeds

    def get_feeds(self, user):
        return self.user_feeds.find_one({'user': user})['rssfeeds']

    def insert_feed(self, user, feed_as_dict):
        self.user_feeds.update({'user': user}, {'$push': {'rssfeeds': feed_as_dict}})


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
        self.rss_feed_url = json.loads(add_feed_request.content.getvalue())['url']

        def finish_request(_):
            add_feed_request.finish()

        d = RssAgent(reactor).run(self.rss_feed_url)
        d.addCallback(self.store_feed_info)
        d.addCallback(finish_request)
        d.addErrback(error)

        return NOT_DONE_YET

    def store_feed_info(self, rss):
        self.rss_feeds.insert_feed('bruno', {'url': self.rss_feed_url, 'main_url': rss.feed.link, 'title': rss.feed.title})
        return None


class CheckRssFeedsResource(resource.Resource):
    isLeaf = True

    def __init__(self, rss_feeds):
        resource.Resource.__init__(self)
        self.rss_feeds = rss_feeds

    def render_GET(self, request):
        rssfeeds = self.rss_feeds.get_feeds('bruno')
        request.setHeader('Content-Type', 'text/event-stream')
        request.setHeader('Cache-Control', 'no-cache')
        self.pending_feed_requests = len(rssfeeds)
        for feed in rssfeeds:
            d = RssAgent(reactor).run(feed['url'])
            d.addCallback(partial(self.write_feed_check, request, feed))
            d.addErrback(error)
        return NOT_DONE_YET

    def write_feed_check(self, request, rss_feed, rss):
        self.pending_feed_requests -= 1
        request.write('data: %s' % json.dumps({'url': rss_feed['main_url'], 'entries': len(rss.entries)}))
        request.write('\n\n')
        if self.pending_feed_requests == 0:
            request.write('event: close\ndata:\n\n')


class RssAgent(Agent):
    def __init__(self, reactor):
        super(RssAgent, self).__init__(reactor)
        self.agent = Agent(reactor)
        self.finished = Deferred()
        self.buffer = StringIO()

    def run(self, rss_feed_url):
        self.rss_feed_url = rss_feed_url
        deferred = self.request('GET', rss_feed_url.encode('utf-8'), Headers({'User-Agent': ['MyRefs']}), None)
        deferred.addCallback(self.response_received)
        deferred.addErrback(error)
        deferred.addCallback(self.parse_feed)
        deferred.addErrback(error)
        return deferred

    def response_received(self, rss_response):
        finished = Deferred()
        rss_response.deliverBody(RssParserProtocol(finished))
        return finished

    def parse_feed(self, xmlfeed):
        return feedparser.parse(xmlfeed)


class RssParserProtocol(Protocol):
    def __init__(self, finished):
        self.finished = finished
        self.buffer = StringIO()

    def dataReceived(self, data):
        self.buffer.write(data)

    def connectionLost(self, reason=connectionDone):
        self.finished.callback(self.buffer.getvalue())


def error(traceback):
    print traceback

startLogging(prefix='myrefs')
rss_feeds = RssFeedsRepository()
root = Resource()
root.putChild('rssfeeds', RssFeedsResource(rss_feeds))
root.putChild('', File('static'))
root.putChild('updatefeeds', CheckRssFeedsResource(rss_feeds))
reactor.listenTCP(8888, server.Site(root))
reactor.run()