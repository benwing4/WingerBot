#!/usr/bin/env python
#coding: utf-8

#    canon_foreign.py is free software: you can redistribute it and/or modify
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

# Canonicalize FOREIGN and LATIN. Return (CANONFOREIGN, CANONLATIN, ACTIONS).
# CANONFOREIGN is accented and/or canonicalized foreign text to
# substitute for the existing foreign text, or False to do nothing.
# CANONLATIN is match-canonicalized or self-canonicalized Latin text to
# substitute for the existing Latin text, or True to remove the Latin
# text parameter entirely, or False to do nothing. ACTIONS is a list of
# actions indicating what was done, to insert into the changelog messages.
# TEMPLATE is the template being processed; PARAM is the name of the
# parameter in this template containing the foreign text; PARAMTR is the
# name of the parameter in this template containing the Latin text. All
# three are used only in status messages and ACTIONS.
def do_canon_param(pagetitle, index, template, param, paramtr, foreign, latin,
    translit_module, include_tempname_in_changelog=False):
  actions = []
  tname = unicode(template.name)
  def pagemsg(text):
    msg("Page %s %s: %s.%s: %s" % (index, pagetitle, tname, param, text))

  if include_tempname_in_changelog:
    paramtrname = "%s.%s" % (template.name, paramtr)
  else:
    paramtrname = paramtr

  # Compute canonforeign and canonlatin
  match_canon = False
  canonlatin = ""
  if latin:
    try:
      canonforeign, canonlatin = translit_module.tr_matching(foreign, latin, True,
          pagemsg)
      match_canon = True
    except Exception as e:
      pagemsg("Unable to accent %s (%s): %s" % (foreign, latin, e))
      canonlatin, canonforeign = translit_module.canonicalize_latin_foreign(latin, foreign)
  else:
    _, canonforeign = translit_module.canonicalize_latin_foreign(None, foreign)

  newlatin = canonlatin == latin and "same" or canonlatin
  newforeign = canonforeign == foreign and "same" or canonforeign

  latintrtext = (latin or canonlatin) and " (%s -> %s)" % (latin, newlatin) or ""

  try:
    translit = translit_module.tr(canonforeign)
    if not translit:
      pagemsg("Unable to auto-translit %s" % foreign)
  except Exception as e:
    pagemsg("Unable to transliterate %s: %s" % (foreign, e))
    translit = None
  if canonforeign == foreign:
    pagemsg("No change in foreign %s%s" % (foreign, latintrtext))
    canonforeign = False
  elif match_canon:
    pagemsg("Vocalize foreign %s -> %s%s" % (foreign, canonforeign, latintrtext))
    actions.append("accent %s=%s -> %s" % (param, foreign, canonforeign))
  # No cross-canonicalizing takes place with foreign.
  #elif latin:
  #  pagemsg("Cross-canoning foreign %s -> %s%s" % (foreign, canonforeign,
  #    latintrtext))
  #  actions.append("cross-canon %s=%s -> %s" % (param, foreign, canonforeign))
  else:
    pagemsg("Self-canoning foreign %s -> %s%s" % (foreign, canonforeign,
      latintrtext))
    actions.append("self-canon %s=%s -> %s" % (param, foreign, canonforeign))
  if not latin:
    pass
  elif translit and translit == canonlatin:
    pagemsg("Removing redundant translit for %s -> %s%s" % (
        foreign, newforeign, latintrtext))
    actions.append("remove redundant %s=%s" % (paramtrname, latin))
    canonlatin = True
  elif canonlatin == latin:
    pagemsg("No change in Latin %s: foreign %s -> %s" %
        (latin, foreign, newforeign))
    canonlatin = False
  elif match_canon:
    pagemsg("Match-canoning Latin %s -> %s: foreign %s -> %s" % (
        latin, canonlatin, foreign, newforeign))
    actions.append("match-canon %s=%s -> %s" % (paramtrname, latin, canonlatin))
  # No cross-canonicalizing takes place with Russian or Ancient Greek.
  #else:
  #  pagemsg("Cross-canoning Latin %s -> %s: foreign %s -> %s" % (
  #      latin, canonlatin, foreign, newforeign))
  #  actions.append("cross-canon %s=%s -> %s" % (paramtrname, latin, canonlatin))
  else:
    pagemsg("Self-canoning Latin %s -> %s: foreign %s -> %s" % (
        latin, canonlatin, foreign, newforeign))
    actions.append("self-canon %s=%s -> %s" % (paramtrname, latin, canonlatin))

  return (canonforeign, canonlatin, actions)

