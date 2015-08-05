#!/usr/bin/env python
#coding: utf-8

#    make_number_entries.py is free software: you can redistribute it and/or modify
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

import ar_translit
from arabiclib import *

site = pywikibot.Site()

class Number(object):
  def __init__(self, eastarabnum, english, nom, femnom=None, obl=None,
      femobl=None, ord=None):
    nom = reorder_shadda(nom)
    if not femnom:
      if nom.endswith(AH):
        femnom = re.sub(AH + "$", "", nom)
      else:
        femnom = nom
    if not obl:
      if nom.endswith(UUN):
        obl = re.sub(UUN + "$", IIN, nom)
      else:
        obl = nom
    femnom = reorder_shadda(femnom)
    if not femobl:
      if femnom.endswith(UUN):
        femobl = re.sub(UUN + "$", IIN, femnom)
      else:
        femobl = femnom
    self.eastarabnum = eastarabnum
    self.english = english
    self.nom = nom
    self.nomtr = ar_translit.tr(nom)
    self.femnom = femnom
    self.femnomtr = ar_translit.tr(femnom)
    self.obl = obl
    self.obltr = ar_translit.tr(obl)
    self.femobl = femobl
    self.femobltr = ar_translit.tr(femobl)
    if ord:
      if len(ord) == 5:
        self.ordroot, self.ordeng, self.cardteeneng, self.ordlemma, \
            self.cardteen = ord
      else:
        self.ordroot, self.ordeng, self.cardteeneng = ord
        self.ordlemma = (self.ordroot[0] + AA + self.ordroot[1] + I +
            self.ordroot[2])
        self.cardteen = self.nom + A + u" عَشَرَ"
      self.femordlemma = (self.ordroot[0] + AA + self.ordroot[1] + I +
          self.ordroot[2] + AH)
      self.ordteen = (self.ordroot[0] + AA + self.ordroot[1] + I +
          self.ordroot[2] + A + u" عَشَرَ")
      self.femordteen = self.femordlemma + A + u" عَشْرَةَ"
      self.ordteeneng = ("twelfth" if self.cardteeneng == "twelve" else
          "twentieth" if self.cardteeneng == "twenty" else
          self.cardteeneng + "th")

digits = {1:Number(u"١", "one", u"وَاحِد", u"وَاحِدَة",
            ord=[u"حدي", "first (combining form)", "eleven", u"حَادٍ",
              u"أَحَدَ عََشَرَ"]),
          2:Number(u"٢", "two", u"اِثْنَان", u"اِثْنَتَان", u"اِثْنَيْن", u"اِثْنَتَيْن",
            ord=[u"ثني", "second", "twelve", u"ثَانٍ",
              u"اِثْنَا عَشَرَ"]),
          3:Number(u"٣", "three", u"ثَلَاثَة",
            ord=[u"ثلث", "third", "thirteen"]),
          4:Number(u"٤", "four", u"أَرْبَعَة",
            ord=[u"ربع", "fourth", "fourteen"]),
          5:Number(u"٥", "five", u"خَمْسَة",
            ord=[u"خمس", "fifth", "fifteen"]),
          6:Number(u"٦", "six", u"سِتَّة",
            ord=[u"سدس", "sixth", "sixteen"]),
          7:Number(u"٧", "seven", u"سَبْعَة",
            ord=[u"سبع", "seventh", "seventeen"]),
          8:Number(u"٨", "eight", u"ثَمَانِيَة", u"ثَمَانٍ",
            ord=[u"ثمن", "eighth", "eighteen"]),
          9:Number(u"٩", "nine", u"تِسْعَة",
            ord=[u"تسع", "ninth", "nineteen"]),
          10:Number(u"١٠", "ten", u"عَشَرَة",
            ord=[u"عشر", "tenth", "twenty"]),
         }
tens = { #10:Number(u"١٠", "ten", u"عَشَرَة", u"عَشْر"),
         20:Number(u"٢٠", "twenty", u"عِشْرُون"),
         30:Number(u"٣٠", "thirty", u"ثَلَاثُون"),
         40:Number(u"٤٠", "forty", u"أَرْبَعُون"),
         50:Number(u"٥٠", "fifty", u"خَمْسُون"),
         60:Number(u"٦٠", "sixty", u"سِتُّون"),
         70:Number(u"٧٠", "seventy", u"سسَبْعُون"),
         80:Number(u"٨٠", "eighty", u"ثَمَانُون"),
         90:Number(u"٩٠", "ninety", u"تِسْعُون")}

