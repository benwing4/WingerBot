#!/usr/bin/env python
#coding: utf-8

import blib, pywikibot, re, string, sys, codecs
import ar_translit

def uniprint(x):
  print x.encode('utf-8')

# Vocalize ARABIC based on LATIN. Return vocalized Arabic text if
# vocalization succeeds and is different from the existing Arabic text,
# else False.
def do_vocalize(param, arabic, latin):
  try:
    vocalized = ar_translit.tr_matching_arabic(arabic, latin, True)
  except Exception as e:
    uniprint("Trying to vocalize %s (%s): %s" % (arabic, latin, e))
    vocalized = None
  if vocalized:
    if vocalized == arabic:
      uniprint("%s: No change in %s (Latin %s)" % (param, arabic, latin))
    else:
      uniprint("%s: Would replace %s with vocalized %s (Latin %s)" % (
          param, arabic, vocalized, latin))
      return vocalized
  else:
    uniprint("%s: Unable to vocalize %s (Latin %s)" % (
        param, arabic, latin))
  return False

# Attempt to vocalize parameter PARAM based on corresponding transliteration
# parameter PARAMTR. If both parameters found, return the vocalized Arabic if
# different from unvocalized, else return True; if either parameter not found,
# return False.
def vocalize(template, param, paramtr):
  if template.has(param) and template.has(paramtr):
    arabic = unicode(template.get(param).value)
    latin = unicode(template.get(paramtr).value)
    if not arabic or not latin:
      return False
    vocalized = do_vocalize(param, arabic, latin)
    if vocalized:
      oldtempl = "%s" % unicode(template)
      template.add(param, vocalized)
      uniprint("Replaced %s with %s" % (oldtempl, unicode(template)))
      return vocalized
    return True
  else:
    return False

def doparam(template, param):
  paramschanged = []
  result = vocalize(template, param, param + "tr")
  if isinstance(result, basestring):
    paramschanged.append(param)
  i = 2
  while result:
    thisparam = param + str(i)
    result = vocalize(template, thisparam, thisparam + "tr")
    if isinstance(result, basestring):
      paramschanged.append(thisparam)
    i += 1
  return paramschanged

def vocalize_head(page, template):
  paramschanged = []
  result = vocalize(template, "1", "tr")
  if isinstance(result, basestring):
    paramschanged.append("1")
  if not result:
    pagetitle = page.title(withNamespace=False)
    if template.has("tr"):
      arabic = unicode(pagetitle)
      latin = unicode(template.get("tr").value)
      if not arabic or not latin:
        return paramschanged
      vocalized = do_vocalize("page title", arabic, latin)
      if vocalized:
        oldtempl = "%s" % unicode(template)
        if template.has("2"):
          template.add("1", vocalized, before="2")
        else:
          template.add("1", vocalized, before="tr")
        paramschanged.append("1")
        uniprint("Replaced %s with %s" % (oldtempl, unicode(template)))
  i = 2
  result = True
  while result:
    thisparam = "head" + str(i)
    result = vocalize(template, thisparam, "tr" + str(i))
    if isinstance(result, basestring):
      paramschanged.append(thisparam)
    i += 1
  return paramschanged

def fix(page, text):
  actions_taken = []
  numchanged = 0
  for template in text.filter_templates():
    paramschanged = []
    if template.name in ["ar-adj", "ar-adv", "ar-coll-noun", "ar-sing-noun", "ar-con", "ar-interj", "ar-noun", "ar-numeral", "ar-part", "ar-prep", "ar-pron", "ar-proper noun", "ar-verbal noun"]: # ar-adj-color, # ar-nisba
      paramschanged += vocalize_head(page, template)
      for param in ["pl", "cpl", "fpl", "f", "el", "sing", "coll", "d", "pauc", "obl",
          "fobl", "plobl", "dobl"]:
        paramschanged += doparam(template, param)
      numchanged += len(paramschanged)
      if len(paramschanged) > 0:
        if template.has("tr"):
          tempname = "%s %s" % (template.name, unicode(template.get("tr").value))
        else:
          tempname = template.name
        actions_taken.append("%s (%s)" % (', '.join(paramschanged), tempname))
  changelog = "vocalize parameters: %s" % '; '.join(actions_taken)
  #if numchanged > 0:
  uniprint("Change log = %s" % changelog)
  return text, changelog

startFrom, upTo = blib.get_args()

#for current in blib.references(u"Template:tracking/ar-head/head", startFrom, upTo):
for current in blib.cat_articles(u"Arabic collective nouns", startFrom, upTo):
  blib.do_edit(current, fix)
