# -*- Mode: python; indent-tabs-mode: nil; c-basic-offset: 2; tab-width: 2 -*-

import re
import sys
import urllib
import StringIO, codecs
import re, os, os.path

## {{{ http://code.activestate.com/recipes/81611/ (r2)
def int_to_roman(input):
   """
   Convert an integer to Roman numerals.

   Examples:
   >>> int_to_roman(0)
   Traceback (most recent call last):
   ValueError: Argument must be between 1 and 3999

   >>> int_to_roman(-1)
   Traceback (most recent call last):
   ValueError: Argument must be between 1 and 3999

   >>> int_to_roman(1.5)
   Traceback (most recent call last):
   TypeError: expected integer, got <type 'float'>

   >>> for i in range(1, 21): print int_to_roman(i)
   ...
   I
   II
   III
   IV
   V
   VI
   VII
   VIII
   IX
   X
   XI
   XII
   XIII
   XIV
   XV
   XVI
   XVII
   XVIII
   XIX
   XX
   >>> print int_to_roman(2000)
   MM
   >>> print int_to_roman(1999)
   MCMXCIX
   """
   if type(input) != type(1):
      raise TypeError, "expected integer, got %s" % type(input)
   if not 0 < input < 4000:
      raise ValueError, "Argument must be between 1 and 3999"   
   ints = (1000, 900,  500, 400, 100,  90, 50,  40, 10,  9,   5,  4,   1)
   nums = ('M',  'CM', 'D', 'CD','C', 'XC','L','XL','X','IX','V','IV','I')
   result = ""
   for i in range(len(ints)):
      count = int(input / ints[i])
      result += nums[i] * count
      input -= ints[i] * count
   return result

def roman_to_int(input):
   """
   Convert a roman numeral to an integer.
   
   >>> r = range(1, 4000)
   >>> nums = [int_to_roman(i) for i in r]
   >>> ints = [roman_to_int(n) for n in nums]
   >>> print r == ints
   1

   >>> roman_to_int('VVVIV')
   Traceback (most recent call last):
    ...
   ValueError: input is not a valid roman numeral: VVVIV
   >>> roman_to_int(1)
   Traceback (most recent call last):
    ...
   TypeError: expected string, got <type 'int'>
   >>> roman_to_int('a')
   Traceback (most recent call last):
    ...
   ValueError: input is not a valid roman numeral: A
   >>> roman_to_int('IL')
   Traceback (most recent call last):
    ...
   ValueError: input is not a valid roman numeral: IL
   """
   if type(input) != type(""):
      raise TypeError, "expected string, got %s" % type(input)
   input = input.upper()
   nums = ['M', 'D', 'C', 'L', 'X', 'V', 'I']
   ints = [1000, 500, 100, 50,  10,  5,   1]
   places = []
   for c in input:
      if not c in nums:
         raise ValueError, "input is not a valid roman numeral: %s" % input
   for i in range(len(input)):
      c = input[i]
      value = ints[nums.index(c)]
      # If the next place holds a larger number, this value is negative.
      try:
         nextvalue = ints[nums.index(input[i +1])]
         if nextvalue > value:
            value *= -1
      except IndexError:
         # there is no next place.
         pass
      places.append(value)
   sum = 0
   for n in places: sum += n
   # Easiest test for validity...
   if int_to_roman(sum) == input:
      return sum
   else:
      raise ValueError, 'input is not a valid roman numeral: %s' % input
## end of http://code.activestate.com/recipes/81611/ }}}


