#!/usr/bin/env python
#coding: utf-8

import blib, pywikibot, re, string, sys, codecs
import ar_translit
from blib import msg

def search_category_for_missing_template(cat, templates, startFrom, upTo):
  if not isinstance(templates, list):
    templates = [templates]
  msg("---Searching [[Category:%s|%s]] for %s:---" %
      (cat, cat, ' or '.join(["{{temp|%s}}" % temp for temp in templates])))
  for page in blib.cat_articles(cat, startFrom, upTo):
    text = unicode(blib.parse(page))
    pagetitle = page.title()
    sawtemp = False
    for temp in templates:
      if "{{%s" % temp in text:
        sawtemp = True
    if not sawtemp:
      msg("* %s not in {{l|ar|%s}}" % (' or '.join(templates), pagetitle))

def search_no_noun_head(startFrom, upTo):
  search_category_for_missing_template("Arabic adjectives", ["ar-adj", "ar-nisba", "ar-adj-color"], startFrom, upTo)
  search_category_for_missing_template("Arabic nouns", "ar-noun", startFrom, upTo)
  search_category_for_missing_template("Arabic proper nouns", "ar-proper noun", startFrom, upTo)
  search_category_for_missing_template("Arabic collective nouns", "ar-coll-noun", startFrom, upTo)
  search_category_for_missing_template("Arabic singulative nouns", "ar-sing-noun", startFrom, upTo)
  search_category_for_missing_template("Arabic verbal nouns", "ar-verbal noun", startFrom, upTo)
  search_category_for_missing_template("Arabic adverbs", "ar-adv", startFrom, upTo)
  search_category_for_missing_template("Arabic conjunctions", "ar-con", startFrom, upTo)
  search_category_for_missing_template("Arabic interjections", "ar-interj", startFrom, upTo)
  search_category_for_missing_template("Arabic participles", "ar-part", startFrom, upTo)
  search_category_for_missing_template("Arabic prepositions", "ar-prep", startFrom, upTo)
  search_category_for_missing_template("Arabic pronouns", "ar-pron", startFrom, upTo)
  # ["ar-adj", "ar-adv", "ar-coll-noun", "ar-sing-noun", "ar-con", "ar-interj", "ar-noun", "ar-numeral", "ar-part", "ar-prep", "ar-pron", "ar-proper noun", "ar-verbal noun"]: # ar-adj-color, # ar-nisba

startFrom, upTo = blib.get_args()

search_no_noun_head(startFrom, upTo)
