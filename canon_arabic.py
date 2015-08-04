#!/usr/bin/env python
#coding: utf-8

#    canon_arabic.py is free software: you can redistribute it and/or modify
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

import re, codecs, unicodedata

import blib, pywikibot
from blib import msg, getparam, addparam

import arabiclib
import ar_translit

show_template=True

def nfd_form(txt):
    return unicodedata.normalize("NFD", unicode(txt))

def diff_string(old, new):
  minlen = min(len(old), len(new))
  i = 0
  while i < minlen:
    if old[i] != new[i]:
      return "at pos %s, old %s vs new %s" % (i, old[i],
          new[i])
      break
    i += 1
  else:
    assert len(old) != len(new)
    if len(old) < len(new):
      return "first stray char at pos %s in new = %s" % (i, new[i])
    else:
      return "first stray char at pos %s in old = %s" % (i, old[i])

# Canonicalize ARABIC and LATIN. Return (CANONARABIC, CANONLATIN, ACTIONS).
# CANONARABIC is vocalized and/or canonicalized Arabic text to
# substitute for the existing Arabic text, or False to do nothing.
# CANONLATIN is match-canonicalized or self-canonicalized Latin text to
# substitute for the existing Latin text, or True to remove the Latin
# text parameter entirely, or False to do nothing. ACTIONS is a list of
# actions indicating what was done, to insert into the changelog messages.
# TEMPLATE is the template being processed; FROMPARAM is the name of the
# parameter in this template containing the arabic text; TOPARAM is the
# name of the parameter into which canonicalized arabic text is saved;
# PARAMTR is the name of the parameter in this template containing the Latin
# text. All four are used only in status messages and ACTIONS.
def do_canon_param(pagetitle, index, template, fromparam, toparam, paramtr,
    arabic, latin, include_tempname_in_changelog=False):
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

  # Compute canonarabic and canonlatin
  match_canon = False
  canonlatin = ""
  if latin:
    try:
      canonarabic, canonlatin = ar_translit.tr_matching(arabic, latin, True,
          msgfun=pagemsg)
      match_canon = True
    except Exception as e:
      pagemsg("NOTE: Unable to vocalize %s (%s): %s: %s" % (arabic, latin, e, unicode(template)))
      canonlatin, canonarabic = ar_translit.canonicalize_latin_arabic(latin,
          arabic, msgfun=pagemsg)
  else:
    _, canonarabic = ar_translit.canonicalize_latin_arabic(None, arabic,
        msgfun=pagemsg)

  newlatin = canonlatin == latin and "same" or canonlatin
  newarabic = canonarabic == arabic and "same" or canonarabic

  latintrtext = (latin or canonlatin) and " (%s -> %s)" % (latin, newlatin) or ""

  try:
    translit = ar_translit.tr(canonarabic, msgfun=pagemsg)
    if not translit:
      pagemsg("NOTE: Unable to auto-translit %s (canoned from %s): %s" %
          (canonarabic, arabic, unicode(template)))
  except Exception as e:
    pagemsg("NOTE: Unable to transliterate %s (canoned from %s): %s: %s" %
        (canonarabic, arabic, e, unicode(template)))
    translit = None

  show_diff_string = False
  if canonarabic == arabic:
    pagemsg("No change in Arabic %s%s" % (arabic, latintrtext))
    canonarabic = False
  else:
    if match_canon:
      operation="Vocalizing"
      actionop="vocalize"
    elif latin:
      operation="Cross-canoning"
      actionop="cross-canon"
      show_diff_string = True
    else:
      operation="Self-canoning"
      actionop="self-canon"
      show_diff_string = True
    if show_diff_string:
      diffmsg = " (%s)" % diff_string(arabic, canonarabic)
    else:
      diffmsg = ""
    pagemsg("%s Arabic %s -> %s%s%s: %s" % (operation, arabic, canonarabic,
      latintrtext, diffmsg, unicode(template)))
    if fromparam == toparam:
      actions.append("%s %s=%s -> %s" % (actionop, fromparam, arabic,
        canonarabic))
    else:
      actions.append("%s %s=%s -> %s=%s" % (actionop, fromparam, arabic,
        toparam, canonarabic))
    rdcanonarabic = ar_translit.remove_diacritics(canonarabic)
    rdarabic = ar_translit.remove_diacritics(arabic)
    if rdarabic != rdcanonarabic:
      msgs = []
      if "  " in rdarabic or rdarabic.startswith(" ") or rdarabic.endswith(" "):
        msgs.append("stray space")
      if re.search("[A-Za-z]", nfd_form(rdarabic)):
        msgs.append("Latin")
      if u"\u00A0" in rdarabic:
        msgs.append("NBSP")
      if re.search(u"[\u200E\u200F]", rdarabic):
        msgs.append("L2R/R2L")
      if u"ی" in rdarabic:
        msgs.append("Farsi Yeh")
      if u"ک" in rdarabic:
        msgs.append("Keheh")
      if re.search(u"[\uFB50-\uFDCF]", rdarabic):
        msgs.append("Arabic Pres-A")
      if re.search(u"[\uFDF0-\uFDFF]", rdarabic):
        msgs.append("Arabic word ligatures")
      if re.search(u"[\uFE70-\uFEFF]", rdarabic):
        msgs.append("Arabic Pres-B")
      diffmsg = diff_string(rdarabic, rdcanonarabic)

      pagemsg("NOTE: Without diacritics, old Arabic %s different from canon %s%s (%s): %s"
          % (arabic, canonarabic, msgs and " (in old: %s)" % ", ".join(msgs) or "",
            diffmsg, unicode(template)))

  if not latin:
    pass
  elif translit and (translit == canonlatin
      # or translit == canonlatin + "un" or
      #    translit == u"ʾ" + canonlatin or
      #    translit == u"ʾ" + canonlatin + "un"
      ):
    pagemsg("Removing redundant translit for %s -> %s%s" % (
        arabic, newarabic, latintrtext))
    actions.append("remove redundant %s=%s" % (paramtrname, latin))
    canonlatin = True
  else:
    if match_canon:
      operation="Match-canoning"
      passive="Match-canoned"
      actionop="match-canon"
    else:
      operation="Cross-canoning"
      passive="Cross-canoned"
      actionop="cross-canon"
    if translit:
      pagemsg("NOTE: %s Latin %s not same as auto-translit %s, can't remove: %s" %
          (passive, canonlatin, translit, unicode(template)))
    if canonlatin == latin:
      pagemsg("No change in Latin %s: Arabic %s -> %s (auto-translit %s)" %
          (latin, arabic, newarabic, translit))
      canonlatin = False
    else:
      pagemsg("%s Latin %s -> %s: Arabic %s -> %s (auto-translit %s): %s" % (
          operation, latin, canonlatin, arabic, newarabic, translit,
          unicode(template)))
      actions.append("%s %s=%s -> %s" % (actionop, paramtrname, latin,
        canonlatin))

  return (canonarabic, canonlatin, actions)