def iter_numerals():
  for tenval, ten in sorted(tens.iteritems(), key=lambda x:x[0]):
    for digval, dig in sorted(digits.iteritems(), key=lambda x:x[0]):
      if digval != 10:
        yield (tenval, ten, digval, dig)

# ==Arabic==
#
# ===Etymology===
# Literally "nine and twenty", from {{m|ar|تِسْعَة}} and {{m|ar|عِشْرُون}}.
#
# ===Numeral===
# {{ar-numeral|تِسْعَة وَعِشْرُون|m|tr=tisʿa wa-ʿišrūn|f=تِسْع وَعِشْرُون|ftr=tisʿ wa-ʿišrūn|obl=تِسْعَة وَعِشْرِين|obltr=tisʿa wa-ʿišrīn|fobl=تِسْع وَعِشْرِين|fobltr=tisʿ wa-ʿišrīn}}
#
# # [[twenty-nine]]
# #: Eastern Arabic numeral: {{l|ar|٢٩}}
#
# ====Declension====
# {{ar-decl-numeral|-|pl=تِسْعَة|fpl=تِسْع|mod=-|modpl=عِشْرُون|modfpl=عِشْرُون|modprefix=وَ/wa-|state=ind,def}}
#
# ====Coordinate terms====
# * Last: {{l|ar|ثَمَانِيَة وَعِشْرُون|tr=ṯamāniya wa-ʿišrūn}} (or {{lang|ar|٢٨}} = 28)
# * Next: {{l|ar|ثَلَاثُون}} (or {{lang|ar|٣٠}} = 30)

def create_lemma(tenval, ten, digval, dig):
  pagename = u"%s وَ%s" % (dig.nom, ten.nom)
  etym = """Literally "%s and %s", from {{m|ar|%s}} and {{m|ar|%s}}.""" % (
      (dig.english, ten.english, dig.nom, ten.nom))
  headword = u"""{{ar-numeral|%s|m|tr=%s wa-%s|f=%s وَ%s|ftr=%s wa-%s|obl=%s وَ%s|obltr=%s wa-%s|fobl=%s وَ%s|fobltr=%s wa-%s}}""" % (
      pagename, dig.nomtr, ten.nomtr,
      dig.femnom, ten.femnom, dig.femnomtr, ten.femnomtr,
      dig.obl, ten.obl, dig.obltr, ten.obltr,
      dig.femobl, ten.femobl, dig.femobltr, ten.femobltr)

  defn = u"""# [[%s-%s]]
#: Eastern Arabic numeral: {{l|ar|%s%s}}""" % (
      ten.english, dig.english, ten.eastarabnum[0], dig.eastarabnum)

  decl = u"""{{ar-decl-numeral|-|pl=%s%s|fpl=%s%s|mod=-|modpl=%s|modfpl=%s|modprefix=وَ/wa-|state=ind,def}}""" % (
      # Force dual for اِثْنَان so it will be conjugated correctly even though
      # labeled as plural
      dig.nom, digval == 2 and ":d" or "",
      dig.femnom, digval == 2 and ":d" or "",
      ten.nom, ten.femnom)

  lastcoordterm = (u"""* Last: {{l|ar|%s}} (or {{lang|ar|%s}} = %s)""" % (
      ten.nom, ten.eastarabnum, tenval) if digval == 1 else
  u"""* Last: {{l|ar|%s وَ%s|tr=%s wa-%s}} (or {{lang|ar|%s%s}} = %s)""" % (
      digits[digval - 1].nom, ten.nom, digits[digval - 1].nomtr, ten.nomtr,
      ten.eastarabnum[0], digits[digval - 1].eastarabnum,
      tenval + digval - 1))
  nextcoordterm = (u"""* Next: {{l|ar|مِائَة|tr=miʾa}} (or {{lang|ar|١٠٠}} = 100)"""
      if tenval == 90 and digval == 9 else
  u"""* Next: {{l|ar|%s}} (or {{lang|ar|%s}} = %s)""" % (
      tens[tenval + 10].nom, tens[tenval + 10].eastarabnum, tenval + 10)
      if digval == 9 else
  u"""* Next: {{l|ar|%s وَ%s|tr=%s wa-%s}} (or {{lang|ar|%s%s}} = %s)""" % (
      digits[digval + 1].nom, ten.nom, digits[digval + 1].nomtr, ten.nomtr,
      ten.eastarabnum[0], digits[digval + 1].eastarabnum,
      tenval + digval + 1))

  text = """
==Arabic==

===Etymology===
%s

===Numeral===
%s

%s

====Declension====
%s

====Coordinate terms====
%s
%s
""" % (etym, headword, defn, decl, lastcoordterm, nextcoordterm)
  changelog = "Create lemma entry for %s (Arabic numeral '%s-%s')" % (
      pagename, ten.english, dig.english)
  return pagename, text, changelog