# Attempt to canonicalize foreign parameter PARAM (which may be a list
# [FROMPARAM, TOPARAM], where FROMPARAM may be "page title") and Latin
# parameter PARAMTR. Return False if PARAM has no value, else list of
# changelog actions.
def canon_param(pagetitle, index, template, param, paramtr, translit_module,
    include_tempname_in_changelog=False):
  if isinstance(param, list):
    fromparam, toparam = param
  else:
    fromparam, toparam = (param, param)
  foreign = (pagetitle if fromparam == "page title" else
    getparam(template, fromparam))
  latin = getparam(template, paramtr)
  if not foreign:
    return False
  canonforeign, canonlatin, actions = do_canon_param(pagetitle, index, template,
      fromparam, paramtr, foreign, latin, translit_module,
      include_tempname_in_changelog)
  oldtempl = "%s" % unicode(template)
  if canonforeign:
    template.add(toparam, canonforeign)
  if canonlatin == True:
    template.remove(paramtr)
  elif canonlatin:
    template.add(paramtr, canonlatin)
  if canonforeign or canonlatin:
    msg("Page %s %s: Replaced %s with %s" % (index, pagetitle,
      oldtempl, unicode(template)))
  return actions

def combine_adjacent(values):
  combined = []
  for val in values:
    if combined:
      last_val, num = combined[-1]
      if val == last_val:
        combined[-1] = (val, num + 1)
        continue
    combined.append((val, 1))
  return ["%s(x%s)" % (val, num) if num > 1 else val for val, num in combined]

def sort_group_changelogs(actions):
  grouped_actions = {}
  begins = ["accent ", "remove redundant ", "match-canon ", "cross-canon ",
      "self-canon ", "remove ", ""]
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

  grouped_action_strs = (
    [begin + ', '.join(combine_adjacent(grouped_actions[begin]))
        for begin in begins
        if len(grouped_actions[begin]) > 0])
  all_grouped_actions = '; '.join([x for x in grouped_action_strs if x])
  return all_grouped_actions

# Canonicalize foreign and Latin in link-like templates on pages from STARTFROM
# to (but not including) UPTO, either page names or 0-based integers. Save
# changes if SAVE is true. Show exact changes if VERBOSE is true. CATTYPE
# should be 'vocab', 'borrowed' or 'translation', indicating which categories
# to examine.
def canon_links(save, verbose, cattype, lang, longlang, script,
    translit_module, langs_with_terms_derived_from, startFrom, upTo,
    pages_to_do=[]):
  def process_param(pagetitle, index, template, param, paramtr):
    result = canon_param(pagetitle, index, template, param, paramtr,
        translit_module, include_tempname_in_changelog=True)
    if getparam(template, "sc") == script:
      msg("Page %s %s: %s.%s: Removing sc=%s" % (index,
        pagetitle, unicode(template.name), "sc", script))
      oldtempl = "%s" % unicode(template)
      template.remove("sc")
      msg("Page %s %s: Replaced %s with %s" %
          (index, pagetitle, oldtempl, unicode(template)))
      newresult = ["remove %s.sc=%s" % (template.name, script)]
      if result != False:
        result = result + newresult
      else:
        result = newresult
    return result

  return blib.process_links(save, verbose, lang, longlang, cattype,
      startFrom, upTo, process_param, sort_group_changelogs,
      langs_with_terms_derived_from=langs_with_terms_derived_from,
      pages_to_do=pages_to_do
      #,split_templates=True
      )
