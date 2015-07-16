#!/usr/bin/env python
#coding: utf-8

#    split_etymologies.py is free software: you can redistribute it and/or modify
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
from blib import msg, getparam, addparam, remove_links
from arabiclib import *

def split_one_page_etymologies(page, index, pagetext, verbose):

  # Fetch pagename, create pagemsg() fn to output msg with page name included
  pagename = page.title()
  pagetext = unicode(pagetext)
  def pagemsg(text):
    msg("Page %s %s: %s" % (index, pagename, text))

  comment = None
  notes = []

  # Split off interwiki links at end
  m = re.match(r"^(.*?\n)(\n*(\[\[[a-z0-9_\-]+:[^\]]+\]\]\n*)*)$",
      pagetext, re.S)
  if m:
    pagebody = m.group(1)
    pagetail = m.group(2)
  else:
    pagebody = pagetext
    pagetail = ""

  # Split into sections
  splitsections = re.split("(^==[^=\n]+==\n)", pagebody, 0, re.M)
  # Extract off pagehead and recombine section headers with following text
  pagehead = splitsections[0]
  sections = []
  for i in xrange(1, len(splitsections)):
    if (i % 2) == 1:
      sections.append("")
    sections[-1] += splitsections[i]

  # Go through each section in turn, looking for existing Arabic section
  for i in xrange(len(sections)):
    m = re.match("^==([^=\n]+)==$", sections[i], re.M)
    if not m:
      pagemsg("WARNING: Can't find language name in text: [[%s]]" % (sections[i]))
    elif m.group(1) == "Arabic":
      # Extract off trailing separator
      mm = re.match(r"^(.*?\n)(\n*--+\n*)$", sections[i], re.S)
      if mm:
        sections[i:i+1] = [mm.group(1), mm.group(2)]
      elif i < len(sections) - 1:
        pagemsg("WARNING: Arabic language section %s is non-final and missing trailing separator" % i)

      for mm in re.finditer("^(==+)[^=\n](==+)$", sections[i], re.M):
        if mm.group(1) != mm.group(2):
          pagemsg("WARNING: Malconstructed header: %s" % mm.group(0))

      subsections = re.split("(^===[^=\n]+=+\n)", sections[i], 0, re.M)
      if len(subsections) < 2:
        pagemsg("WARNING: Page missing any entries")

      etymologies = []
      etymsections = []
      sechead = subsections[0]
      if "\n===Etymology 1=" in sections[i]:
        etyms_were_separate = True
        for j in xrange(1, len(subsections), 2):
          if not re.match("^===Etymology [0-9]+=", subsections[j]):
            pagemsg("WARNING: Non-etymology level-3 header when split etymologies: %s" % subsections[j][0:-1])
        etymsections = [subsections[j] for j in xrange(2, len(subsections), 2)]
        # Reduce indent by one. We will increase it again when we split
        # etymologies.
        for j in xrange(len(etymsections)):
          etymsections[j] = re.sub("^==", "=", etymsections[j], 0, re.M)
      else:
        etyms_were_separate = False
        etymsections = ''.join(subsections[1:])

      for etymsection in etymsections:
        subsections = re.split("(^===[^=\n]+=+\n)", etymsection, 0, re.M)
        if len(subsections) < 2:
          pagemsg("WARNING: Section missing any entries")
        split_sections = []
        next_split_section = 0
        def append_section(k):
          while len(split_sections) <= next_split_section:
            split_sections.append("")
          split_sections[next_split_section] += \
              subsections[k] + subsections[k + 1]

        last_lemma = None
        last_inflection_of_lemma = None
        for j in xrange(1, len(subsections), 2):
          if re.match("^===+(References|Related|See)", subsections[j]):
            pagemsg("Found level-3 section that should maybe be at higher level: %s" % subsections[j][0:-1])
            append_section(j)
          elif re.match("^===+(Alternative|Etymology)", subsections[j]):
            append_section(j)
          else:
            parsed = blib.parse_text(subsections[j + 1])
            lemma = None
            inflection_of_lemma = None
            for t in parsed.filter_templates():
              if t.name in arabic_all_headword_templates:
                if lemma:
                  if t.name not in ["ar-nisba", "ar-noun-nisba", "ar-verb",
                      "ar-verb-form"]:
                    pagemsg("Found multiple headword templates in section %s: %s" % (j, subsections[j][0:-1]))
                # Note: For verbs this is the form class, which we match on
                lemma = reorder_shadda(remove_links(getparam(t, "1")))
              if t.name == "inflection of":
                if inflection_of_lemma:
                  pagemsg("Found multiple 'inflection of' templates in section %s: %s" % (j, subsections[j][0:-1]))
                inflection_of_lemma = remove_diacritics(
                    remove_links(getparam(t, "1")))
            if not lemma:
              pagemsg("Warning: No headword template in section %s: %s" % (j, subsections[j][0:-1]))
              append_section(j)
            else:
              if lemma != last_lemma:
                next_split_section += 1
              elif (inflection_of_lemma and last_inflection_of_lemma and
                  inflection_of_lemma != last_inflection_of_lemma):
                pagemsg("Verb forms have different inflection-of lemmas %s and %s, splitting etym" % (
                  last_inflection_of_lemma, inflection_of_lemma))
                next_split_section += 1
              last_lemma = lemma
              last_inflection_of_lemma = inflection_of_lemma
              append_section(j)
        etymologies += split_sections

      # Combine adjacent etymologies with same verb form class I.
      # FIXME: We might not want to do this; the etymologies might be
      # legitimately split. Need to check each case.
      j = 0
      while j < len(etymologies) - 1:
        def get_form_class(k):
          formclass = None
          parsed = blib.parse_text(etymologies[j])
          for t in parsed.filter_templates():
            if t.name in ["ar-verb", "ar-verb-form"]:
              newformclass = getparam(t, "1")
              if formclass and newformclass and formclass != newformclass:
                pagemsg("WARNING: Something wrong: Two different verb form classes in same etymology: %s != %s" % (formclass, newformclass))
              formclass = newformclass
          return formclass

        formclassj = get_form_class(j)
        formclassj1 = get_form_class(j + 1)
        if formclassj == "I" and formclassj1 == "I":
          if not etymologies[j + 1].startswith("="):
            pagemsg("WARNING: Can't combine etymologies with same verb form class because second has etymology text")
          else:
            pagemsg("Combining etymologies with same verb form class I")
            etymologies[j] = etymologies[j].rstrip() + "\n\n" + etymologies[j + 1]
            # Cancel out effect of incrementing j below since we combined
            # the following etymology into this one
            j -= 1
        j += 1

      if len(etymologies) > 1:
        for j in xrange(len(etymologies)):
          # Stuff like "===Alternative forms===" that goes before the
          # etymology section should be moved after.
          newetymj = re.sub(r"^(.*?\n)(===Etymology===\n(\n|[^=\n].*?\n)*)",
              r"\2\1", etymologies[j], 0, re.S)
          if newetymj != etymologies[j]:
            pagemsg("Moved ===Alternative forms=== and such after Etymology")
            etymologies[j] = newetymj
          # Remove ===Etymology=== from beginning
          etymologies[j] = re.sub("^===Etymology===\n", "", etymologies[j])
          # Fix up newlines around etymology section
          etymologies[j] = etyomologies[j].strip() + "\n\n"
          if etymologies[j].startswith("="):
            etymologies[j] = "\n" + etymologies[j]
        sections[i] = (sechead +
            ''.join(["===Etymology %s===\n" % (j + 1) + etymologies[j]
              for j in xrange(len(etymologies))]))
      elif len(etymologies) == 1:
        if etyms_were_separate:
          # We might need to add an Etymology header at the beginning.
          pagemsg("Combined formerly separate etymologies")
          if not re.match(r"^(=|\{\{wikipedia|\[\[File:)",
              etymologies[0].strip()):
            etymologies[0] = "===Etymology===\n" + etymologies[0]
            pagemsg("Added Etymology header when previously separate etymologies combined")
          # Put Alternative forms section before Etymology.
          newetym0 = re.sub(r"^((?:\n|[^=\n].*?\n)*)(===Etymology===\n(?:\n|[^=\n].*?\n)*)(===(Alternative.*?)===\n(?:\n|[^=\n].*?\n)*)",
              r"\1\3\2", etymologies[0], 0, re.S)
          if newetym0 != etymologies[0]:
            pagemsg("Moved ===Alternative forms=== and such before Etymology")
            etymologies[0] = newetym0

        sections[i] = sechead + etymologies[0]
      else:
        sections[i] = sechead

      break

  # End of loop over sections in existing page; rejoin sections
  newtext = pagehead + ''.join(sections) + pagetail

  # Don't signal a save if only differences are whitespace at end,
  # since it appears that newlines at end get stripped when saving.
  if pagetext.rstrip() == newtext.rstrip():
    pagemsg("No change in text")
  else:
    if verbose:
      pagemsg("Replacing [[%s]] with [[%s]]" % (pagetext, newtext))
    else:
      pagemsg("Text has changed")
    pagetext = newtext

    # Construct and output comment.
    notestext = '; '.join(notes)
    if notestext:
      if comment:
        comment += " (%s)" % notestext
      else:
        comment = notestext
    assert(comment)
    pagemsg("comment = %s" % comment, simple = True)

  return pagetext, comment

def split_etymologies(save, verbose, startFrom, upTo):
  def split_page_etymologies(page, index, pagetext):
    return split_one_page_etymologies(page, index, pagetext, verbose)
  for page, index in blib.cat_articles("Arabic lemmas", startFrom, upTo):
    blib.do_edit(page, index, split_page_etymologies, save=save,
        verbose=verbose)

pa = blib.init_argparser("Split etymology sections")
params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)

split_etymologies(params.save, True, # params.verbose
    startFrom, upTo)
