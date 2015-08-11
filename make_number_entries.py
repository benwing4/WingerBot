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

# Classes have the following fields:
# *********** For the cardinal itself ***********
# -- 'nom': Arabic masculine nominative form of number
# -- 'nomtr': Translit masculine nominative form of number
# -- 'femnom': Arabic feminine nominative form of number
# -- 'femnomtr': Translit feminine nominative form of number
# -- 'obl': Arabic masculine oblique form of number
# -- 'obltr': Translit masculine oblique form of number
# -- 'femobl': Arabic feminine oblique form of number
# -- 'femobltr': Translit feminine oblique form of number
# -- 'english': English text of number
# -- 'eastarabnum': East Arabic numerals for number
# *********** For the ordinal itself ************
# -- 'ordlemma': Arabic lemma for masculine ordinal number
# -- 'ordlemmatr': Translit lemma for masculine ordinal number
# -- 'femordlemma': Arabic lemma for feminine ordinal number
# -- 'femordlemmatr': Arabic lemma for feminine ordinal number
# -- 'ordroot': Three-letter ordinal root
# -- 'ordeng': English text of ordinal number
# -- 'ordgloss': English text of gloss used for ordinal number
# *********** Other forms ************
# -- 'adv': Adverbial
# -- 'frac': Fractional
# -- 'mult': Multiplier
# -- 'dist': Distributive
# -- 'numadj': Numeral adjective
# *********** For number+10 ************
# -- 'cardteen': For numbers 1-10, Arabic form of number+10
# -- 'cardteeneng': For numbers 1-10, English text of number+10
# -- 'ordteen': For numbers 1-10, Arabic form of masculine ordinal number+10
# -- 'femordteen': For numbers 1-10, Arabic form of feminine ordinal number+10
# -- 'ordteeneng': For numbers 1-10, English text of ordinal number+10
# *********** For higher numbers ************
# -- 'hundred': For numbers 1-10, Arabic form of number*100
# -- 'hundredtr': For numbers 1-10, translit form of number*100
# -- 'thousand': For numbers 1-10, Arabic form of number*1000
# -- 'thousandtr': For numgers 1-10, translit form of number*1000
class Number(object):
  thousandpl = u"آلَاف"
  thousandpltr = ar_translit.tr(thousandpl)
  def __init__(self, eastarabnum, english, nom, femnom=None, obl=None,
      femobl=None, hundred=None, thousand=None,
      ord=None, adv=None, frac=None, dist=None, mult=None, numadj=None):
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
    self.hundred = hundred
    self.thousand = thousand
    self.thousandtr = None
    if self.thousand:
      self.thousandtr = ar_translit.tr(self.thousand)
    self.ordroot = None
    self.ordeng = None
    self.ordgloss = None
    self.cardteeneng = None
    self.ordlemma = None
    self.cardteen = None
    self.adv = adv
    self.frac = frac
    self.dist = dist
    self.mult = mult
    self.numadj = numadj
    if ord:
      if len(ord) == 6:
        self.ordroot, self.ordeng, self.ordgloss, self.cardteeneng, \
            self.ordlemma, self.cardteen = ord
      else:
        self.ordroot, self.ordeng, self.cardteeneng = ord
        self.ordgloss = self.ordeng
        self.ordlemma = (self.ordroot[0] + AA + self.ordroot[1] + I +
            self.ordroot[2])
        self.cardteen = self.nom + A + u" عَشَرَ"
      self.ordlemmatr = ar_translit.tr(self.ordlemma)
      R1 = self.ordroot[0]
      R2 = self.ordroot[1]
      R3 = self.ordroot[2]
      self.femordlemma = R1 + AA + R2 + I + R3 + AH
      self.femordlemmatr = ar_translit.tr(self.femordlemma)
      self.ordteen = R1 + AA + R2 + I + R3 + A + u" عَشَرَ"
      self.femordteen = self.femordlemma + A + u" عَشْرَةَ"
      self.ordteeneng = ("twelfth" if self.cardteeneng == "twelve" else
          "twentieth" if self.cardteeneng == "twenty" else
          self.cardteeneng + "th")
      # one and two are totally special-cased
      if self.english != "one" and self.english != "two":
        self.frac = R1 + U + R2 + SK + R3
        self.adv = self.femnom + u" مَرَّات"
        self.mult = u"مُ" + R1 + A + R2 + SH + A + R3
        self.numadj = R1 + U + R2 + AA + R3 + IY + SH
        if not self.hundred:
          self.hundred = self.femnom + U + u"مِائَة"
        if not self.thousand:
          self.thousand = self.nom + " " + self.thousandpl
          self.thousandtr = self.nomtr + "t " + self.thousandpltr
      self.hundredtr = ar_translit.tr(self.hundred.replace(u"مِا", u"مِ"))

