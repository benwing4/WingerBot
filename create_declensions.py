#!/usr/bin/env python
#coding: utf-8

#    create_declensions.py is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re

import blib, pywikibot
from blib import msg

site = pywikibot.Site()

verbose = True

def remove_diacritics(word):
  return re.sub(u"[\u064B\u064C\u064D\u064E\u064F\u0650\u0651\u0652\u0670]", "", word)

def remove_links(text):
  text = re.sub(r"\[\[[^|\]]*?\|", "", text)
  text = re.sub(r"\[\[", "", text)
  text = re.sub(r"\]\]", "", text)
  return text

# Create or insert declension sections in a given page. POS is the part of
# speech of the word (capitalized, e.g. "Noun"). Only save the changed page
# if SAVE is true. TEMPNAME is the name of the headword template, e.g.
# "ar-noun"; DECLTEMPNAME is the corresponding name of the declension template,
# e.g. "ar-decl-noun". REMOVEPARAMS is a list of parameters to remove from
# the headword template when creating the declension template. Parameters
# that are all alphabetic are expanded so that e.g. "f" will also remove
# parameters named "f2", "f3", "f4", etc.
def create_declension(page, save, pos, tempname, decltempname, removeparams):

  def name_should_be_removed(name):
    for param in removeparams:
      if name == param:
        return true
      if re.match("^[a-z]+$", param) and re.match("^%s[0-9]+$" % param, name):
        return true
    return false

  # Split off interwiki links at end
  m = re.match(r"^(.*?\n)(\n*(\[\[[a-z0-9_\-]+:[^\]]+\]\]\n*)*)$",
      page.text, re.S)
  if m:
    body = m.group(1)
    tail = m.group(2)
  else:
    body = page.text
    tail = ""
  splitsections = re.split("(^==[^=\n]+==\n)", body, 0, re.M)
  # Extract off head and recombine section headers with following text
  head = splitsections[0]
  sections = []
  for i in xrange(1, len(splitsections)):
    if (i % 2) == 1:
      sections.append("")
    sections[-1] += splitsections[i]
  for i in xrange(len(sections)):
    m = re.match("^==([^=\n]+)==$", sections[i], re.M)
    if not m:
      msg("Page %s: Can't find language name in text: [[%s]]" % (pagename, sections[i]))
    elif m.group(1) == "Arabic":
      # Extract off trailing separator
      mm = re.match(r"^(.*?\n)(\n*--+\n*)$", sections[i], re.S)
      if mm:
        sections[i:i+1] = [mm.group(1), mm.group(2)]

      # Split into subsections based on headers
      subsections = re.split("(^===+[^=\n]+===+\n)", sections[i], 0, re.M)
      for j in xrange(len(subsections)):
        # Look for subsections matching the given POS
        if j > 0 and (j % 2) == 0 and re.match("^===+%s===+\n" % pos, subsections[j - 1]):
          parsed = blib.parse_text(subsections[j])

          # Check for various conditions causing us to skip this entry and
          # not try to add a declension table
          headword_templates = [temp for temp in parsed.filter_templates() if temp.name in
              ["ar-noun", "ar-proper noun", "ar-coll-noun", "ar-sing-noun",
                "ar-adj"]]
          if len(headword_templates) == 0:
            msg("Page %s: Can't find headword template in text, skipping: [[%s]]" % (pagename, subsections[j]))
            continue
          if len(headword_templates) > 1:
            msg("Page %s: Found multiple headword templates in text, skipping: [[%s]]" % (pagename, subsections[j]))
            continue
          headword_template = headword_templates[0]
          if headword_template.name != tempname:
            msg("Page %s: Headword template should be '%s' but is not, skipping: [[%s]]" % (pagename, tempname, subsections[j]))
            continue
          head = blib.getparam(headword_template, "1")
          if ' ' in head:
            msg("Page %s: Headword template head %s has space in it, skipping: [[%s]]" % (pagename, head, subsections[j]))
            continue
          if '[' in head or ']' in head or '|' in head:
            msg("Page %s: Headword template head %s has link in it, skipping: [[%s]]" % (pagename, head, subsections[j]))
            continue
          broken = false
          for param in headword_template.params:
            if re.search("tr", unicode(param.name)):
              msg("Page %s: Headword template for head %s has explicit translit in it, skipping: [[%s]]" % (pagename, head, subsections[j]))
              broken = true
              break
            if re.match("cpl", unicode(param.name)):
              msg("Page %s: Headword template for head %s has cpl param in it, skipping: [[%s]]" % (pagename, head, subsections[j]))
              broken = true
              break
          if broken:
            continue
          if j + 1 < len(subsections) and re.match("^===+Declension===+\n", subsections[j + 1]):
            msg("Page %s: Declension already found for head %s, skipping: [[%s]]" % (pagename, head, subsections[j]))

          # Now fetch the parameters from the headword template, removing
          # any that we want to remove
          params = '|'.join([unicode(param) for param in headword_template.params if not name_should_be_removed(unicode(param.name))])
          # Separate off any [[Category: Foo]] declarators, insert before them
          m = re.match(r"^(.*?\n+)((\[\[[A-Za-z0-9_\-]+:[^\]]+\]\]\n*)*)$",
              subsections[j], re.S)
          if m:
            body = m.group(1)
            tail = m.group(2)
          else:
            body = subsections[j]
            tail = ""
          # Make sure there are two trailing newlines
          if body.endswith("\n\n"):
            pass
          elif body.endswith("\n"):
            body += "\n"
          else:
            body += "\n\n"
          body += (subsections[j - 1].replace(pos, "=Declension=") +
              "{{%s|%s}}\n\n" % (decltempname, params))
          subsections[j] = body + tail
          comment = "Added declension for %s %s" % (
            tempname, blib.getparam(headword_template, "1"))
          sections[i] = ''.join(subsections)
  newtext = head + ''.join(sections) + tail
  if verbose:
    msg("Replacing [[%s]] with [[%s]]" % (page.text, newtext))
  page.text = newtext
  if comment:
    msg("For page %s, comment = %s" % (pagename, comment))
    if save:
      page.save(comment = comment)

