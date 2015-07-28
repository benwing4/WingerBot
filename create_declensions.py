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

# اِضْمَحَلَّ Form XII? "to disappear, vanish, dwindle, fade away, melt away; to decrease, become less"

import re

import blib, pywikibot
from blib import msg, getparam, addparam, remove_links
from arabiclib import *

import ar_translit

site = pywikibot.Site()

verbose = True

# FIXME! This needs manual fixing:
# -- Cases where multiple heads and/or pl occur in phrases
# -- Cases where phrases of three or more words occur
# -- Make modifier example for كانون الثاني or maybe better كانون الأول
# -- Use عَمُود فَقْرِيّ as example of an adjectival modifier, plural is أَعْمِدَة فَقْرِيَّة

adjectival_phrases = [
    u"كتابة لاتينية",
    u"نقطة مزدوجة",
    u"مرحلة زمنية",
    u"حدث متكرر",
    u"منظومة شمسية",
    u"مدونة إلكترونية",
    u"خيانة عظمى",
    u"فلفل أسود",
    u"نحلة طنانة",
    u"كوارك ساحر",
    u"كوارك غريب",
    u"جسيم مضاد",
    u"وصفة طبية",
    u"مادة مظلمة",
    u"رياح شمسية",
    u"رياح نجمية",
    u"وحدة فلكية",
    u"كيمياء حيوية",
    u"كيمياء عضوية",
    u"عادة سرية",
    u"ثقب أسود",
    u"اشتراكية ديمقراطية",
    u"فعل صحيح",
    u"فعل مضعف",
    u"فعل مهموز",
    u"فعل معتل",
    u"فعل أجوف",
    u"فعل ناقص",
    u"أرقام هندية",
    u"كذا وكذا",
    u"حنطة سوداء",
    u"إبادة جماعية",
]