digits = {1:Number(u"١", "one", u"وَاحِد", u"وَاحِدَة",
            hundred=u"مِائَة", thousand=u"أَلْف",
            ord=[u"حدي", "first", "first|first (combining form)", "eleven", u"حَادٍ",
              u"أَحَدَ عََشَرَ"],
            adv=u"مَرَّة", mult=u"مُفْرَد", dist=[u"أُحَاد", u"وُحَاد", u"مَوْحَد"],
            numadj=u"أُحَادِيّ"),
          2:Number(u"٢", "two", u"اِثْنَان", u"اِثْنَتَان", u"اِثْنَيْن", u"اِثْنَتَيْن",
            hundred=u"مِائَتَان", thousand=u"أَلْفَان",
            ord=[u"ثني", "second", "second", "twelve", u"ثَانٍ", u"اِثْنَا عَشَرَ"],
            frac=u"نِصْف", adv=u"مَرَّتَان", mult=u"مُثَنًّى", dist=[u"ثُنَاء", u"مَثْنَى"],
            numadj=u"ثُنَائِيّ"),
          3:Number(u"٣", "three", u"ثَلَاثَة",
            ord=[u"ثلث", "third", "thirteen"],
            dist=[u"ثُلَاث", u"مَثْلَث"]),
          4:Number(u"٤", "four", u"أَرْبَعَة",
            ord=[u"ربع", "fourth", "fourteen"],
            dist=[u"رُبَاع", u"مَرْبَع"]),
          5:Number(u"٥", "five", u"خَمْسَة",
            ord=[u"خمس", "fifth", "fifteen"]),
          6:Number(u"٦", "six", u"سِتَّة",
            ord=[u"سدس", "sixth", "sixteen"]),
          7:Number(u"٧", "seven", u"سَبْعَة",
            ord=[u"سبع", "seventh", "seventeen"]),
          8:Number(u"٨", "eight", u"ثَمَانِيَة", u"ثَمَانٍ",
            hundred=u"ثَمَانِمِائَة",
            ord=[u"ثمن", "eighth", "eighteen"]),
          9:Number(u"٩", "nine", u"تِسْعَة",
            ord=[u"تسع", "ninth", "nineteen"]),
          10:Number(u"١٠", "ten", u"عَشَرَة", u"عَشْر",
            hundred=u"أَلْف",
            ord=[u"عشر", "tenth", "twenty"]),
         }
tens = { #10:Number(u"١٠", "ten", u"عَشَرَة", u"عَشْر"),
         20:Number(u"٢٠", "twenty", u"عِشْرُون"),
         30:Number(u"٣٠", "thirty", u"ثَلَاثُون"),
         40:Number(u"٤٠", "forty", u"أَرْبَعُون"),
         50:Number(u"٥٠", "fifty", u"خَمْسُون"),
         60:Number(u"٦٠", "sixty", u"سِتُّون"),
         70:Number(u"٧٠", "seventy", u"سَبْعُون"),
         80:Number(u"٨٠", "eighty", u"ثَمَانُون"),
         90:Number(u"٩٠", "ninety", u"تِسْعُون")}