class BibTeXParser:

  def parse(self, raw):

    self.raw = raw
    self.position = 0
    self.state = 0
    self.line = 1
    self.column = 1
    self.errors = list()

    result = list()

    exit = False

    while True:
      # waiting for new segment
      if self.state == 0:
        first = True
        entry = {"type" : None, "fields" : {} }
        expect = [" ", "\t", "\n", "\r"]
        if len(result) > 0:
          expect.append(",")

        if not self._advance(expect):
          break

        if not self._requireNext(["@", "%"]):
          self._error("Expected '@' or '%'")
          return None

        c = self._peek(-1)

        if c == "%":
          pre_comment = 0
          self.state = 11
          continue

        entry["line"] = self.line
        entry["column"] = self.column
        self.state = 1

        continue
      # figuring out what kind of segment it is
      elif self.state == 1:
        start = self.position

        if not self._advanceTo([" ", "\t", "\n", "\r", "{"]):
          self._error("Expected '{'")
          return None

        entry_type = self.raw[start : self.position]

        if (entry_type == ""):
          self._error("Expected segment type")
          return None

        entry['type'] = entry_type

        self.state = 2

        continue
      # moving to start of segment
      elif self.state == 2:
        if not self._advance() or not self._validateNext("{"):
          self._error("Expected '{'")
          return None

        self.state = 3

        continue
      # moving to field key
      elif self.state == 3:
        if not self._advance():
          self._error("Expected '}'")
          return None

        c = self._peek()

        if c == None:
          self._error("Expected '}'")
          return None

        if (c == "}"):
          self._pop()
          self.state = 0
          result.append(entry)
          continue

        self.state = 4
        continue

      # parsing field key
      elif self.state == 4:
        start = self.position
        expect = [" ", "\t", "\n", "\r", "="]
        if first: 
          expect.append(",") # in case this can also be the key

        if not self._advanceTo(expect): 
          if first:
            self._error("Expected '=' or ','")
          else:
            self._error("Expected '='")
          return None;
        key = self.raw[start : self.position]

        if entry_type == "": 
          self._error("Expected field key")
          return None

        if not self._advance(): 
          if first:
            self._error("Expected '=' or ','")
          else:
            self._error("Expected '='")
          return None

        c = self._peek()

        if c == ",": 
          if not first:
            self._error("Entry key not expected here")
            return None
          first = False
          self._pop()
          entry['key'] = key
          self.state = 3
          continue

        self.state = 5

        continue
      # move to field value
      elif self.state == 5:
        if not self._advance():
          self._error("Expected '='")
          return None

        if not self._validateNext("="): 
          self._error("Expected '='")
          return None
        
        if not self._advance():
          self._error("Expected field value")
          return None
        
        self.state = 6;
        continue
      # start processing field value
      elif self.state == 6:
        c = self._peek()
        if (c == "{"):
          brackets = 1
          self.state = 7
          self._pop()
          start = self.position
          continue
        elif (c == "\""):
          self.state = 8;
          self._pop();
          start = self.position;
          continue

        self.state = 9;
        start = self.position;
        continue
      # find matching }
      elif self.state == 7:
        if not self._advanceTo(["{", "}"]):
          self._error("Expected '}'")
          return None
        

        c = self._peek(-1);

        if c == "\\":
          continue

        c = self._pop()

        if c == "{":
          brackets = brackets + 1
          continue

        if c == "}": 
          brackets = brackets - 1;
          if brackets == 0:
            value = self.raw[start : self.position - 1];
            entry["fields"][key] = self._cleanValue(value)
            self.state = 10
          continue

        continue
      # find matching "
      elif self.state == 8:
        if not self._advanceTo(["\""]): 
          self._error("Expected '\"'")
          return None

        c = self._peek(-1);

        if c == "\\":
          continue
        else:
          value = self.raw[start : self.position];
          entry[key] = self._cleanValue(value)
          self._pop()
          self.state = 10
        continue
      # find whole word
      elif self.state == 9:
        if not self._advanceTo([" ", "\t", "\n", "\r", ",", "}"]):
          self._error("Expected a closure")
          return None

        c = self._peek(-1)

        if c == "\\":
          continue
        else:
          value = self.raw[start : self.position];
          entry["fields"][key] = value;
          self.state = 10;

        continue
      # finish processing field
      elif self.state == 10:  
        if not self._advance():
          self._error("Expected '}' or ','")
          return None

        if not self._peekNext(["}", ","]):
          self._error("Expected '}' or ','")
          return None

        c = self._pop()
        if c == "}":
          self.state = 0
        else:
          self.state = 3

        if self.state == 0:
          result.append(entry)

        continue
      # comments
      elif self.state == 11:
        if (self._advanceTo(["\n", "\r"])):
          self._pop();
        self.state = pre_comment
        continue

    return result;


  def _pop(self):
    if self._eos():
      return None

    c = self.raw[self.position]
    self.position = self.position + 1;

    if c == "\n":
      self.line = self.line + 1;
      self.column = 1;
    else:
      self.column = self.column + 1;

    return c

  def _peek(self, offset = 0):
    if self._eos(offset):
      return None
    c = self.raw[self.position + offset]
    return c

  def _advance(self, allowed = [" ", "\t", "\n", "\r"]):
    if self._eos():
      return False

    while True:
      c = self._peek()
      if (c == None):
        return False
      if c in allowed: 
        self._pop()
        continue 
      return True

  def _advanceTo(self, allowed = [" ", "\t", "\n", "\r"]):
    if self._eos():
      return False

    while True:
      c = self._peek()
      if c == None:
        return False
      if c in allowed:
        return True
      self._pop()

  def _validateNext(self, allowed = " "):
    if self._eos(1):
      return False
    
    c = self._pop()
    if type(allowed) == list:
      for a in allowed: 
        if c == a:
          return True
    else:
      if c == allowed:
        return True
    return False

  def _requireNext(self, allowed = " "):

    if self._eos(1):
      if type(allowed) == list: 
        expected = "', '".join(allowed)
      else:
        expected = allowed
      self._error("Expected 'expected' but end of input found")
    
    c = self._pop()
    if type(allowed) == list:
      for a in allowed: 
        if (c == a):
          return True;
    else:
      if (c == allowed):
        return True;

    if type(allowed) == list: 
      expected = "', '".join(allowed)
    else:
      expected = allowed
      self._error("Expected 'expected' but 'c' found")

    return False


  def _peekNext(self, allowed = " "):
    if self._eos():
      return False
    c = self._peek()
    if type(allowed) == list:
      for a in allowed:
        if c == a:
          return True
    else:
      if (c == allowed):
       return True
    return False

  def _eos(self, advance = 0):
    return len(self.raw) <= self.position + advance;

  def _error(self, message, line = None, column = None):
    if (line == None):
      line = self.line
    if (column == None):
      column = self.column
    self.errors.append({"message" : message, "line" : line, "column" : column, "state" : self.state})

  def getErrors(self) :
    return self.errors

  def _cleanValue(self, value):
    value = re.sub( r'[\t\n\r]', " ", value).strip()
    return re.sub(r"/  +([^ ])/", " \\1", value)


  def parsePeople(self, raw):

    auth = explode(" and ", raw);
 
    result = list();  

    for value in auth: 
      r = parsePerson(trim(value));
      if empty(r):
        continue
      result.append(r)

    return result;

