import json
from flask import Flask, render_template, Response

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/rssfeeds")
def rss_feeds():
    return Response(json.dumps([{'url': 'www.url1.com'}, {'url': 'www.url2.com'}]),  mimetype='application/json')

if __name__ == "__main__":
    app.run()