def iter_numerals():
  for tenval, ten in sorted(tens.iteritems(), key=lambda x:x[0]):
    for digval, dig in sorted(digits.iteritems(), key=lambda x:x[0]):
      if digval != 10:
        yield (tenval, ten, digval, dig)

# ==Arabic==
# {{number box|ar|29}}
# 
# ===Etymology===
# {{compound|lang=ar|تِسْعَة|t1=[[nine]]|وَ|tr2=wa-|t2=[[and]]|عِشْرُون|tr3=[[twenty]]}}.
# 
# ===Numeral===
# {{ar-numeral|تِسْعَة وَعِشْرُون|m|tr=tisʿa wa-ʿišrūn|f=تِسْع وَعِشْرُون|ftr=tisʿ wa-ʿišrūn}}
# 
# # [[twenty-nine]]
# #: Eastern Arabic numeral: {{l|ar|٢٩}}
# 
# ====Declension====
# {{ar-decl-numeral|-|pl=تِسْعَة|f=-|fpl=تِسْع|mod=-|modpl=عِشْرُون|modf=-|modfpl=عِشْرُون|modprefix=وَ/wa-|state=ind,def}}

def create_lemma(tenval, ten, digval, dig):
  pagename = u"%s وَ%s" % (dig.nom, ten.nom)
  nbox = "{{number box|ar|%s}}" % (tenval + digval)
  etym = u"""{{compound|lang=ar|%s|t1=[[%s]]|وَ|tr2=wa-|t2=[[and]]|%s|t3=[[%s]]}}.""" % (
      (dig.nom, dig.english, ten.nom, ten.english))
  headword = u"""{{ar-numeral|%s|m|tr=%s wa-%s|f=%s وَ%s|ftr=%s wa-%s}}""" % (
      pagename, dig.nomtr, ten.nomtr,
      dig.femnom, ten.femnom, dig.femnomtr, ten.femnomtr)

  defn = u"""# [[%s-%s]]
#: Eastern Arabic numeral: {{l|ar|%s%s}}""" % (
      ten.english, dig.english, ten.eastarabnum[0], dig.eastarabnum)

  decl = u"""{{ar-decl-numeral|-|pl=%s%s|f=-|fpl=%s%s|mod=-|modpl=%s|modf=-|modfpl=%s|modprefix=وَ/wa-|state=ind,def}}""" % (
      # Force dual for اِثْنَان so it will be conjugated correctly even though
      # labeled as plural
      dig.nom, digval == 2 and ":d" or "",
      dig.femnom, digval == 2 and ":d" or "",
      ten.nom, ten.femnom)

  text = """
==Arabic==
%s

===Etymology===
%s

===Numeral===
%s

%s

====Declension====
%s
""" % (nbox, etym, headword, defn, decl)
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
# {{number box|ar|29}}
# 
# ===Etymology===
# {{compound|lang=ar|تَاسِع|t1=[[ninth]]|وَ|tr2=wa-|t2=[[and]]|عِشْرُون|tr3=[[twenty]]}}.
# 
# ===Adjective===
# {{ar-adj|تَاسِع  وَعِشْرُون|m|tr=tāsiʿ wa-ʿišrūn|f=تَاسِعَة وَعِشْرُون|ftr=tāsiʿa wa-ʿišrūn}}
#
# # {{context|ordinal|lang=ar}} {{l|en|twenty-ninth}}
# 
# ====Declension====
# {{ar-decl-adj|تَاسِع|mod=عِشْرُون:smp|modf=عِشْرُون:smp|modprefix=وَ/wa-|number=sg}}

