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

        render: function () {
            this.$el.addClass('panel panel-default');
            this.$el.html(this.template(this.model.attributes));
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
            var source = new EventSource('/updatefeeds');
            source.onmessage = function (msg) {
                var feedupdates = JSON.parse(msg.data);
                var entries = JSON.parse(feedupdates.entries);

                if (entries.length > 0) {
                    var $feed_title = $('#feeds').find('a[href="#' + feedupdates.id + '"]');
                    $feed_title.append("<span class='badge alert-danger'>" + entries.length + "</span>");
                    var $feedBody = $('#feeds').find('#' + feedupdates.id).find('.panel-body');
                    _(entries).each(function (entry) {
                        entry.feed_id = feedupdates.id;
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
                    if (article.content === undefined) {
                        $('#article_modal').find('.modal-body').html('<p>' + article.summary + '</p>' + '<p><a href="' + article.link + '">'  + article.link + '</a></p>');
                    } else {
                        $('#article_modal').find('.modal-body').html(article.content[0].value);
                    }

                    $('#article_modal').modal();

                    $.ajax({
                        url: '/article',
                        type: 'PUT',
                        data: JSON.stringify({"url": article.link, "feed_id": article.feed_id})
                    });
                });
                console.log("closing feeds update");
                this.close();
            }, false);
        }
    });
    new app.RssListView();
})(jQuery);