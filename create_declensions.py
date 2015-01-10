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
from blib import msg

import ar_translit

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
TAM = u"ة"
UNU = "[" + UN + U + "]"
UNUOPT = UNU + "?"

def remove_diacritics(word):
  return re.sub(u"[\u064B\u064C\u064D\u064E\u064F\u0650\u0651\u0652\u0670]", "", word)

def remove_links(text):
  text = re.sub(r"\[\[[^|\]]*?\|", "", text)
  text = re.sub(r"\[\[", "", text)
  text = re.sub(r"\]\]", "", text)
  return text

def reorder_shadda(text):
  # shadda+short-vowel (including tanwīn vowels, i.e. -an -in -un) gets
  # replaced with short-vowel+shadda during NFC normalisation, which
  # MediaWiki does for all Unicode strings; however, it makes the
  # detection process inconvenient, so undo it.
  return re.sub("(" + DIACRITIC_ANY_BUT_SH + ")" + SH, SH + r"\1", text)

# FIXME! This needs manual fixing:
# -- Create manual declension for ذَقْن pl. ذُقُون "chin" else it
#    will be interpreted as strong masc pl
# -- Cases where multiple heads and/or pl occur in phrases
# -- Cases where phrases of three or more words occur
# -- Error in translit for pl of عمود فقري
# -- various FIXME's below in `adjectival_phrases`
# -- Need to create manual declension tables for the remaining months,
#    for various reasons:
# -- This: ذو الحجة, دو القعدة (because of ذو)
# -- This: ربيع الآخر, ربيع الثاني (because the indefinite of الثاني is irregular, because there is bad i3rab in the other)
# -- This: جمادى الثاني (same as previous for الثاني, also because this is adjectival of a strange sort)
# -- This: جمادى الأولى (same as second reason of previous)
# -- This: جمادى الآخرة (same as previous)
# -- Make modifier example for كانون الثاني or maybe better كانون الأول
# -- Use عَمُود فَقْرِيّ as example of an adjectival modifier, plural is أَعْمِدَة فَقْرِيَّة

