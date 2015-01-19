#!/usr/bin/env python
#coding: utf-8

#    remove_i3rab.py is free software: you can redistribute it and/or modify
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
DIACRITIC_ANY = "[" + A + I + U + AN + IN + UN + SK + SH + DAGGER_ALIF + "]"
ALIF = u"ا"
ALIF_WASLA = u"ٱ"
ALIF_ANY = "[" + ALIF + ALIF_WASLA + "]"

def reorder_shadda(text):
  # shadda+short-vowel (including tanwīn vowels, i.e. -an -in -un) gets
  # replaced with short-vowel+shadda during NFC normalisation, which
  # MediaWiki does for all Unicode strings; however, it makes the
  # detection process inconvenient, so undo it.
  return re.sub("(" + DIACRITIC_ANY_BUT_SH + ")" + SH, SH + r"\1", text)

def remove_i3rab(page, entry, word, nowarn=False):
  def mymsg(text):
    if not nowarn:
      msg("Page %s: Entry %s: %s" % (page, entry, text))
  word = reorder_shadda(word)
  if word.endswith(UN):
    mymsg("Removing i3rab (UN) from %s" % word)
    return re.sub(UN + "$", "", word)
  if word.endswith(U):
    mymsg("Removing i3rab (U) from %s" % word)
    return re.sub(U + "$", "", word)
  if word and word[-1] in [A, I, U, AN]:
    mymsg("FIXME: Strange diacritic at end of %s" % word)
  if word[0] == ALIF_WASLA:
    mymsg("Changing alif wasla to plain alif for %s" % word)
    word = ALIF + word[1:]
  return word

def do_nouns(poses, headtempls, save, startFrom, upTo):
  for pos in poses:
    for page in blib.cat_articles("Arabic %ss" % pos.lower(), startFrom, upTo):
      pagename = page.title()
      msg("Page %s: Begin processing" % pagename)
      nouncount = 0
      nounids = []
      for template in blib.parse(page).filter_templates():
        if template.name in headtempls:
          nouncount += 1
          params_done = []
          entry = blib.getparam(template, "1")
          for param in template.params:
            value = blib.getparam(template, param)
            if not value:
              continue
            newvalue = remove_i3rab(pagename, entry, value)
            if newvalue != value:
              template.add(param, newvalue)
              params_done.append(param)
          if params_done:
            nounids.append("#%s %s %s (%s)" %
                (nouncount, template.name, entry, ", ".join(params_done)))
      if nounids:
        comment = "Remove i3rab from params in %s" % (
            '; '.join(nounids))
        msg("Page %s: comment = %s" % (pagename, comment)
        if save:
          page.save(comment = comment)

def do_verbs(save, startFrom, upTo):
  for page in blib.cat_articles("Arabic verbs", startFrom, upTo):
    pagename = page.title()
    msg("Page %s: Begin processing" % pagename)
    verbcount = 0
    verbids = []
    for template in blib.parse(page).filter_templates():
      if template.name == "ar-conj":
        verbcount += 1
        vnvalue = blib.getparam(template, "vn")
        uncertain = False
        if vnvalue.endswith("?"):
          vnvalue = vnvalue[:-1]
          uncertain = True
        if not vnvalue:
          continue
        vns = re.split(u"[,،]", vnvalue)
        form = blib.getparam(template, "1")
        verbid = "#%s form %s" % (verbcount, form)
        if form == "I" or form == "1":
          verbid += " (%s,%s)" % (blib.getparam(template, "2"), blib.getparam(template, "3"))
        no_i3rab_vns = []
        for vn in vns:
          no_i3rab_vns.append(remove_i3rab(pagename, verbid, vn))
        newvn = ",".join(no_i3rab_vns)
        if uncertain:
          newvn += "?"
        if newvn != vnvalue:
          msg("Page %s: Verb %s, replacing %s with %s" % (
            pagename, verbid, vnvalue, newvn))
          template.add("vn", newvn)
          verbids.append(verbid)
    if verbids:
      comment = "Remove i3rab from verbal nouns for verb(s) %s" % (
          ', '.join(verbids))
      msg("Page %s: comment = %s" % (pagename, comment)
      if save:
        page.save(comment = comment)
          
pa = blib.init_argparser("Remove i3rab")
pa.add_argument("--verb", action='store_true',
    help="Do verbal nouns in verbs")
pa.add_argument("--noun", action='store_true',
    help="Do arguments in nouns")

params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)

if params.noun:
  do_nouns(["noun", "verbal noun", "adjective"],
    ["ar-noun", "ar-verbal noun", "ar-coll-noun", "ar-sing-noun",
      "ar-nisba", "ar-noun-nisba", "ar-adj", "ar-numeral"],
    params.save, startFrom, upTo)
if params.verb:
  do_verbs(params.save, startFrom, upTo)
