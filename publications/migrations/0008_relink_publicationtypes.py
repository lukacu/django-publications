# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

#[
#    {"model": "publications.publicationtype","pk": 0, "fields": { "identifier" : "techreport", "order": 9, "title": "Tech report", "description": "A report published by a school or other institution, usually numbered within a series.", "bibtex_type": "techreport", "public": 1 } },
#    {"model": "publications.publicationtype","pk": 1, "fields": { "identifier" : "booklet", "order": 10, "title": "Booklet", "description": "A work that is printed and bound, but without a named publisher or sponsoring institution.", "bibtex_type": "booklet", "public": 1 } },
#    {"model": "publications.publicationtype","pk": 2, "fields": { "identifier" : "unpublished", "order": 11, "title": "Unpublished", "description": "A document having an author and title, but not formally published.", "bibtex_type": "unpublished", "public": 1 } },
#    {"model": "publications.publicationtype","pk": 3, "fields": { "identifier" : "misc", "order": 12, "title": "Misc", "description": "When nothing else fits.", "bibtex_type": "misc", "public": 1 } },
#    {"model": "publications.publicationtype","pk": 4, "fields": { "identifier" : "masterthesis", "order": 8, "title": "Master thesis", "description": "A Masters thesis.", "bibtex_type": "mastersthesis", "public": 1 } },
#    {"model": "publications.publicationtype","pk": 5, "fields": { "identifier" : "article", "order": 0, "title": "Article", "description": "An article from a journal or magazine", "bibtex_type": "article", "public": 1 } },
#    {"model": "publications.publicationtype","pk": 6, "fields": { "identifier" : "phdthesis", "order": 7, "title": "PhD Thesis", "description": "A Ph.D. Thesis", "bibtex_type": "phdthesis", "public": 1 } },
#    {"model": "publications.publicationtype","pk": 7, "fields": { "identifier" : "inproceedings", "order": 1, "title": "In proceedings", "description": "An article in a conference proceedings.", "bibtex_type": "inproceedings", "public": 1 } },
#    {"model": "publications.publicationtype","pk": 8, "fields": { "identifier" : "incollection", "order": 4, "title": "In collection", "description": "A part of a book having its own title.", "bibtex_type": "incollection", "public": 1 } },
#    {"model": "publications.publicationtype","pk": 9, "fields": { "identifier" : "manual", "order": 6, "title": "Manual", "description": "Technical documentation", "bibtex_type": "manual", "public": 1 } },
#    {"model": "publications.publicationtype","pk": 10, "fields": { "identifier" : "proceedings", "order": 5, "title": "Proceedings", "description": " The proceedings of a conference.", "bibtex_type": "proceedings", "public": 1 } },
#    {"model": "publications.publicationtype","pk": 11, "fields": { "identifier" : "book", "order": 2, "title": "Book", "description": "A book with an explicit publisher", "bibtex_type": "book", "public": 1 } },
#    {"model": "publications.publicationtype","pk": 12, "fields": { "identifier" : "inbook", "order": 3, "title": "In book", "description": "A part of a book, which may be a chapter (or section or whatever) and/or a range of pages.", "bibtex_type": "inbook", "public": 1 } }
#]

# paper
# book
# other
# unpublished


order = [9, 10, 11, 12, 8, 0, 7, 1, 4, 6, 5, 2, 3]

mapping = [
  0,
  0,
  1,
  0,
  1,
  2,
  2,
  1,
  1,
  3,
  2,
  3,
  2
]

type_identifiers = ["paper", "book", "other", "unpublished"]

bibtex_mapping = [
  "article",
  "inproceedings",
  "book",
  "inbook",
  "incollection",
  "proceedings",
  "manual",
  "phdthesis",
  "masterthesis",
  "techreport",
  "booklet",
  "unpublished",
  "misc"
]

class Migration(DataMigration):

    def forwards(self, orm):

      for publication in orm.Publication.objects.all():
        t = int(publication.type)
        if t < 0 or t > len(order)-1:
          t = 12
        else:
          t = order[t]

        bibtype = orm.Metadata(publication=publication, key="bibtex.type", value=bibtex_mapping[t])
        bibtype.save()

        publication.type = type_identifiers[mapping[t]]
        publication.save()

    def backwards(self, orm):
      raise RuntimeError("Cannot reverse this migration.")


    models = {
        'publications.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'publications.import': {
            'Meta': {'ordering': "['date_added']", 'object_name': 'Import'},
            'data': ('django.db.models.fields.TextField', [], {}),
            'date_added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'publications.metadata': {
            'Meta': {'unique_together': "(('publication', 'key'),)", 'object_name': 'Metadata'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'publication': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['publications.Publication']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'publications.person': {
            'Meta': {'ordering': "['family_name', 'primary_name']", 'object_name': 'Person'},
            'family_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['publications.Group']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'primary_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'publications.publication': {
          'Meta': {'ordering': "['-year', '-month', '-id']", 'object_name': 'Publication'},
          'abstract': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
          'code': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
          'date_added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
          'date_modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
          'doi': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
          'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
          'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['publications.Group']", 'symmetrical': 'False'}),
          'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
          'keywords': ('tagging.fields.TagField', [], {'default': "''"}),
          'month': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
          'note': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
          'number': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
          'pages': ('publications.fields.PagesField', [], {'max_length': '32', 'blank': 'True'}),
          'people': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['publications.Person']", 'through': "orm['publications.Role']", 'symmetrical': 'False'}),
          'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
          'publisher': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
          'title': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
          'type': ('django.db.models.fields.CharField', [], {'max_length': '16', 'blank': 'False', 'null' : "False"}),
          'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
          'volume': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
          'within': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
          'year': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '4'})
        },
        'publications.role': {
            'Meta': {'object_name': 'Role'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['publications.Person']"}),
            'publication': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['publications.Publication']"})
        }
    }

    complete_apps = ['publications']
