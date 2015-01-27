#!/usr/bin/env python
#coding: utf-8
 
import blib, pywikibot, re, string, sys, codecs
 
def fix(page, index, text):
  for template in text.filter_templates():
    if template.name in ["ar-adj", "ar-adj-color", "ar-adv", "ar-coll-noun", "ar-sing-noun", "ar-con", "ar-interj", "ar-noun", "ar-numeral", "ar-particle", "ar-prep", "ar-pron", "ar-proper noun", "ar-verbal noun"]:
      if template.has("head") and not template.has(1) and not template.has(2) and not template.has(3) and not template.has(4) and not template.has(5) and not template.has(6) and not template.has(7) and not template.has(8):
        head = unicode(template.get("head").value)
        template.remove("head")
        template.add("head", head, before=template.params[0].name if len(template.params) > 0 else None)
 
        if template.params[0].name == "head":
          template.get("head").showkey = False
 
  return text, "ar headword: head= > 1="
 
startFrom, upTo = blib.get_args()
 
for page, index in blib.references(u"Template:tracking/ar-head/head", startFrom, upTo):
  blib.do_edit(page, index, fix)
