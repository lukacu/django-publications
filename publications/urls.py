__license__ = 'MIT License <http://www.opensource.org/licenses/mit-license.php>'
__author__ = 'Lucas Theis <lucas@theis.io>'
__docformat__ = 'epytext'

from django.conf.urls.defaults import *
from django.views.static import serve
import os
import publications

urlpatterns = patterns('',
	# Default url: a list of publications ordered by time
	url(r'^$', 'publications.views.recent', name='publications'),

	# Individual publication
	url(r'^(?P<publication_id>\d+)(?:/.*)?$', 'publications.views.publication', name='publication'),

	# Keywords
	url(r'^keyword/(?P<keyword>.+)/$', 'publications.views.keyword', name='publications-keyword'),

	# Person catalogue of publications
	url(r'^person/$', 'publications.views.person', name='publications-person-list'),
	url(r'^person/(?P<person_id>\d+)(?:/.*)?$', 'publications.views.person', name='publications-person'),

	# Year catalogoue of publications
	url(r'^year/$', 'publications.views.years', name='publications-year-list'),
	url(r'^year/(?P<year>\d+)/$', 'publications.views.years', name='publications-year'),

	# Type catalogoue of publications
	url(r'^type/$', 'publications.views.types', name='publications-type-list'),
	url(r'^type/(?P<publication_type>.+)/$', 'publications.views.types', name='publications-type'),

	# Group urls
	url(r'^groups/$', 'publications.views.groups', name='publications-group-list'),
	url(r'^groups/(?P<group>[^/]+)/$', 'publications.views.groups', name='publications-group'),
	url(r'^groups/(?P<group>[^/]+)/year/$', 'publications.views.years', name='publications-group-year-list'),
	url(r'^groups/(?P<group>[^/]+)/year/(?P<year>\d+)/$', 'publications.views.years', name='publications-group-year'),
	url(r'^groups/(?P<group>[^/]+)/type/$', 'publications.views.types', name='publications-group-type-list'),
	url(r'^groups/(?P<group>[^/]+)/type/(?P<publication_type>.+)/$', 'publications.views.types', name='publications-group-type'),
	url(r'^groups/(?P<group>[^/]+)/person/$', 'publications.views.person', name='publications-group-person-list'),
	url(r'^groups/(?P<group>[^/]+)/person/(?P<person_id>\d+)(?:/.*)?$', 'publications.views.person', name='publications-group-person'),

  url(r'^files/(?P<publication_id>\d+)(?:/.*)?$', 'publications.views.files', name='publication-files'),
)
