# -*- Mode: python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

from django.core.management.base import BaseCommand, CommandError
from publications.models import *
from string import split, join
from publications.models import Import, Publication, PublicationImportException, PublicationUpdateException, PeopleMergeException
from django.conf import settings

def interactive_choose(message, choices):
  print message
  i = 0
  for choice in choices:
    i = i + 1
    print "(%d) %s" % (i, choice)
  i = i + 1
  print "(%d) <none>" % i

  while True:
    c = int(input("Select option: "))
    if c > 0 and c <= len(choices):
      return c-1
    if c == len(choices) + 1:
      return -1


class Command(BaseCommand):
  args = '[ guided_import | automatic_import | flush ]'
  help = 'Manage import queue'

  def handle(self, *args, **options):
    if len(args) < 1:
      raise CommandError("No command given")

    if args[0] == "flush":
      Import.objects.all().delete()

    elif args[0] == "guided_import" or args[0] == "automatic_import":
      queue = Import.objects.all()
      for entry in queue:
        print "Importing '%s'" % entry
        if args[0] == "guided_import":
          publication_update = None
          people_merge = None
        else:
          publication_update = -1
          people_merge = {}
        while True:
          try:
            publication = entry.construct_publication_object(publication_update, people_merge)
            publication.save()
            entry.delete()
            break
          except PeopleMergeException, e:
            people_merge = {}
            for candidate, options in e.candidates.items():
              choice = interactive_choose("Merge '%s' with one of the existing people entries?" % candidate, options)
              if choice > -1:
                people_merge[candidate] = options[choice]
          except PublicationUpdateException, e:
            choice = interactive_choose("Update one of similar entries?", ["%s (%d)" % (c, c.year) for c in e.candidates])
            if choice > -1:
              publication_update = e.candidates[choice].pk
          except PublicationImportException, e:
            print "Import error for '%s': %s" % (queue.title, e.message)
            break
    else:
      raise CommandError("Invalid command")

