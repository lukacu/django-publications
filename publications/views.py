__license__ = 'MIT License <http://www.opensource.org/licenses/mit-license.php>'
__author__ = 'Lucas Theis <lucas@theis.io>'
__docformat__ = 'epytext'

from django.shortcuts import render_to_response
from django.template import RequestContext
from publications.models import Publication, Group, Person
from django.http import HttpResponse
from string import replace, split
from django.utils import simplejson 
from string import capwords, replace, split
from django.core.urlresolvers import reverse
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from publications.bibtex import BIBTEX_TYPES
from django.http import Http404

def keyword(request, keyword):

	keyword = replace(keyword.lower(), ' ', '+')

	candidates = Publication.objects.filter(keywords__icontains=split(keyword, '+')[0], public=True)

	group = None
	if 'group' in request.GET:
		group = request.GET['group']
	elif getattr(settings, 'PUBLICATIONS_DEFAULT_GROUP', None):
		group = settings.PUBLICATIONS_DEFAULT_GROUP
	if group:
		candidates = candidates.filter(groups__name__iexact=group)

	publications = []

	# todo ... do this with tagging!!!
	for i, publication in enumerate(candidates):
		if keyword in [k[1] for k in publication.keywords_escaped()]:
			publications.append(publication)

	if 'format' in request.GET:
		format = request.GET['format']
	else:
		format = 'default'

	return render_result(request, candidates, "Publications for keyword %s" % keyword, format, group)


def id(request, publication_id):
	publications = Publication.objects.filter(pk=publication_id)

	if 'format' in request.GET:
		format = request.GET['format']
	else:
		format = 'default'

	if format == "json":
		data = list()
		for publication in publications:
			entry = publication.to_dictionary()
			entry["pubtype"] = publication.type.bibtex_type
			data.append(entry)
		return HttpResponse(simplejson.dumps(data), mimetype='text/plain; charset=UTF-8')
	elif format == 'bibtex':
		return render_to_response('publications/publications.bib', {
				'publications': publications
			}, context_instance=RequestContext(request), mimetype='text/plain; charset=UTF-8')
	else:
		absolute_url = request.build_absolute_uri(reverse("publication", kwargs={"publication_id" : publication_id}))
		return render_to_response('publications/id.html', {
				'publications': publications, 'absolute_url' : absolute_url
			}, context_instance=RequestContext(request))

def person(request, person_id):
	try:
		author = Person.objects.get(pk = person_id)
	except ObjectDoesNotExist:
		raise Http404

	# find publications of this author
	publications = []
	types = []
	
	for t, d in BIBTEX_TYPES.items():
		types.append((t, d['name']))

	candidates = Publication.objects.filter(public=True, role__person = author).order_by('-year', '-month', '-id')

	group = None
	if 'group' in request.GET:
		group = request.GET['group']
#	elif getattr(settings, 'PUBLICATIONS_DEFAULT_GROUP', None):
#		group = settings.PUBLICATIONS_DEFAULT_GROUP

	if group:
		candidates = candidates.filter(groups__name__iexact=group)

	if 'format' in request.GET:
		format = request.GET['format']
	else:
		format = 'default'

	return render_result(request, candidates, "Publications by %s" % author.display, format, group)

def year(request, year=None):

	years = []
	if year:
		candidates = Publication.objects.filter(year=year, public=True)
	else:
		candidates = Publication.objects.filter(public=True)
	candidates = candidates.order_by('-year', '-month', '-id')

	group = None
	if 'group' in request.GET:
		group = request.GET['group']
	elif getattr(settings, 'PUBLICATIONS_DEFAULT_GROUP', None):
		group = settings.PUBLICATIONS_DEFAULT_GROUP
	if group:
		candidates = candidates.filter(groups__name__iexact=group)

	if 'format' in request.GET:
		format = request.GET['format']
	else:
		format = 'default'

	if year:
		return render_result(request, candidates, "Publications in %s" % year, format, group)
	else:
		return render_result(request, candidates, "Publications", format, group)
	


def render_result(request, publications, title, format, group):
	print format
	if format == "json":
		data = list()
		for publication in publications:
			entry = publication.to_dictionary()
			entry["type"] = publication.type
			entry["id"] = publication.pk
			data.append(entry)
		return HttpResponse(simplejson.dumps(data), mimetype='text/plain; charset=UTF-8')
	elif format == 'bibtex':
		return render_to_response('publications/publications.bib', {
				'title': title,
				'publications': publications,
				'format': format,
				'group': group
			}, context_instance=RequestContext(request), mimetype='text/plain; charset=UTF-8')
	elif format == 'annual':
		years = []
		for publication in publications:
			if not years or (years[-1][0] != publication.year):
				years.append((publication.year, []))
			years[-1][1].append(publication)
		return render_to_response('publications/years.html', {
				'years': years,
				'title': title,
				'format': format,
				'group': group
			}, context_instance=RequestContext(request))
	elif format == 'types':
		types_dict = {}
		for publication in publications:
			if types_dict.has_key(publication.type):
				types_dict[publication.type].append(publication)
			else:
				types_dict[publication.type] = [publication]
		types = []
		for type_id, type_data in BIBTEX_TYPES.items():
			if types_dict.has_key(type_id):
				types.append((type_id, type_data['name'], types_dict[type_id]))
		return render_to_response('publications/types.html', {
				'types': types,
				'title': title,
				'format': format,
				'group': group
			}, context_instance=RequestContext(request))
	else:
		return render_to_response('publications/list.html', {
				'publications': publications,
				'title': title,
				'format': "default",
				'group': group
			}, context_instance=RequestContext(request))

