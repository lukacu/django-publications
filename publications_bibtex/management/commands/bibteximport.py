# -*- Mode: python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

from django.core.management.base import BaseCommand, CommandError
from publications.models import Import
from publications_bibtex import BibTeXImporter

class Command(BaseCommand):
  args = '<bib_file>'
  help = 'Imports BibTeX entries from a file'

  def handle(self, *args, **options):
    if len(args) < 1:
      raise CommandError("No file given")

    f = open(args[0], 'r')
    content = f.read()
    f.close()

    importer = BibTeXImporter()
    publications = list()
    errors = list()

    importer.import_from_string(content, lambda x : publications.append(x), lambda x : errors.append(x))

    if len(errors) > 0:
      for error in errors:
        print error
      raise CommandError("Import errors")

    print "Adding %d entries to import queue" % len(publications)

    for publication in publications:
      i = Import(title = publication["title"], data = publication, source = "bibtex")
      i.save()


