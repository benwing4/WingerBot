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
    vocalized = ar_translit.tr_latin_matching(latin, arabic, True)
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
# parameter PARAMTR. Return True if both parameters found, False otherwise.
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
    return True
  else:
    return False

def doparam(template, param):
  result = vocalize(template, param, param + "tr")
  i = 2
  while result:
    result = vocalize(template, param + str(i), param + str(i) + "tr")
    i += 1

def vocalize_head(page, template):
  if not vocalize(template, "1", "tr"):
    pagetitle = page.title(withNamespace=False)
    if template.has("tr"):
      arabic = unicode(pagetitle)
      latin = unicode(template.get("tr").value)
      if not arabic or not latin:
        return
      vocalized = do_vocalize("page title", arabic, latin)
      if vocalized:
        oldtempl = "%s" % unicode(template)
        if template.has("2"):
          template.add("1", vocalized, before="2")
        else:
          template.add("1", vocalized, before="tr")
        uniprint("Replaced %s with %s" % (oldtempl, unicode(template)))
  i = 2
  result = True
  while result:
    result = vocalize(template, "head" + str(i), "tr" + str(i))
    i += 1

def fix(page, text):
  for template in text.filter_templates():
    if template.name in ["ar-adj", "ar-adv", "ar-coll-noun", "ar-sing-noun", "ar-con", "ar-interj", "ar-noun", "ar-numeral", "ar-part", "ar-prep", "ar-pron", "ar-proper noun", "ar-verbal noun"]: # ar-adj-color, # ar-nisba
      vocalize_head(page, template)
      doparam(template, "pl")
      doparam(template, "cpl")
      doparam(template, "fpl")
      doparam(template, "f")
      doparam(template, "el")
      doparam(template, "sing")
      doparam(template, "coll")
      doparam(template, "d")
      doparam(template, "pauc")
      doparam(template, "obl")
      doparam(template, "fobl")
      doparam(template, "plobl")
      doparam(template, "dobl")
  return text, "vocalize parameters"

startFrom, upTo = blib.get_args()

#for current in blib.references(u"Template:tracking/ar-head/head", startFrom, upTo):
for current in blib.cat_articles(u"Arabic collective nouns", startFrom, upTo):
  blib.do_edit(current, fix)
