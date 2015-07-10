#!/usr/bin/env python
#coding: utf-8

#    vocalize.py is free software: you can redistribute it and/or modify
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

import arabiclib
import ar_translit

# Canonicalize ARABIC and LATIN. Return (CANONARABIC, CANONLATIN, ACTIONS).
# CANONARABIC is vocalized and/or canonicalized Arabic text to
# substitute for the existing Arabic text, or False to do nothing.
# CANONLATIN is match-canonicalized or self-canonicalized Latin text to
# substitute for the existing Latin text, or True to remove the Latin
# text parameter entirely, or False to do nothing. ACTIONS is a list of
# actions indicating what was done, to insert into the changelog messages.
# TEMPLATE is the template being processed; PARAM is the name of the
# parameter in this template containing the Arabic text; PARAMTR is the
# name of the parameter in this template containing the Latin text. All
# three are used only in status messages and ACTIONS.
def do_canon_param(page, index, template, param, paramtr, arabic, latin,
    include_tempname_in_changelog=False):
  actions = []
  tname = unicode(template.name)
  def pagemsg(text):
    msg("Page %s %s: %s.%s: %s" % (index, page.title(), tname, param, text))

  if include_tempname_in_changelog:
    paramtrname = "%s.%s" % (template.name, paramtr)
  else:
    paramtrname = paramtr

  # Compute canonarabic and canonlatin
  match_canon = False
  if latin:
    try:
      canonarabic, canonlatin = ar_translit.tr_matching(arabic, latin, True,
          pagemsg)
      match_canon = True
    except Exception as e:
      pagemsg("Unable to vocalize %s (%s): %s" % (arabic, latin, e))
      canonlatin, canonarabic = ar_translit.canonicalize_latin_arabic(latin, arabic)
  else:
    _, canonarabic = ar_translit.canonicalize_latin_arabic(None, arabic)

  newlatin = canonlatin == latin and "same" or canonlatin
  newarabic = canonarabic == arabic and "same" or canonarabic

  try:
    translit = ar_translit.tr(arabic)
    if not translit:
      pagemsg("Unable to auto-translit %s" % arabic)
  except Exception as e:
    pagemsg("Unable to transliterate %s: %s" % (arabic, e))
    translit = None
  if canonarabic == arabic:
    pagemsg("No change in Arabic %s (%s -> %s)" % (
        arabic, latin, newlatin))
    canonarabic = False
  elif match_canon:
    pagemsg("Vocalize Arabic %s -> %s (%s -> %s)" % (
        arabic, canonarabic, latin, newlatin))
    actions.append("vocalize %s=%s -> %s" % (param, arabic, canonarabic))
  elif latin:
    pagemsg("Cross-canoning Arabic %s -> %s (%s -> %s)" % (
        arabic, canonarabic, latin, newlatin))
    actions.append("cross-canon %s=%s -> %s" % (param, arabic, canonarabic))
  else:
    pagemsg("Self-canoning Arabic %s -> %s (%s -> %s)" % (
        arabic, canonarabic, latin, newlatin))
    actions.append("self-canon %s=%s -> %s" % (param, arabic, canonarabic))
  if not latin:
    pass
  elif translit and (translit == canonlatin
      # or translit == canonlatin + "un" or
      #    translit == u"ʾ" + canonlatin or
      #    translit == u"ʾ" + canonlatin + "un"
      ):
    pagemsg("Removing redundant translit for %s -> %s (%s -> %s)" % (
        arabic, newarabic, latin, newlatin))
    actions.append("remove redundant %s=%s" % (paramtrname, latin))
    canonlatin = True
  elif canonlatin == latin:
    pagemsg("No change in Latin %s: Arabic %s -> %s" %
        (latin, arabic, newarabic))
    canonlatin = False
  elif match_canon:
    pagemsg("Match-canoning Latin %s -> %s: Arabic %s -> %s" % (
        latin, canonlatin, arabic, newarabic))
    actions.append("match-canon %s=%s -> %s" % (paramtrname, latin, canonlatin))
  else:
    pagemsg("Cross-canoning Latin %s -> %s: Arabic %s -> %s" % (
        latin, canonlatin, arabic, newarabic))
    actions.append("cross-canon %s=%s -> %s" % (paramtrname, latin, canonlatin))

  return (canonarabic, canonlatin, actions)

