// -*- Mode: javascript; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

// If no jQuery available then no fun
if (jQuery) {

    $(document).ready(function () {
        $("a.publications").each(function (i) {

            var authorsTemplate = function (authors) {

                if (authors.length == 0)
                    return $('<span />');

                var wrapper = $('<div />').addClass("authors");

                if (authors.length == 1)
                    return wrapper.append($("<span />").addClass("person").text(authors[0]));

                for (var i = 0; i < authors.length - 1; i++) {
                    wrapper.append($("<span />").addClass("person").text(authors[i])).append(", ");

                }
                return wrapper.append(" and ").append($("<span />").addClass("person").text( authors[authors.length - 1]));

            }

            var publicationTemplate = function (publication) {
                var title = $("<div />").addClass("title").append($('<a>' + publication.title + '</a>').attr("href", publication.url));
                var authors = authorsTemplate(publication.authors);
                var published = $("<div />").addClass("published").text(
                    (publication.within === '' ? "" : publication.within + ", ") +
                    (publication.publisher === '' ? "" : publication.publisher + ", ")
                        + publication.year);
                return ($('<div/>').addClass("publication_inline publication_type_" + publication.type).append(title, authors, published));
            }
/*
            <div class="publication_inline publication_type_{{ publication.type }}">
                <div class="title"><a href="{{ publication.get_absolute_url }}/{{ publication.title|slugify }}" class="title">{{ publication.title }}</a></div>
                <div class="authors">
{% for author in publication.authors %}
                    <span class="person">
{% if author.public %}<a href="{{ author.get_absolute_url }}/{{ author.full_name|slugify }}">{{ author.full_name }}</a>{% else %}{{ author.full_name }}{% endif %}</span>{% if not forloop.last %}{% if forloop.revcounter == 2 %}{% if not forloop.first %},{% endif %} and {% else %}, {% endif %}{% endif %}
{% endfor %}
                </div>
                <div class="published">{% if publication.within %}{{ publication.within }}, {% endif %}{% if publication.publisher %}{{ publication.publisher }}, {% endif %}{{ publication.year }}</div>
            </div>
            */
            var a = $(this);
            var queryParameters = {}, queryString = this.search.substring(1),
                re = /([^&=]+)=([^&]*)/g, m;
            while (m = re.exec(queryString)) {
                queryParameters[decodeURIComponent(m[1])] = decodeURIComponent(m[2]);
            }
            if ('format' in queryParameters) return;
            queryParameters['format'] = 'json';
            //    this.search = $.param(queryParameters);
            a.addClass("waiting");
            $.ajax({
                url:this.href,
                data:{"format":"json"},
                dataType:"json",
                error:function () {
                    a.removeClass("waiting");
                },
                success:function (data) {
                    a.removeClass("waiting");

                    if (data.length < 1) return;

                        var single = data.length == 1;

                        if (!single || a.hasClass("list")) {

                        var list = $('<ul/>', {'class':a.attr("class")});
                        list.addClass("embedded");
                        data.forEach(function (publication) {
                            list.append($('<li/>').append(publicationTemplate(publication)));
                        });

                        a.replaceWith(list);
                        list.after($("<a/>").attr({"href" : a.attr("href")}).addClass("publications external").text("More"));
                    } else {
                        a.replaceWith(publicationTemplate(data[0]));
                    }
                }
            });
        });
    });

}
