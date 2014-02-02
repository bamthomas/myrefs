import json
from flask import request, Flask, render_template, Response, current_app
from pymongo.mongo_client import MongoClient


class RssFeeds(object):
    def __init__(self):
        self.client = MongoClient()
        db = self.client.myrefs
        self.userfeeds = db.userfeeds

    def get_feeds(self, user):
        return self.userfeeds.find_one({'user': user})['rssfeeds']

    def insert_feed(self, user, feed_as_dict):
        self.userfeeds.update({'user': user}, {'$push': {'rssfeeds': feed_as_dict}})


def create_app():
    app = Flask(__name__)
    app.config['mongo_rss_feeds'] = RssFeeds()
    return app

app = create_app()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/rssfeeds")
def rss_feeds():
    rssfeeds = current_app.config['mongo_rss_feeds'].get_feeds('bruno')
    return Response(json.dumps(rssfeeds),  mimetype='application/json')

@app.route("/rssfeed", methods=["POST"])
def new_rss_feed():
    current_app.config['mongo_rss_feeds'].insert_feed('bruno', request.get_json())
    return Response(status=200)

if __name__ == "__main__":
    app.run()