# Parses a single name. Tries to figure out what is name and what surname.
# Returns an array with two elements: surname and name.
def parsePerson(raw):

  matches = re.match("/^(?:([^ ,]+) *, *([^ ].*))$/", raw)
  if (matches != None):
    return (matches[1], matches[2])

  matches = re.match("/^(?:([^ ]+) *([^ ].*))$/", raw)
  if (matches != None):
    return (matches[2], matches[1])

  return None


BIBTEX_FIELDS = {
  "address" : {"description" : "Publisher's address (usually just the city, but can be the full address for lesser-known publishers)", "type" : "string"},
  "annote" : {"description" : "An annotation for annotated bibliography styles (not typical)", "type" : "string"},
  "author" : {"description" : "The name(s) of the author(s) (in the case of more than one author, separated by and)", "type" : "people"},
  "booktitle" : {"description" : "The title of the book, if only part of it is being cited", "type" : "string"},
  "chapter" : {"description" : "The chapter number", "type" : "string"},
  "crossref" : {"description" : "The key of the cross-referenced entry", "type" : "string"},
  "edition" : {"description" : "The edition of a book, long form (such as first or second)", "type" : "string"},
  "editor" : {"description" : "The name(s) of the editor(s)", "type" : "people"},
  "eprint" : {"description" : "A specification of an electronic publication, often a preprint or a technical report", "type" : "string"},
  "howpublished" : {"description" : "How it was published, if the publishing method is nonstandard", "type" : "string"},
  "institution" : {"description" : "The institution that was involved in the publishing, but not necessarily the publisher", "type" : "string"},
  "journal" : {"description" : "The journal or magazine the work was published in", "type" : "string"},
  "key" : {"description" : "A hidden field used for specifying or overriding the alphabetical order of entries (when the author and editor fields are missing). Note that this is very different from the key (mentioned just after this list) that is used to cite or cross-reference the entry.", "type" : "string"},
  "month" : {"description" : "The month of publication (or, if unpublished, the month of creation)", "type" : "string"},
  "note" : {"description" : "Miscellaneous extra information", "type" : "text"},
  "number" : {"description" : "The number of a journal, magazine, or tech-report, if applicable. (Most publications have a volume, but no number field.)", "type" : "number"},
  "organization" : {"description" : "The conference sponsor", "type" : "string"},
  "pages" : {"description" : "Page numbers, separated either by commas or double-hyphens", "type" : "range"},
  "publisher" : {"description" : "The publisher's name", "type" : "string"},
  "school" : {"description" : "The school where the thesis was written", "type" : "string"},
  "series" : {"description" : "The series of books the book was published in", "type" : "string"},
  "title" : {"description" : "The title of the work", "type" : "string"},
  "type" : {"description" : "The type of tech-report, for example, Research Note", "type" : "string"},
  "url" : {"description" : "The WWW address to the electronic version of document", "type" : "url"},
  "volume" : {"description" : "The volume of a journal or multi-volume book", "type" : "range"},
  "year" : {"description" : "The year of publication (or, if unpublished, the year of creation)", "type" : "number"},
# the fields that are not part of the original BibTeX standard
  "abstract" : {"description" : "An abstract of the work", "type" : "text"},
  "doi" : {"description" : "Digital Object Identifier", "type" : "string"},
  "isbn" : {"description" : "The International Standard Book Number", "type" : "string"},
  "issn" : {"description" : "The International Standard Serial Number. Used to identify a journal.", "type" : "string"},
  "keywords" : {"description" : "Keywords associated with this entry.", "type" : "string"},
  "owner" : {"description" : "Owner of the entry.", "type" : "string"},
  "timestamp" : {"description" : "Timestamp of the entry.", "type" : "date"},
  "groups" : {"description" : "Comma-separated list of groups that the entry belongs to.", "type" : "string"}
}