# Attempt to canonicalize Arabic parameter PARAM and Latin parameter PARAMTR.
# Return False if PARAM has no value, else list of changelog actions.
def canon_param(page, index, template, param, paramtr,
    include_tempname_in_changelog=False):
  arabic = getparam(template, param)
  latin = getparam(template, paramtr)
  if not arabic:
    return False
  canonarabic, canonlatin, actions = do_canon_param(page, index, template,
      param, paramtr, arabic, latin, include_tempname_in_changelog)
  oldtempl = "%s" % unicode(template)
  if canonarabic:
    template.add(param, canonarabic)
  if canonlatin == True:
    template.remove(paramtr)
  elif canonlatin:
    template.add(paramtr, canonlatin)
  if canonarabic or canonlatin:
    msg("Page %s %s: Replaced %s with %s" % (index, page.title(),
      oldtempl, unicode(template)))
  return actions

def sort_group_changelogs(actions):
  grouped_actions = {}
  begins = ["vocalize ", "remove redundant ", "match-canon ", "cross-canon ",
      "self-canon ", ""]
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

# Vocalize the parameter chain for PARAM in TEMPLATE. For example, if PARAM
# is "pl" then this will attempt to vocalize "pl", "pl2", "pl3", etc. based on
# "pltr", "pl2tr", "pl3tr", etc., stopping when "plN" isn't found. Return
# list of changelog actions.
def canon_param_chain(page, index, template, param):
  actions = []
  result = canon_param(page, index, template, param, param + "tr")
  if result != False:
    actions.extend(result)
  i = 2
  while result != False:
    thisparam = param + str(i)
    result = canon_param(page, index, template, thisparam, thisparam + "tr")
    if result != False:
      actions.extend(result)
    i += 1
  return actions

# Vocalize the head param(s) for the given headword template on the given page.
# Modifies the templates in place. Return list of changed parameters, for
# use in the changelog message.
def canon_head(page, index, template):
  actions = []
  pagetitle = unicode(page.title(withNamespace=False))

  # Handle existing 1= and head from page title
  if template.has("tr"):

    # Check for multiple transliterations of head or 1. If so, split on
    # the multiple transliterations, with separate vocalized heads.
    latin = getparam(template, "tr")
    if "," in latin:
      trs = re.split(",\\s*", latin)
      # Find the first alternate head (head2, head3, ...) not already present
      i = 2
      while template.has("head" + str(i)):
        i += 1
      template.add("tr", trs[0])
      if template.has("1"):
        head = getparam(template, "1")
        # for new heads, only use existing head in 1= if ends with -un (tanwīn),
        # because many of the existing 1= values are vocalized according to the
        # first transliterated entry in the list and won't work with the others
        if not head.endswith(u"\u064C"):
          head = pagetitle
      else:
        head = pagetitle
      for tr in trs[1:]:
        template.add("head" + str(i), head)
        template.add("tr" + str(i), tr)
        i += 1
      actions.append("split translit into multiple heads")

    # Try to vocalize 1=
    result = canon_param(page, index, template, "1", "tr")
    if result != False:
      actions.extend(result)

    # If 1= not found, try vocalizing the page title and make it the 1= value
    if result == False:
      arabic = pagetitle
      latin = getparam(template, "tr")
      if arabic and latin:
        canonarabic, canonlatin, newactions = do_canon_param(
            page, index, template, "page title", "tr", arabic, latin)
        oldtempl = "%s" % unicode(template)
        if canonarabic:
          if template.has("2"):
            template.add("1", canonarabic, before="2")
          else:
            template.add("1", canonarabic, before="tr")
        if canonlatin == True:
          template.remove("tr")
        elif canonlatin:
          template.add("tr", canonlatin)
        actions.extend(newactions)
        if canonarabic or canonlatin:
          msg("Page %s %s: Replaced %s with %s" % (index, pagetitle,
            oldtempl, unicode(template)))

  # Check and try to vocalize extra heads
  i = 2
  result = True
  while result != False:
    thisparam = "head" + str(i)
    result = canon_param(page, index, template, thisparam, "tr" + str(i))
    if result != False:
      actions.extend(result)
    i += 1
  return actions

