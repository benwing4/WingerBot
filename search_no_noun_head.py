#!/usr/bin/env python
#coding: utf-8

import blib, pywikibot, re, string, sys, codecs
import ar_translit
from blib import msg

def search_category_for_missing_template(pos, templates, startFrom, upTo):
  if not isinstance(templates, list):
    templates = [templates]
  cat = "Arabic %ss" % pos
  repltemplate = templates[0]
  msg("---Searching [[Category:%s|%s]] for %s:---" %
      (cat, cat, ' or '.join(["{{temp|%s}}" % temp for temp in templates])))

  def parse_infls(infltext, tr):
    fs = []
    ftrs = []
    pls = []
    pltrs = []
    for rawinfl in re.split(", *", infltext):
      if not rawinfl:
        continue
      infl = re.match("'*\{\{(?:lang|l)\|ar\|(.*?)\}\}'* *(?:(?:\{\{IPAchar\|)?\((.*?)\)(?:\}\})?)? *\{\{g\|(.*?)\}\}",
        rawinfl)
      if not infl:
        msg("WARNING: Unable to match infl-outside-head %s" % rawinfl)
        continue
      msg("Found infl outside head: %s" % infl.group(0))
      if "|" in infl.group(1):
        msg("WARNING: Found | in head, skipping: %s" % infl.group(1))
        continue
      if infl.group(3) == "f":
        fs.append(infl.group(1))
        ftrs.append(infl.group(2))
      elif infl.group(3) == "p":
        pls.append(infl.group(1))
        pltrs.append(infl.group(2))
      else:
        msg("WARNING: Unrecognized inflection gender '%s'" % infl.group(2))
    infls = ""
    if tr:
      infls += "|tr=%s" % tr
    def handle_infls(infls, arabic, latin, argname):
      count = 1
      for ar in arabic:
        if count == 1:
          arg = argname
        else:
          arg = "%s%s" % (argname, count)
        infls += "|%s=%s" % (arg, ar)
        if latin[count - 1] != None:
          if count == 1:
            larg = "%str" % argname
          else:
            larg = "%s%str" % (argname, count)
          infls += "|%s=%s" % (larg, latin[count - 1])
        count += 1
      return infls
    infls = handle_infls(infls, fs, ftrs, "f")
    infls = handle_infls(infls, pls, pltrs, "pl")
    return infls

  def remove_empty_args(templ):
    templ = re.sub(r"\|+\}", "}", templ)
    templ = re.sub(r"\|\|+([A-Za-z0-9_]+=)", r"|\1", templ)
    return templ

  for page in blib.cat_articles(cat, startFrom, upTo):
    text = unicode(blib.parse(page))
    pagetitle = page.title()
    sawtemp = False
    for temp in templates:
      if "{{%s" % temp in text:
        sawtemp = True
    if not sawtemp:
      if "{{head|ar|" in text:
        msg("* %s not in {{l|ar|%s}} but {{temp|head|ar}} is" % (' or '.join(templates), pagetitle))
      else:
        msg("* %s not in {{l|ar|%s}}, nor {{temp|head|ar}}" % (' or '.join(templates), pagetitle))
    replsfound = 0
    for m in re.finditer(r'===+%s===+\s*\{\{head\|ar\|(?:sc=Arab\|)?%s((?:\|[A-Za-z0-9_]+=(?:\[[^\]]*\]|[^|}])*)*)\}\} *(?:(?:\{\{IPAchar\|)?\((.*?)\)(?:\}\})?)? *((?:,[^,\n]*)*)(.*)' % (pos, pos), text, re.I):
      replsfound += 1
      msg("Found match: %s" % m.group(0))
      if m.group(4):
        msg("WARNING: Trailing text %s" % m.group(4))
      head = ""
      g = ""
      tr = None
      for infl in re.finditer(r"\|([A-Za-z0-9_]+)=((?:\[[^\]]*\]|[^|}])*)", m.group(1)):
        msg("Found infl within head: %s" % infl.group(0))
        if infl.group(1) == "head":
          head = infl.group(2).replace("'", "")
        elif infl.group(1) == "g":
          g = infl.group(2).replace("'", "")
        elif infl.group(1) == "tr":
          tr = infl.group(2)
        elif infl.group(1) == "sc":
          pass
        else:
          msg("WARNING: Unrecognized argument '%s'" % infl.group(1))
      if m.group(2):
        tr = m.group(2)
      infls = parse_infls(m.group(3), tr)
      repl = "{{%s|%s|%s%s}}" % (repltemplate, head, g, infls)
      repl = remove_empty_args(repl)
      repl = repl + m.group(4) # Include trailing text
      msg("Replacing\n%s\nwith\n%s" % (m.group(0), repl))
      newtext = text.replace(m.group(0), repl, 1)
      if newtext == text:
        msg("WARNING: Unable to do replacement")
      else:
        text = newtext
    for m in re.finditer(r"===+%s===+\s*(?:'*{\{(?:lang|l)\|ar\|(.*?)\}\}'*|'+([^{}']+)'+) *(?:(?:\{\{IPAchar\|)?\((.*?)\)(?:\}\})?)? *(?:\{\{g\|(.*?)\}\})? *((?:,[^,\n]*)*)(.*)" % pos, text, re.I):
      replsfound += 1
      msg("Found match: %s" % m.group(0))
      if m.group(6):
        msg("WARNING: Trailing text %s" % m.group(6))
      head = m.group(1) or m.group(2)
      g = m.group(4) or ""
      tr = m.group(3)
      infls = parse_infls(m.group(5), tr)
      repl = "{{%s|%s|%s%s}}" % (repltemplate, head, g, infls)
      repl = remove_empty_args(repl)
      repl = repl + m.group(6) # Include trailing text
      msg("Replacing\n%s\nwith\n%s" % (m.group(0), repl))
      newtext = text.replace(m.group(0), repl, 1)
      if newtext == text:
        msg("WARNING: Unable to do replacement")
      else:
        text = newtext
      newtext = re.sub(r"\[\[Category:%s\]\]\n?" % cat, "", text, 1)
      if newtext != text:
        msg("Removed [[Category:%s]]" % cat)
        text = newtext
      else:
        msg("WARNING: Unable to remove [[Category:%s]]" % cat)
    if not sawtemp and replsfound == 0:
      msg("WARNING: No replacements found for {{l|ar|%s}}" % pagetitle)

