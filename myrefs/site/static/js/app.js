var app = app || {};

(function ($) {
    'use strict';

    var RssFeed = Backbone.Model.extend({
    });

    var RssFeeds = Backbone.Collection.extend({
        model: RssFeed,
        url: '/rssfeeds'
    });

    app.RssView = Backbone.View.extend({
        el: $('#rss'),
        initialize: function () {
            _.bindAll(this, 'render', 'appendRssFeed');
            this.model = new RssFeeds();
            this.model.bind('reset',this.render);
            this.model.fetch({reset: true});
        },
        appendRssFeed: function (rssFeed) {
            $('ul', this.el).append("<li>" + rssFeed.get('url') + "</li>");
        },
        render: function () {
            $(this.el).append("<ul></ul>");
            var self = this;
            _(this.model.models).each(function (rssFeed) {
                self.appendRssFeed(rssFeed);
            }, this);
            return this;
        }
    });
    new app.RssView();
})(jQuery);