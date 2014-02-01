var app = app || {};

(function ($) {
    'use strict';

    var RssFeed = Backbone.Model.extend({
    });

    var RssFeeds = Backbone.Collection.extend({
        model: RssFeed
    });

    app.RssView = Backbone.View.extend({
        el: $('#rss'),
        initialize: function () {
            _.bindAll(this, 'render', 'appendRssFeed');

            this.rssList = new RssFeeds();
            this.rssList.url = '/rssfeeds';
            this.rssList.fetch();

            this.render();
        },
        appendRssFeed: function (rssFeed) {
            $('ul', this.el).append("<li>" + rssFeed.get('url') + "</li>");
        },
        render: function () {
            $(this.el).append("<ul></ul>");
            _(this.rssList.models).each(function (rssFeed) {
                self.appendRssFeed(rssFeed);
            }, this);
        }
    });
    new app.RssView();
})(jQuery);