# Create or insert declension sections in a given page. POS is the part of
# speech of the word (capitalized, e.g. "Noun"). Only save the changed page
# if SAVE is true. TEMPNAME is the name of the headword template, e.g.
# "ar-noun"; DECLTEMPNAME is the corresponding name of the declension template,
# e.g. "ar-decl-noun". SGNUM is the number (possible value of 'number')
# corresponding to the singular (either 'sg', 'coll' or 'sing').
# REMOVEPARAMS is a list of parameters to remove from the headword template
# when creating the declension template. Parameters that are all alphabetic
# are expanded so that e.g. "f" will also remove parameters named
# "f2", "f3", "f4", etc. and "ftr", "f2tr", "f3tr", etc.
def create_declension(page, index, save, pos, tempname, decltempname, sgnum,
    removeparams, is_proper=False):
  pagename = page.title()
  comments = []

  def pgmsg(text):
    msg("Page %s %s: %s" % (index, pagename, text))

  # Starts with definite article al-
  def starts_with_al(text):
    return re.match(ALIF_ANY + A + "?" + L, text)

  def sub_if(fr, to, text):
    if re.search(fr, text):
      return re.sub(fr, to, text)
    else:
      return ""

  # Remove definite article al- from text
  def remove_al(text):
    return (sub_if("^" + ALIF_ANY + A + "?" + L + SK + "?(.)" + SH, r"\1", text)
        or sub_if("^" + ALIF_ANY + A + "?" + L + SK + "?", "", text)
        or text)

  # Remove definite article al- from transliterated text
  def remove_al_tr(text):
    return (sub_if(ur"^a?([sšṣtṯṭdḏḍzžẓnrḷ])-\1", r"\1", text) or
        sub_if("^a?l-", "", text) or
        text)

  # Split off interwiki links at end
  m = re.match(r"^(.*?\n+)((\[\[[a-z0-9_\-]+:[^\]]+\]\]\n*)*)$",
      page.text, re.S)
  if m:
    pagebody = m.group(1)
    pagetail = m.group(2)
  else:
    pagebody = page.text
    pagetail = ""

  # Split top-level sections (by language)
  splitsections = re.split("(^==[^=\n]+==\n)", pagebody, 0, re.M)

  # Extract off head and recombine section headers with following text
  pagehead = splitsections[0]
  sections = []
  for i in xrange(1, len(splitsections)):
    if (i % 2) == 1:
      sections.append("")
    sections[-1] += splitsections[i]

  # Look for Arabic section
  for seci in xrange(len(sections)):
    m = re.match("^==([^=\n]+)==$", sections[seci], re.M)
    if not m:
      pgmsg("Can't find language name in text: [[%s]]" % (sections[seci]))
    elif m.group(1) == "Arabic":
      # Extract off trailing separator
      mm = re.match(r"^(.*?\n+)(--+\n*)$", sections[seci], re.S)
      if mm:
        secbody = mm.group(1)
        sectail = mm.group(2)
      else:
        secbody = sections[seci]
        sectail = ""

      # Split into subsections based on headers
      subsections = re.split("(^===+[^=\n]+===+\n)", secbody, 0, re.M)

      # Go through each subsection
      for j in xrange(len(subsections)):
        notes = []

        def add_note(note):
          if note not in notes:
            notes.append(note)

        # Look for subsections matching the given POS
        if j > 0 and (j % 2) == 0 and re.match("^===+%s===+\n" % pos, subsections[j - 1]):
          # Call reorder_shadda here so the templates we work with have
          # shadda in correct order but we don't mess with other text to
          # avoid unnecessary saving
          parsed = blib.parse_text(reorder_shadda(subsections[j]))

          def pagemsg(text):
            pgmsg("%s: [[%s]]" % (text, subsections[j]))

          # Check for various conditions causing us to skip this entry and
          # not try to add a declension table

          # Skip declension if certain templates found in definition.
          # We don't check for {{alternative form of|...}}, because it's
          # used for e.g. different ways of spelling "camera" in Arabic,
          # some with -ā and some with -a, so we still want to create
          # declensions for those.
          altspelling_templates = [temp for temp in parsed.filter_templates() if temp.name in
              ["alternative spelling of"]]
          if len(altspelling_templates) > 0:
            pagemsg("Alternative spelling redirect found in text, skipping")
            continue
          if pos == "Adjective":
            feminine_of_templates = [temp for temp in parsed.filter_templates() if temp.name in
                ["feminine of"]]
            if len(feminine_of_templates) > 0:
              pagemsg("feminine-of template found for adjective, skipping")
              continue

          # Retrieve headword_template, make sure exactly one and it is the right type
          headword_templates = [temp for temp in parsed.filter_templates() if temp.name in
              ["ar-noun", "ar-proper noun", "ar-coll-noun", "ar-sing-noun",
                "ar-noun-pl", "ar-noun-dual", "ar-adj-fem", "ar-adj-pl",
                "ar-noun-inf-cons", "ar-adj-inf-def",
                "ar-adj-dual", "ar-adj", "ar-nisba", "ar-noun-nisba",
                "ar-adj-sound", "ar-adj-in", "ar-adj-an"]]
          if len(headword_templates) == 0:
            pagemsg("WARNING: Can't find headword template in text, skipping")
            continue
          if len(headword_templates) > 1:
            pagemsg("WARNING: Found multiple headword templates in text, skipping")
            continue
          headword_template = headword_templates[0]
          if headword_template.name != tempname:
            pagemsg("Headword template should be '%s' but is '%s', skipping" % (tempname, headword_template.name))
            continue
          def getp(param):
            return getparam(headword_template, param)
          # NOTE: We physically add and remove parameters from the headword
          # template to get the list of parameters to use in creating the
          # declension template. These changes don't get propagated to the
          # headword template because we don't convert the parsed text back
          # to a string.
          def putp(param, value):
            addparam(headword_template, param, value)
          head = getp("1")
          orighead = head

          # Check for declension already present
          if (j + 1 < len(subsections) and
              re.match("^===+Declension===+\n", subsections[j + 1])
              or j + 3 < len(subsections) and
              re.match("^===+Usage", subsections[j + 1]) and
              re.match("^===+Declension===+\n", subsections[j + 3])
              ):
            pagemsg("Declension already found for head %s, skipping" % head)
            continue

          # Check for cpl
          # FIXME: Convert cpl into pl and fpl
          if getp("cpl"):
            pagemsg("WARNING: Headword template for head %s has cpl param in it, skipping" % (head))
            continue

          # Check for empty head. If w/o explicit translit, skip; else,
          # fetch head from page title.
          if not head:
            if not getp("tr"):
              pagemsg("WARNING: Headword template head is empty and without explicit translit, skipping")
              continue
            else:
              pagemsg("Headword template head is empty but has explicit translit")
              add_note("empty head, using page name")
            head = pagename
            putp("1", head)

          # Try to handle cases with a modifier; we can't handle all of them yet
          headspace = False
          if ' ' in head:
            headspace = True
            words = re.split(r"\s", remove_links(head))
            head = words[0]
            if len(words) > 2:
              pagemsg("WARNING: Headword template head %s has two or more spaces in it, skipping" % orighead)
              continue
            assert(len(words) == 2)

            # Check for params we don't yet know how to handle
            must_continue = False
            for badparam in ["pl2", "pltr", "head2", "sing", "coll"]:
              if getp(badparam):
                # FIXME
                pagemsg("WARNING: Headword template head %s has space in it and param %s, skipping" % (orighead, badparam))
                must_continue = True
                break
            if must_continue:
              continue

            # Now check for various types of construction, all either
            # construct (ʾidāfa) or adjectival

            def remove_nom_gen_i3rab(word, nomgen, undia, undiatext, udia, udiatext):
              if word.endswith(undia):
                pagemsg("Removing %s i3rab (%s) from %s" % (nomgen, undiatext, word))
                add_note("removing %s i3rab (%s)" % (nomgen, undiatext))
                return re.sub(undia + "$", "", word)
              if word.endswith(udia):
                pagemsg("Removing %s i3rab (%s) from %s" % (nomgen, udiatext, word))
                add_note("removing %s i3rab (%s)" % (nomgen, udiatext))
                return re.sub(udia + "$", "", word)
              if re.search(DIACRITIC_ANY_BUT_SH + "$", word):
                pagemsg("WARNING: Strange diacritic at end of %s %s" % (nomgen, word))
              if word[0] == ALIF_WASLA:
                pagemsg("Changing %s alif wasla to plain alif for %s" % (nomgen, word))
                add_note("changing %s alif wasla to plain alif" % (nomgen))
                word = ALIF + word[1:]
              return word

            def remove_gen_i3rab(word):
              return remove_nom_gen_i3rab(word, "genitive", IN, "IN", I, "I")

            def remove_nom_i3rab(word):
              return remove_nom_gen_i3rab(word, "nominative", UN, "UN", U, "U")

            def remove_gen_i3rab_tr(word):
              return remove_nom_gen_i3rab(word, "genitive", "in", "in", "i", "i")

            def remove_nom_i3rab_tr(word):
              return remove_nom_gen_i3rab(word, "nominative", "un", "un", "u", "u")

            idafa = False
            word0al = starts_with_al(words[0])
            word1al = starts_with_al(words[1])
            words[0] = remove_al(words[0])
            words[1] = remove_al(words[1])
            putp("1", words[0])
            putp("mod", words[1])
            if word0al and word1al:
              pagemsg("Headword template head %s has space in it and found definite adjective construction" % (orighead))
              add_note("modifier definite adjective construction")
              putp("state", "def")
            elif word0al and not word1al:
              pagemsg("WARNING: Headword template head %s has space in it and found al-X + Y construction, can't handle, skipping" % (orighead))
              continue
            elif is_proper:
              if words[0].endswith(ALIF) and word1al:
                pagemsg("Proper noun headword template head %s has space in it and found ind-def with definite adjectival modifier" % (orighead))
                add_note("modifier proper noun + definite adjective construction")
                putp("state", "ind-def")
              elif remove_diacritics(words[0]) == u"جمهورية":
                if word1al:
                  pagemsg("Proper noun headword template head %s has space in it and found definite idafa" % (orighead))
                  add_note("modifier definite idafa construction")
                  idafa = True
                  assert sgnum == "sg"
                  idafaval = "def"
                  putp("idafa", idafaval)
                elif words[1].endswith(ALIF):
                  pagemsg("Proper noun headword template head %s has space in it and found idafa with ind-def modifier" % (orighead))
                  add_note("modifier proper-noun ind-def idafa construction")
                  assert sgnum == "sg"
                  idafaval = "ind-def"
                  putp("idafa", idafaval)
                else:
                  pagemsg("WARNING: Proper noun headword template head %s has space in it and found idafa construction we can't handle, skipping" % (orighead))
                  continue
              else:
                  pagemsg("WARNING: Proper noun headword template head %s has space in it and can't determine whether idafa, skipping" % (orighead))
                  continue

            elif not word0al and word1al:
              # Found an ʾidāfa construction
              pagemsg("Headword template head %s has space in it and found definite idafa" % (orighead))
              add_note("modifier definite idafa construction")
              idafa = True
              idafaval = "def-" + sgnum
              if idafaval == "def-sg":
                idafaval = "def"
              putp("idafa", idafaval)
            elif words[1].endswith(I + Y):
              pagemsg("WARNING: Headword template head %s has space in it and appears to end in badly formatted nisba, FIXME, skipping" % (orighead))
              continue
            elif words[1].endswith(I + Y + SH):
              pagemsg("Headword template head %s has space in it and found indefinite adjective nisba construction" % (orighead))
              add_note("modifier indefinite nisba adjective construction")
            elif pagename in adjectival_phrases:
              pagemsg("Headword template head %s has space in it, indefinite, and manually specified to be adjectival" % (orighead))
              add_note("modifier indefinite adjective construction")
            else:
              pagemsg("Headword template head %s has space in it, indefinite, and not specified to be adjectival, assuming idafa" % (orighead))
              add_note("modifier indefinite idafa construction")
              idafa = True
              putp("idafa", sgnum)

            # Now remove any i3rab diacritics
            putp("1", remove_nom_i3rab(getp("1")))
            if idafa:
              putp("mod", remove_gen_i3rab(getp("mod")))
            else:
              putp("mod", remove_nom_i3rab(getp("mod")))

            # Now check if the lemma is plural
            if re.match(r"\bp\b", getp("2")):
              pagemsg("Headword template head %s has space in it and is plural" % (orighead))
              add_note("plural lemma")
              if getp("tr"):
                # FIXME (doesn't occur though)
                pagemsg("WARNING: Headword template head %s has space in it and manual translit and is plural, skipping" % (orighead))
                continue
              putp("pl", getp("1"))
              putp("1", "-")
              if not idafa:
                putp("modpl", getp("mod"))
                putp("mod", "-")

            # Now check if lemma has plural specified
            elif getp("pl"):
              pls = re.split(r"\s", remove_links(getp("pl")))
              assert(len(pls) == 2)
              pls[0] = remove_al(pls[0])
              pls[1] = remove_al(pls[1])
              putp("pl", remove_nom_i3rab(pls[0]))
              if not idafa:
                putp("modpl", remove_nom_i3rab(pls[1]))
              else:
                if pls[1] != getp("mod"):
                  pagemsg("FIXME: Headword template head %s, plural modifier %s not same as singular modifier %s in idafa construction" % (orighead, pls[1], getp("mod")))

            # Now check if there's manual translit. We need to split the
            # manual translit in two and pair up manual translit with
            # corresponding Arabic words. But first remove -t indicating
            # construct state, and check to see if manual translit is
            # same as auto translit, in which case it's unnecessary.
            if getp("tr"):
              pagemsg("Headword template head %s has space in it and manual translit" % (orighead))
              trwords = re.split(r"\s", getp("tr"))
              assert(len(trwords) == 2)
              trwords[0] = remove_nom_i3rab_tr(remove_al_tr(trwords[0]))
              if idafa:
                trwords[1] = remove_gen_i3rab_tr(remove_al_tr(trwords[1]))
              else:
                trwords[1] = remove_nom_i3rab_tr(remove_al_tr(trwords[1]))
              # Remove any extraneous -t from translit, either from construct
              # state of from removal of i3rab in a feminine noun/adj.
              for i in [0, 1]:
                if words[i].endswith(TAM) and trwords[i].endswith("t"):
                  trwords[i] = trwords[i][0:-1]
                if words[i].endswith(ALIF + TAM) and not trwords[i].endswith("h"):
                  trwords[i] += "h"
              if ar_translit.tr(words[0]) != trwords[0]:
                pagemsg("Headword template head %s has space in it and manual translit %s which is different from auto-translit of %s" % (orighead, trwords[0], words[0]))
                add_note("modified head w/manual translit")
                putp("1", "%s/%s" % (getp("1"), trwords[0]))
              else:
                pagemsg("Headword template head %s has space in it and manual translit %s which is same as auto-translit of %s" % (orighead, trwords[0], words[0]))
                add_note("modified head w/ignored manual translit")
              if ar_translit.tr(words[1]) != trwords[1]:
                pagemsg("Headword template head %s has space in it and manual translit %s which is different from auto-translit of %s" % (orighead, trwords[1], words[1]))
                add_note("modifier w/manual translit")
                putp("mod", "%s/%s" % (getp("mod"), trwords[1]))
              else:
                pagemsg("Headword template head %s has space in it and manual translit %s which is same as auto-translit of %s" % (orighead, trwords[1], words[1]))
                add_note("modifier w/ignored manual translit")

          else:
            # no space in head, not dealing with a modifier

            # If has link in it, just remove it
            if '[' in head or ']' in head or '|' in head:
              pagemsg("Headword template head %s has link in it" % (head))
              add_note("removed links from head")
              head = remove_links(head)
              putp("1", head)

            # If starts with definite article, remove article from everything,
            # including transliterations, and set state=def
            if starts_with_al(head):
              pagemsg("Headword template head %s starts with definite article" % (head))
              add_note("definite lemma")
              head = remove_al(head)
              putp("1", head)
              putp("state", "def")
              # Also remove al- from remaining head and pl params
              def check_for_al(param):
                param = remove_links(param)
                value = getparam(headword_template, param)
                if value:
                  if '[' in value or ']' in value or '|' in value:
                    pagemsg("Param %s value %s has link in it" % (param, value))
                    add_note("removed links from %s" % param)
                    value = remove_links(value)
                  putp(param, remove_al(value))
              params_to_check = ["pl", "sing", "coll", "pauc", "f", "fpl"]
              for param in params_to_check:
                check_for_al(param)
              for i in xrange(2, 10):
                check_for_al("head%s" % i)
                for param in params_to_check:
                  check_for_al("%s%s" % (param, i))
              # Also remove al- from transliteration
              def check_for_al_tr(param):
                value = getparam(headword_template, param)
                if value:
                  putp(param, remove_al_tr(value))
              check_for_al("tr")
              for param in params_to_check:
                check_for_al("%str" % param)
              for i in xrange(2, 10):
                check_for_al("tr%s" % i)
                for param in params_to_check:
                  check_for_al("%s%str" % (param, i))
            elif is_proper:
              if head.endswith(ALIF):
                pagemsg(u"Headword template head %s ends in -ā" % (head))
                putp("state", "ind-def")
              else:
                pagemsg(u"WARNING: Headword template head %s is indefinite proper noun, not ending in -ā, skipping" % (head))
                continue

            if head.endswith(UN):
              pagemsg("Headword template head %s ends with explicit i3rab (UN)" % (head))
              add_note("head has explicit i3rab (UN)")
              # We don't continue here because we handle this case below
            elif head.endswith(U):
              pagemsg("Headword template head %s ends with explicit i3rab (U)" % (head))
              add_note("head has explicit i3rab (U)")
              # We don't continue here because we don't need to handle this case

            # Now check if the lemma is plural
            if re.match(r"\bp\b", getp("2")):
              pagemsg("Headword template head %s is plural" % (head))
              add_note("plural lemma")
              if getp("tr"):
                # FIXME (doesn't occur though)
                pagemsg("WARNING: Headword template head %s has manual translit and is plural, skipping" % (head))
                continue
              putp("pl", getp("1"))
              putp("1", "-")

          # Now fetch the parameters from the headword template, removing
          # any that we want to remove, removing the i3rab -UN ending, and
          # adding any specified manual translit as a / annotation.

          def param_should_be_removed(param):
            name = unicode(param.name)
            if name == "sc" and unicode(param.value) == "Arab":
              return True
            if name.endswith("tr"):
              return True
            for remove in removeparams:
              if name == remove:
                return True
              if re.match("^[a-z]+$", remove) and re.match("^%s([0-9]+)?$" % remove, name):
                return True
            return False

          def remove_i3rab(param):
            text = unicode(param)
            if text.endswith(UN):
              pgmsg("Removing i3rab from %s: %s" % (text,
                unicode(headword_template)))
              add_note("removing i3rab")
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
            # Value of + is used in ar-nisba, ar-noun-nisba, ar-adj-in
            # to signal the strong plural.
            if arabic.endswith("=+"):
              newarabic = re.sub(r"=\+$", "=sp", arabic)
              pgmsg("Converting %s to %s: %s" % (arabic,
                newarabic, unicode(headword_template)))
              arabic = newarabic
            # Value of - is used in ar-adj-in to signal an unknown
            # feminine plural.
            if arabic.endswith("=-"):
              newarabic = re.sub(r"=-$", "=?", arabic)
              pgmsg("Converting %s to %s: %s" % (arabic,
                newarabic, unicode(headword_template)))
              arabic = newarabic
            # Don't process translit in modifier constructions, where the
            # translit is also processed.
            if not headspace:
              tr = getparam(headword_template, trparam(unicode(param.name)))
              if tr:
                return arabic + "/" + tr
            return arabic

          params = '|'.join([process_param(param) for param in headword_template.params if not param_should_be_removed(param)])
          # For templates that automatically supply the masculine plural,
          # supply it here, too if not overridden.
          if tempname in ["ar-nisba", "ar-noun-nisba", "ar-adj-sound", "ar-adj-an"] and not getp("pl"):
            params += '|pl=sp'

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
          comment = "added declension for %s %s" % (tempname,
            remove_links(orighead) or "%s/%s" % (pagename, getp("tr")))
          note = ', '.join(notes)
          if note:
            comment = "%s (%s)" % (comment, note)
          comments.append(comment)
          sections[seci] = ''.join(subsections) + sectail
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