def create_ordinal_lemma(tenval, ten, digval, dig):
  pagename = u"%s وَ%s" % (dig.ordlemma, ten.nom)
  nbox = "{{number box|ar|%s}}" % (tenval + digval)
  etym = u"""{{compound|lang=ar|%s|t1=[[%s]]|وَ|tr2=wa-|t2=[[and]]|%s|t3=[[%s]]}}.""" % (
      (dig.ordlemma, dig.ordgloss, ten.nom, ten.english))
  headword = u"""{{ar-adj|%s|m|tr=%s wa-%s|f=%s وَ%s|ftr=%s wa-%s}}""" % (
      pagename, dig.ordlemmatr, ten.nomtr,
      dig.femordlemma, ten.femnom, dig.femordlemmatr, ten.femnomtr)

  defn = u"""# {{context|ordinal|lang=ar}} {{l|en|%s-%s}}""" % (
      ten.english, dig.ordeng)

  decl = u"""{{ar-decl-adj|%s|mod=%s:smp|modf=%s:smp|modprefix=وَ/wa-|number=sg}}""" % (
      dig.ordlemma, ten.nom, ten.femnom)

  text = """
==Arabic==
%s

===Etymology===
%s

===Adjective===
%s

%s

====Declension====
%s
""" % (nbox, etym, headword, defn, decl)
  changelog = "Create lemma entry for %s (Arabic ordinal numeral '%s-%s')" % (
      pagename, ten.english, dig.ordeng)
  return pagename, text, changelog

# ==Arabic==
# {{number box|ar|9}}
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

def create_unit_ordinal_lemma(digval, dig):
  pagename = dig.ordlemma
  nbox = "{{number box|ar|%s}}" % digval
  etym = u"""From the root {{ar-root|%s}}; compare {{m|ar|%s||%s}}.""" % (
      " ".join(dig.ordroot), u"أَحَد" if digval == 1 else dig.nom,
      dig.english)

  headword = u"""{{ar-adj|%s|f=%s}}""" % (dig.ordlemma, dig.femordlemma)

  defn = u"""# {{context|ordinal|lang=ar}} {{l|en|%s}}""" % dig.ordeng

  decl = u"""{{ar-decl-adj|%s|number=sg}}""" % dig.ordlemma

  text = """
==Arabic==
%s

===Etymology===
%s

===Adjective===
%s

%s

====Declension====
%s
""" % (etym, nbox, headword, defn, decl)
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
# {{number box|ar|19}}
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

def create_teen_ordinal_lemma(digval, dig):
  pagename = dig.ordteen
  nbox = "{{number box|ar|%s}}" % (10 + digval)
  etym = u"""{{compound|lang=ar|%s|t1=%s|عَشَرَ|t2=-ten}}, with both parts in the accusative case as with the cardinal numeral {{m|ar|%s|%s}}, and the same form for the tens part as with the cardinal. Units part from the root {{ar-root|%s}}.""" % (
      dig.ordlemma, dig.ordeng, dig.cardteen, dig.cardteeneng,
      " ".join(dig.ordroot))

  headword = u"""{{ar-adj|%s|f=%s}}""" % (dig.ordteen, dig.femordteen)

  defn = u"""# {{context|ordinal|lang=ar}} {{l|en|%s}}""" % dig.ordteeneng

  decl = u"""{{ar-decl-adj|%s:inv|f=%s:inv|number=sg}}""" % (dig.ordteen, dig.femordteen)

  text = """
==Arabic==
%s

===Etymology===
%s

===Adjective===
%s

%s

====Declension====
%s
""" % (nbox, etym, headword, defn, decl)
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

