__license__ = 'MIT License <http://www.opensource.org/licenses/mit-license.php>'
__author__ = 'Lucas Theis <lucas@theis.io>'
__docformat__ = 'epytext'

from django.conf.urls.defaults import *
from django.views.static import serve

urlpatterns = patterns('',
	url(r'^$', 'publications.views.year', name='publications'),
	url(r'^(?P<publication_id>\d+)/$', 'publications.views.id', name='publication'),
	url(r'^year/(?P<year>\d+)/$', 'publications.views.year', name='publications-year'),
	url(r'^keyword/(?P<keyword>.+)/$', 'publications.views.keyword', name='publications-keyword'),
	url(r'^(?P<name>.+)/$', 'publications.views.person', name='publications-author'),
)
