#!/usr/bin/env python
#coding: utf-8

#    rewrite_verb_headword.py is free software: you can redistribute it and/or modify
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

numeric_to_roman_form = {
  "1":"I", "2":"II", "3":"III", "4":"IV", "5":"V",
  "6":"VI", "7":"VII", "8":"VIII", "9":"IX", "10":"X",
  "11":"XI", "12":"XII", "13":"XIII", "14":"XIV", "15":"XV",
  "1q":"Iq", "2q":"IIq", "3q":"IIIq", "4q":"IVq"
}

# convert numeric form to roman-numeral form
def canonicalize_form(form):
  return numeric_to_roman_form.get(form, form)

# Clean the verb headword templates on a given page with the given text.
# Returns the changed text along with a changelog message.
def rewrite_one_page_verb_headword(page, text):
  pagetitle = page.title()
  msg("Processing page %s" % pagetitle)
  actions_taken = []

  for template in text.filter_templates():
    if template.name in ["ar-verb"]:
      origtemp = unicode(template)
      # In order to keep in the same order, just forcibly change the
      # param "names" (numbers)
      for pno in xrange(10, 0, -1):
        if template.has(str(pno)):
          template.get(str(pno)).name = str(pno + 1)
      form = blib.getparam(template, "form")
      if form:
        # Make sure form= param is first ...
        template.remove("form")
        template.add("form", canonicalize_form(form), before=template.params[0].name if len(template.params) > 0 else None)
        # ... then forcibly change its name to 1=
        template.get("form").name = "1"
        template.get("1").showkey = False
      newtemp = unicode(template)
      if origtemp != newtemp:
        msg("Replacing %s with %s" % (origtemp, newtemp))
      if re.match("^[1I](-|$)", form):
        actions_taken.append("form=%s (%s/%s)" % (form,
          blib.getparam(template, "2"), blib.getparam(template, "3")))
      else:
        actions_taken.append("form=%s" % form)
  changelog = "ar-verb: form= -> 1=, move other params up: %s" % '; '.join(actions_taken)
  if len(actions_taken) > 0:
    msg("Change log = %s" % changelog)
  return text, changelog

def rewrite_verb_headword(save, startFrom, upTo):
  for cat in [u"Arabic verbs"]:
    for page in blib.cat_articles(cat, startFrom, upTo):
      blib.do_edit(page, rewrite_one_page_verb_headword, save=save)

pa = blib.init_argparser("Rewrite form= to 1= in verb headword templates")
parms = pa.parse_args()
startFrom, upTo = blib.parse_start_end(parms.start, parms.end)

rewrite_verb_headword(parms.save, startFrom, upTo)