BIBTEX_TYPES = {
"article" : {"required" : {"author", "title", "journal", "year"},
    "optional" : {"volume", "number", "pages", "month", "note", "url", "abstract", "ISSN"},
    "description" : "An article from a journal or magazine", "name" : "Article"
    },
"book" : {"required" : {"author", "title", "publisher", "year"},
    "optional" : {"editor", "volume", "series", "address", "edition", "month", "note", "url", "abstract", "ISBN"},
    "description" : "A book with an explicit publisher", "name" : "Book"
    },
"booklet" : {"required" : {"title"},
    "optional" : {"author", "howpublished", "address", "month", "year", "note", "url"},
    "description" : "A work that is printed and bound, but without a named publisher or sponsoring institution.", 
    "name" : "Booklet"
    },
"conference" : {"required" : {"author", "title", "booktitle", "year"},
    "optional" : {"editor", "pages", "organization", "publisher", "address", "month", "note", "url"},
    "description" : "The same as inproceedings, included for Scribe (markup language) compatibility.", "name" : "Title"
    },
"inbook" : {"required" : {"author", "title", "chapter", "pages", "year"},
    "optional" : {"editor", "volume", "series", "address", "edition", "month", "note", "url", "abstract", "ISBN"},
    "description" : "A part of a book, which may be a chapter (or section or whatever) and/or a range of pages.",
    "name" : "In book"
    },
"incollection" : {"required" : {"author", "title", "booktitle", "year"},
    "optional" : {"editor", "pages", "organization", "address", "publisher", "month", "note", "url", "abstract"},
    "description" : "A part of a book having its own title.",
    "name" : "In collection"
    },
"inproceedings" : {"required" : {"author", "title", "booktitle", "year"},
    "optional" : {"editor", "pages", "organization", "address", "publisher", "month", "note", "url", "abstract"},
    "description" : "An article in a conference proceedings.",
    "name" : "In proceedings"
    },
"manual" : {"required" : {"title"},
    "optional" : {"author", "organization", "address", "edition", "month", "year", "note", "url"},
    "description" : "Technical documentation",
    "name" : "Manual"
    },
"mastersthesis" : {"required" : {"author", "title", "school", "year"},
    "optional" : {"address", "month", "note", "url", "abstract"},
    "description" : "A Masters thesis.",
    "name" : "Master thesis"
    },
"misc" : {"required" : {},
    "optional" : {"author", "title", "howpublished", "month", "year", "note", "url"},
    "description" : "For use when nothing else fits.",
    "name" : "Misc"
    },
"phdthesis" : {"required" : {"author", "title", "school", "year"},
    "optional" : {"address", "month", "note", "url", "abstract"},
    "description" : "A Ph.D. Thesis",
    "name" : "PhD Thesis"
    },
"proceedings" : {"required" : {"title", "year"},
    "optional" : {"editor", "publish", "organization", "address", "month", "note", "url"},
    "description" : " The proceedings of a conference.",
    "name" : "Proceedings"
    },
"techreport" : {"required" : {"author", "title", "institution", "year"},
    "optional" : {"type", "number", "address", "month", "note", "url", "abstract"},
    "description" : "A report published by a school or other institution, usually numbered within a series.",
    "name" : "Tech report"
    },
"unpublished" : {"required" : {"author", "title", "note"},
    "optional" : {"month", "year", "url"},
    "description" : "A document having an author and title, but not formally published.",
    "name" : "Unpublished"
    }
}

