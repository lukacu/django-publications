# -*- Mode: python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-
__license__ = 'MIT License <http://www.opensource.org/licenses/mit-license.php>'
__author__ = 'Lucas Theis <lucas@theis.io>'
__docformat__ = 'epytext'

from django.contrib import admin
import publications.models
from publications.orderedmodel import OrderedModelAdmin
from publications.models import Publication, Group, Role, Person, PersonNaming, PublicationType, RoleType, Metadata

def merge_people_by_family_name(modeladmin, request, queryset):
  groups = publications.models.group_people_by_family_name(list(queryset))
  for fn, group in groups.items():
    publications.models.merge_people(group)

def merge_people(modeladmin, request, queryset):
    publications.models.merge_people(list(queryset))

class MetadataInline(admin.TabularInline):
    model = Metadata

class RoleInline(admin.TabularInline):
    model = Role

class NamingInline(admin.TabularInline):
    model = PersonNaming

class PublicationAdmin(admin.ModelAdmin):
	list_display = ('type', 'first_author', 'title', 'year', 'journal_or_book_title')
	list_display_links = ('title',)
	change_list_template = 'admin/publications/change_list.html'
	search_fields = ('title', 'journal', 'authors', 'keywords', 'year')
	fieldsets = (
		("Basic information", {'fields': 
			('type', 'title', 'abstract', 'note')}),
		("Publishing information", {'fields': 
			('year', 'month', 'journal', 'book_title', 'publisher', 'volume', 'number', 'pages')}),
		("Resources", {'fields': 
			('url', 'code', 'file', 'doi')}),
		("Categoritzation", {'fields': 
			('keywords', 'public', 'groups')}),
	)
	inlines = [RoleInline, MetadataInline]


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
