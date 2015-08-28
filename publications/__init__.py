__license__ = 'MIT License <http://www.opensource.org/licenses/mit-license.php>'
__author__ = 'Luka Cehovin <luka.cehovin@gmail.com>'
__docformat__ = 'epytext'

from django.conf import settings

__publication_importers = {}
__publication_exporters = {}

def get_publications_exporter(identifier):
  return __publication_exporters.get(identifier, None)

def get_publications_importer(identifier):
  return __publication_importers.get(identifier, None)

def list_export_formats():
  return [{"identifier" : v.get_format_identifier(), "name" : v.get_format_name()} for v in __publication_exporters.itervalues()]

def list_import_formats():
  return [{"identifier" : v.get_format_identifier(), "name" : v.get_format_name()} for v in __publication_importers.itervalues()]

def __on_init():
  global __publication_exporters, __publication_importers
  __publication_importers = {}
  __publication_exporters = {}
  importers = getattr(settings, 'PUBLICATIONS_IMPORTERS', None)
  if importers and type(importers) == tuple or type(importers) == list:
    for importerClass in importers:
      (module, sep, importerClass) = importerClass.rpartition(".")
      module = __import__(module, fromlist=[importerClass])
      importer = getattr(module, importerClass)()
      __publication_importers[importer.get_format_identifier()] = importer

  exporters = getattr(settings, 'PUBLICATIONS_EXPORTERS', None)
  if exporters and type(exporters) == tuple or type(exporters) == list:
    for exporterClass in exporters:
      (moduleName, sep, exporterClass) = exporterClass.rpartition(".")
      module = __import__(moduleName, fromlist=[exporterClass])
      exporter = getattr(module, exporterClass)()
      __publication_exporters[exporter.get_format_identifier()] = exporter

__on_init()
