#!/usr/bin/env python
#coding: utf-8

#    create_plurals.py is free software: you can redistribute it and/or modify
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

import re, string
import argparse

import blib, pywikibot
from blib import msg

site = pywikibot.Site()

verbose = True

def remove_diacritics(word):
  return re.sub(u"[\u064B\u064C\u064D\u064E\u064F\u0650\u0652\u0670]", "", word)

# Create or insert a section describing the plural of a given word.
# PLTR and SINGTR are the associated manual transliterations (if any).
# POS is the part of speech of the word (capitalized, e.g. "Noun").
# Only save the changed page if SAVE is true.
def create_plural(plural, pltr, singular, singtr, pos, save):
  msg("Creating plural entry %s%s for singular %s%s" % (
    plural, " (%s)" % pltr if pltr else "",
    singular, " (%s)" % singtr if singtr else ""))
  pagename = remove_diacritics(plural)
  page = pywikibot.Page(site, pagename)
  newposbody = u"""{{ar-plural|%s%s}}

# {{plural of|lang=ar|%s%s}}
""" % (plural, "|tr=%s" % pltr if pltr else "", singular,
    "|tr=%s" % singtr if singtr else "")
  newpos = "===%s===\n" % pos + newposbody
  newposl4 = "====%s====\n" % pos + newposbody
  newsection = "==Arabic==\n" + newpos
  comment = None
  if not page.exists():
    msg("Page %s: creating" % pagename)
    comment = "Creating page for Arabic plural %s of %s, pos=%s" % (
        plural, singular, pos)
    page.text = newsection
    if verbose:
      msg("New text is [[%s]]" % page.text)
  else:
    sections = re.split("(^--+\n)", page.text, 0, re.M)
    for i in xrange(sections):
      if (i % 2) == 1:
        continue
      m = re.match("^==([^=]*)==$", sections[i], re.M)
      if not m:
        msg("Page %s: Can't find language name in text: [[%s]]" % (pagename, sections[i]))
      elif m.group(1) == "Arabic":
        if re.match(r"===+%s===+\s+\{\{ar-plural\|%s[|}]" % (pos, plural), sections[i]):
          msg("Page %s: exists and has Arabic section with plural %s already in it, taking no action"
              % (pagename, plural))
          break
        else:
          msg("Page %s: exists and has Arabic section, appending to end of section"
              % pagename)
          comment = "Creating entry in existing Arabic section for plural %s of %s, pos=%s" % (
              plural, singular, pos)
          # FIXME! Conceivably instead of inserting at end we should insert
          # next to any existing ===Noun=== (or corresponding POS, whatever
          # it is), in particular after the last one. However, this makes less
          # sense when we create separate etymologies, as we do. Conceivably
          # this would mean inserting after the last etymology section
          # containing an entry of the same part of speech.
          #
          # (Perhaps for now we should just skip creating entries if we find
          # an existing Arabic entry?)
          if "\n===Etymology 1===\n" in sections[i]:
            j = 2
            while ("\n===Etymology %s===\n" % j) in section[i]:
              j += 1
            msg("Page %s: found multiple etymologies, adding new section \"Etymology %s\"" % (pagename, j))
            sections[i] += "\n===Etymology %s===\n" % j + newposl4
          else:
            msg("Page %s: wrapping existing text in \"Etymology 1\" and adding \"Etymology 2\"" % pagename)
            # Wrap existing text in "Etymology 1" and increase the indent level
            # by one of all headers
            sections[i] = ("===Etymology 1===\n" +
                re.sub("^==(.*?)==$", r"===\1===", sections[i], 0, re.M) +
                "\n===Etymology 2===\n" + newposl4)
          break
      elif m.group(1) > "Arabic":
        msg("Page %s: exists; inserting before %s section" %
            (pagename, m.group(1)))
        comment = "Creating Arabic section and entry for plural %s of %s, pos=%s" % (
            plural, singular, pos)
        sections[i:i] = [newsection, "----"]
        break
    else:
      msg("Page %s: exists; adding section to end" % pagename)
      comment = "Creating Arabic section and entry for plural %s of %s, pos=%s" % (
          plural, singular, pos)
      sections += ["----", newsection]
    newtext = ''.join(sections)
    if verbose:
      msg("Replacing [[%s]] with [[%s]]" % (page.text, newtext))
    page.text = newtext
  if comment:
    msg("For page %s, comment = %s" % (pagename, comment))
    if save:
      page.save(comment = comment)

def create_plurals(pos, tempname, save, startFrom, upTo):
  for cat in [u"Arabic %ss" % pos]:
    for page in blib.cat_articles(cat, startFrom, upTo):
      for template in blib.parse(page).filter_templates():
        if template.name == tempname:
          sing = blib.getparam(template, "1")
          singtr = blib.getparam(template, "tr")
          pl = blib.getparam(template, "pl")
          pltr = blib.getparam(template, "pltr")
          if pl:
            create_plural(pl, pltr, sing, singtr, pos, save)
          i = 2
          while pl:
            pl = blib.getparam(template, "pl" + str(i))
            pltr = blib.getparam(template, "pl" + str(i) + "tr")
            if pl:
              create_plural(pl, pltr, sing, singtr, pos, save)
            i += 1

pa = argparse.ArgumentParser(description="Create Arabic plurals")
pa.add_argument("-s", "--save", action='store_true',
    help="Save changed pages")
pa.add_argument("start", nargs="?", help="First page to work on")
pa.add_argument("end", nargs="?", help="Last page to work on")

params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)

create_plurals("Noun", "ar-noun", params.save, startFrom, upTo)
create_plurals("Adjective", "ar-adj", params.save, startFrom, upTo)