# Attempt to canonicalize Arabic parameter PARAM (which may be a list
# [FROMPARAM, TOPARAM], where FROMPARAM may be "page title") and Latin
# parameter PARAMTR. Return False if PARAM has no value, else list of
# changelog actions.
def canon_param(pagetitle, index, template, param, paramtr,
    include_tempname_in_changelog=False):
  if isinstance(param, list):
    fromparam, toparam = param
  else:
    fromparam, toparam = (param, param)
  arabic = (pagetitle if fromparam == "page title" else
    getparam(template, fromparam))
  latin = getparam(template, paramtr)
  if not arabic:
    return False
  canonarabic, canonlatin, actions = do_canon_param(pagetitle, index, template,
      fromparam, toparam, paramtr, arabic, latin, include_tempname_in_changelog)
  oldtempl = "%s" % unicode(template)
  if canonarabic:
    addparam(template, toparam, canonarabic)
  if canonlatin == True:
    template.remove(paramtr)
  elif canonlatin:
    addparam(template, paramtr, canonlatin)
  if canonarabic or canonlatin:
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
  begins = ["split ", "vocalize ", "match-canon ", "cross-canon ",
      "self-canon ", "remove redundant ", "remove ", ""]
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

# Vocalize the parameter chain for PARAM in TEMPLATE. For example, if PARAM
# is "pl" then this will attempt to vocalize "pl", "pl2", "pl3", etc. based on
# "pltr", "pl2tr", "pl3tr", etc., stopping when "plN" isn't found. Return
# list of changelog actions.
def canon_param_chain(pagetitle, index, template, param):
  actions = []
  result = canon_param(pagetitle, index, template, param, param + "tr")
  if result != False:
    actions.extend(result)
  i = 2
  while result != False:
    thisparam = param + str(i)
    result = canon_param(pagetitle, index, template, thisparam, thisparam + "tr")
    if result != False:
      actions.extend(result)
    i += 1
  return actions

