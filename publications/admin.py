# -*- Mode: python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-
__license__ = 'MIT License <http://www.opensource.org/licenses/mit-license.php>'
__author__ = 'Lucas Theis <lucas@theis.io>'
__docformat__ = 'epytext'

from django.contrib import admin
from django import forms
import publications.models
from publications.orderedmodel import OrderedModelAdmin
from publications.models import Publication, Group, Role, Person, PersonNaming, PublicationType, RoleType, Metadata
from publications.widgets import PeopleWidget
from publications.fields import PeopleField

def merge_people_by_family_name(modeladmin, request, queryset):
  groups = publications.models.group_people_by_family_name(list(queryset))
  for fn, group in groups.items():
    publications.models.merge_people(group)

def merge_people(modeladmin, request, queryset):
    publications.models.merge_people(list(queryset))

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

class NamingInline(admin.TabularInline):
    model = PersonNaming

class PublicationAdmin(admin.ModelAdmin):
  radio_fields = {"type": admin.HORIZONTAL}
  raw_id_fields = ["people"]
	list_display = ('type', 'first_author', 'title', 'year', 'journal_or_book_title')
	list_display_links = ('title',)
	change_list_template = 'admin/publications/change_list.html'
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

class GroupAdmin(admin.ModelAdmin):
  list_display = ('identifier', 'title', 'public')

class PersonAdmin(admin.ModelAdmin):
  list_display = ('primary_name', 'family_name', 'url', 'public', 'group')
  list_display_links = ('primary_name', 'family_name',)
  inlines = [NamingInline,]
  actions = [merge_people, merge_people_by_family_name]

class PublicationTypeAdmin(OrderedModelAdmin):
  list_display = ('title', 'description', 'public', 'bibtex_type')

class RoleTypeAdmin(OrderedModelAdmin):
  list_display = ('name', 'public', 'bibtex_field')

admin.site.register(Publication, PublicationAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(PublicationType, PublicationTypeAdmin)
admin.site.register(RoleType, RoleTypeAdmin)