class BibTeXProcessor:

  def __init__(self, strict = True, require = []):

    self.errors = [];
    self._replace = {};
    self.required = require;
    self.strict = strict;

  def registerReplacement(key, value):
    self._replace[' ' + key + ' '] = ' ' + value + ' '

  def process(self, entry):
    self.errors = list()

    bibtex_type = entry["type"].lower()
    bibtex_key = entry["key"]
    self.line = entry["line"]
    self.column = entry["column"]

    if not BIBTEX_TYPES.has_key(bibtex_type):
      self._error("Unsupported entry type '%s'" % bibtex_type)
      return None

    fields = BIBTEX_TYPES[bibtex_type]

    required = fields['required'].copy()
    required.update(self.required)

    result = {}

    error = False

    for key, value in entry["fields"].items():
      new_key = key.lower()

      errormsg = self.validate(key, value)
      if errormsg != None : 
        self._error("Incorrect format for field '%s': %s" % (bibtex_type, errormsg))
        error = True
        continue

      result[new_key] = self.decode(key, value)

    keys = result.keys();

    missing = set(required) ^ (set(keys) & set(required));

    for key in missing: 
      self._error("Missing required field '%s'" % key)
      error = True

    # second processing stage
    entry = result
    result = {}

    for key, value in entry.items(): 

      new_key = self.renameField(key);

      if self.strict and not BIBTEX_FIELDS.has_key(new_key):
        self._error("Unknown field '%s'" % key)
        error = True
      elif not self.strict and not BIBTEX_FIELDS.has_key(new_key):
        continue

      result[new_key] = self.parseField(new_key, value)

    result["@type"] = bibtex_type
    result["@key"] = bibtex_key

    if error:
      return None

    return result

  def _error(self, message, line = None, column = None):
    if (line == None):
      line = self.line
    if (column == None):
      column = self.column

    self.errors.append({"message" : message, "line" : line, "column" : column})

  def getErrors(self):
    return self.errors

  def validate(self, field, value):
    return None

  def decode(self, field, value):
    if BIBTEX_FIELDS.has_key(field):
      t = BIBTEX_FIELDS[field]["type"]
    else: 
      t = "string"

    if t == "string" or t == "text":
      return self._substitute(self._unicode(value)).strip()
    if t == "number":
      value = value.strip()
      try:
        return str(int(value))
      except:
        if value == "":
          return value
        else:
          try:
            return str(roman_to_int(value))
          except:
            return ""

    if t == "range":
      value = value.strip()
      m = re.match(r'([0-9]+) *-+ *([0-9]+)', value)
      if m:
        return "%s--%s" % (m.group(1), m.group(2))
      try:
        return str(int(value))
      except:
        if value == "":
          return value
        else:
          try:
            return str(roman_to_int(value))
          except:
            return ""
    elif t == "people":
      value = self._unicode(value).strip()

      if " and " in value:
        people_raw = [e.strip() for e in value.split(" and ")]
      else:
        people_raw = [e.strip() for e in value.split(",")]

      print people_raw

      people = []

      for person_raw in people_raw:
        if "," in person_raw:
          parts = [e.strip() for e in person_raw.split(",")]
          name = parts[1]
          surname = parts[0]
        else:
          parts = [e.strip() for e in person_raw.split(" ")]
          name = parts[0]
          surname = parts[1]

        people.append((surname, name))

      return " and ".join([ "%s, %s" % e for e in people ])

    return value.strip()

  def _substitute(self, value):

    tmp = value
    for key, value in self._replace.items():
      tmp = tmp.replace(key, value)

    return tmp

  def _unicode(self, text):
    from publications.transcode import tex_to_unicode

    text = tex_to_unicode(text)
    return re.sub(r'([^\\\\]?)([{}])', "\\1", text)


  def renameField(self, key):
    return key

  def parseField(self, key, value):
    return value


