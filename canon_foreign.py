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

import re, unicodedata

import blib, pywikibot
from blib import msg, getparam, addparam

show_template=True

def nfd_form(txt):
    return unicodedata.normalize("NFD", unicode(txt))

# Canonicalize FOREIGN and LATIN. Return (CANONFOREIGN, CANONLATIN, ACTIONS).
# CANONFOREIGN is accented and/or canonicalized foreign text to
# substitute for the existing foreign text, or False to do nothing.
# CANONLATIN is match-canonicalized or self-canonicalized Latin text to
# substitute for the existing Latin text, or True to remove the Latin
# text parameter entirely, or False to do nothing. ACTIONS is a list of
# actions indicating what was done, to insert into the changelog messages.
# TEMPLATE is the template being processed; FROMPARAM is the name of the
# parameter in this template containing the foreign text; TOPARAM is the
# name of the parameter into which canonicalized foreign text is saved;
# PARAMTR is the name of the parameter in this template containing the Latin
# text. All four are used only in status messages and ACTIONS.
def do_canon_param(pagetitle, index, template, fromparam, toparam, paramtr,
    foreign, latin, translit_module, include_tempname_in_changelog=False):
  actions = []
  tname = unicode(template.name)
  def pagemsg(text):
    msg("Page %s %s: %s.%s: %s" % (index, pagetitle, tname, fromparam, text))

  if show_template:
    pagemsg("Processing %s" % (unicode(template)))

  if include_tempname_in_changelog:
    paramtrname = "%s.%s" % (tname, paramtr)
  else:
    paramtrname = paramtr

  if latin == "-":
    pagemsg("Latin is -, taking no action")
    return False, False, []

  # Compute canonforeign and canonlatin
  match_canon = False
  canonlatin = ""
  if latin:
    try:
      canonforeign, canonlatin = translit_module.tr_matching(foreign,
          latin, True, msgfun=pagemsg)
      match_canon = True
    except Exception as e:
      pagemsg("NOTE: Unable to match-canon %s (%s): %s: %s" % (
        foreign, latin, e, unicode(template)))
      canonlatin, canonforeign = (
          translit_module.canonicalize_latin_foreign(latin, foreign,
            msgfun=pagemsg))
  else:
    _, canonforeign = (
        translit_module.canonicalize_latin_foreign(None, foreign,
          msgfun=pagemsg))

  newlatin = canonlatin == latin and "same" or canonlatin
  newforeign = canonforeign == foreign and "same" or canonforeign

  latintrtext = (latin or canonlatin) and " (%s -> %s)" % (latin, newlatin) or ""

  try:
    translit = translit_module.tr(canonforeign, msgfun=pagemsg)
    if not translit:
      pagemsg("NOTE: Unable to auto-translit %s (canoned from %s): %s" %
          (canonforeign, foreign, unicode(template)))
  except Exception as e:
    pagemsg("NOTE: Unable to transliterate %s (canoned from %s): %s: %s" %
        (canonforeign, foreign, e, unicode(template)))
    translit = None

  if canonforeign == foreign:
    pagemsg("No change in foreign %s%s" % (foreign, latintrtext))
    canonforeign = False
  else:
    if match_canon:
      operation="Match-canoning"
      actionop="match-canon"
    # No cross-canonicalizing takes place with Russian or Ancient Greek.
    # (FIXME not true with Russian, but the cross-canonicalizing is minimal.)
    #elif latin:
    #  operation="Cross-canoning"
    #  actionop="cross-canon"
    else:
      operation="Self-canoning"
      actionop="self-canon"
    pagemsg("%s foreign %s -> %s%s" % (operation, foreign, canonforeign,
      latintrtext))
    if fromparam == toparam:
      actions.append("%s %s=%s -> %s" % (actionop, fromparam, foreign,
        canonforeign))
    else:
      actions.append("%s %s=%s -> %s=%s" % (actionop, fromparam, foreign,
        toparam, canonforeign))
    if (translit_module.remove_diacritics(canonforeign) !=
        translit_module.remove_diacritics(foreign)):
      msgs = ""
      if "  " in foreign or foreign.startswith(" ") or foreign.endswith(" "):
        msgs += " (stray space in old foreign)"
      if re.search("[A-Za-z]", nfd_form(foreign)):
        msgs += " (Latin in old foreign)"
      if u"\u00A0" in foreign:
        msgs += " (NBSP in old foreign)"
      if re.search(u"[\u200E\u200F]", foreign):
        msgs += " (L2R/R2L in old foreign)"
      pagemsg("NOTE: Without diacritics, old foreign %s different from canon %s%s: %s"
          % (foreign, canonforeign, msgs, unicode(template)))

  if not latin:
    pass
  elif translit and translit == canonlatin:
    pagemsg("Removing redundant translit for %s -> %s%s" % (
        foreign, newforeign, latintrtext))
    actions.append("remove redundant %s=%s" % (paramtrname, latin))
    canonlatin = True
  else:
    if translit:
      pagemsg("NOTE: Canoned Latin %s not same as auto-translit %s, can't remove: %s" %
          (canonlatin, translit, unicode(template)))
    if canonlatin == latin:
      pagemsg("No change in Latin %s: foreign %s -> %s (auto-translit %s)" %
          (latin, foreign, newforeign, translit))
      canonlatin = False
    else:
      if match_canon:
        operation="Match-canoning"
        actionop="match-canon"
      # No cross-canonicalizing takes place with Russian or Ancient Greek.
      # (FIXME not true with Russian, but the cross-canonicalizing is minimal.)
      #else:
      #  operation="Cross-canoning"
      #  actionop="cross-canon"
      else:
        operation="Self-canoning"
        actionop="self-canon"
      pagemsg("%s Latin %s -> %s: foreign %s -> %s (auto-translit %s)" % (
          operation, latin, canonlatin, foreign, newforeign, translit))
      actions.append("%s %s=%s -> %s" % (actionop, paramtrname, latin,
        canonlatin))

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
  canonforeign, canonlatin, actions = do_canon_param(pagetitle, index,
      template, fromparam, toparam, paramtr, foreign, latin, translit_module,
      include_tempname_in_changelog)
  oldtempl = "%s" % unicode(template)
  if canonforeign:
    addparam(template, toparam, canonforeign)
  if canonlatin == True:
    template.remove(paramtr)
  elif canonlatin:
    addparam(template, paramtr, canonlatin)
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
  begins = ["split ", "match-canon ", "cross-canon ", "self-canon ",
      "remove redundant ", "remove ", ""]
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
# should be 'vocab', 'borrowed', 'translation', 'links', 'pagetext' or 'pages',
# indicating which pages to examine. If CATTYPE is 'pagetext', PAGES_TO_DO
# should be a list of (PAGETITLE, PAGETEXT). If CATTYPE is 'pages', PAGES_TO_DO
# should be a list of page titles, specifying the pages to do. LANG is a
# language code and LONGLANG the canonical language name, as in
# blib.process_links(). SCRIPT is a script code or list of script codes to
# remove from templates. TRANSLIT_MODULE is the module handling
# transliteration, match-canonicalization and removal of diacritics.
def canon_links(save, verbose, cattype, lang, longlang, script,
    translit_module, startFrom, upTo, pages_to_do=[]):
  if not isinstance(script, list):
    script = [script]
  def process_param(pagetitle, index, template, param, paramtr):
    result = canon_param(pagetitle, index, template, param, paramtr,
        translit_module, include_tempname_in_changelog=True)
    scvalue = getparam(template, "sc")
    if scvalue in script:
      tname = unicode(template.name)
      if show_template and result == False:
        msg("Page %s %s: %s.%s: Processing %s" % (index,
          pagetitle, tname, "sc", unicode(template)))
      msg("Page %s %s: %s.%s: Removing sc=%s" % (index,
        pagetitle, tname, "sc", scvalue))
      oldtempl = "%s" % unicode(template)
      template.remove("sc")
      msg("Page %s %s: Replaced %s with %s" %
          (index, pagetitle, oldtempl, unicode(template)))
      newresult = ["remove %s.sc=%s" % (tname, scvalue)]
      if result != False:
        result = result + newresult
      else:
        result = newresult
    return result

  return blib.process_links(save, verbose, lang, longlang, cattype,
      startFrom, upTo, process_param, sort_group_changelogs,
      pages_to_do=pages_to_do)
