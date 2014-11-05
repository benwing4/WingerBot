#!/usr/bin/env python
#coding: utf-8

#    remove_translit.py is free software: you can redistribute it and/or modify
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

import re, string, sys, codecs
import argparse

import blib, pywikibot
from blib import msg

import ar_translit

# Compare the auto-translit of PARAM with the corresponding transliteration
# parameter PARAMTR. If both found and both the same, remove the translit
# parameter. Otherwise, if PARAM found, try to canonicalize. If a change
# made, return a string describing the action, else True. If PARAM not found,
# return False.
def process_param(page, template, param, paramtr,
    include_tempname_in_changelog=False):
  def prn(text):
    msg("Page %s, %s.%s: %s" % (page.title(), template.name, param, text))
  arabic = blib.getparam(template, param)
  latin = blib.getparam(template, paramtr)
  if include_tempname_in_changelog:
    paramname = "%s.%s" % (template.name, param)
  else:
    paramname = param
  if not arabic:
    return False
  if latin == "-":
    prn("Translit is '-', skipping")
    return True
  if latin:
    try:
      canonlatin = ar_translit.tr_matching_latin(arabic, latin, True)
      if not canonlatin:
        prn("Unable to match-canonicalize %s (%s)" % (arabic, latin))
    except Exception as e:
      prn("Trying to match-canonicalize %s (%s): %s" % (arabic, latin, e))
      canonlatin = None
    try:
      translit = ar_translit.tr(arabic)
      if not translit:
        prn("Unable to auto-translit %s" % arabic)
    except Exception as e:
      prn("Trying to transliterate %s: %s" % (arabic, e))
      translit = None
    if translit and canonlatin:
      if translit == canonlatin:
      #if (translit == canonlatin or
      #    translit == canonlatin + "un" or
      #    translit == u"ʾ" + canonlatin or
      #    translit == u"ʾ" + canonlatin + "un"):
        prn("Removing redundant translit for %s (%s)" % (arabic, latin))
        oldtempl = "%s" % unicode(template)
        template.remove(paramtr)
        msg("Page %s: Replaced %s with %s" %
            (page.title(), oldtempl, unicode(template)))
        return ("removing param %s redundant translit %s" % (paramname, latin))
      else:
        prn("Auto-translit for %s (%s) not same as manual translit %s (canonicalized %s)" %
            (arabic, translit, latin, canonlatin))
    if canonlatin:
      if latin != canonlatin:
        prn("Match-canonicalizing Latin %s to %s" % (latin, canonlatin))
        oldtempl = "%s" % unicode(template)
        template.add(paramtr, canonlatin)
        msg("Page %s: Replaced %s with %s" %
            (page.title(), oldtempl, unicode(template)))
        return ("match-canonicalizing param %s %s -> %s" %
            (paramname, latin, canonlatin))
      return True
    canonlatin = ar_translit.canonicalize_latin(latin)
    if latin != canonlatin:
      prn("Self-canonicalizing Latin %s to %s" % (latin, canonlatin))
      oldtempl = "%s" % unicode(template)
      template.add(paramtr, canonlatin)
      msg("Page %s: Replaced %s with %s" %
          (page.title(), oldtempl, unicode(template)))
      return ("self-canonicalizing param %s %s -> %s" %
          (paramname, latin, canonlatin))
  return True

# Process the parameter chain for PARAM in TEMPLATE, looking for translits
# to remove or canonicalize. For example, if PARAM is "pl" then this will
# attempt to process "pl", "pl2", "pl3", etc. based on "pltr", "pl2tr",
# "pl3tr", etc., stopping when "plN" isn't found. Return list of actions
# taken, for use in the changelog message.
def process_param_chain(page, template, param):
  actions = []
  result = process_param(page, template, param, param + "tr")
  if isinstance(result, basestring):
    actions.append(result)
  i = 2
  while result:
    thisparam = param + str(i)
    result = process_param(page, template, thisparam, thisparam + "tr")
    if isinstance(result, basestring):
      actions.append(result)
    i += 1
  return actions

# Proces the head param(s) for the given headword template on the given page,
# looking for translits to remove or canonicalize. Modifies the templates in
# place. Return list of actions taken, for use in the changelog message.
def process_head(page, template):
  actions = []

  # Handle existing 1= and head from page title
  if template.has("tr"):
    # Try to process 1=
    result = process_param(page, template, "1", "tr")
    if isinstance(result, basestring):
      actions.append(result)

  # Check and try to process extra heads
  i = 2
  result = True
  while result:
    thisparam = "head" + str(i)
    result = process_param(page, template, thisparam, "tr" + str(i))
    if isinstance(result, basestring):
      actions.append(result)
    i += 1
  return actions

# Process the headword templates on the given page with the given text,
# removing translit params when the auto-translit returns the same thing, or
# canonicalizing. Returns the changed text along with a changelog message.
def process_one_page_headwords(page, text):
  actions = []
  for template in text.filter_templates():
    if template.name in ["ar-adj", "ar-adv", "ar-coll-noun", "ar-sing-noun", "ar-con", "ar-interj", "ar-noun", "ar-numeral", "ar-part", "ar-prep", "ar-pron", "ar-proper noun", "ar-verbal noun", "ar-plural"]: # ar-adj-color, # ar-nisba
      thisactions = []
      tr = blib.getparam(template, "tr")
      thisactions += process_head(page, template)
      for param in ["pl", "cpl", "fpl", "f", "el", "sing", "coll", "d", "pauc", "obl",
          "fobl", "plobl", "dobl"]:
        thisactions += process_param_chain(page, template, param)
      if len(thisactions) > 0:
        actions.append("%s: %s" % (template.name, ', '.join(thisactions)))
  changelog = '; '.join(actions)
  #if len(actions) > 0:
  msg("Change log for page %s = %s" % (page.title(), changelog))
  return text, changelog

# Remove translit params from headword templates when the auto-translit
# returns the same thing, or canonicalizing, on pages from STARTFROM to
# (but not including) UPTO, either page names or 0-based integers. Save
# changes if SAVE is true.
def process_headwords(save, startFrom, upTo):
  #for current in blib.references(u"Template:tracking/ar-head/head", startFrom, upTo):
  for cat in [u"Arabic lemmas", u"Arabic non-lemma forms"]:
    for page in blib.cat_articles(cat, startFrom, upTo):
      blib.do_edit(page, process_one_page_headwords, save=save)

# Remove translit params from link-like templates when the auto-translit
# returns the same thing, or canonicalizing, on pages from STARTFROM to
# (but not including) UPTO, either page names or 0-based integers. Save
# changes if SAVE is true.
def process_links(save, startFrom, upTo):
  def do_process_param(page, template, param, paramtr):
    return process_param(page, template, param, paramtr,
        include_tempname_in_changelog=True)
  return blib.process_links(save, startFrom, upTo, do_process_param)

pa = argparse.ArgumentParser(description="Remove redundant translit")
pa.add_argument("-s", "--save", action='store_true',
    help="Save changed pages")
pa.add_argument("-l", "--links", action='store_true',
    help="Vocalize links")
pa.add_argument("start", nargs="?", help="First page to work on")
pa.add_argument("end", nargs="?", help="Last page to work on")

parms = pa.parse_args()
startFrom, upTo = blib.parse_start_end(parms.start, parms.end)

if parms.links:
  process_links(parms.save, startFrom, upTo)
else:
  process_headwords(parms.save, startFrom, upTo)
