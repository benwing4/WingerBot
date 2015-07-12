#!/usr/bin/env python
#coding: utf-8

#    format_template.py is free software: you can redistribute it and/or modify
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

def search_category_for_missing_template(pos, templates, save, startFrom, upTo):
  return search_category_for_missing_form(pos, pos, templates, save, startFrom,
      upTo)

def search_category_for_missing_form(form, pos, templates, save, startFrom,
    upTo):
  if not isinstance(templates, list):
    templates = [templates]
  cat = "Arabic %ss" % form
  repltemplate = templates[0]
  msg("---Searching [[Category:%s|%s]] for %s:---" %
      (cat, cat, ' or '.join(["{{temp|%s}}" % temp for temp in templates])))

  def parse_infls(infltext, tr):
    fs = []
    ftrs = []
    pls = []
    pltrs = []
    fpls = []
    fpltrs = []
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
      elif infl.group(3) == "f-p":
        fpls.append(infl.group(1))
        fpltrs.append(infl.group(2))
      else:
        msg("WARNING: Unrecognized inflection gender '%s'" % infl.group(3))
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
    infls = handle_infls(infls, fpls, fpltrs, "fpl")
    return infls

  def remove_empty_args(templ):
    templ = re.sub(r"\|+\}", "}", templ)
    templ = re.sub(r"\|\|+([A-Za-z0-9_]+=)", r"|\1", templ)
    return templ

  def correct_one_page_headword_formatting(page, index, text):
    text = unicode(text)
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
    for m in re.finditer(r'(===+%s===+\s*)\{\{head\|ar\|(?:sc=Arab\|)?%s((?:\|[A-Za-z0-9_]+=(?:\[[^\]]*\]|[^|}])*)*)\}\} *(?:(?:\{\{IPAchar\|)?\((.*?)\)(?:\}\})?)? *((?:,[^,\n]*)*)(.*)' % (pos, form), text, re.I):
      replsfound += 1
      msg("Found match: %s" % m.group(0))
      if m.group(5):
        msg("WARNING: Trailing text %s" % m.group(5))
      head = ""
      g = ""
      tr = None
      for infl in re.finditer(r"\|([A-Za-z0-9_]+)=((?:\[[^\]]*\]|[^|}])*)", m.group(2)):
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
      if m.group(3):
        tr = m.group(3)
      infls = parse_infls(m.group(4), tr)
      repl = "{{%s|%s|%s%s}}" % (repltemplate, head, g, infls)
      repl = remove_empty_args(repl)
      repl = m.group(1) + repl + m.group(5) # Include leading, trailing text
      msg("Replacing\n%s\nwith\n%s" % (m.group(0), repl))
      newtext = text.replace(m.group(0), repl, 1)
      if newtext == text:
        msg("WARNING: Unable to do replacement")
      else:
        text = newtext
    for m in re.finditer(r"(===+%s===+\s*)(?:'*\{\{(?:lang|l)\|ar\|(.*?)\}\}'*|'+([^{}']+)'+) *(?:(?:\{\{IPAchar\|)?\((.*?)\)(?:\}\})?)? *(?:\{\{g\|(.*?)\}\})? *((?:,[^,\n]*)*)(.*)" % pos, text, re.I):
      replsfound += 1
      msg("Found match: %s" % m.group(0))
      if m.group(7):
        msg("WARNING: Trailing text %s" % m.group(7))
      head = m.group(2) or m.group(3)
      g = m.group(5) or ""
      tr = m.group(4)
      infls = parse_infls(m.group(6), tr)
      repl = "{{%s|%s|%s%s}}" % (repltemplate, head, g, infls)
      repl = remove_empty_args(repl)
      repl = m.group(1) + repl + m.group(7) # Include leading, trailing text
      msg("Replacing\n%s\nwith\n%s" % (m.group(0), repl))
      newtext = text.replace(m.group(0), repl, 1)
      if newtext == text:
        msg("WARNING: Unable to do replacement")
      else:
        text = newtext
      # If there's a blank line before and after the category, leave a single
      # blank line
      newtext, nsubs = \
        re.subn(r"\n\n\[\[Category:%s\]\]\n\n" % cat, "\n\n", text, 1)
      if nsubs == 0:
        newtext = re.sub(r"\[\[Category:%s\]\]\n?" % cat, "", text, 1)
      if newtext != text:
        msg("Removed [[Category:%s]]" % cat)
        text = newtext
      else:
        msg("WARNING: Unable to remove [[Category:%s]]" % cat)
    if not sawtemp and replsfound == 0:
      msg("WARNING: No replacements found for {{l|ar|%s}}" % pagetitle)
    return text, "Correct headword formatting for [[:Category:%s]]" % cat

  for page, index in blib.cat_articles(cat, startFrom, upTo):
    blib.do_edit(page, index, correct_one_page_headword_formatting, save=save)