# ==Arabic==
#
# ===Numeral===
# {{head|ar|numeral form|head=تِسْعَة وَعِشْرِين|m|tr=tisʿa wa-ʿišrīn}}
#
# # {{inflection of|lang=ar|تِسْعَة وَعِشْرُون|tr=tisʿa wa-ʿišrūn||m|informal|gloss=twenty-nine}}
# # {{inflection of|lang=ar|تِسْعَة وَعِشْرُون|tr=tisʿa wa-ʿišrūn||m|acc|gloss=twenty=nine}}
# # {{inflection of|lang=ar|تِسْعَة وَعِشْرُون|tr=tisʿa wa-ʿišrūn||m|gen|gloss=twenty=nine}}

# ==Arabic==
#
# ===Numeral===
# {{head|ar|numeral form|head=تِسْع وَعِشْرُون|f|tr=tisʿ wa-ʿišrūn}}
#
# # {{inflection of|lang=ar|تِسْعَة وَعِشْرُون|tr=tisʿa wa-ʿišrūn||f|nom|gloss=twenty=nine}}

def create_non_lemma(tenval, ten, digval, dig, obl=False, fem=False):
  assert obl or fem
  def arabic(num):
    return num.femobl if fem and obl else num.fem if fem else num.obl
  def tr(num):
    return num.femobltr if fem and obl else num.femtr if fem else num.obltr
  pagename = u"%s وَ%s" % (arabig(dig), arabic(ten))
  headword = u"""{{head|ar|numeral form|head=%s|%s|tr=%s wa-%s}}""" % (
      pagename, "f" if fem else "m", tr(dig), tr(ten))
  defns = []
  for case in ["informal", "acc", "gen"] if obl else ["nom"]:
    defns.append(u"""# {{inflection of|lang=ar|%s وَ%s|tr=%s wa-%s||%s|%s|gloss=[[%s-%s]]}}""" % (
      dig.nom, ten.nom, dig.nomtr, ten.nomtr, "f" if fem else "m", case,
      ten.english, dig.english))
  defn = "\n".join(defns)
  text = """\
==Arabic==

===Numeral===
%s

%s
""" % (headword, defn)
  changelog = "Create non-lemma entry (%s) for %s وََ%s (Arabic numeral '%s-%s')" % (
      fem and obl and "feminine oblique" or fem and "feminine nominative" or
      "masculine oblique", dig.nom, ten.nom, ten.english, dig.english)
  return pagename, text, changelog

# ==Arabic==
#
# ===Etymology===
# From the root {{ar-root|ت س ع}}; compare {{m|ar|تِسْعَة||nine}}.
#
# ===Adjective===
# {{ar-adj|تَاسِع|f=تَاسِعَة}}
#
# # {{context|ordinal|lang=ar}} {{l|en|ninth}}
#
# ====Declension====
# {{ar-decl-adj|تَاسِع|number=sg}}
#
# ====Coordinate terms====
# * Cardinal: {{l|ar|تِسْعَة||nine}}
# * Last: {{l|ar|ثَامِن||eighth}}
# * Next: {{l|ar|عَاشِر||tenth}}

