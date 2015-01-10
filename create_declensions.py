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

A  = u"\u064E" # fatḥa
AN = u"\u064B" # fatḥatān (fatḥa tanwīn)
U  = u"\u064F" # ḍamma
UN = u"\u064C" # ḍammatān (ḍamma tanwīn)
I  = u"\u0650" # kasra
IN = u"\u064D" # kasratān (kasra tanwīn)
SK = u"\u0652" # sukūn = no vowel
SH = u"\u0651" # šadda = gemination of consonants
DAGGER_ALIF = u"\u0670"
DIACRITIC_ANY_BUT_SH = "[" + A + I + U + AN + IN + UN + SK + DAGGER_ALIF + "]"
ALIF = u"ا"
ALIF_WASLA = u"ٱ"
ALIF_ANY = "[" + ALIF + ALIF_WASLA + "]"
L = u"ل"
Y = u"ي"

def remove_diacritics(word):
  return re.sub(u"[\u064B\u064C\u064D\u064E\u064F\u0650\u0651\u0652\u0670]", "", word)

def remove_links(text):
  text = re.sub(r"\[\[[^|\]]*?\|", "", text)
  text = re.sub(r"\[\[", "", text)
  text = re.sub(r"\]\]", "", text)
  return text

def reorder_shadda(word):
  # shadda+short-vowel (including tanwīn vowels, i.e. -an -in -un) gets
  # replaced with short-vowel+shadda during NFC normalisation, which
  # MediaWiki does for all Unicode strings; however, it makes the
  # detection process inconvenient, so undo it.
  word = re.sub("(" + DIACRITIC_ANY_BUT_SH + ")" + SH, SH + r"\1", word)
  return word

