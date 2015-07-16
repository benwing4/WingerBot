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
from blib import msg, getparam, addparam

import arabiclib
import ar_translit

# Vocalize ARABIC based on LATIN. Return vocalized Arabic text if
# vocalization succeeds and is different from the existing Arabic text,
# else False. TEMPLATE is the template being processed and PARAM is the
# name of the parameter in this template being vocalized; both are used
# only in status messages.
def do_vocalize_param(pagetitle, index, template, param, arabic, latin):
  def pagemsg(text):
    msg("Page %s %s: %s.%s: %s" % (index, pagetitle, template.name, param,
      text))
  try:
    vocalized, _ = ar_translit.tr_matching(arabic, latin, True, pagemsg)
  except Exception as e:
    pagemsg("Trying to vocalize %s (%s): %s" % (arabic, latin, e))
    vocalized = None
  if vocalized:
    if vocalized == arabic:
      pagemsg("No change in %s (Latin %s)" % (arabic, latin))
    else:
      pagemsg("Would replace %s with vocalized %s (Latin %s)" % (
          arabic, vocalized, latin))
      return vocalized
  else:
    pagemsg("Unable to vocalize %s (Latin %s)" % (arabic, latin))
  return False

# Attempt to vocalize parameter PARAM based on corresponding transliteration
# parameter PARAMTR. If PARAM not found, return False. Else, return the
# vocalized Arabic if different from unvocalized, else return True.
def vocalize_param(pagetitle, index, template, param, paramtr):
  arabic = getparam(template, param)
  latin = getparam(template, paramtr)
  if not arabic:
    return False
  if latin:
    vocalized = do_vocalize_param(pagetitle, index, template, param, arabic, latin)
    if vocalized:
      oldtempl = "%s" % unicode(template)
      addparam(template, param, vocalized)
      msg("Page %s %s: Replaced %s with %s" % (index, pagetitle,
        oldtempl, unicode(template)))
      return vocalized
  return True

# Vocalize the parameter chain for PARAM in TEMPLATE. For example, if PARAM
# is "pl" then this will attempt to vocalize "pl", "pl2", "pl3", etc. based on
# "pltr", "pl2tr", "pl3tr", etc., stopping when "plN" isn't found. Return
# list of changed parameters, for use in the changelog message.
def vocalize_param_chain(pagetitle, index, template, param):
  paramschanged = []
  result = vocalize_param(pagetitle, index, template, param, param + "tr")
  if isinstance(result, basestring):
    paramschanged.append(param)
  i = 2
  while result:
    thisparam = param + str(i)
    result = vocalize_param(pagetitle, index, template, thisparam, thisparam + "tr")
    if isinstance(result, basestring):
      paramschanged.append(thisparam)
    i += 1
  return paramschanged

# Vocalize the head param(s) for the given headword template on the given page.
# Modifies the templates in place. Return list of changed parameters, for
# use in the changelog message.
def vocalize_head(pagetitle, index, template):
  paramschanged = []
  #pagetitle = unicode(page.title(withNamespace=False))

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
      paramschanged.append("split translit into multiple heads")

    # Try to vocalize 1=
    result = vocalize_param(pagetitle, index, template, "1", "tr")
    if isinstance(result, basestring):
      paramschanged.append("1")

    # If 1= not found, try vocalizing the page title and make it the 1= value
    if not result:
      arabic = unicode(pagetitle)
      latin = getparam(template, "tr")
      if arabic and latin:
        vocalized = do_vocalize_param(pagetitle, index, template, "page title",
            arabic, latin)
        if vocalized:
          oldtempl = "%s" % unicode(template)
          if template.has("2"):
            addparam(template, "1", vocalized, before="2")
          else:
            addparam(template, "1", vocalized, before="tr")
          paramschanged.append("1")
          msg("Page %s %s: Replaced %s with %s" % (index, pagetitle,
            oldtempl, unicode(template)))

  # Check and try to vocalize extra heads
  i = 2
  result = True
  while result:
    thisparam = "head" + str(i)
    result = vocalize_param(pagetitle, index, template, thisparam, "tr" + str(i))
    if isinstance(result, basestring):
      paramschanged.append(thisparam)
    i += 1
  return paramschanged

# Vocalize the headword templates on the given page with the given text.
# Returns the changed text along with a changelog message.
def vocalize_one_page_headwords(pagetitle, index, text):
  actions_taken = []
  for template in text.filter_templates():
    paramschanged = []
    if template.name in arabiclib.arabic_non_verbal_headword_templates:
      paramschanged += vocalize_head(pagetitle, index, template)
      for param in ["pl", "plobl", "cpl", "cplobl", "fpl", "fplobl", "f",
          "fobl", "m", "mobl", "obl", "el", "sing", "coll", "d", "dobl",
          "pauc", "cons"]:
        paramschanged += vocalize_param_chain(pagetitle, index, template, param)
      if len(paramschanged) > 0:
        if template.has("tr"):
          tempname = "%s %s" % (template.name, getparam(template, "tr"))
        else:
          tempname = template.name
        actions_taken.append("%s (%s)" % (', '.join(paramschanged), tempname))
  changelog = "vocalize parameters: %s" % '; '.join(actions_taken)
  #if len(actions_taken) > 0:
  msg("Page %s %s: Change log = %s" % (index, pagetitle, changelog))
  return text, changelog

# Vocalize headword templates on pages from STARTFROM to (but not including)
# UPTO, either page names or 0-based integers. Save changes if SAVE is true.
# Show exact changes if VERBOSE is true.
def vocalize_headwords(save, verbose, startFrom, upTo):
  def process_page(page, index, text):
    return vocalize_one_page_headwords(unicode(page.title()), index, text)
  #for page in blib.references(u"Template:tracking/ar-head/head", startFrom, upTo):
  #for page in blib.references("Template:ar-nisba", startFrom, upTo):
  for cat in [u"Arabic lemmas", u"Arabic non-lemma forms"]:
    for page, index in blib.cat_articles(cat, startFrom, upTo):
      blib.do_edit(page, index, process_page, save=save, verbose=verbose)

# Vocalize link-like templates on pages from STARTFROM to (but not including)
# UPTO, either page names or 0-based integers. Save changes if SAVE is true.
# Show exact changes if VERBOSE is true. CATTYPE should be 'vocab', 'borrowed'
# or 'translation', indicating which categories to examine.
def vocalize_links(save, verbose, cattype, startFrom, upTo):
  def process_param(pagetitle, index, template, param, paramtr):
    result = vocalize_param(pagetitle, index, template, param, paramtr)
    if isinstance(result, basestring):
      result = ["%s (%s)" % (result, template.name)]
    return result
  def join_actions(actions):
    return "vocalize links: %s" % '; '.join(actions)

  return blib.process_links(save, verbose, "ar", "Arabic", cattype,
      startFrom, upTo, process_param, join_actions)

pa = blib.init_argparser("Correct vocalization and translit")
pa.add_argument("-l", "--links", action='store_true',
    help="Vocalize links")
pa.add_argument("--cattype", default="borrowed",
    help="Categories to examine ('vocab', 'borrowed', 'translation')")

params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)

if params.links:
  vocalize_links(params.save, params.verbose, params.cattype, startFrom, upTo)
else:
  vocalize_headwords(params.save, params.verbose, startFrom, upTo)
