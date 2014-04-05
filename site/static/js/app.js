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

    app.ArticleView = Backbone.View.extend({
        tagName : 'div',
        template: _.template('\
        <div class="modal fade" id="article_modal" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">\
          <div class="modal-dialog"> \
            <div class="modal-content">\
              <div class="modal-header">\
                <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>\
                <h4 class="modal-title" id="myModalLabel"><%=title%></h4>\
              </div>\
              <div class="modal-body">\
                 <%=body%>\
              </div>\
              <div class="modal-footer">\
                <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>\
              </div>\
            </div>\
          </div>\
          </div>\
        </div>'),

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
                data: JSON.stringify({"url": article.get('link'), "feed_id": article.get('feed_id')})
            });
            $('#modal_container').html(this.template(article.attributes));
            $(this.$el).modal();
            return this.$el;
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
            new app.ArticleView({model: this.model}).render();
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
                        $feedBody.find('ul').append(new app.ArticleLinkView({model: new Article(entry)}).render());
                    });
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