__license__ = 'MIT License <http://www.opensource.org/licenses/mit-license.php>'
__author__ = 'Luka Cehovin <luka.cehovin@gmail.com>'
__docformat__ = 'epytext'

__publication_types_mapping = {}
__publication_types = []

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
    if not i:
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

register_publication_type("paper", "Paper", "An article in a journal or magazine, paper in conference proceedings, part of a book")
register_publication_type("book", "Book", "A book with an explicit publisher, booklet, or a thesis")
register_publication_type("other", "Other", "Any other published content")
register_publication_type("unpublished", "Unpublished", "A document having an author and title, but not formally published, technical report")

