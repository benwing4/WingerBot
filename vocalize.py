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
  pagetitle = page.title(withNamespace=False)

  # Handle existing 1= and head from page title
  if template.has("tr"):

    # Check for multiple transliterations of head or 1. If so, split on
    # the multiple transliterations, with separate vocalized heads.
    latin = unicode(template.get("tr").value)
    if "," in latin:
      trs = re.split(",\\s*", latin)
      # Find the first alternate head (head2, head3, ...) not already present
      i = 2
      while template.has("head" + str(i)):
        i += 1
      template.add("tr", trs[0])
      if template.has("1"):
        head = unicode(template.get("1").value)
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
    result = vocalize(template, "1", "tr")
    if isinstance(result, basestring):
      paramschanged.append("1")

    # If no, try vocalizing the page title and make it the 1= value
    if not result:
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

  # Check and try to vocalize extra heads
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

def vocalize(startFrom, upTo):
  #for current in blib.references(u"Template:tracking/ar-head/head", startFrom, upTo):
  for current in blib.cat_articles(u"Arabic nouns", startFrom, upTo):
    blib.do_edit(current, fix)

def search_noconj(startFrom, upTo):
  for page in blib.cat_articles(u"Arabic verbs", startFrom, upTo):
    text = unicode(blib.parse(page))
    pagetitle = page.title()
    if "{{ar-verb" not in text:
      uniprint("ar-verb not in %s" % pagetitle)
    if "{{ar-conj" not in text:
      uniprint("ar-conj not in %s" % pagetitle)

def search_category_for_missing_template(cat, template, startFrom, upTo):
  uniprint("Searching %s for {{%s|...}}:" % (cat, template))
  for page in blib.cat_articles(cat, startFrom, upTo):
    text = unicode(blib.parse(page))
    pagetitle = page.title()
    if "{{%s" % template not in text:
      uniprint("%s not in %s" % (template, pagetitle))

def search_no_noun_head(startFrom, upTo):
  search_category_for_missing_template("Arabic nouns", "ar-noun", startFrom, upTo)
  search_category_for_missing_template("Arabic proper nouns", "ar-proper noun", startFrom, upTo)
  search_category_for_missing_template("Arabic collective nouns", "ar-coll-noun", startFrom, upTo)
  search_category_for_missing_template("Arabic singulative nouns", "ar-sing-noun", startFrom, upTo)
  search_category_for_missing_template("Arabic verbal nouns", "ar-verbal noun", startFrom, upTo)
  #Might use {{ar-nisba}} or {{ar-adj-color}}
  #search_category_for_missing_template("Arabic adjectives", "ar-adj", startFrom, upTo)
  search_category_for_missing_template("Arabic adverbs", "ar-adv", startFrom, upTo)
  search_category_for_missing_template("Arabic conjunctions", "ar-con", startFrom, upTo)
  search_category_for_missing_template("Arabic interjections", "ar-interj", startFrom, upTo)
  search_category_for_missing_template("Arabic participles", "ar-part", startFrom, upTo)
  search_category_for_missing_template("Arabic prepositions", "ar-prep", startFrom, upTo)
  search_category_for_missing_template("Arabic pronouns", "ar-pron", startFrom, upTo)
  # ["ar-adj", "ar-adv", "ar-coll-noun", "ar-sing-noun", "ar-con", "ar-interj", "ar-noun", "ar-numeral", "ar-part", "ar-prep", "ar-pron", "ar-proper noun", "ar-verbal noun"]: # ar-adj-color, # ar-nisba

startFrom, upTo = blib.get_args()

vocalize(startFrom, upTo)
# search_noconj(startFrom, upTo)
# search_no_noun_head(startFrom, upTo)
