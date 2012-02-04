# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'RoleType'
        db.create_table('publications_roletype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('identifier', self.gf('django.db.models.fields.CharField')(unique=True, max_length=64)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('public', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('authorship', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('bibtex_field', self.gf('django.db.models.fields.CharField')(unique=True, max_length=64, blank=True)),
        ))
        db.send_create_signal('publications', ['RoleType'])

        # Adding model 'PublicationType'
        db.create_table('publications_publicationtype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('identifier', self.gf('django.db.models.fields.CharField')(unique=True, max_length=64)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('public', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('bibtex_type', self.gf('django.db.models.fields.CharField')(unique=True, max_length=64, blank=True)),
        ))
        db.send_create_signal('publications', ['PublicationType'])

        # Adding model 'Group'
        db.create_table('publications_group', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('identifier', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('public', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('publications', ['Group'])

        # Adding model 'Person'
        db.create_table('publications_person', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('primary_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('middle_name', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('family_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            ('public', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['publications.Group'], null=True, blank=True)),
        ))
        db.send_create_signal('publications', ['Person'])

        # Adding model 'Role'
        db.create_table('publications_role', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('person', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['publications.Person'])),
            ('publication', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['publications.Publication'])),
            ('role', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['publications.RoleType'])),
        ))
        db.send_create_signal('publications', ['Role'])

        # Adding model 'Metadata'
        db.create_table('publications_metadata', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('publication', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['publications.Publication'])),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal('publications', ['Metadata'])

        # Adding unique constraint on 'Metadata', fields ['publication', 'key']
        db.create_unique('publications_metadata', ['publication_id', 'key'])

        # Adding model 'Publication'
        db.create_table('publications_publication', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['publications.PublicationType'])),
            ('date_added', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, auto_now_add=True, blank=True)),
            ('date_modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, auto_now=True, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('year', self.gf('django.db.models.fields.PositiveIntegerField')(max_length=4)),
            ('month', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('journal', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('book_title', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('publisher', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('volume', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True)),
            ('number', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True)),
            ('pages', self.gf('publications.fields.PagesField')(max_length=32, blank=True)),
            ('note', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('keywords', self.gf('tagging.fields.TagField')(default='')),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            ('code', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            ('file', self.gf('django.db.models.fields.files.FileField')(max_length=100, null=True, blank=True)),
            ('doi', self.gf('django.db.models.fields.CharField')(max_length=128, blank=True)),
            ('abstract', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('public', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('publications', ['Publication'])

        # Adding M2M table for field groups on 'Publication'
        db.create_table('publications_publication_groups', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('publication', models.ForeignKey(orm['publications.publication'], null=False)),
            ('group', models.ForeignKey(orm['publications.group'], null=False))
        ))
        db.create_unique('publications_publication_groups', ['publication_id', 'group_id'])

        # Adding model 'Import'
        db.create_table('publications_import', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('source', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('data', self.gf('django.db.models.fields.TextField')()),
            ('date_added', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('publications', ['Import'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'Metadata', fields ['publication', 'key']
        db.delete_unique('publications_metadata', ['publication_id', 'key'])

        # Deleting model 'RoleType'
        db.delete_table('publications_roletype')

        # Deleting model 'PublicationType'
        db.delete_table('publications_publicationtype')

        # Deleting model 'Group'
        db.delete_table('publications_group')

        # Deleting model 'Person'
        db.delete_table('publications_person')

        # Deleting model 'Role'
        db.delete_table('publications_role')

        # Deleting model 'Metadata'
        db.delete_table('publications_metadata')

        # Deleting model 'Publication'
        db.delete_table('publications_publication')

        # Removing M2M table for field groups on 'Publication'
        db.delete_table('publications_publication_groups')

        # Deleting model 'Import'
        db.delete_table('publications_import')


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
            'Meta': {'object_name': 'Person'},
            'family_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['publications.Group']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'middle_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'primary_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'publications.publication': {
            'Meta': {'ordering': "['-year', '-month', '-id']", 'object_name': 'Publication'},
            'abstract': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'book_title': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'code': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'date_added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now': 'True', 'blank': 'True'}),
            'doi': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['publications.Group']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'journal': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
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
            'publication': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['publications.Publication']"}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['publications.RoleType']"})
        },
        'publications.roletype': {
            'Meta': {'ordering': "('order',)", 'object_name': 'RoleType'},
            'authorship': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'bibtex_field': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        }
    }

    complete_apps = ['publications']
