# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'RoleType'
        db.delete_table('publications_roletype')

        # Deleting field 'Role.role'
        db.delete_column('publications_role', 'role_id')


    def backwards(self, orm):
        
        # Adding model 'RoleType'
        db.create_table('publications_roletype', (
            ('public', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('identifier', self.gf('django.db.models.fields.CharField')(max_length=64, unique=True)),
            ('authorship', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('bibtex_field', self.gf('django.db.models.fields.CharField')(max_length=64, unique=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('publications', ['RoleType'])

        # User chose to not deal with backwards NULL issues for 'Role.role'
        raise RuntimeError("Cannot reverse this migration. 'Role.role' and its values cannot be restored.")


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
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['publications.PublicationType']"}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'volume': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'within': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'year': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '4'})
        },
        'publications.publicationtype': {
            'Meta': {'ordering': "('order',)", 'object_name': 'PublicationType'},
            'bibtex_type': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
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
