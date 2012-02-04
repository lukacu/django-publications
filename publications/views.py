# -*- Mode: python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

from django.shortcuts import render_to_response
from django.template import RequestContext, loader
from publications.models import Publication, Group, Person, PublicationType
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count
from django.http import HttpResponse
from string import replace, split
from django.utils import simplejson 
from string import capwords, replace, split
from django.core.urlresolvers import reverse
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from tagging.models import Tag, TaggedItem

def keyword(request, keyword):

  try:
    tag = Tag.objects.get(slug = keyword)
  except ObjectDoesNotExist:
    raise Http404

  candidates = TaggedItem.objects.get_by_model(Publication.objects.filter(public=True).order_by('-year', '-month', '-id'), tag)

  if 'format' in request.GET:
    format = request.GET['format']
  else:
    format = 'default'

  return render_result(request, candidates, "Publications for keyword %s" % tag.name, format, None)


def publication(request, publication_id):
  try:
    publication = Publication.objects.get(pk=publication_id)
  except ObjectDoesNotExist:
    raise Http404

  if 'format' in request.GET:
    format = request.GET['format']
  else:
    format = 'default'
  if format == "json":
    data = list()
    for publication in [publication]:
      entry = publication.to_dictionary()
      entry["pubtype"] = publication.type.bibtex_type
      data.append(entry)
    return HttpResponse(simplejson.dumps(data), mimetype='application/json; charset=UTF-8')
  elif format == 'bibtex':
    return render_to_response('publications/publications.bib', {
        'publications': [publication]
      }, context_instance=RequestContext(request), mimetype='application/x-bibtex; charset=UTF-8')
  else:
    try:
      return render_to_response('publications/publication_%s.html' % publication.type.identifier, {
          'publication': publication, 'title' : publication.title
        }, context_instance=RequestContext(request))
    except loader.TemplateDoesNotExist:
      return render_to_response('publications/publication.html', {
          'publication': publication, 'title' : publication.title
        }, context_instance=RequestContext(request))

def person(request, person_id = None, group = None):

  if group:
    try:
      group = Gropu.objects.get(identifier__iexact=group)
    except ObjectDoesNotExist:
      raise Http404

  if person_id:
    try:
      author = Person.objects.get(pk = person_id)
    except ObjectDoesNotExist:
      raise Http404

    candidates = Publication.objects.filter(public=True, role__person = author).order_by('-year', '-month', '-id')

    if group:
      candidates = candidates.filter(groups=group)

    if 'format' in request.GET:
      format = request.GET['format']
    else:
      format = 'default'

    return render_result(request, candidates, "Publications by %s" % author.full_name(), format, group)

  else:
    people = Person.objects.annotate(count = Count('role__publication')).order_by('family_name', 'primary_name')

    if group:
      people = people.filter(groups=group)

    return render_to_response('publications/people.html', {
        'people': people,
        'group': group
      }, context_instance=RequestContext(request))


def years(request, year = None, group = None):

  if not group and getattr(settings, 'PUBLICATIONS_DEFAULT_GROUP', None):
    group = settings.PUBLICATIONS_DEFAULT_GROUP

  if group:
    try:
      group = Group.objects.get(identifier__iexact=group)
    except ObjectDoesNotExist:
      raise Http404

  if year:
    candidates = Publication.objects.filter(year=year, public=True).order_by('-year', '-month', '-id')

    if group:
      candidates = candidates.filter(groups=group)

    if 'format' in request.GET:
      format = request.GET['format']
    else:
      format = 'default'

      return render_result(request, candidates, "Publications in %s" % year, format, group)

  else:
    years = Publication.objects.filter(public=True).values('year').annotate(count = Count('year')).order_by()

    if group:
      years = years.filter(groups=group)

    return render_to_response('publications/years.html', {
        'years': years,
        'group': group
      }, context_instance=RequestContext(request))

def types(request, publication_type = None, group = None):

  if not group and getattr(settings, 'PUBLICATIONS_DEFAULT_GROUP', None):
    group = settings.PUBLICATIONS_DEFAULT_GROUP

  if group:
    try:
      group = Group.objects.get(identifier__iexact=group)
    except ObjectDoesNotExist:
      raise Http404

  if publication_type:
    try:
      ptype = PublicationType.objects.get(identifier = publication_type)
    except ObjectDoesNotExist:
      raise Http404

    candidates = Publication.objects.filter(type=ptype, public=True).order_by('-year', '-month', '-id')

    if group:
      candidates = candidates.filter(groups=group)

    if 'format' in request.GET:
      format = request.GET['format']
    else:
      format = 'default'

      return render_result(request, candidates, "Publications of type %s" % ptype.title, format, group)

  else:
    types = PublicationType.objects.filter(publication__public=True).distinct()

    if group:
      types = types.filter(publication__groups=group)

    types = types.annotate(count = Count('publication__id')).order_by("title")

    return render_to_response('publications/types.html', {
        'types': types,
        'group': group
      }, context_instance=RequestContext(request))

def recent(request, group = None):

  if not group and getattr(settings, 'PUBLICATIONS_DEFAULT_GROUP', None):
    group = settings.PUBLICATIONS_DEFAULT_GROUP

  if group:
    try:
      group = Group.objects.get(identifier__iexact=group)
    except ObjectDoesNotExist:
      raise Http404

  limit = getattr(settings, 'PUBLICATIONS_PAGE_SIZE', 20)

  candidates = Publication.objects.filter(public=True).order_by('-year', '-month', '-id')

  if group:
    candidates = candidates.filter(groups=group)

  if 'format' in request.GET:
    format = request.GET['format']
  else:
    format = 'default'

  return render_result(request, candidates[0:limit], "Recent publications", format, group)

def groups(request, group = None):

  if group:
    try:
      group = Group.objects.get(identifier__iexact=group)
    except ObjectDoesNotExist:
      raise Http404

  print group

  if group:
    candidates = Publication.objects.filter(public=True, groups = group).order_by('-year', '-month', '-id')

    if 'format' in request.GET:
      format = request.GET['format']
    else:
      format = 'default'

      return render_result(request, candidates, "Publications in %s" % group.title, format, group)

  else:
    groups = Group.objects.filter(publication__public=True, public=True).annotate(count = Count('publication__id')).order_by("title")

    return render_to_response('publications/groups.html', {
        'groups': groups
      }, context_instance=RequestContext(request))

def render_result(request, publications, title, format, group):
  if format == "json":
    data = list()
    for publication in publications:
      entry = publication.to_dictionary()
      entry["type"] = publication.type.pk
      entry["id"] = publication.pk
      data.append(entry)
    return HttpResponse(simplejson.dumps(data), mimetype='application/json; charset=UTF-8')
  elif format == 'bibtex':
    return render_to_response('publications/publications.bib', {
        'title': title,
        'publications': publications,
        'format': format,
        'group': group
      }, context_instance=RequestContext(request), mimetype='application/x-bibtex; charset=UTF-8')
  else:
    limit = getattr(settings, 'PUBLICATIONS_PAGE_SIZE', 20)

    paginator = Paginator(publications, limit)

    page = request.GET.get('page', 1)
    try:
        publications = paginator.page(page)
    except PageNotAnInteger:
        publications = paginator.page(1)
    except EmptyPage:
        publications = paginator.page(paginator.num_pages)

    return render_to_response('publications/list.html', {
        'publications': publications,
        'title': title,
        'format': "html",
        'group': group
      }, context_instance=RequestContext(request))

