from Queue import Queue
from nose.twistedtools import reactor, deferred
from app_twisted import CheckRssFeedsResource
from nose import with_setup
from twisted.web import resource, server
from twisted.web.test.test_web import DummyRequest
from nose.tools import eq_


class MockFeedsRepository(object):
    def __init__(self, get_feed_return_value):
        self.get_feed_return_value = get_feed_return_value

    def get_feeds(self, _):
        return self.get_feed_return_value


class DummyRssFeedsProviderResource(resource.Resource):
    isLeaf = True

    def __init__(self):
        resource.Resource.__init__(self)
        self.requests = Queue()

    def render_GET(self, request):
        self.requests.put(request)
        return 'OK'


class TestCheckRssFeedsResource(object):
    def setup(self):
        self.feed_provider = DummyRssFeedsProviderResource()
        reactor.listenTCP(12345, server.Site(self.feed_provider))

    @with_setup(setup)
    @deferred(timeout=5.0)
    def test_feeds_checked_with_get(self):
        check_resource = CheckRssFeedsResource(MockFeedsRepository([{'id': 'md5', 'url': 'http://localhost:12345/feeds', 'main_url': 'main_url'}]))

        d = check_resource._get(DummyRequest(['postpath']))

        def check(_):
            eq_(1, self.feed_provider.requests.qsize())
            eq_('/feeds', self.feed_provider.requests.get().uri)

        d.addCallback(check)
        return d






