
# abbreviations used in BibTex
import collections
from django.http import HttpResponse

BIBTEX_MONTHS = {
  1: 'Jan',
  2: 'Feb',
  3: 'Mar',
  4: 'Apr',
  5: 'May',
  6: 'Jun',
  7: 'Jul',
  8: 'Aug',
  9: 'Sep',
  10: 'Oct',
  11: 'Nov',
  12: 'Dec'
}

BIBTEX_MAPPING = {
  "article" : {"authors" : "author", "title" : "title", "year" : "year", "within" : "journal", "volume" : "volume", "number" : "number", "pages" : "pages",
               "month" : "month", "note" : "note", "url" : "url", "abstract" : "abstract"
  },
  "book" : {"authors" : "author", "title" : "title", "year" : "year", "publisher" : "publisher",
            "volume" : "volume",  "month" : "month", "note" : "note", "url" : "url", "abstract" : "abstract"
  },
  "booklet" : {"authors" : "author", "title" : "title", "year" : "year", "address" : "address", "publisher" : "howpublished",
               "month" : "month", "note" : "note", "url" : "url"
  },
  "conference" : {"authors" : "author", "title" : "title", "year" : "year", "within" : "booktitle", "address" : "address", "publisher" : "publisher",
       "month" : "month", "note" : "note", "url" : "url", "pages" : "pages", "abstract" : "abstract"
  },
  "inbook" : {"authors" : "author", "title" : "title", "year" : "year", "pages" : "pages", "publisher" : "publisher",
             "volume" : "volume",  "month" : "month", "note" : "note", "url" : "url", "abstract" : "abstract"
  },
  "incollection" : {"authors" : "author", "title" : "title", "year" : "year", "within" : "booktitle", "publisher" : "publisher",
                    "month" : "month", "note" : "note", "url" : "url", "pages" : "pages", "abstract" : "abstract"
  },
  "inproceedings" : {"authors" : "author", "title" : "title", "year" : "year", "within" : "booktitle", "publisher" : "publisher",
                     "month" : "month", "note" : "note", "url" : "url", "pages" : "pages", "abstract" : "abstract"
  },
  "manual" : {"authors" : "author", "title" : "title", "year" : "year", "publisher" : "organization",
             "month" : "month", "note" : "note", "url" : "url"
  },
  "mastersthesis" : {"authors" : "author", "title" : "title", "year" : "year", "publisher" : "school",
                    "month" : "month", "note" : "note", "url" : "url", "abstract" : "abstract"
  },
  "misc" :{"authors" : "author", "title" : "title", "year" : "year", "publisher" : "howpublished",
           "month" : "month", "note" : "note", "url" : "url"
  },
  "phdthesis" : {"authors" : "author", "title" : "title", "year" : "year", "publisher" : "school",
                 "month" : "month", "note" : "note", "url" : "url", "abstract" : "abstract"
  },
  "proceedings" :{"authors" : "editor", "title" : "title", "year" : "year", "publisher" : "publisher",
                  "month" : "month", "note" : "note", "url" : "url"
  },
  "techreport" : {"authors" : "author", "title" : "title", "year" : "year", "publisher" : "institution",
                  "month" : "month", "note" : "note", "url" : "url", "abstract" : "abstract", "number" : "number"
  },
  "unpublished" : {"authors" : "author", "title" : "title", "year" : "year",
       "month" : "month", "note" : "note", "url" : "url"
  }
}


from publications_bibtex.parser import BibTeXParser, BibTeXProcessor, BibTeXFormatter

class BibTeXImporter:

  def __init__(self):
    self._type_mapping = {
      "article": 'paper',
      "inproceedings": 'paper',
      "book": 'book',
      "inbook": 'paper',
      "incollection": 'book',
      "proceedings": 'other',
      "manual": 'other',
      "phdthesis": 'book',
      "masterthesis": 'book',
      "techreport": 'unpublished',
      "booklet": 'other',
      "unpublished": 'unpublished',
      "misc": 'other'
    }

  def get_format_identifier(self):
    return "bibtex"

  def get_format_name(self):
    return "BibTeX"

  def import_from_string(self, data, publication_callback, error_callback):

    parser = BibTeXParser()
    entries = parser.parse(data)
    if not entries:
      for error in parser.getErrors():
        error_callback("%s (line: %d, column %d)" % (error["message"], error["line"], error["column"]))
      return

    processor = BibTeXProcessor()
    for entry in entries:
      processed_entry = processor.process(entry)
      if not processed_entry:
        for error in processor.getErrors():
          error_callback("%s (line: %d, column %d)" % (error["message"], error["line"], error["column"]))
        continue

      publication = {}
      for key, value in processed_entry.items():
        reverse = [k for k, v in BIBTEX_MAPPING[processed_entry["type"]].iteritems() if v == key]
        if reverse:
          publication[reverse[0]] = value



      month = BIBTEX_MONTHS.get(entry.get('month', '').lower(), None)
      if month:
        publication['month'] = month

      publication["type"] = self._type_mapping.get(entry["type"], "other")
      publication["groups"] = processed_entry.get("groups", "")
      publication["tags"] = processed_entry.get("keywords", "").split(",")
      if publication.has_key("authors"):
        publication["authors"] = publication["authors"].split(" and ")
      publication["metadata"] = {"bibtex.type" : entry["type"], "import.bibtexkey": entry["key"]}
      publication_callback(publication)


class BibTeXExporter:

  def __init__(self):
    pass

  def get_format_identifier(self):
    return "bibtex"

  def get_format_name(self):
    return "BibTeX"

  def _bibtex_key_base(self, publication):
    first_author = publication.first_author()
    if first_author:
      author_identifier = first_author.identifier()
    else:
      author_identifier = "UNCREDITED"
    return author_identifier + str(publication.year)


  def export_to_string(self, publications):

    from publications.models import Metadata
    bibtex_keys = set()

    if not isinstance(publications, collections.Iterable):
      publications = [publications]

    formatter = BibTeXFormatter()
    output = []

    for publication in publications:

      entry = publication.to_dictionary()
      if entry.has_key("authors"):
        entry["authors"] = " and ".join(entry["authors"])

      if entry.has_key("month"):
        entry["month"] = BIBTEX_MONTHS.get(entry["month"], None)

      bibentry = {}

      if entry["metadata"].has_key("bibtex.type"):
        if BIBTEX_MAPPING.has_key(entry["metadata"]["bibtex.type"]):
          bibentry["type"] = entry["metadata"]["bibtex.type"]
        else:
          bibentry["type"] = "misc"
      else:
        bibentry["type"] = "misc"

      for key, value in entry.items():
        bibkey = BIBTEX_MAPPING[bibentry["type"]].get(key, None)
        if bibkey:
          bibentry[bibkey] = value


      key_base = self._bibtex_key_base(publication)

      char = ord('a')
      bibtex_key = key_base + chr(char)
      while bibtex_key in bibtex_keys:
        char += 1
        bibtex_key = key_base + chr(char)

      bibtex_keys.add(bibtex_key)
      bibentry["key"] = bibtex_key
      output.append(formatter.format(bibentry))

    return "\n".join(output)


  def export_to_response(self, publications):
    response = HttpResponse(self.export_to_string(publications), content_type='application/x-bibtex')
    if not isinstance(publications, collections.Iterable):
      response["Content-Disposition"] = "filename=%s.bib" % (self._bibtex_key_base(publications))
    return response
