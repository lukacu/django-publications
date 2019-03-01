# -*- Mode: python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-
import mimetypes, json
from os.path import splitext
from os.path import join, exists
from posix import stat
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse

from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext, loader
from django.utils.encoding import smart_str
from publications.models import Publication, PublicationType, Group, Person
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from publications import get_publications_exporter, list_export_formats

mimetypes.init()

PUBLICATION_ORDER = {
  'date': ('-year', '-month', '-id'),
  'type': ('publication_type__weight', '-year', '-month', '-id')
}

def tag(request, tag):

  order_by = PUBLICATION_ORDER[request.GET['order']] if 'order' in request.GET and PUBLICATION_ORDER.has_key(request.GET['order']) else PUBLICATION_ORDER['type']

  candidates = Publication.objects.filter(public=True, tags__name=tag).order_by(*order_by)

  if 'format' in request.GET:
    format = request.GET['format']
  else:
    format = 'default'

  return render_result(request, candidates, "Publications for keyword %s" % tag, format, None)


def publication(request, publication_id):

  publication = get_object_or_404(Publication, pk=publication_id)

  if 'format' in request.GET:
    format = request.GET['format']
  else:
    format = 'default'
  if format == "json":
    data = prepare_json(publication)
    response = HttpResponse(json.dumps(data), content_type='application/json')
    response['Access-Control-Allow-Origin'] = "*"
    return response
  elif format == 'default':
    try:
      return render_to_response('publications/publication_%s.html' % publication.type(), {
          'publication': publication, 'title' : publication.title, 'exporters' : list_export_formats()
        }, context_instance=RequestContext(request))
    except loader.TemplateDoesNotExist:
      return render_to_response('publications/publication.html', {
          'publication': publication, 'title' : publication.title, 'exporters' : list_export_formats()
        }, context_instance=RequestContext(request))
  else:
    exporter = get_publications_exporter(format)
    if not exporter:
      raise Http404
    else:
      return exporter.export_to_response(publication)



def person(request, person_id = None, group = None):

  if person_id:
    author = get_object_or_404(Person, pk = person_id)

    order_by = PUBLICATION_ORDER[request.GET['order']] if 'order' in request.GET and PUBLICATION_ORDER.has_key(request.GET['order']) else PUBLICATION_ORDER['type']

    candidates = Publication.objects.filter(public=True, authorship__person = author).order_by(*order_by)

    if group:
      group = get_object_or_404(Group, identifier__iexact=group)
      candidates = candidates.filter(groups=group)

    if 'format' in request.GET:
      format = request.GET['format']
    else:
      format = 'default'

    return render_result(request, candidates, "Publications by %s" % author.full_name(), format, group)

  else:

    people = Person.objects.annotate(count = Count('authorship__publication')).filter(count__gt = 0).order_by('family_name', 'primary_name')

    if group:
      people = people.filter(group=group)

    return render_to_response('publications/people.html', {
        'people': people,
        'group': group
      }, context_instance=RequestContext(request))


def years(request, year = None, group = None):

  if not group and getattr(settings, 'PUBLICATIONS_DEFAULT_GROUP', None):
    group = settings.PUBLICATIONS_DEFAULT_GROUP

  order_by = PUBLICATION_ORDER[request.GET['order']] if 'order' in request.GET and PUBLICATION_ORDER.has_key(request.GET['order']) else PUBLICATION_ORDER['type']

  if year:
    candidates = Publication.objects.filter(year=year, public=True).order_by(*order_by)

    if group:
      group = get_object_or_404(Group, identifier__iexact=group)
      candidates = candidates.filter(groups=group)

    if 'format' in request.GET:
      format = request.GET['format']
    else:
      format = 'default'

      return render_result(request, candidates, "Publications in %s" % year, format, group)

  else:
    years = Publication.objects.filter(public=True).values('year').annotate(count = Count('year')).order_by()

    if group:
      group = get_object_or_404(Group, identifier__iexact=group)
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

  order_by = PUBLICATION_ORDER[request.GET['order']] if 'order' in request.GET and PUBLICATION_ORDER.has_key(request.GET['order']) else PUBLICATION_ORDER['type']

  if publication_type:
    type = get_object_or_404(PublicationType, identifier=publication_type)

    candidates = Publication.objects.filter(publication_type=type, public=True).order_by(*order_by)

    if group:
      candidates = candidates.filter(groups=group)

    if 'format' in request.GET:
      format = request.GET['format']
    else:
      format = 'default'

      return render_result(request, candidates, "Publications of type %s" % type.title, format, group)

  else:
    type_count = Publication.objects.filter(public=True).values('publication_type', 'publication_type__identifier', 'publication_type__title').annotate(count = Count('publication_type')).order_by()

    if group:
      type_count = type_count.filter(groups=group)

    types = []
    for type in type_count:
      types.append({"title" : type["publication_type__title"], "identifier" : type["publication_type__identifier"], "count": type["count"]})

    return render_to_response('publications/types.html', {
        'types': types,
        'group': group
      }, context_instance=RequestContext(request))

