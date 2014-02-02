import json
from flask import Flask, render_template, Response, current_app
from pymongo.mongo_client import MongoClient


class RssFeeds(object):
    def __init__(self):
        self.client = MongoClient()
        db = self.client.myrefs
        self.userfeeds = db.userfeeds

    def get_feeds(self, user):
        return self.userfeeds.find_one({'user': user})['rssfeeds']


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



if __name__ == "__main__":
    app.run()