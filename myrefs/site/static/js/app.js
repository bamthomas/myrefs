var app = app || {};

(function ($) {
    'use strict';

    var RssFeed = Backbone.Model.extend({
        url: '/rssfeeds'
    });

    var RssFeeds = Backbone.Collection.extend({
        model: RssFeed,
        url: '/rssfeeds'
    });

    var MyRefsRouter = Backbone.Router.extend({
        routes: {
            'rss': function() {
                $(".content").hide();
                $("#rss").show();
            },
            'marks': function() {
                $(".content").hide();
                $("#marks").show();
            }
        }
    });

    var appRouter = new MyRefsRouter();
    Backbone.history.start();
    appRouter.navigate('rss', {trigger: true});
    app.RssView = Backbone.View.extend({
        el: $('#rss'),
        events: {
            "click .new-rss-btn": "addRssFeed"
        },
        initialize: function () {
            _.bindAll(this, 'render', 'appendRssFeed');
            this.$new_feed_input = $('#new_feed_input');
            this.model = new RssFeeds();
            this.model.bind('reset', this.render);
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
        },
        addRssFeed: function (e) {
            var url = this.$new_feed_input.val().trim();
            if (url !== '') {
                var newRssFeed = new RssFeed();
                newRssFeed.set({'url': url});
                this.model.create(newRssFeed);
                this.$new_feed_input.val('');
            }
        }
    });
    new app.RssView();
})(jQuery);