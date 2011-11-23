__license__ = 'MIT License <http://www.opensource.org/licenses/mit-license.php>'
__author__ = 'Lucas Theis <lucas@theis.io>'
__docformat__ = 'epytext'

from django.contrib import admin
from publications.models import Publication, Group, Role, Person

class RoleInline(admin.StackedInline):
    model = Role


class PublicationAdmin(admin.ModelAdmin):
	list_display = ('type', 'first_author', 'title', 'type', 'year', 'journal_or_book_title')
	list_display_links = ('title',)
	change_list_template = 'admin/publications/change_list.html'
	search_fields = ('title', 'journal', 'authors', 'keywords', 'year')
	fieldsets = (
		("Basic information", {'fields': 
			('type', 'title', 'abstract', 'note')}),
		("Publishing information", {'fields': 
			('year', 'month', 'journal', 'book_title', 'publisher', 'volume', 'number', 'pages')}),
		("Resources", {'fields': 
			('url', 'code', 'pdf', 'doi')}),
		("Categoritzation", {'fields': 
			('keywords', 'public', 'groups')}),
	)
	inlines = [RoleInline,]


class GroupAdmin(admin.ModelAdmin):
	list_display = ('name', 'text')

class PersonAdmin(admin.ModelAdmin):
	list_display = ('display', 'name', 'surname')


admin.site.register(Publication, PublicationAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Person, PersonAdmin)
