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

import re

import blib, pywikibot
from blib import msg

site = pywikibot.Site()

verbose = True

def remove_diacritics(word):
  return re.sub(u"[\u064B\u064C\u064D\u064E\u064F\u0650\u0651\u0652\u0670]", "", word)

# Create or insert a section describing the plural or similar inflection
# of a given word. PLTR and SINGTR are the associated manual transliterations
# (if any). POS is the part of speech of the word (capitalized, e.g. "Noun").
# Only save the changed page if SAVE is true. PLWORD is e.g. "plural" or
# "feminine"; SINGWORD is e.g. "singular" or "masculine"; PLTEMP is e.g.
# "ar-noun-pl", "ar-adj-pl" or "ar-feminine"; SINGTEMP is e.g. "plural of",
# "masculine plural of" or "feminine of".
def create_inflection(save, plural, pltr, singular, singtr, pos,
    plword, singword, pltemp, singtemp):
  if plural == "-":
    msg("Not creating %s entry - for %s %s%s" % (
      plword, singword, singular, " (%s)" % singtr if singtr else ""))
    return
  # FIXME! Need to split off trailing interwiki links
  msg("Creating %s entry %s%s for %s %s%s" % (
    plword, plural, " (%s)" % pltr if pltr else "",
    singword, singular, " (%s)" % singtr if singtr else ""))
  pagename = remove_diacritics(plural)
  pl_no_vowels = pagename
  sing_no_vowels = remove_diacritics(singular)
  page = pywikibot.Page(site, pagename)
  newposbody = u"""{{%s|%s%s%s}}

# {{%s|%s%s|lang=ar}}
""" % (pltemp, plural,
    "", #"|m-p" if pos == "Adjective" and plword == "plural" else "",
    "|tr=%s" % pltr if pltr else "",
    singtemp, singular,
    "|tr=%s" % singtr if singtr else "")
  newpos = "===%s===\n" % pos + newposbody
  newposl4 = "====%s====\n" % pos + newposbody
  newsection = "==Arabic==\n\n" + newpos
  comment = None
  if not page.exists():
    msg("Page %s: creating" % pagename)
    comment = "Create page for Arabic %s %s of %s, pos=%s" % (
        plword, plural, singular, pos)
    page.text = newsection
    if verbose:
      msg("New text is [[%s]]" % page.text)
  else:
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
        subsections = re.split("(^===+[^=\n]+===+\n)", sections[i], 0, re.M)
        for j in xrange(len(subsections)):
          if j > 0 and (j % 2) == 0 and re.match("^===+%s===+\n" % pos, subsections[j - 1]):
            parsed = blib.parse_text(subsections[j])
            headword_template = None
            headword_collective_template = None
            inflection_template = None
            # For singular قطءة and plural قطء, three different possible
            # sets of vocalizations. For this case, require that the
            # existing versions match exactly, rather than matching with
            # removed diacritics.
            must_match_exactly = plword == "plural" and pl_no_vowels == u"قطء" and sing_no_vowels == u"قطءة"
            for template in parsed.filter_templates():
              def compare_param(param, value):
                paramval = blib.getparam(template, param)
                if must_match_exactly:
                  return paramval == value
                else:
                  return remove_diacritics(paramval) == remove_diacritics(value)
              if (plword == "plural" and template.name == "ar-coll-noun" and compare_param("1", plural)
                  and compare_param("sing", singular)):
                headword_collective_template = template
                break
              if template.name == pltemp and compare_param("1", plural):
                headword_template = template
              if template.name == singtemp and compare_param("1", singular):
                inflection_template = template
                break
            if headword_collective_template:
              msg("Page %s: exists and has Arabic section and found collective noun with %s %s already in it; taking no action"
                  % (pagename, plword, plural))
              break
            if inflection_template and headword_template:
              msg("Page %s: exists and has Arabic section and found %s %s already in it"
                  % (pagename, plword, plural))
              comment = "Update Arabic with more vocalized versions: %s %s, %s %s, pos=%s" % (
                  plword, plural, singword, singular, pos)
              existing_pl = blib.getparam(headword_template, "1")
              if len(plural) > len(existing_pl):
                msg("Page %s: updating existing %s %s with %s" %
                    (pagename, pltemp, existing_pl, plural))
                headword_template.add("1", plural)
                if pltr:
                  headword_template.add("tr", pltr)
              existing_sing = blib.getparam(inflection_template, "1")
              if len(singular) > len(existing_sing):
                msg("Page %s: updating existing '%s' %s with %s" %
                    (pagename, singtemp, existing_sing, singular))
                inflection_template.add("1", singular)
                if singtr:
                  inflection_template.add("tr", singtr)
              #if pos == "Adjective" and plword == "plural":
              #  headword_template.add("2", "m-p")
              subsections[j] = unicode(parsed)
              sections[i] = ''.join(subsections)
              break
        else:
          msg("Page %s: exists and has Arabic section, appending to end of section"
              % pagename)
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
            while ("\n===Etymology %s===\n" % j) in sections[i]:
              j += 1
            msg("Page %s: found multiple etymologies, adding new section \"Etymology %s\"" % (pagename, j))
            comment = "Append entry (Etymology %s) for %s %s of %s, pos=%s in existing Arabic section" % (
              j, plword, plural, singular, pos)
            sections[i] += "\n===Etymology %s===\n\n" % j + newposl4
          else:
            msg("Page %s: wrapping existing text in \"Etymology 1\" and adding \"Etymology 2\"" % pagename)
            comment = "Wrap existing Arabic section in Etymology 1, append entry (Etymology 2) for %s %s of %s, pos=%s" % (
                plword, plural, singular, pos)
            # Wrap existing text in "Etymology 1" and increase the indent level
            # by one of all headers
            sections[i] = re.sub("^\n*==Arabic==\n+", "", sections[i])
            wikilink_re = r"^(\{\{wikipedia\|.*?\}\})\n*"
            mmm = re.match(wikilink_re, sections[i])
            wikilink = (mmm.group(1) + "\n") if mmm else ""
            if mmm:
              sections[i] = re.sub(wikilink_re, "", sections[i])
            sections[i] = re.sub("^===Etymology===\n", "", sections[i])
            sections[i] = ("==Arabic==\n" + wikilink + "\n===Etymology 1===\n" +
                ("\n" if sections[i].startswith("==") else "") +
                re.sub("^==(.*?)==$", r"===\1===", sections[i], 0, re.M) +
                "\n===Etymology 2===\n\n" + newposl4)
        break
      elif m.group(1) > "Arabic":
        msg("Page %s: exists; inserting before %s section" %
            (pagename, m.group(1)))
        comment = "Create Arabic section and entry for %s %s of %s, pos=%s; insert before %s section" % (
            plword, plural, singular, pos, m.group(1))
        sections[i:i] = [newsection, "\n----\n\n"]
        break
    else:
      msg("Page %s: exists; adding section to end" % pagename)
      comment = "Create Arabic section and entry for %s %s of %s, pos=%s; append at end" % (
          plword, plural, singular, pos)
      # Make sure there are two trailing newlines
      if sections[-1].endswith("\n\n"):
        pass
      elif sections[-1].endswith("\n"):
        sections[-1] += "\n"
      else:
        sections[-1] += "\n\n"
      sections += ["----\n\n", newsection]
    newtext = head + ''.join(sections) + tail
    if verbose:
      msg("Replacing [[%s]] with [[%s]]" % (page.text, newtext))
    page.text = newtext
  if comment:
    msg("For page %s, comment = %s" % (pagename, comment))
    if save:
      page.save(comment = comment)

