__license__ = 'MIT License <http://www.opensource.org/licenses/mit-license.php>'
__author__ = 'Lucas Theis <lucas@theis.io>'
__docformat__ = 'epytext'

from django.conf.urls.defaults import *
from django.views.static import serve
import os
import publications

urlpatterns = patterns('',
	url(r'^$', 'publications.views.year', name='publications'),
	url(r'^(?P<publication_id>\d+)/(?P<slug>.*)$', 'publications.views.publication', name='publication'),
	url(r'^year/(?P<year>\d+)/$', 'publications.views.year', name='publications-year'),
	url(r'^keyword/(?P<keyword>.+)/$', 'publications.views.keyword', name='publications-keyword'),
	url(r'^person/(?P<person_id>\d+)/(?P<slug>.*)$', 'publications.views.person', name='publications-person'),
	url(r'^media(?P<path>/.*)$', serve, {'document_root': os.path.join(os.path.dirname(publications.__file__), "media"), 'show_indexes': True}, name='publications-media'),
)
