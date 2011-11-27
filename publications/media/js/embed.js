// -*- Mode: javascript; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

// If no jQuery available then no fun
if (jQuery) {

$(document).ready(function () {
  $("a.publications").each(function (i) {
    var a = $(this);
    var queryParameters = {}, queryString = this.search.substring(1),
    re = /([^&=]+)=([^&]*)/g, m;
    while (m = re.exec(queryString)) {
        queryParameters[decodeURIComponent(m[1])] = decodeURIComponent(m[2]);
    }
    if ('format' in queryParameters && queryParameters['format'] == 'json')
      return;
    queryParameters['format'] = 'json';
//    this.search = $.param(queryParameters);

    $.ajax({url : this.href, data : {"format":"json"}, dataType : "json", success : function(data) {
      var list = $('<ul/>', {'class': a.attr("class")});
      for each (var publication in data) {
        var title = $('<div>' + publication.title + '</div>').addClass("title");
        var authors = $('<div>' + publication.author + '</div>').addClass("authors");
        list.append($('<li/>').append(title).append(authors));
      }
      a.replaceWith(list); }
    });
  });
});

}