# Canonicalize the Arabic and Latin in the headword templates on the
# given page. Returns the changed text along with a changelog message.
def canon_one_page_headwords(page, index, text):
  actions = []
  for template in text.filter_templates():
    if template.name in arabiclib.arabic_non_verbal_headword_templates:
      thisactions = []
      thisactions += canon_head(page, index, template)
      for param in ["pl", "plobl", "cpl", "cplobl", "fpl", "fplobl", "f",
          "fobl", "m", "mobl", "obl", "el", "sing", "coll", "d", "dobl",
          "pauc", "cons"]:
        thisactions += canon_param_chain(page, index, template, param)
      if len(thisactions) > 0:
        actions.append("%s: %s" % (template.name, ', '.join(thisactions)))
  changelog = '; '.join(actions)
  #if len(actions) > 0:
  msg("Change log for page %s = %s" % (page.title(), changelog))
  return text, changelog

# Canonicalize Arabic and Latin in headword templates on pages from STARTFROM
# to (but not including) UPTO, either page names or 0-based integers. Save
# changes if SAVE is true. Show exact changes if VERBOSE is true.
def canon_headwords(save, verbose, startFrom, upTo):
  #for page in blib.references(u"Template:tracking/ar-head/head", startFrom, upTo):
  #for page in blib.references("Template:ar-nisba", startFrom, upTo):
  for cat in [u"Arabic lemmas", u"Arabic non-lemma forms"]:
    for page, index in blib.cat_articles(cat, startFrom, upTo):
      blib.do_edit(page, index, canon_one_page_headwords, save=save,
          verbose=verbose)

# Canonicalize Arabic and Latin in link-like templates on pages from STARTFROM
# to (but not including) UPTO, either page names or 0-based integers. Save
# changes if SAVE is true. Show exact changes if VERBOSE is true. CATTYPE
# should be 'arabic', 'borrowed' or 'translit', indicating which categories to
# examine.
def canon_links(save, verbose, cattype, startFrom, upTo):
  def process_param(page, index, template, param, paramtr):
    result = canon_param(page, index, template, param, paramtr,
        include_tempname_in_changelog=True)
    if getparam(template, "sc") == "Arab":
      msg("Page %s %s: %s.%s: Removing sc=Arab" % (index,
        unicode(page.title()), unicode(template.name), "sc"))
      oldtempl = "%s" % unicode(template)
      template.remove("sc")
      msg("Page %s %s: Replaced %s with %s" %
          (index, unicode(page.title()), oldtempl, unicode(template)))
      newresult = ["remove %s.sc=Arab" % template.name]
      if result != False:
        result = result + newresult
      else:
        result = newresult
    return result

  return blib.process_links(save, verbose, cattype, startFrom, upTo,
      process_param, sort_group_changelogs, split_translit_templates=True)

pa = blib.init_argparser("Correct vocalization and translit")
pa.add_argument("-l", "--links", action='store_true',
    help="Correct vocalization and translit of links")
pa.add_argument("--cattype", default="borrowed",
    help="Categories to examine ('arabic', 'borrowed', 'translit')")

parms = pa.parse_args()
startFrom, upTo = blib.parse_start_end(parms.start, parms.end)

if parms.links:
  canon_links(parms.save, parms.verbose, parms.cattype, startFrom, upTo)
else:
  canon_headwords(parms.save, parms.verbose, startFrom, upTo)