def create_declensions(save, pos, tempname, decltempname, sgnum,
    startFrom, upTo, removeparams, is_proper=False):
  for page, index in blib.references("Template:%s" % tempname, startFrom, upTo):
    create_declension(page, index, save, pos, tempname, decltempname, sgnum,
        removeparams, is_proper=is_proper)

pa = blib.init_argparser("Create Arabic declensions")
pa.add_argument("--proper", action='store_true',
    help="Do proper nouns only")

params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)

params_to_remove = [
    "2", # gender; not included in declension tables
    "g2", # second gender; not included in declension tables
    "singg", # singulative gender; not included in declension tables
    "collg", # collective gender; not included in declension tables
    "tr", # transliterations; we check for them in the declension code and
          # handle them specially
    "cons", # construct state; always predictable and we do it
    "dcons", # dual construct state; always predictable and we do it
    "pauccons", # paucal construct state; always predictable and we do it
    "plcons", # plural construct state; always predictable and we do it
    "cplcons", # common plural construct state; always predictable and we do it
    "fplcons", # feminine plural construct state; always predictable and we do it
    "inf", # informal; always predictable and we do it
    "dinf", # dual informal; always predictable and we do it
    "paucinf", # paucal informal; always predictable and we do it
    "plinf", # plural informal; always predictable and we do it
    "cplinf", # common plural informal; always predictable and we do it
    "fplinf", # feminine plural informal; always predictable and we do it
    "obl", # oblique; always predictable and we do it
    "dobl", # dual oblique; always predictable and we do it
    "paucobl", # paucal oblique; always predictable and we do it
    "plobl", # plural oblique; always predictable and we do it
    "cplobl", # common plural oblique; always predictable and we do it
    "fplobl", # feminine plural oblique; always predictable and we do it
    "el" # adjectival elative; not included in declension tables
]

