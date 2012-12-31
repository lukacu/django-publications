__license__ = 'MIT License <http://www.opensource.org/licenses/mit-license.php>'
__author__ = 'Luka Cehovin <luka.cehovin@gmail.com>'
__docformat__ = 'epytext'

from django.conf import settings

__publication_types_mapping = {}
__publication_types = []

__publication_importers = {}
__publication_exporters = {}

def register_publication_type(identifier, title, description):
  id = len(__publication_types)
  __publication_types.append({ "identifier" : identifier, "title" : title, "description" : description, "id" : id})
  __publication_types_mapping[identifier] = id

def resolve_publication_type(identifier):
  if type(identifier) == int:
    if identifier < 0 or identifier >= len(__publication_types):
      return None
    return __publication_types[identifier]
  else:
    i = __publication_types_mapping.get(identifier, None)
    if i is None:
      return None
    return __publication_types[i]

def resolve_publication_type_identifier(id):
  type = resolve_publication_type(id)
  if type:
    return type["identifier"]
  else:
    return "other"

def get_publication_type_choices():
  return [(t["identifier"], t["title"]) for t in __publication_types]

register_publication_type("paper", "Paper", "A paper in conference proceedings")
register_publication_type("article", "Journal article", "An article in a journal or magazine, part of a book")
register_publication_type("book", "Book", "A book with an explicit publisher, booklet, or a thesis")
register_publication_type("other", "Other", "Any other published content")
register_publication_type("unpublished", "Unpublished", "A document having an author and title, but not formally published, technical report")

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
