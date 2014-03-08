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
            'rss': function () {
                $(".content").hide();
                $("#rss").show();
            },
            'marks': function () {
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
            $('ul', this.el).append("<li><a href='" + rssFeed.get('main_url') + "'>" + rssFeed.get('title') + "</a></li>");
        },
        render: function () {
            $(this.el).find('#rssfeeds').append("<ul></ul>");
            var self = this;
            _(this.model.models).each(function (rssFeed) {
                self.appendRssFeed(rssFeed);
            }, this);
            self.updateFeeds();
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
        },
        updateFeeds: function () {
            var source = new EventSource('/updatefeeds');
            source.onmessage = function (msg) {
                var feedupdates = JSON.parse(msg.data);
                var entries = JSON.parse(feedupdates.entries);

                var $feed = $('#rssfeeds').find('a[href="' + feedupdates.url + '"]');
                $feed.append("<span class='badge alert-danger'>" + entries.length + "</span>");
                $feed.parent().append('<ul></ul>');
                _(entries).each(function(entry) {
                    localStorage[entry.link] = JSON.stringify(entry);
                    $feed.parent().find('ul').append('<li><a class="article" href="' + entry.link + '">' + entry.title + '</a></li>');
                });
                $('#rssfeeds').find('a.article').on('click', function(evt) {
                    evt.preventDefault();
                    $('#article_modal').find('.modal-title').html($(this).html());
                    var article = JSON.parse(localStorage[this.href]);
                    $('#article_modal').find('.modal-body').html(article.content[0].value);
                    $('#article_modal').modal();
                });
            };
            source.addEventListener('close', function () {
                console.log("closing feeds update");
                this.close();
            }, false);
        }
    });
    new app.RssView();
})(jQuery);