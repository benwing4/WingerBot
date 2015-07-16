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
from blib import msg, getparam, addparam
from arabiclib import *

site = pywikibot.Site()

verbose = True

def remove_i3rab(page, index, entry, word, nowarn=False):
  def mymsg(text):
    if not nowarn:
      msg("Page %s %s: Entry %s: %s" % (index, page, entry, text))
  word = reorder_shadda(word)
  if word.endswith(UN):
    mymsg("Removing i3rab (UN) from %s" % word)
    return re.sub(UN + "$", "", word)
  if word.endswith(U):
    mymsg("Removing i3rab (U) from %s" % word)
    return re.sub(U + "$", "", word)
  if word.endswith(UUNA):
    mymsg("Removing i3rab (UUNA -> UUN) from %s" % word)
    return re.sub(UUNA + "$", UUN, word)
  if word and word[-1] in [A, I, U, AN]:
    mymsg("FIXME: Strange diacritic at end of %s" % word)
  if word and word[0] == ALIF_WASLA:
    mymsg("Changing alif wasla to plain alif for %s" % word)
    word = ALIF + word[1:]
  return word

def do_nouns(poses, headtempls, save, startFrom, upTo):
  def do_one_page_noun(page, index, text):
    pagename = page.title()
    nouncount = 0
    nounids = []
    for template in text.filter_templates():
      if template.name in headtempls:
        nouncount += 1
        params_done = []
        entry = getparam(template, "1")
        for param in template.params:
          value = param.value
          newvalue = remove_i3rab(pagename, index, entry, unicode(value))
          if newvalue != value:
            param.value = newvalue
            params_done.append(unicode(param.name))
        if params_done:
          nounids.append("#%s %s %s (%s)" %
              (nouncount, template.name, entry, ", ".join(params_done)))
    return text, "Remove i3rab from params in %s" % (
          '; '.join(nounids))

  for pos in poses:
    for page, index in blib.cat_articles("Arabic %ss" % pos.lower(), startFrom, upTo):
      blib.do_edit(page, index, do_one_page_noun, save=save, verbose=verbose)

def do_verbs(save, startFrom, upTo):
  def do_one_page_verb(page, index, text):
    pagename = page.title()
    verbcount = 0
    verbids = []
    for template in text.filter_templates():
      if template.name == "ar-conj":
        verbcount += 1
        vnvalue = getparam(template, "vn")
        uncertain = False
        if vnvalue.endswith("?"):
          vnvalue = vnvalue[:-1]
          msg("Page %s %s: Verbal noun(s) identified as uncertain" % (
            index, pagename))
          uncertain = True
        if not vnvalue:
          continue
        vns = re.split(u"[,،]", vnvalue)
        form = getparam(template, "1")
        verbid = "#%s form %s" % (verbcount, form)
        if re.match("^[1I](-|$)", form):
          verbid += " (%s,%s)" % (getparam(template, "2"), getparam(template, "3"))
        no_i3rab_vns = []
        for vn in vns:
          no_i3rab_vns.append(remove_i3rab(pagename, index, verbid, vn))
        newvn = ",".join(no_i3rab_vns)
        if uncertain:
          newvn += "?"
        if newvn != vnvalue:
          msg("Page %s %s: Verb %s, replacing %s with %s" % (
            index, pagename, verbid, vnvalue, newvn))
          addparam(template, "vn", newvn)
          verbids.append(verbid)
    return text, "Remove i3rab from verbal nouns for verb(s) %s" % (
          ', '.join(verbids))
  for page, index in blib.cat_articles("Arabic verbs", startFrom, upTo):
    blib.do_edit(page, index, do_one_page_verb, save=save, verbose=verbose)
          
pa = blib.init_argparser("Remove i3rab")
pa.add_argument("--verb", action='store_true',
    help="Do verbal nouns in verbs")
pa.add_argument("--noun", action='store_true',
    help="Do arguments in nouns")

params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)

if params.noun:
  do_nouns(["noun", "adjective"],
    ["ar-noun", "ar-coll-noun", "ar-sing-noun", "ar-nisba", "ar-noun-nisba",
      "ar-adj", "ar-numeral"],
    params.save, startFrom, upTo)
if params.verb:
  do_verbs(params.save, startFrom, upTo)
