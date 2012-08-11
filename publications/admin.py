# -*- Mode: python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-
from publications import list_import_formats, get_publications_importer

__license__ = 'MIT License <http://www.opensource.org/licenses/mit-license.php>'
__author__ = 'Lucas Theis <lucas@theis.io>'
__docformat__ = 'epytext'

from django.contrib import admin
from django import forms
import publications.models
from publications.models import Publication, Group, Authorship, Person, Metadata, Import
from publications.fields import PeopleField
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

def merge_people_by_family_name(modeladmin, request, queryset):
  groups = publications.models.group_people_by_family_name(list(queryset))
  groups = filter(lambda x : len(x) > 2, [group for fn, group in groups.items()])
  if not len(groups):
    messages.info(request, "Nothing to merge")
    return HttpResponseRedirect(reverse("admin:publications_person_changelist"))
  return render_to_response('admin/publications/person/merge.html', {
      'groups': groups
    }, context_instance=RequestContext(request))

def merge_people(modeladmin, request, queryset):
  return render_to_response('admin/publications/person/merge.html', {
      'groups': [list(queryset)]
    }, context_instance=RequestContext(request))


class PublicationForm(forms.ModelForm):
  class Meta:
    model = Publication
  people_authorship = PeopleField(label="People", max_length=1024, help_text = 'List of authors separated by semicolon. Both first-name last-name and last-name, first name forms can be used. Example: John Doe; Smith, David; William, Chris.')

  latitude = forms.FloatField(required=False)
  def __init__(self, *args, **kwargs):
    super(PublicationForm, self).__init__(*args, **kwargs)

    if kwargs.has_key('instance'):
      instance = kwargs['instance']
      self.initial['people_authorship'] = instance.people_as_string()

  def save(self, commit=True):
    model = super(PublicationForm, self).save(commit=False)

    model.set_people = self.cleaned_data['people_authorship']

    if commit:
        model.save()

    return model

class MetadataInline(admin.TabularInline):
    model = Metadata

class AuthorshipInline(admin.TabularInline):
    model = Authorship

class PublicationAdmin(admin.ModelAdmin):
  radio_fields = {"type": admin.HORIZONTAL}
  raw_id_fields = ["people"]
  list_display = ('type', 'first_author', 'title', 'year', 'within')
  list_display_links = ('title',)
  search_fields = ('title', 'within', 'authors', 'tags', 'year')
  fieldsets = (
    ("Basic information", {'fields': 
      ('type', 'title', 'people_authorship', 'abstract', 'note')}),
    ("Publishing information", {'fields': 
      ('year', 'month', 'within', 'publisher', 'volume', 'number', 'pages')}),
    ("Resources", {'fields': 
      ('url', 'code', 'file', 'doi')}),
    ("Categoritzation", {'fields': 
      ('tags', 'public', 'groups')}),
  )
  inlines = [MetadataInline]
  form = PublicationForm

  def import_publications(self, request):
    if request.method == 'POST':
      # container for error messages
      errors = {"publications" : [], "importer" : []}

      # check for errors
      if not request.POST['publications']:
        errors["publications"].append('This field is required.')

      if not request.POST['importer']:
        errors["importer"].append('This field is required.')
      else:
        importer = get_publications_importer(request.POST['importer'])
        if importer:      
 
          publications = []
          importer.import_from_string(request.POST['publications'], lambda x : publications.append(x), lambda x : errors["publications"].append(x))

          for publication in publications:
            i = Import(title = publication["title"], data = publication, source = importer.get_format_identifier())
            i.save()

          if not publications:
            errors["publications"].append('No valid entries found.')
        else:
          errors["importer"].append('Not a registered importer.')

      if errors["publications"] or errors["importer"]:
        # some error occurred
        return render_to_response(
          'admin/publications/publication/import.html', {
            'errors': errors,
            'title': 'Import publications',
            'importers' : list_import_formats(),
            'request': request},
          RequestContext(request))
      else:
        if len(publications) > 1:
          msg = 'Successfully added ' + str(len(publications)) + ' publications to import queue.'
        else:
          msg = 'Successfully added publication to import queue.'

        # show message
        messages.info(request, msg)

        # redirect to publication listing
        return HttpResponseRedirect(reverse("admin:publications_publication_changelist"))
    else:
      return render_to_response(
        'admin/publications/publication/import.html', {
          'title': 'Import publications', 'importers' : list_import_formats(),
          'request': request},
        RequestContext(request))

  def get_urls(self):
      from django.conf.urls import patterns, url
      urls = super(PublicationAdmin, self).get_urls()
      my_urls = patterns('',
          url(
              r'import',
              self.admin_site.admin_view(self.import_publications),
              name='import_publications',
          ),
      )
      return my_urls + urls

class GroupAdmin(admin.ModelAdmin):
  list_display = ('identifier', 'title', 'public')

class PersonAdmin(admin.ModelAdmin):
  list_display = ('family_name', 'primary_name' , 'url', 'public', 'group')
  list_display_links = ('primary_name', 'family_name',)
  actions = [merge_people, merge_people_by_family_name]

  def merge(self, request):
    if request.method == 'POST':
      if request.POST.has_key("_cancel"):
        return HttpResponseRedirect(reverse("admin:publications_person_changelist"))
      groups_count = int(request.POST.get("groups_count", 0))
      groups = []
      for group_id in xrange(1, groups_count+1):
        #TODO: more validation
        group_entries = [ int(i.strip()) for i in request.POST.get("group%d_set" % group_id, "").strip().split(" ") ]
        pivot_id = int(request.POST.get("group%d" % group_id, "-1"))
        if pivot_id in group_entries and len(group_entries) > 1:
          group = list(Person.objects.filter(id__in = group_entries))
          pivot = filter(lambda x : x.id == pivot_id, group)[0]
          publications.models.merge_people(group, pivot)
          messages.info(request, "Merged %d people entries" % len(group))
        elif len(group_entries) == 1:
          continue
        else:
          groups.append(list(Person.objects.filter(id__in = group_entries)))

      if len(groups) > 0:
        return render_to_response('admin/publications/person/merge.html', {
          'groups': groups
          }, context_instance=RequestContext(request))

    return HttpResponseRedirect(reverse("admin:publications_person_changelist"))

  def get_urls(self):
      from django.conf.urls.defaults import patterns, url
      urls = super(PersonAdmin, self).get_urls()
      my_urls = patterns('',
          url(
              r'merge',
              self.admin_site.admin_view(self.merge),
              name='merge_people',
          ),
      )
      return my_urls + urls


admin.site.register(Publication, PublicationAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Person, PersonAdmin)