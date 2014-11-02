#!/usr/bin/env python
#coding: utf-8

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
def process_param(template, param, paramtr):
  arabic = blib.getparam(template, param)
  latin = blib.getparam(template, paramtr)
  if not arabic:
    return False
  if latin:
    try:
      canonlatin = ar_translit.tr_matching_latin(arabic, latin, True)
    except Exception as e:
      msg("Trying to match-canonicalize %s (%s): %s" % (arabic, latin, e))
      canonlatin = None
    try:
      translit = ar_translit.tr(arabic)
    except Exception as e:
      msg("Trying to transliterate %s: %s" % (arabic, e))
      translit = None
    if not translit or not canonlatin:
      msg("%s, %s: Unable to auto-translit Arabic" % (param, arabic))
    if translit and canonlatin:
      if translit == canonlatin:
      #if (translit == canonlatin or
      #    translit == canonlatin + "un" or
      #    translit == u"ʾ" + canonlatin or
      #    translit == u"ʾ" + canonlatin + "un"):
        msg("%s, %s: Removing translit %s" % (param, arabic, latin))
        oldtempl = "%s" % unicode(template)
        template.remove(paramtr)
        msg("Replaced %s with %s" % (oldtempl, unicode(template)))
        return "removing param %s translit %s" % (param, latin)
      else:
        msg("%s, %s: Auto-translit %s not same as manual translit %s (canonicalized %s)" %
            (param, arabic, translit, latin, canonlatin))
    if canonlatin:
      if latin != canonlatin:
        msg("%s: Match-canonicalizing Latin %s to %s" % (param, latin, canonlatin))
        oldtempl = "%s" % unicode(template)
        template.add(paramtr, canonlatin)
        msg("Replaced %s with %s" % (oldtempl, unicode(template)))
        return "match-canonicalizing param %s %s -> %s" % (param, latin, canonlatin)
      return True
    canonlatin = ar_translit.canonicalize_latin(latin)
    if latin != canonlatin:
      msg("%s: Self-canonicalizing Latin %s to %s" % (param, latin, canonlatin))
      oldtempl = "%s" % unicode(template)
      template.add(paramtr, canonlatin)
      msg("Replaced %s with %s" % (oldtempl, unicode(template)))
      return "self-canonicalizing param %s %s -> %s" % (param, latin, canonlatin)
  return True

# Process the parameter chain for PARAM in TEMPLATE, looking for translits
# to remove or canonicalize. For example, if PARAM is "pl" then this will
# attempt to process "pl", "pl2", "pl3", etc. based on "pltr", "pl2tr",
# "pl3tr", etc., stopping when "plN" isn't found. Return list of actions
# taken, for use in the changelog message.
def process_param_chain(template, param):
  actions = []
  result = process_param(template, param, param + "tr")
  if isinstance(result, basestring):
    actions.append(result)
  i = 2
  while result:
    thisparam = param + str(i)
    result = process_param(template, thisparam, thisparam + "tr")
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
    result = process_param(template, "1", "tr")
    if isinstance(result, basestring):
      actions.append(result)

  # Check and try to process extra heads
  i = 2
  result = True
  while result:
    thisparam = "head" + str(i)
    result = process_param(template, thisparam, "tr" + str(i))
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
    if template.name in ["ar-adj", "ar-adv", "ar-coll-noun", "ar-sing-noun", "ar-con", "ar-interj", "ar-noun", "ar-numeral", "ar-part", "ar-prep", "ar-pron", "ar-proper noun", "ar-verbal noun"]: # ar-adj-color, # ar-nisba
      thisactions = []
      tr = blib.getparam(template, "tr")
      thisactions += process_head(page, template)
      for param in ["pl", "cpl", "fpl", "f", "el", "sing", "coll", "d", "pauc", "obl",
          "fobl", "plobl", "dobl"]:
        thisactions += process_param_chain(template, param)
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
  templates_changed = {}

  # Vocalize the link-like templates on the given page with the given text.
  # Returns the changed text along with a changelog message.
  def process_one_page_links(page, text):
    actions = []
    for template in text.filter_templates():
      result = None
      tr = blib.getparam(template, "tr")
      if (#template.name in ["l", "m"] and
          blib.getparam(template, "1") == "ar"):
        # Try to process 2=
        result = process_param(template, "2", "tr")
      elif (#template.name in ["term", "plural of", "definite of", "feminine of", "diminutive of"] and
          blib.getparam(template, "lang") == "ar"):
        # Try to process 1=
        result = process_param(template, "1", "tr")
      if isinstance(result, basestring):
        actions.append(result)
        tempname = unicode(template.name)
        templates_changed[tempname] = templates_changed.get(tempname, 0) + 1
    changelog = '; '.join(actions)
    #if len(terms_processed) > 0:
    msg("Change log for page %s = %s" % (page.title(), changelog))
    return text, changelog

  for cat in [u"Arabic lemmas", u"Arabic non-lemma forms"]:
    for page in blib.cat_articles(cat, startFrom, upTo):
      blib.do_edit(page, process_one_page_links, save=save)
  msg("Templates processed:")
  for template, count in sorted(templates_changed.items(), key=lambda x:-x[1]):
    msg("  %s = %s" % (template, count))

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