non_gendered_params_to_remove = params_to_remove + [
    "f", "m" # masculine, feminine; not included in non-gendered declension
             # table (FIXME, perhaps instead we should generate a gendered
             # declension table)
]

if not params.proper:
  create_declensions(params.save, "Noun", "ar-noun", "ar-decl-noun",
      "sg", startFrom, upTo, non_gendered_params_to_remove)
  create_declensions(params.save, "Noun", "ar-coll-noun", "ar-decl-coll-noun",
      "coll", startFrom, upTo, non_gendered_params_to_remove)
  create_declensions(params.save, "Noun", "ar-sing-noun", "ar-decl-sing-noun",
      "sing", startFrom, upTo, non_gendered_params_to_remove)
  create_declensions(params.save, "Noun", "ar-noun-nisba", "ar-decl-gendered-noun",
      "sg", startFrom, upTo, params_to_remove)
  for adj_template in ["ar-adj", "ar-nisba", "ar-adj-sound", "ar-adj-in",
      "ar-adj-an"]:
    create_declensions(params.save, "Adjective", adj_template, "ar-decl-adj",
        "sg", startFrom, upTo, params_to_remove)
create_declensions(params.save, "Proper noun", "ar-proper noun", "ar-decl-noun",
    "sing", startFrom, upTo, non_gendered_params_to_remove,
    is_proper=True)
