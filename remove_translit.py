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

import re

import blib, pywikibot
from blib import msg, getparam, addparam

import arabiclib
import ar_translit

# Compare the auto-translit of PARAM with the corresponding transliteration
# parameter PARAMTR. If both found and both the same, remove the translit
# parameter. Otherwise, if PARAM found, try to canonicalize. If a change
# made, return a string describing the action, else True. If PARAM not found,
# return False.
def process_param(pagetitle, index, template, param, paramtr,
    include_tempname_in_changelog=False):
  def pagemsg(text):
    msg("Page %s %s: %s.%s: %s" % (index, pagetitle, template.name, param,
      text))
  arabic = getparam(template, param)
  latin = getparam(template, paramtr)
  if include_tempname_in_changelog:
    paramtrname = "%s.%s" % (template.name, paramtr)
  else:
    paramtrname = paramtr
  if not arabic:
    return False
  if latin == "-":
    pagemsg("Translit is '-', skipping")
    return True
  if latin:
    try:
      _, canonlatin = tr_matching(arabic, latin, True, pagemsg)
      if not canonlatin:
        pagemsg("Unable to match-canonicalize %s (%s)" % (arabic, latin))
    except Exception as e:
      pagemsg("Trying to match-canonicalize %s (%s): %s" % (arabic, latin, e))
      canonlatin = None
    try:
      translit = ar_translit.tr(arabic)
      if not translit:
        pagemsg("Unable to auto-translit %s" % arabic)
    except Exception as e:
      pagemsg("Trying to transliterate %s: %s" % (arabic, e))
      translit = None
    if translit and canonlatin:
      if translit == canonlatin:
      #if (translit == canonlatin or
      #    translit == canonlatin + "un" or
      #    translit == u"ʾ" + canonlatin or
      #    translit == u"ʾ" + canonlatin + "un"):
        pagemsg("Removing redundant translit for %s (%s)" % (arabic, latin))
        oldtempl = "%s" % unicode(template)
        template.remove(paramtr)
        msg("Page %s %s: Replaced %s with %s" %
            (index, pagetitle, oldtempl, unicode(template)))
        return ["remove redundant %s=%s" % (paramtrname, latin)]
      else:
        pagemsg("Auto-translit for %s (%s) not same as manual translit %s (canonicalized %s)" %
            (arabic, translit, latin, canonlatin))
    if canonlatin:
      if latin != canonlatin:
        pagemsg("Match-canonicalizing Latin %s to %s" % (latin, canonlatin))
        oldtempl = "%s" % unicode(template)
        addparam(template, paramtr, canonlatin)
        msg("Page %s %s: Replaced %s with %s" %
            (index, pagetitle, oldtempl, unicode(template)))
        return ["match-canon %s=%s -> %s" % (paramtrname, latin, canonlatin)]
      return True
    canonlatin, _ = ar_translit.canonicalize_latin_arabic(latin, None)
    if latin != canonlatin:
      pagemsg("Self-canonicalizing Latin %s to %s" % (latin, canonlatin))
      oldtempl = "%s" % unicode(template)
      addparam(template, paramtr, canonlatin)
      msg("Page %s %s: Replaced %s with %s" %
          (index, pagetitle, oldtempl, unicode(template)))
      return ["self-canon %s=%s -> %s" % (paramtrname, latin, canonlatin)]
  return True

def sort_group_changelogs(actions):
  grouped_actions = {}
  begins = ["remove redundant ", "match-canon ", "self-canon ", ""]
  for begin in begins:
    grouped_actions[begin] = []
  actiontype = None
  action = ""
  for action in actions:
    for begin in begins:
      if action.startswith(begin):
        actiontag = action.replace(begin, "", 1)
        grouped_actions[begin].append(actiontag)
        break
  grouped_action_strs = \
    [begin + ', '.join(grouped_actions[begin]) for begin in begins
        if len(grouped_actions[begin]) > 0]
  all_grouped_actions = '; '.join([x for x in grouped_action_strs if x])
  return all_grouped_actions

# Process the parameter chain for PARAM in TEMPLATE, looking for translits
# to remove or canonicalize. For example, if PARAM is "pl" then this will
# attempt to process "pl", "pl2", "pl3", etc. based on "pltr", "pl2tr",
# "pl3tr", etc., stopping when "plN" isn't found. Return list of actions
# taken, for use in the changelog message.
def process_param_chain(pagetitle, index, template, param):
  actions = []
  result = process_param(pagetitle, index, template, param, param + "tr")
  if isinstance(result, list):
    actions.extend(result)
  i = 2
  while result:
    thisparam = param + str(i)
    result = process_param(pagetitle, index, template, thisparam, thisparam + "tr")
    if isinstance(result, list):
      actions.extend(result)
    i += 1
  return actions