adjectival_phrases = [
    "كتابة لاتينية",
    "نقطة مزدوجة",
    "مرحلة زمنية",
    "حدث متكرر",
    "منظومة شمسية",
    "مدونة إلكترونية",
    "خيانة عظمى",
    "تين شوكي", # FIXME translit
    "فلفل أسود",
    "سنبل هندي", # FIXME nisba ending
"نحلة طنانة",
    "كوارك ساحر",
    "كوارك غريب",
    "جسيم مضاد",
    "وصفة طبية", # FIXME translit should be "waṣfa ṭibbiyya" and fix vowels
    "مادة مظلمة",
    "رياح شمسية",
    "رياح نجمية",
    "وحدة فلكية",
    "كيمياء حيوية",
    "كيمياء عضوية",
    "عادة سرية",
    "ثقب أسود",
    "اشتراكية ديمقراطية",
    "فعل صحيح",
    "فعل مضعف",
    "فعل مهموز",
    "فعل معتل",
    "فعل أجوف",
    "فعل ناقص",
    "أرقام هندية", # FIXME mark gender as plural
"كذا وكذا",
"نعناع فلفلي", # FIXME nisba ending
"حنطة سوداء",
"إبادة جماعية",
"إعداد ضماء", # FIXME DELETE THIS WORD, NOT ATTESTED
]

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

      # Go through each subsection
      for j in xrange(len(subsections)):
        # Look for subsections matching the given POS
        if j > 0 and (j % 2) == 0 and re.match("^===+%s===+\n" % pos, subsections[j - 1]):
          # Call reorder_shadda here so the templates we work with have
          # shadda in correct order but we don't mess with other text to
          # avoid unnecessary saving
          parsed = blib.parse_text(reorder_shadda(subsections[j]))

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
          def getp(param):
            return blib.getparam(headword_template, param)
          def putp(param, value):
            headword_template.add(param, value)
          head = getp("1")
          orighead = head

          # Check for declension already present
          if j + 1 < len(subsections) and re.match("^===+Declension===+\n", subsections[j + 1]):
            msg("Page %s: Declension already found for head %s, skipping: [[%s]]" % (pagename, head, subsections[j]))
            continue

          # Try to handle cases with a modifier; we can't handle all of them yet
          if ' ' in head:
            words = re.split(r"\s", remove_links(head))
            head = words[0]
            if len(words) > 2:
              msg("Page %s: Headword template head %s has two or more spaces in it, skipping: [[%s]]" % (pagename, orighead, subsections[j]))
              continue
            assert(len(words) == 2)

            # Check for params we don't yet know how to handle
            must_continue = False
            for badparam in ["pl", "pltr", "head2"]:
              if getp(badparam):
                # FIXME
                msg("Page %s: Headword template head %s has space in it and param %s, skipping: [[%s]]" % (pagename, orighead, badparam, subsections[j]))
                must_continue = True
                break
            if must_continue:
              continue

            # Now check for various types of construction, all either
            # construct (ʾidāfa) or adjectival

            def remove_gen_i3rab(word):
              if word.endswith(IN):
                msg("Page %s: Removing genitive i3rab (IN) from %s: %s" % (pagename, word, subsections[j]))
                return re.sub(IN + "$", "", word)
              if word.endswith(I):
                msg("Page %s: Removing genitive i3rab (I) from %s: %s" % (pagename, word, subsections[j]))
                return re.sub(I + "$", "", word)
              if re.search(DIACRITIC_ANY_BUT_SH + "$", word):
                msg("Page %s: FIXME: Strange diacritic at end of genitive %s: %s" % (pagename, word, subsections[j]))
              return word

            def remove_nom_i3rab(word):
              if word.endswith(UN):
                msg("Page %s: Removing nominative i3rab (UN) from %s: %s" % (pagename, word, subsections[j]))
                return re.sub(UN + "$", "", word)
              if word.endswith(U):
                msg("Page %s: Removing nominative i3rab (U) from %s: %s" % (pagename, word, subsections[j]))
                return re.sub(U + "$", "", word)
              if re.search(DIACRITIC_ANY_BUT_SH + "$", word):
                msg("Page %s: FIXME: Strange diacritic at end of nominative %s: %s" % (pagename, word, subsections[j]))
              return word

            idafa = False
            if not starts_with_al(words[0]) and starts_with_al(words[1]):
              # Found an ʾidāfa construction
              msg("Page %s: Headword template head %s has space in it and found ʾidāfa: [[%s]]" % (pagename, orighead, subsections[j]))
              idafa = True
              putp("1", words[0])
              putp("state", "con")
              putp("mod", remove_al(words[1]))
              putp("modstate", "def")
              putp("modcase", "gen")
              putp("modnumber", sgparam)
            elif starts_with_al(words[0]) and starts_with_al(words[1]):
              msg("Page %s: Headword template head %s has space in it and found definite adjective construction: [[%s]]" % (pagename, orighead, subsections[j]))
              putp("1", remove_al(words[0]))
              putp("state", "def")
              putp("mod", remove_al(words[1]))
            elif (not starts_with_al(words[0]) and not starts_with_al(words[1])
                and words[1].endswith(I + Y)):
              msg("Page %s: Headword template head %s has space in it and appears to end in badly formatted nisba, FIXME, skipping: [[%s]]" % (pagename, orighead, subsections[j]))
              continue
            elif (not starts_with_al(words[0]) and not starts_with_al(words[1])
                and words[1].endswith(I + Y + SH)):
              msg("Page %s: Headword template head %s has space in it and found indefinite adjective nisba construction: [[%s]]" % (pagename, orighead, subsections[j]))
              putp("1", words[0])
              putp("state", "ind,def")
              putp("mod", words[1])
            elif (not starts_with_al(words[0]) and not starts_with_al(words[1])
                and pagename in adjectival_phrases):
              msg("Page %s: Headword template head %s has space in it, indefinite, and manually specified to be adjectival: [[%s]]" % (pagename, orighead, subsections[j]))
              putp("1", words[0])
              putp("state", "ind,def")
              putp("mod", words[1])
            else:
              msg("Page %s: Headword template head %s has space in it, indefinite, and not specified to be adjectival, assuming ʾidāfa: [[%s]]" % (pagename, orighead, subsections[j]))
              idafa = True
              putp("1", words[0])
              putp("state", "con")
              putp("mod", words[1])
              putp("modstate", "ind")
              putp("modcase", "gen")
              putp("modnumber", sgparam)

            # Now remove any i3rab diacritics
            putp("1", remove_nom_i3rab(getp("1")))
            if idafa:
              putp("mod", remove_gen_i3rab(getp("mod")))
            else:
              putp("mod", remove_nom_i3rab(getp("mod")))

            # Now check if the expression is plural
            if getp("2") == "p":
              msg("Page %s: Headword template head %s has space in it and is plural: [[%s]]" % (pagename, orighead, subsections[j]))
              putp("pl", getp("1"))
              putp("1", "-")
              if not idafa:
                putp("modpl", getp("mod"))
                putp("mod", "-")

            # Now check if there's manual translit. We need to split the
            # manual translit in two and pair up manual translit with
            # corresponding Arabic words. But first remove -t indicating
            # construct state, and check to see if manual translit is
            # same as auto translit, in which case it's unnecessary.
            if getp("tr"):
              msg("Page %s: Headword template head %s has space in it and manual translit: [[%s]]" % (pagename, orighead, subsections[j]))
              trwords = re.split(r"\s", getp("tr"))
              assert(len(trwords) == 2)
              if getp("2") == "p":
                # FIXME (doesn't occur though)
                msg("Page %s: Headword template head %s has space in it and manual translit and is plural, skipping: [[%s]]" % (pagename, orighead, subsections[j]))
                continue
              if words[0].endswith(TAM) and trwords[0].endswith("t"):
                trwords[0] = trwords[0][0:-1]
              if words[0].endswith(ALIF + TAM) and not trwords[0].endswith("h"):
                trwords[0] += "h"
              if ar_translit.tr(words[0]) != trwords[0]:
                msg("Page %s: Headword template head %s has space in it and manual translit %s which is different from auto-translit of %s: [[%s]]" % (pagename, orighead, trwords[0], words[0], subsections[j]))
                putp("1", "%s/%s" % (getp("1"), trwords[0]))
              else:
                msg("Page %s: Headword template head %s has space in it and manual translit %s which is same as auto-translit of %s: [[%s]]" % (pagename, orighead, trwords[0], words[0], subsections[j]))
              if ar_translit.tr(words[1]) != trwords[1]:
                msg("Page %s: Headword template head %s has space in it and manual translit %s which is different from auto-translit of %s: [[%s]]" % (pagename, orighead, trwords[1], words[1], subsections[j]))
                putp("mod", "%s/%s" % (getp("mod"), trwords[1]))
              else:
                msg("Page %s: Headword template head %s has space in it and manual translit %s which is same as auto-translit of %s: [[%s]]" % (pagename, orighead, trwords[1], words[1], subsections[j]))

          # no space in head
          else:
            if '[' in head or ']' in head or '|' in head:
              msg("Page %s: Headword template head %s has link in it: [[%s]]" % (pagename, head, subsections[j]))
              head = remove_links(words[0])
              putp("1", head)
            if starts_with_al(head):
              msg("Page %s: Headword template head %s starts with definite article: [[%s]]" % (pagename, head, subsections[j]))
              head = remove_al(words[0])
              putp("1", head)
              def check_for_al(param):
                value = blib.getparam(headword_template, param)
                if value:
                  putp(param, remove_al(value))
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
            if not getp("tr"):
              msg("Page %s: Headword template head is empty and without explicit translit, skipping: [[%s]]" % (pagename, subsections[j]))
              continue
            putp("1", pagename)

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
          if (tempname == "ar-noun-nisba" or tempname == "ar-nisba") and not getp("pl"):
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
          comments.append("added declension for %s %s" % (tempname,
            remove_links(orighead) or "%s/%s" % (pagename, getp("tr"))))
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
