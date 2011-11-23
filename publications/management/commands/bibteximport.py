# -*- Mode: python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

from django.core.management.base import BaseCommand, CommandError
from publications.models import *
from string import split, join
from publications.bibtex import BibTeXParser, BibTeXProcessor
from publications.admin_views.import_bibtex import generate_objects
from django.conf import settings

class Command(BaseCommand):
  args = '<bib_file>'
  help = 'Imports BibTeX entries from a file'

  def handle(self, *args, **options):
    if len(args) < 1:
      raise CommandError("No file given")

    f = open(args[0], 'r')
    content = f.read()
    f.close()

    parser = BibTeXParser()

    entries = parser.parse(content)

    errors = parser.getErrors()
    if len(errors) > 0:
      for error in errors:
        print error
      raise CommandError("Parse errors")

    processor = BibTeXProcessor(strict=False)

    bibliography = list()
    publications = list()

    for entry in entries:
      entry = processor.process(entry)
      if entry == None:
        for error in processor.getErrors():
          print error
        raise CommandError("Validation errors")
      bibliography.append(entry)

    print "Found %d entries" % len(bibliography)

    if getattr(settings, 'PUBLICATIONS_IMPORT_HANDLER', None):
      (module, sep, method) = settings.PUBLICATIONS_IMPORT_HANDLER.rpartition(".")
      handlermodule = __import__(module)
      if hasattr(handlermodule, method):
        handler = getattr(handlermodule, method)
        bibliography = [ handler(b) for b in bibliography ]

#    for publication in generate_objects(bibliography):
#      print "Saving %s" % publication.title
#      publication.save()