def create_declensions(save, pos, tempname, decltempname, startFrom, upTo,
    removeparams):
  for page in blib.references("Template:%s" % tempname, startFrom, upTo):
    create_declension(page, save, pos, tempname, decltempname, removeparams)

pa = blib.init_argparser("Create Arabic declensions")

params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)

create_declensions(params.save, "Noun", "ar-noun", "ar-decl-noun",
    startFrom, upTo, ["2", "g2", "f", "m", "cons", "dobl", "plobl"])
create_declensions(params.save, "Noun", "ar-coll-noun", "ar-decl-coll-noun",
    startFrom, upTo, ["2", "g2", "singg", "cons", "dobl", "paucobl", "plobl"])
create_declensions(params.save, "Noun", "ar-sing-noun", "ar-decl-sing-noun",
    startFrom, upTo, ["2", "g2", "collg", "cons", "dobl", "paucobl", "plobl"])
create_declensions(params.save, "Adjective", "ar-nisba", "ar-decl-adj",
    startFrom, upTo, ["2", "g2", "collg", "cons", "dobl", "paucobl", "plobl"])
# FIXME: Add pl=smp as argument.
#create_declensions(params.save, "Noun", "ar-nisba-noun", "ar-decl-noun",
#    startFrom, upTo, ["2", "g2", "f", "m", "cons", "dobl", "plobl"])
# FIXME: Do this only when there's a plural available.
#create_declensions(params.save, "Adjective", "ar-adj", "ar-decl-adj",
#    startFrom, upTo, ["el", "cons", "dobl", "cplobl", "plobl", "fplobl"])
