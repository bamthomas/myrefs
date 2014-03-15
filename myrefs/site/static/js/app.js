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
            $('#feeds', this.el).append('<div class="panel panel-default"> <div class="panel-heading"> ' +
                '<h4 class="panel-title"> ' +
                '<a data-toggle="collapse" data-parent="#feeds" href="#' + rssFeed.get('id') + '"> ' + rssFeed.get('title') + ' </a> ' +
                '</h4> ' +
                '</div> ' +
                '<div id="' + rssFeed.get('id') + '" class="panel-collapse collapse"> <div class="panel-body"><ul></ul></div></div></div>');
        },
        render: function () {
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

                if (entries.length > 0) {
                    var $feed_title = $('#feeds').find('a[href="#' + feedupdates.id + '"]');
                    $feed_title.append("<span class='badge alert-danger'>" + entries.length + "</span>");
                    var $feedBody = $('#feeds').find('#' + feedupdates.id).find('.panel-body');
                    _(entries).each(function (entry) {
                        localStorage[entry.link] = JSON.stringify(entry);
                        $feedBody.find('ul').append('<li><a class="article" href="' + entry.link + '">' + entry.title + '</a></li>');
                    });
                }
            };
            source.addEventListener('close', function () {
                $('#feeds').find('a.article').on('click', function (evt) {
                    evt.preventDefault();
                    $('#article_modal').find('.modal-title').html($(this).html());
                    var article = JSON.parse(localStorage[this.href]);
                    $('#article_modal').find('.modal-body').html(article.content[0].value);
                    $('#article_modal').modal();
                });
                console.log("closing feeds update");
                this.close();
            }, false);
        }
    });
    new app.RssView();
})(jQuery);