# Create or insert declension sections in a given page. POS is the part of
# speech of the word (capitalized, e.g. "Noun"). Only save the changed page
# if SAVE is true. TEMPNAME is the name of the headword template, e.g.
# "ar-noun"; DECLTEMPNAME is the corresponding name of the declension template,
# e.g. "ar-decl-noun". REMOVEPARAMS is a list of parameters to remove from
# the headword template when creating the declension template. Parameters
# that are all alphabetic are expanded so that e.g. "f" will also remove
# parameters named "f2", "f3", "f4", etc.
def create_declension(page, save, pos, tempname, decltempname, sgparam,
    removeparams):
  pagename = page.title()
  comments = []

  def starts_with_al(word):
    return re.match(ALIF_ANY + A + "?" + L, word)

  def sub_if(fr, to, word):
    if re.search(fr, word):
      return re.sub(fr, to, word)
    else:
      return ""

  def remove_al(word):
    word = reorder_shadda(word)
    return (sub_if("^" + ALIF_ANY + A + "?" + L + SK + "?(.)" + SH, r"\1", word)
        or sub_if("^" + ALIF_ANY + A + "?" + L + SK + "?", "", word)
        or word)

  # Split off interwiki links at end
  m = re.match(r"^(.*?\n+)((\[\[[a-z0-9_\-]+:[^\]]+\]\]\n*)*)$",
      page.text, re.S)
  if m:
    pagebody = m.group(1)
    pagetail = m.group(2)
  else:
    pagebody = page.text
    pagetail = ""
  splitsections = re.split("(^==[^=\n]+==\n)", pagebody, 0, re.M)
  # Extract off head and recombine section headers with following text
  pagehead = splitsections[0]
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
      mm = re.match(r"^(.*?\n+)(--+\n*)$", sections[i], re.S)
      if mm:
        secbody = mm.group(1)
        sectail = mm.group(2)
      else:
        secbody = sections[i]
        sectail = ""

      # Split into subsections based on headers
      subsections = re.split("(^===+[^=\n]+===+\n)", secbody, 0, re.M)
      for j in xrange(len(subsections)):
        # Look for subsections matching the given POS
        if j > 0 and (j % 2) == 0 and re.match("^===+%s===+\n" % pos, subsections[j - 1]):
          parsed = blib.parse_text(subsections[j])

          # Check for various conditions causing us to skip this entry and
          # not try to add a declension table
          headword_templates = [temp for temp in parsed.filter_templates() if temp.name in
              ["ar-noun", "ar-proper noun", "ar-coll-noun", "ar-sing-noun",
                "ar-adj", "ar-nisba", "ar-noun-nisba"]]

          # We don't check for {{alternative form of|...}}, because it's
          # used for e.g. different ways of spelling "camera" in Arabic,
          # some with -ā and some with -a, so we still want to create
          # declensions for those.
          altspelling_templates = [temp for temp in parsed.filter_templates() if temp.name in
              ["alternative spelling of"]]
          if len(altspelling_templates) > 0:
            msg("Page %s: Alternative spelling redirect found in text, skipping: [[%s]]" % (pagename, subsections[j]))
            continue
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

          # Check for declension already present
          if j + 1 < len(subsections) and re.match("^===+Declension===+\n", subsections[j + 1]):
            msg("Page %s: Declension already found for head %s, skipping: [[%s]]" % (pagename, head, subsections[j]))
            continue

          # Try to handle cases with a modifier; we can't handle all of them
          if ' ' in head:
            orighead = head
            words = re.split(r"\s", remove_links(head))
            head = words[0]
            if len(words) > 2:
              msg("Page %s: Headword template head %s has two or more spaces in it, skipping: [[%s]]" % (pagename, orighead, subsections[j]))
              continue
            assert(len(words) == 2)
            if blib.getparam(headword_template, "pl"):
              # FIXME
              msg("Page %s: Headword template head %s has space in it and plural, skipping: [[%s]]" % (pagename, orighead, subsections[j]))
              continue
            if blib.getparam(headword_template, "head2"):
              # FIXME
              msg("Page %s: Headword template head %s has space in it and head2, skipping: [[%s]]" % (pagename, orighead, subsections[j]))
              continue
            idafa = False
            if not starts_with_al(words[0]) and starts_with_al(words[1]):
              # Found an ʾidāfa construction
              msg("Page %s: Headword template head %s has space in it and found ʾidāfa: [[%s]]" % (pagename, orighead, subsections[j]))
              idafa = True
              headword_template.add("1", words[0])
              headword_template.add("state", "con")
              headword_template.add("mod", remove_al(words[1]))
              headword_template.add("modstate", "def")
              headword_template.add("modcase", "gen")
              headword_template.add("modnumber", sgparam)
            elif starts_with_al(words[0]) and starts_with_al(words[1]):
              msg("Page %s: Headword template head %s has space in it and found definite adjective construction: [[%s]]" % (pagename, orighead, subsections[j]))
              # Found a definite adjective construction
              headword_template.add("1", remove_al(words[0]))
              headword_template.add("state", "def")
              headword_template.add("mod", remove_al(words[1]))
            elif (not starts_with_al(words[0]) and not starts_with_al(words[1])
                and words[1].endswith(I + Y)):
              msg("Page %s: Headword template head %s has space in it and appears to end in badly formatted nisba, FIXME, skipping: [[%s]]" % (pagename, orighead, subsections[j]))
              continue
            elif (not starts_with_al(words[0]) and not starts_with_al(words[1])
                and words[1].endswith(I + Y + SH)):
              msg("Page %s: Headword template head %s has space in it and found indefinite adjective nisba construction: [[%s]]" % (pagename, orighead, subsections[j]))
              # Found an indefinite adjective nisba construction
              headword_template.add("1", words[0])
              headword_template.add("state", "ind,def")
              headword_template.add("mod", words[1])
            else:
              msg("Page %s: Headword template head %s has space in it and don't know whether construct or adjectival, skipping: [[%s]]" % (pagename, orighead, subsections[j]))
              continue
            if blib.getparam(headword_template, "2") == "p":
              msg("Page %s: Headword template head %s has space in it and is plural: [[%s]]" % (pagename, orighead, subsections[j]))
              headword_template.add("pl", blib.getparam(headword_template, "2"))
              headword_template.add("1", "-")
              if not idafa:
                headword_template.add("modpl", blib.getparam(headword_template, "mod"))
                headword_template.add("mod", "-")

          # no space in head
          else:
            if '[' in head or ']' in head or '|' in head:
              msg("Page %s: Headword template head %s has link in it: [[%s]]" % (pagename, head, subsections[j]))
              head = remove_links(words[0])
              headword_template.add("1", head)
            if starts_with_al(head):
              msg("Page %s: Headword template head %s starts with definite article: [[%s]]" % (pagename, head, subsections[j]))
              head = remove_al(words[0])
              headword_template.add("1", head)
              def check_for_al(param):
                value = blib.getparam(headword_template, param)
                if value:
                  headword_template.add(param, remove_al(value))
              check_for_al("pl")
              for i in xrange(2, 10):
                check_for_al("pl%s" % i)
                check_for_al("head%s" % i)

          if head.endswith(UN):
            msg("Page %s: Headword template head %s ends with explicit i3rab (UN): [[%s]]" % (pagename, head, subsections[j]))
            # We don't continue here because we handle this case below
          elif head.endswith(U):
            msg("Page %s: Headword template head %s ends with explicit i3rab (U): [[%s]]" % (pagename, head, subsections[j]))
            # We don't continue here because we don't need to handle this case

          # Check for cpl
          # FIXME: Convert cpl into pl and fpl
          saw_cpl = False
          for param in headword_template.params:
            if re.match("cpl", unicode(param.name)):
              msg("Page %s: Headword template for head %s has cpl param in it, skipping: [[%s]]" % (pagename, head, subsections[j]))
              saw_cpl = True
              break
          if saw_cpl:
            continue

          # Check for empty head. If w/o explicit translit, skip; else,
          # fetch head from page title.
          if not head:
            if not blib.getparam(headword_template, "tr"):
              msg("Page %s: Headword template head is empty and without explicit translit, skipping: [[%s]]" % (pagename, subsections[j]))
              continue
            headword_template.add("1", page.title())

          # Now fetch the parameters from the headword template, removing
          # any that we want to remove, removing the i3rab -UN ending, and
          # adding any specified manual translit as a / annotation.

          def param_should_be_removed(param):
            name = unicode(param.name)
            if name == "sc" and unicode(param.value) == "Arab":
              return True
            for remove in removeparams:
              if name == remove:
                return True
              if re.match("^[a-z]+$", remove) and re.match("^%s[0-9]+$" % remove, name):
                return True
            return False

          # FIXME: Create manual declension for ذَقْن pl. ذُقُون "chin" else it
          # will be interpreted as strong masc pl
          def remove_i3rab(param):
            text = unicode(param)
            if text.endswith(UN):
              msg("Page %s: Removing i3rab from %s: %s" % (pagename, text,
                unicode(headword_template)))
            return re.sub(UN + "$", "", text)

          def trparam(name):
            if name == "1":
              return "tr"
            elif name.startswith("head"):
              return name.replace("head", "tr")
            else:
              return name + "tr"

          def process_param(param):
            arabic = remove_i3rab(param)
            tr = blib.getparam(headword_tempate, trparam(unicode(param.name)))
            if tr:
              return arabic + "/" + tr
            else:
              return arabic

          params = '|'.join([process_param(param) for param in headword_template.params if not param_should_be_removed(param)])
          if (tempname == "ar-noun-nisba" or tempname == "ar-nisba") and not blib.getparam(headword_template, "pl"):
            params += '|pl=smp'

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
          comments.append("added declension for %s %s" % (
            tempname, blib.getparam(headword_template, "1")))
          sections[i] = ''.join(subsections) + sectail
  newtext = pagehead + ''.join(sections) + pagetail
  comment = '; '.join(comments)
  assert((not comment) == (newtext == page.text))
  if newtext != page.text:
    if verbose:
      msg("Replacing [[%s]] with [[%s]]" % (page.text, newtext))
    page.text = newtext
    msg("For page %s, comment = %s" % (pagename, comment))
    if save:
      page.save(comment = comment)