def correct_headword_formatting(save, startFrom, upTo):
  search_category_for_missing_form("plural", "noun", "ar-plural", save, startFrom, upTo)
  search_category_for_missing_template("noun", ["ar-noun", "ar-coll-noun", "ar-sing-noun"], save, startFrom, upTo)
  search_category_for_missing_template("proper noun", "ar-proper noun", save, startFrom, upTo)
  search_category_for_missing_template("adjective", ["ar-adj", "ar-nisba"], save, startFrom, upTo)
  search_category_for_missing_template("collective noun", "ar-coll-noun", save, startFrom, upTo)
  search_category_for_missing_template("singulative noun", "ar-sing-noun", save, startFrom, upTo)
  search_category_for_missing_template("adverb", "ar-adv", save, startFrom, upTo)
  search_category_for_missing_template("conjunction", "ar-con", save, startFrom, upTo)
  search_category_for_missing_template("interjection", "ar-interj", save, startFrom, upTo)
  search_category_for_missing_template("particle", "ar-particle", save, startFrom, upTo)
  search_category_for_missing_template("preposition", "ar-prep", save, startFrom, upTo)
  search_category_for_missing_template("pronoun", "ar-pron", save, startFrom, upTo)

def correct_one_page_link_formatting(page, index, text):
  text = unicode(text)
  pagetitle = page.title()
  linkschanged = []
  for m in re.finditer(r"\{\{l\|ar\|([^}]*?)\}\} *(?:'*(?:(?:\{\{IPAchar\|)?\(([^{})]*?)\)(?:\}\})?)'*)? *(?:\{\{g\|(.*?)\}\})?", text):
    if not m.group(2) and not m.group(3):
      continue
    msg("On page %s, found match: %s" % (pagetitle, m.group(0)))
    if "|tr=" in m.group(1):
      msg("Skipping because translit already present")
      continue
    if m.group(3):
      if m.group(3) == "m|f":
        gender = "|g=m|g2=f"
      else:
        gender = "|g=%s" % m.group(3)
    else:
      gender = ""
    if m.group(2):
      tr = "|tr=%s" % m.group(2)
    else:
      tr = ""
    repl = "{{l|ar|%s%s%s}}" % (m.group(1), tr, gender)
    msg("Replacing\n%s\nwith\n%s" % (m.group(0), repl))
    newtext = text.replace(m.group(0), repl, 1)
    if newtext == text:
      msg("WARNING: Unable to do replacement")
    else:
      text = newtext
      linkschanged.append(m.group(1))
  return text, "incorporated translit/gender into links: %s" % ', '.join(linkschanged)

def correct_link_formatting(save, startFrom, upTo):
  for cat in [u"Arabic lemmas", u"Arabic non-lemma forms"]:
    for page, index in blib.cat_articles(cat, startFrom, upTo):
      blib.do_edit(page, index, correct_one_page_link_formatting, save=save)

pa = blib.init_argparser("Correct formatting of headword templates")
pa.add_argument("-l", "--links", action='store_true',
    help="Vocalize links")

params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)

if params.links:
  correct_link_formatting(params.save, startFrom, upTo)
else:
  correct_headword_formatting(params.save, startFrom, upTo)