def create_unit_ordinal_lemma(digval, dig):
  pagename = dig.ordlemma
  etym = u"""From the root {{ar-root|%s}}; compare {{m|ar|%s||%s}}.""" % (
      " ".join(dig.ordroot), u"أَحَد" if digval == 1 else dig.nom,
      dig.english)

  headword = u"""{{ar-adj|%s|f=%s}}""" % (dig.ordlemma, dig.femordlemma)

  defn = u"""# {{context|ordinal|lang=ar}} {{l|en|%s}}""" % dig.ordeng

  decl = u"""{{ar-decl-adj|%s|number=sg}}""" % dig.ordlemma

  cardcoordterm = u"""* Cardinal: {{l|ar|%s||%s}}""" % (dig.nom, dig.english)
  lastcoordterm = (u"""* Last: {{l|ar|أَوَّل||first}}""" if digval == 2 else
    u"""* Last: {{l|ar|%s||%s}}""" % (digits[digval - 1].ordlemma,
      digits[digval - 1].ordeng))
  nextcoordterm = (u"""* Next: {{l|ar|حَادِيَ عَشَرَ||eleventh}}""" if digval == 10 else
    u"""* Next: {{l|ar|%s||%s}}""" % (digits[digval + 1].ordlemma,
      digits[digval + 1].ordeng))

  text = """
==Arabic==

===Etymology===
%s

===Adjective===
%s

%s

====Declension====
%s

====Coordinate terms====
%s
%s
%s
""" % (etym, headword, defn, decl, cardcoordterm, lastcoordterm, nextcoordterm)
  changelog = "Create lemma entry for %s (Arabic ordinal numeral '%s')" % (
      pagename, dig.ordeng)
  return pagename, text, changelog

# ==Arabic==
#
# ===Adjective===
# {{ar-adj-fem|تَاسِعَة}}
#
# # {{inflection of|lang=ar|تَاسِع||f|gloss=ninth}}

def create_unit_ordinal_non_lemma(digval, dig):
  pagename = dig.femordlemma
  headword = u"""{{ar-adj-fem|%s}}}""" % pagename
  defn = u"""# {{inflection of|lang=ar|%s||f|gloss=%s}}""" % (
      dig.ordlemma, dig.ordeng)
  text = """\
==Arabic==

===Adjective===
%s

%s
""" % (headword, defn)
  changelog = "Create non-lemma entry (feminine) for %s (Arabic ordinal numeral '%s')" % (
      dig.ordlemma, dig.ordeng)
  return pagename, text, changelog

# ==Arabic==
#
# ===Etymology===
# {{compound|lang=ar|تَاسِع|t1=ninth|عَشَرَ|t2=-ten}}, with both parts in the accusative case as with the cardinal numeral {{m|ar|تِسْعَةَ عَشَرَ|nineteen}}, and the same form for the tens part as with the cardinal. Units part from the root {{ar-root|ت س ع}}.
#
# ===Adjective===
# {{ar-adj|تَاسِعَ عَشَرَ|f=تَاسِعَةَ عَشْرَةَ}}
#
# # {{context|ordinal|lang=ar}} {{l|en|nineteenth}}
#
# ====Declension====
# {{ar-decl-adj|تَاسِعَ عَشَرَ:inv|f=تَاسِعَةَ عَشْرَةَ:inv|number=sg}}
#
# ====Coordinate terms====
# * Cardinal: {{l|ar|تِسْعَةَ عَشَرَ||nineteen}}
# * Last: {{l|ar|ثَامِنَ عَشَرَ||eighteenth}}
# * Next: {{l|ar|عِشْرُون||twentieth}}

def create_teen_ordinal_lemma(digval, dig):
  pagename = dig.ordteen
  etym = u"""{{compound|lang=ar|%s|t1=%s|عَشَرَ|t2=-ten}}, with both parts in the accusative case as with the cardinal numeral {{m|ar|%s|%s}}, and the same form for the tens part as with the cardinal. Units part from the root {{ar-root|%s}}.""" % (
      dig.ordlemma, dig.ordeng, dig.cardteen, dig.cardteeneng,
      " ".join(dig.ordroot))

  headword = u"""{{ar-adj|%s|f=%s}}""" % (dig.ordteen, dig.femordteen)

  defn = u"""# {{context|ordinal|lang=ar}} {{l|en|%s}}""" % dig.ordteeneng

  decl = u"""{{ar-decl-adj|%s:inv|f=%s:inv|number=sg}}""" % (dig.ordteen, dig.femordteen)

  cardcoordterm = u"""* Cardinal: {{l|ar|%s||%s}}""" % (dig.cardteen,
      dig.cardteeneng)
  lastcoordterm = (u"""* Last: {{l|ar|عَاشِر||tenth}}""" if digval == 1 else
    u"""* Last: {{l|ar|%s||%s}}""" % (digits[digval - 1].ordteen,
      digits[digval - 1].ordteeneng))
  nextcoordterm = (u"""* Next: {{l|ar|عِشْرُون||twentieth}}""" if digval == 9 else
    u"""* Next: {{l|ar|%s||%s}}""" % (digits[digval + 1].ordteen,
      digits[digval + 1].ordteeneng))

  text = """
==Arabic==

===Etymology===
%s

===Adjective===
%s

%s

====Declension====
%s

====Coordinate terms====
%s
%s
%s
""" % (etym, headword, defn, decl, cardcoordterm, lastcoordterm, nextcoordterm)
  changelog = "Create lemma entry for %s (Arabic ordinal numeral '%s')" % (
      pagename, dig.ordteeneng)
  return pagename, text, changelog