def create_declensions(save, pos, tempname, decltempname, sgparam,
    startFrom, upTo, removeparams):
  for page in blib.references("Template:%s" % tempname, startFrom, upTo):
    create_declension(page, save, pos, tempname, decltempname, sgparam,
        removeparams)

pa = blib.init_argparser("Create Arabic declensions")

params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)

create_declensions(params.save, "Noun", "ar-noun", "ar-decl-noun",
    "sg", startFrom, upTo,
    ["2", "g2", "f", "m", "cons", "dobl", "plobl"])
create_declensions(params.save, "Noun", "ar-coll-noun", "ar-decl-coll-noun",
    "coll", startFrom, upTo,
    ["2", "g2", "singg", "cons", "dobl", "paucobl", "plobl"])
create_declensions(params.save, "Noun", "ar-sing-noun", "ar-decl-sing-noun",
    "sing", startFrom, upTo,
    ["2", "g2", "collg", "cons", "dobl", "paucobl", "plobl"])
create_declensions(params.save, "Adjective", "ar-nisba", "ar-decl-adj",
    "sg", startFrom, upTo,
    ["2", "g2", "collg", "cons", "dobl", "paucobl", "plobl"])
create_declensions(params.save, "Noun", "ar-noun-nisba", "ar-decl-noun",
    "sg", startFrom, upTo,
    ["2", "g2", "f", "m", "cons", "dobl", "plobl"])
create_declensions(params.save, "Adjective", "ar-adj", "ar-decl-adj",
    "sg", startFrom, upTo,
    ["el", "cons", "dobl", "cplobl", "plobl", "fplobl"])
