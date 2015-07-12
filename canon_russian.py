#!/usr/bin/env python
#coding: utf-8

#    canon_russian.py is free software: you can redistribute it and/or modify
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

import ru_translit

# Canonicalize RUSSIAN and LATIN. Return (CANONRUSSIAN, CANONLATIN, ACTIONS).
# CANONRUSSIAN is accented and/or canonicalized Russian text to
# substitute for the existing Russian text, or False to do nothing.
# CANONLATIN is match-canonicalized or self-canonicalized Latin text to
# substitute for the existing Latin text, or True to remove the Latin
# text parameter entirely, or False to do nothing. ACTIONS is a list of
# actions indicating what was done, to insert into the changelog messages.
# TEMPLATE is the template being processed; PARAM is the name of the
# parameter in this template containing the Russian text; PARAMTR is the
# name of the parameter in this template containing the Latin text. All
# three are used only in status messages and ACTIONS.
def do_canon_param(page, index, template, param, paramtr, russian, latin,
    include_tempname_in_changelog=False):
  actions = []
  tname = unicode(template.name)
  def pagemsg(text):
    msg("Page %s %s: %s.%s: %s" % (index, page.title(), tname, param, text))

  if include_tempname_in_changelog:
    paramtrname = "%s.%s" % (template.name, paramtr)
  else:
    paramtrname = paramtr

  # Compute canonrussian and canonlatin
  match_canon = False
  canonlatin = ""
  if latin:
    try:
      canonrussian, canonlatin = ru_translit.tr_matching(russian, latin, True,
          pagemsg)
      match_canon = True
    except Exception as e:
      pagemsg("Unable to accent %s (%s): %s" % (russian, latin, e))
      canonlatin, canonrussian = ru_translit.canonicalize_latin_russian(latin, russian)
  else:
    _, canonrussian = ru_translit.canonicalize_latin_russian(None, russian)

  newlatin = canonlatin == latin and "same" or canonlatin
  newrussian = canonrussian == russian and "same" or canonrussian

  latintrtext = (latin or canonlatin) and " (%s -> %s)" % (latin, newlatin) or ""

  try:
    translit = ru_translit.tr(canonrussian)
    if not translit:
      pagemsg("Unable to auto-translit %s" % russian)
  except Exception as e:
    pagemsg("Unable to transliterate %s: %s" % (russian, e))
    translit = None
  if canonrussian == russian:
    pagemsg("No change in Russian %s%s" % (russian, latintrtext))
    canonrussian = False
  elif match_canon:
    pagemsg("Vocalize Russian %s -> %s%s" % (russian, canonrussian, latintrtext))
    actions.append("accent %s=%s -> %s" % (param, russian, canonrussian))
  # No cross-canonicalizing takes place with Russian.
  #elif latin:
  #  pagemsg("Cross-canoning Russian %s -> %s%s" % (russian, canonrussian,
  #    latintrtext))
  #  actions.append("cross-canon %s=%s -> %s" % (param, russian, canonrussian))
  else:
    pagemsg("Self-canoning Russian %s -> %s%s" % (russian, canonrussian,
      latintrtext))
    actions.append("self-canon %s=%s -> %s" % (param, russian, canonrussian))
  if not latin:
    pass
  elif translit and (translit == canonlatin
      # or translit == canonlatin + "un" or
      #    translit == u"ʾ" + canonlatin or
      #    translit == u"ʾ" + canonlatin + "un"
      ):
    pagemsg("Removing redundant translit for %s -> %s%s" % (
        russian, newrussian, latintrtext))
    actions.append("remove redundant %s=%s" % (paramtrname, latin))
    canonlatin = True
  elif canonlatin == latin:
    pagemsg("No change in Latin %s: Russian %s -> %s" %
        (latin, russian, newrussian))
    canonlatin = False
  elif match_canon:
    pagemsg("Match-canoning Latin %s -> %s: Russian %s -> %s" % (
        latin, canonlatin, russian, newrussian))
    actions.append("match-canon %s=%s -> %s" % (paramtrname, latin, canonlatin))
  # No cross-canonicalizing takes place with Russian.
  #else:
  #  pagemsg("Cross-canoning Latin %s -> %s: Russian %s -> %s" % (
  #      latin, canonlatin, russian, newrussian))
  #  actions.append("cross-canon %s=%s -> %s" % (paramtrname, latin, canonlatin))
  else:
    pagemsg("Self-canoning Latin %s -> %s: Russian %s -> %s" % (
        latin, canonlatin, russian, newrussian))
    actions.append("self-canon %s=%s -> %s" % (paramtrname, latin, canonlatin))

  return (canonrussian, canonlatin, actions)

# Attempt to canonicalize Russian parameter PARAM and Latin parameter PARAMTR.
# Return False if PARAM has no value, else list of changelog actions.
def canon_param(page, index, template, param, paramtr,
    include_tempname_in_changelog=False):
  russian = getparam(template, param)
  latin = getparam(template, paramtr)
  if not russian:
    return False
  canonrussian, canonlatin, actions = do_canon_param(page, index, template,
      param, paramtr, russian, latin, include_tempname_in_changelog)
  oldtempl = "%s" % unicode(template)
  if canonrussian:
    template.add(param, canonrussian)
  if canonlatin == True:
    template.remove(paramtr)
  elif canonlatin:
    template.add(paramtr, canonlatin)
  if canonrussian or canonlatin:
    msg("Page %s %s: Replaced %s with %s" % (index, page.title(),
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

# Canonicalize Russian and Latin in link-like templates on pages from STARTFROM
# to (but not including) UPTO, either page names or 0-based integers. Save
# changes if SAVE is true. Show exact changes if VERBOSE is true. CATTYPE
# should be 'russian', 'borrowed' or 'translit', indicating which categories to
# examine.
def canon_links(save, verbose, cattype, startFrom, upTo):
  def process_param(page, index, template, param, paramtr):
    result = canon_param(page, index, template, param, paramtr,
        include_tempname_in_changelog=True)
    if getparam(template, "sc") == "Cyrl":
      msg("Page %s %s: %s.%s: Removing sc=Cyrl" % (index,
        unicode(page.title()), unicode(template.name), "sc"))
      oldtempl = "%s" % unicode(template)
      template.remove("sc")
      msg("Page %s %s: Replaced %s with %s" %
          (index, unicode(page.title()), oldtempl, unicode(template)))
      newresult = ["remove %s.sc=Cyrl" % template.name]
      if result != False:
        result = result + newresult
      else:
        result = newresult
    return result

  return blib.process_links(save, verbose, "ru", "Russian", cattype,
      startFrom, upTo, process_param, sort_group_changelogs,
      split_translit_templates=True)

pa = blib.init_argparser("Correct accentation and translit")
pa.add_argument("--cattype", default="borrowed",
    help="Categories to examine ('russian', 'borrowed', 'translit')")

parms = pa.parse_args()
startFrom, upTo = blib.parse_start_end(parms.start, parms.end)

canon_links(parms.save, parms.verbose, parms.cattype, startFrom, upTo)

