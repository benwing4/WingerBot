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
from blib import msg

import ar_translit

# Vocalize ARABIC based on LATIN. Return vocalized Arabic text if
# vocalization succeeds and is different from the existing Arabic text,
# else False. PARAM is the name of the parameter being vocalized and is
# used only in status messages.
def do_vocalize_param(param, arabic, latin):
  try:
    vocalized = ar_translit.tr_matching_arabic(arabic, latin, True)
  except Exception as e:
    msg("Trying to vocalize %s (%s): %s" % (arabic, latin, e))
    vocalized = None
  if vocalized:
    if vocalized == arabic:
      msg("%s: No change in %s (Latin %s)" % (param, arabic, latin))
    else:
      msg("%s: Would replace %s with vocalized %s (Latin %s)" % (
          param, arabic, vocalized, latin))
      return vocalized
  else:
    msg("%s: Unable to vocalize %s (Latin %s)" % (
        param, arabic, latin))
  return False

# Attempt to vocalize parameter PARAM based on corresponding transliteration
# parameter PARAMTR. If PARAM not found, return False. Else, return the
# vocalized Arabic if different from unvocalized, else return True.
def vocalize_param(template, param, paramtr):
  arabic = blib.getparam(template, param)
  latin = blib.getparam(template, paramtr)
  if not arabic:
    return False
  if latin:
    vocalized = do_vocalize_param(param, arabic, latin)
    if vocalized:
      oldtempl = "%s" % unicode(template)
      template.add(param, vocalized)
      msg("Replaced %s with %s" % (oldtempl, unicode(template)))
      return vocalized
  return True

# Vocalize the parameter chain for PARAM in TEMPLATE. For example, if PARAM
# is "pl" then this will attempt to vocalize "pl", "pl2", "pl3", etc. based on
# "pltr", "pl2tr", "pl3tr", etc., stopping when "plN" isn't found. Return
# list of changed parameters, for use in the changelog message.
def vocalize_param_chain(template, param):
  paramschanged = []
  result = vocalize_param(template, param, param + "tr")
  if isinstance(result, basestring):
    paramschanged.append(param)
  i = 2
  while result:
    thisparam = param + str(i)
    result = vocalize_param(template, thisparam, thisparam + "tr")
    if isinstance(result, basestring):
      paramschanged.append(thisparam)
    i += 1
  return paramschanged

# Vocalize the head param(s) for the given headword template on the given page.
# Modifies the templates in place. Return list of changed parameters, for
# use in the changelog message.
def vocalize_head(page, template):
  paramschanged = []
  pagetitle = page.title(withNamespace=False)

  # Handle existing 1= and head from page title
  if template.has("tr"):

    # Check for multiple transliterations of head or 1. If so, split on
    # the multiple transliterations, with separate vocalized heads.
    latin = blib.getparam(template, "tr")
    if "," in latin:
      trs = re.split(",\\s*", latin)
      # Find the first alternate head (head2, head3, ...) not already present
      i = 2
      while template.has("head" + str(i)):
        i += 1
      template.add("tr", trs[0])
      if template.has("1"):
        head = blib.getparam(template, "1")
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
      paramschanged.append("split translit into multiple heads")

    # Try to vocalize 1=
    result = vocalize_param(template, "1", "tr")
    if isinstance(result, basestring):
      paramschanged.append("1")

    # If 1= not found, try vocalizing the page title and make it the 1= value
    if not result:
      arabic = unicode(pagetitle)
      latin = blib.getparam(template, "tr")
      if arabic and latin:
        vocalized = do_vocalize_param("page title", arabic, latin)
        if vocalized:
          oldtempl = "%s" % unicode(template)
          if template.has("2"):
            template.add("1", vocalized, before="2")
          else:
            template.add("1", vocalized, before="tr")
          paramschanged.append("1")
          msg("Replaced %s with %s" % (oldtempl, unicode(template)))

  # Check and try to vocalize extra heads
  i = 2
  result = True
  while result:
    thisparam = "head" + str(i)
    result = vocalize_param(template, thisparam, "tr" + str(i))
    if isinstance(result, basestring):
      paramschanged.append(thisparam)
    i += 1
  return paramschanged

# Vocalize the headword templates on the given page with the given text.
# Returns the changed text along with a changelog message.
def vocalize_one_page_headwords(page, text):
  actions_taken = []
  for template in text.filter_templates():
    paramschanged = []
    if template.name in ["ar-adj", "ar-adv", "ar-coll-noun", "ar-sing-noun",
        "ar-con", "ar-interj", "ar-noun", "ar-numeral", "ar-part", "ar-prep",
        "ar-pron", "ar-proper noun", "ar-verbal noun", "ar-noun-pl",
        "ar-adj-pl", "ar-noun-dual", "ar-adj-dual", "ar-nisba"]: # ar-adj-color
      paramschanged += vocalize_head(page, template)
      for param in ["pl", "plobl", "cpl", "cplobl", "fpl", "fplobl", "f",
          "fobl", "m", "mobl", "obl", "el", "sing", "coll", "d", "dobl",
          "pauc", "cons"]:
        paramschanged += vocalize_param_chain(template, param)
      if len(paramschanged) > 0:
        if template.has("tr"):
          tempname = "%s %s" % (template.name, blib.getparam(template, "tr"))
        else:
          tempname = template.name
        actions_taken.append("%s (%s)" % (', '.join(paramschanged), tempname))
  changelog = "vocalize parameters: %s" % '; '.join(actions_taken)
  #if len(actions_taken) > 0:
  msg("Change log = %s" % changelog)
  return text, changelog

# Vocalize headword templates on pages from STARTFROM to (but not including)
# UPTO, either page names or 0-based integers. Save changes if SAVE is true.
def vocalize_headwords(save, startFrom, upTo):
  #for page in blib.references(u"Template:tracking/ar-head/head", startFrom, upTo):
  #for page in blib.references("Template:ar-nisba", startFrom, upTo):
  for cat in [u"Arabic lemmas", u"Arabic non-lemma forms"]:
    for page in blib.cat_articles(cat, startFrom, upTo):
      blib.do_edit(page, vocalize_one_page_headwords, save=save)

# Vocalize link-like templates on pages from STARTFROM to (but not including)
# UPTO, either page names or 0-based integers. Save changes if SAVE is true.
def vocalize_links(save, startFrom, upTo):
  def process_param(page, template, param, paramtr):
    result = vocalize_param(template, param, paramtr)
    if isinstance(result, basestring):
      result = ["%s (%s)" % (result, template.name)]
    return result
  def join_actions(actions):
    return "vocalize links: %s" % '; '.join(actions)

  return blib.process_links(save, startFrom, upTo, process_param, join_actions)

pa = blib.init_argparser("Correct vocalization and translit")
pa.add_argument("-l", "--links", action='store_true',
    help="Vocalize links")

parms = pa.parse_args()
startFrom, upTo = blib.parse_start_end(parms.start, parms.end)

if parms.links:
  vocalize_links(parms.save, startFrom, upTo)
else:
  vocalize_headwords(parms.save, startFrom, upTo)
