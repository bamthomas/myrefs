var app = app || {};

(function ($) {
    'use strict';

    var RssFeed = Backbone.Model.extend({
        url: '/rssfeeds',
        defaults: {
            entries: []
        },

        removeArticle: function(article) {
            var entries_without_article = _(this.get('entries')).filter(function (entry) {
                return entry.get('link') !== article.get('link')
            });
            this.set('entries', entries_without_article);
        }
    });

    var RssFeeds = Backbone.Collection.extend({
        model: RssFeed,
        url: '/rssfeeds'
    });

    var Article = Backbone.Model.extend({});

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

    app.fileSelected = function () {
        var file = document.getElementById('opmlFile').files[0];
        if (file) {
            var xhr = new XMLHttpRequest();
            var fd = new FormData();
            fd.append("opmlFile", document.getElementById('opmlFile').files[0]);
            xhr.open("POST", '/opml/import');
            xhr.send(fd);
        }
    };

    app.ArticleView = Backbone.View.extend({
        tagName : 'div',
        template: _.template('<%=body%>'),
        initialize: function (options) {
            if (options.model.get('content') == undefined) {
                options.model.set('body', options.model.get('summary'));
            } else {
                options.model.set('body', options.model.get('content')[0].value);
            }
        },
        render: function() {
            var article = this.model;
            $.ajax({
                url: '/article',
                type: 'PUT',
                data: JSON.stringify({"url": article.get('link'), "feed_id": article.get('feed').id})
            });
            article.get('feed').removeArticle(article);
            this.$el.html(this.template(this.model.attributes));
            return this;
        }
    });

    app.ArticleLinkView = Backbone.View.extend({
        tagName: 'li',
        template: _.template('<a class="article" href="<%=link%>"><%=title%></a>'),
        events: {
            'click .article': 'showArticle'
        },
        render: function () {
            this.$el.html(this.template(this.model.attributes));
            return this.$el;
        },
        showArticle: function (e) {
            e.preventDefault();
            var modal = new Backbone.BootstrapModal({
                    content: new app.ArticleView({model: this.model}),
                    title: this.model.get('title'),
                    cancelText: false,
                    okText: 'Fermer',
                    animate: true
                });
            modal.open();
        }
    });

    var appRouter = new MyRefsRouter();
    Backbone.history.start();
    appRouter.navigate('rss', {trigger: true});

    app.RssView = Backbone.View.extend({
        tagName: 'div',

        template: _.template('\
                <div class="panel-heading"> \
                    <h4 class="panel-title"> \
                        <a data-toggle="collapse" data-parent="#feeds" href="#<%=id%>"><%=title%></a> \
                    </h4> \
                </div>\
                <div id="<%=id%>" class="panel-collapse collapse"> \
                    <div class="panel-body"> \
                        <ul></ul> \
                    </div> \
                </div>'),

        initialize: function() {
            _.bindAll(this, "render");
            this.model.bind('change', this.render);
        },

        render: function () {
            this.$el.addClass('panel panel-default');
            this.$el.html(this.template(this.model.attributes));
            var self = this;
            if (this.model.get('entries').length > 0) {
                this.$el.find('.panel-title').append("<span class='badge alert-danger'>" + this.model.get('entries').length + "</span>");
            }
            _(this.model.get('entries')).each(function (entry) {
                self.$el.find('ul').append(new app.ArticleLinkView({model: entry}).render());
            });
            return this.$el;
        }
    });

    app.RssListView = Backbone.View.extend({
        id: 'feeds',
        events: {
            "click .new-rss-btn": "addRssFeed"
        },
        initialize: function () {
            _.bindAll(this, 'render');
            this.$new_feed_input = $('#new_feed_input');
            this.$el.addClass('panel-group');

            this.model = new RssFeeds();
            this.model.bind('reset', this.render);
            this.model.fetch({reset: true});
        },

        render: function () {
            var self = this;
            $('#rssfeeds_row').find('div.col-lg-12').html(this.$el);
            _(this.model.models).each(function (rssFeed) {
                self.$el.append(new app.RssView({model: rssFeed}).render());
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
            var self = this;
            var source = new EventSource('/updatefeeds');
            source.onmessage = function (msg) {
                var feedupdates = JSON.parse(msg.data);
                var entries = JSON.parse(feedupdates.entries);

                if (entries.length > 0) {
                    var feed = self.model.findWhere({id: feedupdates.id});
                    feed.set('entries', _(entries).map(function(entry) {
                        entry.feed = feed;
                        return new Article(entry)
                    }));
                }
            };
            source.addEventListener('close', function () {
                console.log("closing feeds update");
                this.close();
            }, false);
        }
    });
    new app.RssListView();
})(jQuery);