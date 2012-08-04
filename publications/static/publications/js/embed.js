// -*- Mode: javascript; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

// If no jQuery available then no fun
if (jQuery) {

    $(document).ready(function () {
        $("a.publications").each(function (i) {

            var authorsTemplate = function (authors) {

                if (authors.length == 0)
                    return "";

                if (authors.length == 1)
                    return authors[0];

                var str = "";
                for (var i = 0; i < authors.length - 1; i++) {
                    str += authors[i] + ", ";
                }
                return str + " and " + authors[authors.length - 1];

            }

            var publicationTemplate = function (publication) {
                var title = $('<a>' + publication.title + '</a>').addClass("title").attr("href", publication.url);
                var authors = $('<span>' + authorsTemplate(publication.authors) + '</span>').addClass("authors");
                var within = $('<span>' + publication.within + '</span>').addClass("within");
                var year = $('<span>' + publication.year + '</span>').addClass("year");
                return ($('<div/>').addClass("publication type_" + publication.type).append(title, authors, within, year));
            }


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