# Proces the head param(s) for the given headword template on the given page,
# looking for translits to remove or canonicalize. Modifies the templates in
# place. Return list of actions taken, for use in the changelog message.
def process_head(pagetitle, index, template):
  actions = []

  # Handle existing 1= and head from page title
  if template.has("tr"):
    # Try to process 1=
    result = process_param(pagetitle, index, template, "1", "tr")
    if isinstance(result, list):
      actions.extend(result)

  # Check and try to process extra heads
  i = 2
  result = True
  while result:
    thisparam = "head" + str(i)
    result = process_param(pagetitle, index, template, thisparam, "tr" + str(i))
    if isinstance(result, list):
      actions.extend(result)
    i += 1
  return actions

# Process the headword templates on the given page with the given text,
# removing translit params when the auto-translit returns the same thing, or
# canonicalizing. Returns the changed text along with a changelog message.
def process_one_page_headwords(pagetitle, index, text):
  actions = []
  for template in text.filter_templates():
    if template.name in arabiclib.arabic_non_verbal_headword_templates:
      thisactions = []
      tr = getparam(template, "tr")
      thisactions += process_head(pagetitle, index, template)
      for param in ["pl", "plobl", "cpl", "cplobl", "fpl", "fplobl", "f",
          "fobl", "m", "mobl", "obl", "el", "sing", "coll", "d", "dobl",
          "pauc", "cons"]:
        thisactions += process_param_chain(pagetitle, index, template, param)
      if len(thisactions) > 0:
        actions.append("%s: %s" % (template.name, ', '.join(thisactions)))
  changelog = '; '.join(actions)
  #if len(actions) > 0:
  msg("Change log for page %s = %s" % (pagetitle, changelog))
  return text, changelog

# Remove translit params from headword templates when the auto-translit
# returns the same thing, or canonicalizing, on pages from STARTFROM to
# (but not including) UPTO, either page names or 0-based integers. Save
# changes if SAVE is true. Show exact changes if VERBOSE is true.
def process_headwords(save, verbose, startFrom, upTo):
  def process_page(page, index, text):
    return process_one_page_headwords(unicode(page.title()), index, text)
  #for page in blib.references(u"Template:tracking/ar-head/head", startFrom, upTo):
  #for page in blib.references("Template:ar-nisba", startFrom, upTo):
  for cat in [u"Arabic lemmas", u"Arabic non-lemma forms"]:
    for page, index in blib.cat_articles(cat, startFrom, upTo):
      blib.do_edit(page, index, process_page, save=save, verbose=verbose)

# Remove translit params from link-like templates when the auto-translit
# returns the same thing, or canonicalizing, on pages from STARTFROM to
# (but not including) UPTO, either page names or 0-based integers. Save
# changes if SAVE is true. Show exact changes if VERBOSE is true.
# CATTYPE should be 'vocab', 'borrowed' or 'translation', indicating which
# categories to examine.
def process_links(save, verbose, cattype, startFrom, upTo):
  def do_process_param(pagetitle, index, template, param, paramtr):
    result = process_param(pagetitle, index, template, param, paramtr,
        include_tempname_in_changelog=True)
    if getparam(template, "sc") == "Arab":
      msg("Page %s %s: %s.%s: Removing sc=Arab" % (index, pagetitle,
        template.name, "sc"))
      oldtempl = "%s" % unicode(template)
      template.remove("sc")
      msg("Page %s %s: Replaced %s with %s" %
          (index, pagetitle, oldtempl, unicode(template)))
      newresult = ["remove %s.sc=Arab" % template.name]
      if isinstance(result, list):
        result = result + newresult
      else:
        result = newresult
    return result
  return blib.process_links(save, verbose, "ar", "Arabic", cattype,
      startFrom, upTo, do_process_param, sort_group_changelogs)

pa = blib.init_argparser("Remove redundant translit")
pa.add_argument("-l", "--links", action='store_true',
    help="Vocalize links")
pa.add_argument("--cattype", default="borrowed",
    help="Categories to examine ('vocab', 'borrowed', 'translation')")

params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)

if params.links:
  process_links(params.save, params.verbose, params.cattype, startFrom, upTo)
else:
  process_headwords(params.save, params.verbose, startFrom, upTo)