class BibTeXFormatter:

  def format(self, entry):

    from publications.transcode import unicode_to_tex

    bibtex_type = entry["@type"]
    bibtex_key = entry["@key"]
    o = list()

    for key, value in entry.items():
      if (key == "@type" or key == "@key"):
        continue
      o.append("\t" + key + " = {" + unicode_to_tex(value) + "}")

    return "@" + bibtex_type + " {" + bibtex_key + ",\n" + ",\n".join(o) + "\n}\n"

  def formatPeople(self, people, nice = False):
    if not type(people) == list: 
      people = parsePeople(people)
    if nice:
      last = array_pop(people)

      temp = list()
      for person in people:
        temp.apppend(person[1] + " " + person[0])

      if len(temp) < 1:
        return last[1] + " " + last[0]
      return ", ".join(temp) + " and " + last[1] + " " + last[0]

    else:
      processed = list();

      for a in people:
        processed.append(", ".join(a))

      return " and ".join(processed)


if __name__ == "__main__":
  f = open(sys.argv[1], 'r')
  content = f.read()
  f.close()

  parser = BibTeXParser()

  entries = parser.parse(content)

  errors = parser.getErrors()
  if len(errors) > 0:
    print errors

  processor = BibTeXProcessor(strict=False)
  formatter = BibTeXFormatter()

  for entry in entries:
    e = processor.process(entry)
    if e == None:
      print processor.getErrors()
    else:
      print formatter.format(e)