# Vocalize the head param(s) for the given headword template on the given page.
# Modifies the templates in place. Return list of changed parameters, for
# use in the changelog message.
def canon_head(pagetitle, index, template):
  actions = []
  #pagetitle = unicode(page.title(withNamespace=False))

  # Handle existing 1= and head from page title
  if template.has("tr"):

    # Check for multiple transliterations of head or 1. If so, split on
    # the multiple transliterations, with separate vocalized heads.
    latin = getparam(template, "tr")
    if "," in latin or "/" in latin:
      trs = re.split("\\s*[,/]\\s*", latin)
      # Find the first alternate head (head2, head3, ...) not already present
      i = 2
      while template.has("head" + str(i)):
        i += 1
      addparam(template, "tr", trs[0])
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
        addparam(template, "head" + str(i), head)
        addparam(template, "tr" + str(i), tr)
        i += 1
      actions.append("split translit into multiple heads")

    # Try to vocalize 1=
    result = canon_param(pagetitle, index, template, "1", "tr")
    if result != False:
      actions.extend(result)

    # If 1= not found, try vocalizing the page title and make it the 1= value
    if result == False:
      arabic = pagetitle
      latin = getparam(template, "tr")
      if arabic and latin:
        canonarabic, canonlatin, newactions = do_canon_param(
            pagetitle, index, template, "page title", "1", "tr", arabic, latin)
        oldtempl = "%s" % unicode(template)
        if canonarabic:
          if template.has("2"):
            addparam(template, "1", canonarabic, before="2")
          else:
            addparam(template, "1", canonarabic, before="tr")
        if canonlatin == True:
          template.remove("tr")
        elif canonlatin:
          addparam(template, "tr", canonlatin)
        actions.extend(newactions)
        if canonarabic or canonlatin:
          msg("Page %s %s: Replaced %s with %s" % (index, pagetitle,
            oldtempl, unicode(template)))

  # Check and try to vocalize extra heads
  i = 2
  result = True
  while result != False:
    thisparam = "head" + str(i)
    result = canon_param(pagetitle, index, template, thisparam, "tr" + str(i))
    if result != False:
      actions.extend(result)
    i += 1
  return actions

# Canonicalize the Arabic and Latin in the headword templates on the
# given page. Returns the changed text along with a changelog message.
def canon_one_page_headwords(pagetitle, index, text):
  actions = []
  for template in text.filter_templates():
    tname = unicode(template.name)
    if tname in arabiclib.arabic_non_verbal_headword_templates:
      thisactions = []
      thisactions += canon_head(pagetitle, index, template)
      for param in ["pl", "plobl", "cpl", "cplobl", "fpl", "fplobl", "f",
          "fobl", "m", "mobl", "obl", "el", "sing", "coll", "d", "dobl",
          "pauc", "cons"]:
        thisactions += canon_param_chain(pagetitle, index, template, param)
      if len(thisactions) > 0:
        actions.append("%s: %s" % (tname, ', '.join(thisactions)))
  changelog = '; '.join(actions)
  #if len(actions) > 0:
  msg("Change log for page %s = %s" % (pagetitle, changelog))
  return text, changelog

