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

# Clean the verb headword templates on a given page with the given text.
# Returns the changed text along with a changelog message.
def rewrite_one_page_verb_headword(page, text):
  pagetitle = page.title()
  msg("Processing page %s" % pagetitle)
  actions_taken = []
  for template in text.filter_templates():
    if template.name in ["ar-verb"]:
      origtemp = unicode(template)
      for pno in xrange(10, 0, -1):
        param = blib.getparam(template, str(pno))
        if param:
          template.add(str(pno + 1), param)
      form = blib.getparam(template, "form")
      template.add("1", form)
      newtemp = unicode(template)
      if origtemp != newtemp:
        msg("Replacing %s with %s" % (origtemp, newtemp))
      if re.match("^[1I](-|$)", form):
        actions_taken.append("form=%s (%s/%s)" % (form,
          blib.getparam(template, "2"), blib.getparam(template, "3"))
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