def create_number_list_data():
  msg("local export = {numbers = {}}")
  # Do 1-10
  for digval, dig in sorted(digits.iteritems(), key=lambda x:x[0]):
    msg("""
export.numbers[%s] = {
	numeral = "%s",
	cardinal = "%s",
	ordinal = "%s",""" % (digval, dig.eastarabnum, dig.nom, dig.ordlemma))
    if dig.adv:
      msg("""	adverbial = "%s",""" % dig.adv)
    if dig.frac:
      msg("""	fractional = "%s",""" % dig.frac)
    if dig.mult:
      msg("""	multiplier = "%s",""" % dig.mult)
    if dig.dist:
      msg("""	distributive = {%s},""" % ", ".join(
        ['"' + x+ '"' for x in dig.dist]))
    if dig.numadj:
      msg("""	other_title = "Numeral adjective",
	other = "%s",""" % dig.numadj)
    msg("""}""")
  # Do 11-19
  for digval, dig in sorted(digits.iteritems(), key=lambda x:x[0]):
    if digval != 10:
      msg(u"""
export.numbers[%s] = {
	numeral = "١%s",
	cardinal = "%s",
	ordinal = %s",
}""" % (digval + 10, dig.eastarabnum, dig.cardteen, dig.ordteen))
  # Do 20-99
  for tenval, ten in sorted(tens.iteritems(), key=lambda x:x[0]):
    # Do 20, 30, 40, ..., 90
    msg("""
export.numbers[%s] = {
	numeral = "%s",
	cardinal = "%s",
	ordinal = "%s",
}""" % (tenval, ten.eastarabnum, ten.nom, ten.nom))
    # Do 21-29, 31-39, 41-49, ..., 91-99
    for digval, dig in sorted(digits.iteritems(), key=lambda x:x[0]):
      if digval != 10:
        msg("""
export.numbers[%s] = {
	numeral = "%s",
	cardinal = {{"%s", "%s"}},
	ordinal = {{"%s", "%s"}},
}""" % (tenval + digval, ten.eastarabnum[0] + dig.eastarabnum,
        dig.nom + u" وَ" + ten.nom, dig.nomtr + " wa-" + ten.nomtr,
        dig.ordlemma + u" وَ" + ten.nom, dig.ordlemmatr + " wa-" + ten.nomtr))
  # Do 100, 200, 300, ..., 900
  for digval, dig in sorted(digits.iteritems(), key=lambda x:x[0]):
    if digval != 10:
      msg(u"""
export.numbers[%s] = {
	numeral = "%s٠٠",
	cardinal = {{"%s", "%s"}},
}""" % (digval * 100, dig.eastarabnum, dig.hundred, dig.hundredtr))
  # Do 1000, 2000, 3000, ..., 10000
  for digval, dig in sorted(digits.iteritems(), key=lambda x:x[0]):
    msg(u"""
export.numbers[%s] = {
      numeral = "%s٠٠٠",
      cardinal = {{"%s", "%s"}},
}""" % (digval * 1000, dig.eastarabnum, dig.thousand, dig.thousandtr))
  msg(u"""
return export""")

pa = blib.init_argparser("Save numbers to Wiktionary")
pa.add_argument("--lemmas", action="store_true",
    help="Do lemmas from 21-99.")
pa.add_argument("--non-lemmas", action="store_true",
    help="Do non-lemmas from 21-99.")
pa.add_argument("--ordinal-lemmas", action="store_true",
    help="Do ordinal lemmas from 11-19.")
pa.add_argument("--ordinal-non-lemmas", action="store_true",
    help="Do ordinal non-lemmas from 11-19.")
pa.add_argument("--number-list-data", action="store_true",
    help="Output number list data.")
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
  do_pages(create_ordinal_lemma)
  do_pages(create_unit_ordinal_lemma, lambda fn:iter_pages_units(fn, include_ten=True, skip_one=True))
  do_pages(create_teen_ordinal_lemma, iter_pages_units)
if params.ordinal_non_lemmas:
  do_pages(create_unit_ordinal_non_lemma, lambda fn:iter_pages_units(fn, include_ten=True, skip_one=True))
  do_pages(create_teen_ordinal_non_lemma, iter_pages_units)
if params.number_list_data:
  create_number_list_data()