def create_noun_plural(save, plural, pltr, singular, singtr, pos):
  return create_inflection(save, plural, pltr, singular, singtr, pos,
      "plural", "singular", "ar-noun-pl", "plural of")

def create_adj_plural(save, plural, pltr, singular, singtr, pos):
  return create_inflection(save, plural, pltr, singular, singtr, pos,
      "plural", "singular", "ar-adj-pl", "masculine plural of")

def create_noun_feminine(save, plural, pltr, singular, singtr, pos):
  return create_inflection(save, plural, pltr, singular, singtr, pos,
      "feminine", "masculine", None, "feminine of")

def create_adj_feminine(save, plural, pltr, singular, singtr, pos):
  return create_inflection(save, plural, pltr, singular, singtr, pos,
      "feminine", "masculine", "ar-feminine", "feminine of")

def create_inflections(save, pos, tempname, startFrom, upTo, createfn, param):
  for cat in [u"Arabic %ss" % pos.lower()]:
    for page in blib.cat_articles(cat, startFrom, upTo):
      for template in blib.parse(page).filter_templates():
        if template.name == tempname:
          sing = blib.getparam(template, "1")
          singtr = blib.getparam(template, "tr")
          pl = blib.getparam(template, param)
          pltr = blib.getparam(template, param + "tr")
          if pl:
            createfn(save, pl, pltr, sing, singtr, pos)
          i = 2
          while pl:
            pl = blib.getparam(template, param + str(i))
            pltr = blib.getparam(template, param + str(i) + "tr")
            if pl:
              createfn(save, pl, pltr, sing, singtr, pos)
            i += 1

def create_plurals(save, pos, tempname, startFrom, upTo):
  return create_inflections(save, pos, tempname, startFrom, upTo,
      create_noun_plural if pos == "Noun" else create_adj_plural, "pl")

def create_feminines(save, pos, tempname, startFrom, upTo):
  return create_inflections(save, pos, tempname, startFrom, upTo,
      create_noun_feminine if pos == "Noun" else create_adj_feminine, "f")

pa = blib.init_argparser("Create Arabic inflections")
pa.add_argument("-p", "--plural", action='store_true',
    help="Do plural inflections")
pa.add_argument("-f", "--feminine", action='store_true',
    help="Do feminine inflections")

params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)

if params.plural:
  create_plurals(params.save, "Noun", "ar-noun", startFrom, upTo)
  create_plurals(params.save, "Adjective", "ar-adj", startFrom, upTo)
if params.feminine:
  #create_feminines(params.save, "Noun", "ar-noun", startFrom, upTo)
  create_feminines(params.save, "Adjective", "ar-adj", startFrom, upTo)