def search_no_noun_head(startFrom, upTo):
  search_category_for_missing_template("noun", ["ar-noun", "ar-coll-noun", "ar-sing-noun"], startFrom, upTo)
  search_category_for_missing_template("proper noun", "ar-proper noun", startFrom, upTo)
  search_category_for_missing_template("adjective", ["ar-adj", "ar-nisba", "ar-adj-color"], startFrom, upTo)
  search_category_for_missing_template("collective noun", "ar-coll-noun", startFrom, upTo)
  search_category_for_missing_template("singulative noun", "ar-sing-noun", startFrom, upTo)
  search_category_for_missing_template("verbal noun", "ar-verbal noun", startFrom, upTo)
  search_category_for_missing_template("adverb", "ar-adv", startFrom, upTo)
  search_category_for_missing_template("conjunction", "ar-con", startFrom, upTo)
  search_category_for_missing_template("interjection", "ar-interj", startFrom, upTo)
  search_category_for_missing_template("participle", "ar-part", startFrom, upTo)
  search_category_for_missing_template("preposition", "ar-prep", startFrom, upTo)
  search_category_for_missing_template("pronoun", "ar-pron", startFrom, upTo)
  # ["ar-adj", "ar-adv", "ar-coll-noun", "ar-sing-noun", "ar-con", "ar-interj", "ar-noun", "ar-numeral", "ar-part", "ar-prep", "ar-pron", "ar-proper noun", "ar-verbal noun"]: # ar-adj-color, # ar-nisba

startFrom, upTo = blib.get_args()

search_no_noun_head(startFrom, upTo)