def recent(request, group = None):

  if not group and getattr(settings, 'PUBLICATIONS_DEFAULT_GROUP', None):
    group = settings.PUBLICATIONS_DEFAULT_GROUP

  limit = getattr(settings, 'PUBLICATIONS_PAGE_SIZE', 20)

  order_by = PUBLICATION_ORDER[request.GET['order']] if 'order' in request.GET and PUBLICATION_ORDER.has_key(request.GET['order']) else PUBLICATION_ORDER['type']

  candidates = Publication.objects.filter(public=True).order_by(*order_by)

  if group:
    group = get_object_or_404(Group, identifier__iexact=group)
    candidates = candidates.filter(groups=group)

  if 'format' in request.GET:
    format = request.GET['format']
  else:
    format = 'default'

  return render_result(request, candidates[0:limit], "Recent publications", format, group)

def groups(request, group = None):

  order_by = PUBLICATION_ORDER[request.GET['order']] if 'order' in request.GET and PUBLICATION_ORDER.has_key(request.GET['order']) else PUBLICATION_ORDER['type']

  if group:
    group = get_object_or_404(Group, identifier__iexact=group)
    candidates = Publication.objects.filter(public=True, groups = group).order_by(*order_by)

    format = request.GET.get('format', 'default')

    return render_result(request, candidates, "Publications in %s" % group.title, format, group)

  else:
    groups = Group.objects.filter(publication__public=True, public=True).annotate(count = Count('publication__id')).order_by("title")

    return render_to_response('publications/groups.html', {
        'groups': groups
      }, context_instance=RequestContext(request))

def files(request, publication_id):

  publication = get_object_or_404(Publication, pk=publication_id)
  filepath = publication.file.__unicode__()

  name, ext = splitext(filepath)

  filepath_absolute = join(settings.MEDIA_ROOT, filepath)

  if not exists(filepath_absolute):
    raise Http404

  statinfo = stat(filepath_absolute)

  mimetype = mimetypes.guess_type(filepath_absolute)

  mode = getattr(settings, 'PUBLICATIONS_DOWNLOAD_MODE', '')
  if mode == 'apache':
    response = HttpResponse(content_type=mimetype)
    response['X-Sendfile'] = smart_str(filepath_absolute)
  if mode == 'nginx':
    response = HttpResponse(content_type=mimetype)
    response['X-Accel-Redirect'] = smart_str(settings.MEDIA_URL + filepath)
  else:
    response = HttpResponse(open(filepath_absolute, "r"), content_type=mimetype)

  response['Content-Length'] = statinfo.st_size
  response['Content-Disposition'] = 'attachment; filename=%s%s' % (smart_str(publication.generate_identifier()), ext)
  response['Cache-Control'] = 'no-cache, must-revalidate'

  return response


def prepare_json(publication):

  protocol = getattr(settings, 'SITE_URL_PROTOCOL', "http://")

  current_site = Site.objects.get_current()

  url = protocol + current_site.domain + reverse("publication", kwargs={"publication_id" : publication.id })

  entry = {"title": publication.title, "year": publication.year,
    "authors": [author.full_name() for author in publication.authors()],
    "within" : publication.within, "publisher" : publication.publisher, "type" : publication.type(), "url" : url}

  return entry


def render_result(request, publications, title, format, group):
  if format == "json":
    data = []
    limit = getattr(settings, 'PUBLICATIONS_JSON_SIZE', -1)
    for publication in publications[0:limit] if limit > 0 else publications:
      data.append(prepare_json(publication))
    response = HttpResponse(json.dumps(data), content_type='application/json')
    response['Access-Control-Allow-Origin'] = "*"
    return response
  elif format == 'default':
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
  else:
    exporter = get_publications_exporter(format)
    if not exporter:
      raise Http404
    else:
      return exporter.export_to_response(publications)