# ==Arabic==
#
# ===Adjective===
# {{ar-adj-fem|تَاسِعَةَ عَشْرَةَ}}
#
# # {{inflection of|lang=ar|تَاسِعَ عَشَرَ||f|gloss=nineteenth}}

def create_teen_ordinal_non_lemma(digval, dig):
  pagename = dig.femordteen
  headword = u"""{{ar-adj-fem|%s}}}""" % pagename
  defn = u"""# {{inflection of|lang=ar|%s||f|gloss=%s}}""" % (
      dig.ordteen, dig.ordteeneng)
  text = """\
==Arabic==

===Adjective===
%s

%s
""" % (headword, defn)
  changelog = "Create non-lemma entry (feminine) for %s (Arabic ordinal numeral '%s')" % (
      dig.ordteen, dig.ordteeneng)
  return pagename, text, changelog

pa = blib.init_argparser("Save numbers to Wiktionary")
pa.add_argument("--lemmas", action="store_true",
    help="Do lemmas from 21-99.")
pa.add_argument("--non-lemmas", action="store_true",
    help="Do non-lemmas from 21-99.")
pa.add_argument("--ordinal-lemmas", action="store_true",
    help="Do ordinal lemmas from 11-19.")
pa.add_argument("--ordinal-non-lemmas", action="store_true",
    help="Do ordinal non-lemmas from 11-19.")
pa.add_argument("--offline", action="store_true",
    help="Run offline, checking output only.")

params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)

def iter_pages(createfn):
  for tenval, ten, digval, dig in iter_numerals():
    yield createfn(tenval, ten, digval, dig)

def iter_pages_units(createfn, include_ten=False, skip_one=False):
  for digval, dig in sorted(digits.iteritems(), key=lambda x:x[0]):
    if (digval != 10 or include_ten) and (digval != 1 or not skip_one):
      yield createfn(digval, dig)

def do_pages(createfn, iterfn=iter_pages):
  pages = iterfn(createfn)
  for current, index in blib.iter_pages(pages, startFrom, upTo,
      key=lambda x:x[0]):
    pagename, text, changelog = current
    pagetitle = remove_diacritics(pagename)
    if params.offline:
      msg("Text for %s: [[%s]]" % (pagename, text))
      msg("Changelog = %s" % changelog)
    else:
      page = pywikibot.Page(site, pagetitle)
      if page.exists():
        msg("Page %s %s: WARNING, page already exists, skipping" % (
          index, pagename))
      else:
        def save_text(page, index, parsed):
          return text, changelog
        blib.do_edit(page, index, save_text, save=params.save,
            verbose=params.verbose)

if params.lemmas:
  do_pages(create_lemma)
if params.non_lemmas:
  do_pages(lambda tv, t, dv, d:create_non_lemma(tv, t, dv, d, obl=True))
  do_pages(lambda tv, t, dv, d:create_non_lemma(tv, t, dv, d, fem=True))
  do_pages(lambda tv, t, dv, d:create_non_lemma(tv, t, dv, d, obl=True, fem=True))
if params.ordinal_lemmas:
  do_pages(create_unit_ordinal_lemma, lambda fn:iter_pages_units(fn, include_ten=True, skip_one=True))
  do_pages(create_teen_ordinal_lemma, iter_pages_units)
if params.ordinal_non_lemmas:
  do_pages(create_unit_ordinal_non_lemma, lambda fn:iter_pages_units(fn, include_ten=True, skip_one=True))
  do_pages(create_teen_ordinal_non_lemma, iter_pages_units)