# Canonicalize Arabic and Latin in headword templates on pages from STARTFROM
# to (but not including) UPTO, either page names or 0-based integers. Save
# changes if SAVE is true. Show exact changes if VERBOSE is true.
def canon_headwords(save, verbose, startFrom, upTo):
  def process_page(page, index, text):
    return canon_one_page_headwords(unicode(page.title()), index, text)
  #for page in blib.references(u"Template:tracking/ar-head/head", startFrom, upTo):
  #for page in blib.references("Template:ar-nisba", startFrom, upTo):
  for cat in [u"Arabic lemmas", u"Arabic non-lemma forms"]:
    for page, index in blib.cat_articles(cat, startFrom, upTo):
      blib.do_edit(page, index, process_page, save=save, verbose=verbose)

# Canonicalize Arabic and Latin in link-like templates on pages from STARTFROM
# to (but not including) UPTO, either page names or 0-based integers. Save
# changes if SAVE is true. Show exact changes if VERBOSE is true. CATTYPE
# should be 'vocab', 'borrowed', 'translation', 'links', 'pagetext' or 'pages',
# indicating which pages to examine. If CATTYPE is 'pagetext', PAGES_TO_DO
# should be a list of (PAGETITLE, PAGETEXT). If CATTYPE is 'pages', PAGES_TO_DO
# should be a list of page titles, specifying the pages to do.
def canon_links(save, verbose, cattype, startFrom, upTo, pages_to_do=[]):
  def process_param(pagetitle, index, template, param, paramtr):
    result = canon_param(pagetitle, index, template, param, paramtr,
        include_tempname_in_changelog=True)
    if getparam(template, "sc") == "Arab":
      tname = unicode(template.name)
      if show_template and result == False:
        msg("Page %s %s: %s.%s: Processing %s" % (index,
          pagetitle, tname, "sc", unicode(template)))
      msg("Page %s %s: %s.%s: Removing sc=Arab" % (index,
        pagetitle, tname, "sc"))
      oldtempl = "%s" % unicode(template)
      template.remove("sc")
      msg("Page %s %s: Replaced %s with %s" %
          (index, pagetitle, oldtempl, unicode(template)))
      newresult = ["remove %s.sc=Arab" % tname]
      if result != False:
        result = result + newresult
      else:
        result = newresult
    return result

  return blib.process_links(save, verbose, "ar", "Arabic", cattype,
      startFrom, upTo, process_param, sort_group_changelogs,
      pages_to_do=pages_to_do, split_templates=u"[,،/]")

if __name__ == "__main__":
  pa = blib.init_argparser("Correct vocalization and translit")
  pa.add_argument("--headwords", action='store_true',
      help="Correct vocalization and translit of headwords")
  pa.add_argument("--cattype", default="borrowed",
      help="""Categories to examine ('vocab', 'borrowed', 'translation',
  'links', 'pagetext', 'pages' or comma-separated list)""")
  pa.add_argument("--page-file",
      help="""File containing "pages" to process when --cattype pagetext,
  or list of pages when --cattype pages""")

  params = pa.parse_args()
  startFrom, upTo = blib.parse_start_end(params.start, params.end)
  pages_to_do = []
  if params.page_file:
    for line in codecs.open(params.page_file, "r", encoding="utf-8"):
      line = line.strip()
      if params.cattype == "pages":
        pages_to_do.append(line)
      else:
        m = re.match(r"^Page [0-9]+ (.*?): [^:]*: Processing (.*?)$", line)
        if not m:
          msg("WARNING: Unable to parse line: [%s]" % line)
        else:
          pages_to_do.append(m.groups())

  if params.headwords:
    canon_headwords(params.save, params.verbose, startFrom, upTo)
  else:
    canon_links(params.save, params.verbose, params.cattype, startFrom, upTo,
        pages_to_do=pages_to_do)
