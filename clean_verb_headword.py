#!/usr/bin/env python
#coding: utf-8

#    clean_verb_headword.py is free software: you can redistribute it and/or modify
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
from blib import msg, getparam

# Clean the verb headword templates on a given page with the given text.
# Returns the changed text along with a changelog message.
def clean_one_page_verb_headword(page, index, text):
  pagetitle = page.title()
  actions_taken = []
  for template in text.filter_templates():
    paramschanged = []
    if template.name in ["ar-verb"]:
      form = getparam(template, "form")
      if form == "1" or form == "I":
        msg("Page %s %s: skipped ar-verb because form I" % (index, pagetitle))
        continue
      elif getparam(template, "useparam"):
        msg("Page %s %s: skipped ar-verb because useparam" % (index, pagetitle))
        continue
      origtemp = unicode(template)
      def remove_param(param):
        if template.has(param):
          template.remove(param)
          paramschanged.append(param)
      remove_param("head")
      remove_param("head2")
      remove_param("head3")
      remove_param("tr")
      remove_param("impf")
      remove_param("impfhead")
      remove_param("impftr")
      if getparam(template, "sc") == "Arab":
        remove_param("sc")
      I = getparam(template, "I")
      if I in [u"ء", u"و", u"ي"] and form not in ["8", "VIII"]:
        msg("Page %s %s: form=%s, removing I=%s" % (index, pagetitle, form, I))
        remove_param("I")
      II = getparam(template, "II")
      if (II == u"ء" or II in [u"و", u"ي"] and
          form in ["2", "II", "3", "III", "5", "V", "6", "VI"]):
        msg("Page %s %s: form=%s, removing II=%s" % (index, pagetitle, form, II))
        remove_param("II")
      III = getparam(template, "III")
      if III == u"ء":
        msg("Page %s %s: form=%s, removing III=%s" % (index, pagetitle, form, III))
        remove_param("III")
      newtemp = unicode(template)
      if origtemp != newtemp:
        msg("Replacing %s with %s" % (origtemp, newtemp))
      if len(paramschanged) > 0:
        actions_taken.append("form=%s (%s)" % (form, ', '.join(paramschanged)))
  changelog = "ar-verb: remove params: %s" % '; '.join(actions_taken)
  #if len(actions_taken) > 0:
  msg("Change log = %s" % changelog)
  return text, changelog

def clean_verb_headword(save, startFrom, upTo):
  for cat in [u"Arabic verbs"]:
    for page, index in blib.cat_articles(cat, startFrom, upTo):
      blib.do_edit(page, index, clean_one_page_verb_headword, save=save)

pa = blib.init_argparser("Clean up verb headword templates")
params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)

clean_verb_headword(params.save, startFrom, upTo)
