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
      femobl=None):
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
    femnom = reorder_shadda(nom)
    if not femobl:
      if femnom.endswith(UUN):
        obl = re.sub(UUN + "$", IIN, femnom)
      else:
        obl = femnom
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

digits = {1:Number(u"١", "one", u"وَاحِد", u"وَاحِدَة"),
          2:Number(u"٢", "two", u"اِثْنَان", u"اِثْنَتَان", u"اِثْنَيْن", u"اِثْنَتَيْن"),
          3:Number(u"٣", "three", u"ثَلَاثَةث"),
          4:Number(u"٤", "four", u"أَرْبَعَة"),
          5:Number(u"٥", "five", u"خَمْسَة"),
          6:Number(u"٦", "six", u"سِتَّة"),
          7:Number(u"٧", "seven", u"سَبْعَة"),
          8:Number(u"٨", "eight", u"ثَمَانِيَة", u"ثَمَانٍ"),
          9:Number(u"٩", "nine", u"تِسْعَة")}
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
# {{ar-decl-numeral|تِسْعَة|mod=عِشْرُون|modprefix=وَ/wa-|state=ind,def}}
#
# ====Coordinate terms====
# * Last: {{l|ar|ثَمَانِيَة وَعِشْرُون|tr=ṯamāniya wa-ʿišrūn}} (or {{lang|ar|٢٨}} = 28)
# * Next: {{l|ar|ثَلَاثُون}} (or {{lang|ar|٣٠}} = 30)

def create_lemma(tenval, ten, digval, dig):
  etym = """Literally "%s and %s", from {{m|ar|%s}} and {{m|ar|%s}}.""" % (
      (dig.english, ten.english, dig.nom, ten.nom))
  headword = u"""{{ar-numeral|%s وَ%s|m|tr=%s wa-%s|f=%s وَ%s|ftr=%s wa-%s|obl=%s وَ%s|obltr=%s wa-%s|fobl=%s وَ%s|fobltr=%s wa-%s}}""" % (
      dig.nom, ten.nom, dig.nomtr, ten.nomtr,
      dig.femnom, ten.femnom, dig.femnomtr, ten.femnomtr,
      dig.oblnom, ten.oblnom, dig.oblnomtr, ten.oblnomtr,
      dig.femoblnom, ten.femoblnom, dig.femoblnomtr, ten.femoblnomtr)

  defn = u"""# [[%s-%s]]
#: Eastern Arabic numeral: {{l|ar|%s%s}}""" % (
      ten.english, dig.english, ten.eastarabnum[0], dig.eastarabnum)

  decl = u"""{{ar-decl-numeral|%s|mod=%s|modprefix=وَ/wa-|state=ind,def}}""" % (
      dig.nom, ten.nom)

  lastcoordterm = (u"""* Last: {{l|ar|%s}} (or {{lang|ar|%s}} = %s)""" % (
      ten.nom, ten.eastarabnum, tenval) if digval == 1 else
  u"""* Last: {{l|ar|%s وَ%s|tr=%s wa-%s}} (or {{lang|ar|%s%s}} = %s)""" % (
      digits[digval - 1].nom, ten.nom, digits[digval - 1].nomtr, ten.nomtr,
      ten.eastarabnum[0], digits[digitval - 1].eastarabnum,
      tenval + digval - 1))
  nextcoordterm = (u"""* Next: {{l|ar|مِائَة|tr=miʾa}} (or {{lang|ar|١٠٠}} = 100)"""
      if tenval == 90 and digval == 9 else
  u"""* Next: {{l|ar|%s}} (or {{lang|ar|%s}} = %s)""" % (
      tens[tenval + 10].nom, tens[tenval + 10].eastarabnum, tenval + 10)
      if digval == 9 else
  u"""* Next: {{l|ar|%s وَ%s|tr=%s wa-%s}} (or {{lang|ar|%s%s}} = %s)""" % (
      digits[digval + 1].nom, ten.nom, digits[digval + 1].nomtr, ten.nomtr,
      ten.eastarabnum[0], digits[digitval + 1].eastarabnum,
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
  msg(text)

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
  headword = u"""{{head|ar|numeral form|head=%s وَ%s|%s|tr=%s wa-%s}}""" % (
      arabic(dig), arabic(ten), "f" if fem else "m", tr(dig), tr(ten))
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
  msg(text)

pa = blib.init_argparser("Save numbers to Wiktionary")
pa.add_argument("--lemmas", action="store_true",
    help="Do lemmas from 21-99.")
pa.add_argument("--non-lemmas", action="store_true",
    help="Do non-lemmas from 21-99.")

params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)
for tenval, ten, digval, dig in iter_numerals():
  if params.lemmas:
    create_lemma(tenval, ten, digval, dig)
  if params.non_lemmas:
    create_non_lemma(tenval, ten, digval, dig, obl=True)
    create_non_lemma(tenval, ten, digval, dig, fem=True)
    create_non_lemma(tenval, ten, digval, dig, obl=True, fem=True)
