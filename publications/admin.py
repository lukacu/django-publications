# -*- Mode: python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-
__license__ = 'MIT License <http://www.opensource.org/licenses/mit-license.php>'
__author__ = 'Lucas Theis <lucas@theis.io>'
__docformat__ = 'epytext'

from django.contrib import admin
from django import forms
import publications.models
from publications.orderedmodel import OrderedModelAdmin
from publications.models import Publication, Group, Role, Person, PublicationType, RoleType, Metadata, generate_publication_objects
from publications.widgets import PeopleWidget
from publications.fields import PeopleField
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

def merge_people_by_family_name(modeladmin, request, queryset):
  groups = publications.models.group_people_by_family_name(list(queryset))
  groups = filter(lambda x : len(x) > 2, [group for fn, group in groups.items()])
  if len(groups) == 0:
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
  people_roles = PeopleField(label="People", max_length=1024)

  latitude = forms.FloatField(required=False)
  # Step 2: Override the constructor to manually set the form's latitude and
  # longitude fields if a Location instance is passed into the form
  def __init__(self, *args, **kwargs):
    super(PublicationForm, self).__init__(*args, **kwargs)

    # Set the form fields based on the model object
    if kwargs.has_key('instance'):
      instance = kwargs['instance']
      self.initial['people_roles'] = instance.people_as_string()

  # Step 3: Override the save method to manually set the model's latitude and
  # longitude properties based on what was submitted from the form
  def save(self, commit=True):
    model = super(PublicationForm, self).save(commit=False)

    model.set_people = self.cleaned_data['people_roles']
    # Save the latitude and longitude based on the form fields
    #model.set_people = self.cleaned_data['latitude']
    #model.longitude = self.cleaned_data['longitude']

    if commit:
        model.save()

    return model

class MetadataInline(admin.TabularInline):
    model = Metadata

class RoleInline(admin.TabularInline):
    model = Role

class PublicationAdmin(admin.ModelAdmin):
  radio_fields = {"type": admin.HORIZONTAL}
  raw_id_fields = ["people"]
  list_display = ('type', 'first_author', 'title', 'year', 'journal_or_book_title')
  list_display_links = ('title',)
  search_fields = ('title', 'journal', 'authors', 'keywords', 'year')
  fieldsets = (
    ("Basic information", {'fields': 
      ('type', 'title', 'people_roles', 'abstract', 'note')}),
    ("Publishing information", {'fields': 
      ('year', 'month', 'journal', 'book_title', 'publisher', 'volume', 'number', 'pages')}),
    ("Resources", {'fields': 
      ('url', 'code', 'file', 'doi')}),
    ("Categoritzation", {'fields': 
      ('keywords', 'public', 'groups')}),
  )
  inlines = [MetadataInline]
  form = PublicationForm

  def import_bibtex(self, request):
    if request.method == 'POST':
      # container for error messages
      errors = list()

      # check for errors
      if not request.POST['bibliography']:
        errors.append('This field is required.')

      from publications.bibtex import BibTeXParser, BibTeXProcessor

      bibliography = list()
      if not errors:
        parser = BibTeXParser()
        entries = parser.parse(request.POST['bibliography'])
        if not entries:
          for error in parser.getErrors():
            errors.append("%s (line: %d, column %d)" % (error["message"], error["line"], error["column"]))
        else:
          processor = BibTeXProcessor()
          for entry in entries:
            processed_entry = processor.process(entry)
            if not processed_entry:
              for error in processor.getErrors():
                errors.append("%s (line: %d, column %d)" % (error["message"], error["line"], error["column"]))
              continue
            processed_entry["type"] = entry["type"]
            bibliography.append(processed_entry)

      if not errors:
        try:
          publications = generate_publication_objects(bibliography)
        except Exception, e:
          errors.append(str(e))

      if not errors and not publications:
        errors.append('No valid BibTex entries found.')

      if errors:
        # some error occurred
        errors = {"bibliography" : errors}
        return render_to_response(
          'admin/publications/publication/import_bibtex.html', {
            'errors': errors,
            'title': 'Import BibTex',
            'request': request},
          RequestContext(request))
      else:
        try:
          # save publications
          for publication in publications:
            publication.save()
        except:
          msg = 'Some error occured during saving of publications.'
        else:
          if len(publications) > 1:
            msg = 'Successfully added ' + str(len(publications)) + ' publications.'
          else:
            msg = 'Successfully added ' + str(len(publications)) + ' publication.'

        # show message
        messages.info(request, msg)

        # redirect to publication listing
        return HttpResponseRedirect(reverse("admin:publications_publication_changelist"))
    else:
      return render_to_response(
        'admin/publications/publication/import_bibtex.html', {
          'title': 'Import BibTex',
          'request': request},
        RequestContext(request))

  def get_urls(self):
      from django.conf.urls.defaults import patterns, url
      urls = super(PublicationAdmin, self).get_urls()
      my_urls = patterns('',
          url(
              r'import_bibtex',
              self.admin_site.admin_view(self.import_bibtex),
              name='import_bibtex',
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

class PublicationTypeAdmin(OrderedModelAdmin):
  list_display = ('title', 'description', 'public', 'bibtex_type')

class RoleTypeAdmin(OrderedModelAdmin):
  list_display = ('name', 'public', 'bibtex_field')

admin.site.register(Publication, PublicationAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(PublicationType, PublicationTypeAdmin)
admin.site.register(RoleType, RoleTypeAdmin)
