#!/usr/bin/env python
#coding: utf-8

#    find_russian_need_vowels.py is free software: you can redistribute it and/or modify
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

import re, codecs

import blib, pywikibot
from blib import msg, getparam, addparam
from ru_translit import remove_diacritics

site = pywikibot.Site()

# List of Russian vowels minus soft/hard signs
russian_vowels = u"АОУҮЫЭЯЁЮИЕІѢѴаоуүыэяёюиеіѣѵAEIOUYĚƐaeiouyěɛ"
not_russian_vowel_class = "[^%s]" % russian_vowels

templates = ["ru-noun", "ru-proper noun", "ru-verb", "ru-adj", "ru-adv",
  "ru-phrase"]

def find_vocalized(term, pagemsg):
  # We can't handle [[FOO|BAR]] currently; in any case, BAR is generally
  # an inflected term that probably won't have an entry
  if "|" in term:
    pagemsg("Can't handle links with vertical bars: %s" % term)
    return term
  if "<" in term or ">" in term:
    pagemsg("Can't handle stray < or >: %s" % term)
    return term
  # But we can handle plain [[FOO]]
  m = re.match(r"\[\[([^\[\]]*)\]\]$", term)
  if m:
    return "[[" + find_vocalized(m.group(1), pagemsg) + "]]"
  # This can happen if e.g. we're passed "[[FOO]] [[BAR]]".
  if "[" in term or "]" in term:
    pagemsg("Can't handle stray bracket in %s" % term)
    return term
  pagename = remove_diacritics(term)
  page = pywikibot.Page(site, pagename)
  try:
    if not page.exists():
      return term
  except Exception as e:
    pagemsg("WARNING: Error checking page existence: %s" % unicode(e))
    return term
  heads = set()
  def add_if(val):
    val_to_add = blib.remove_links(val)
    if val_to_add:
      heads.add(val_to_add)
  saw_head = False
  for t in blib.parse(page).filter_templates():
    if t.name in templates:
      saw_head = True
      add_if(getparam(t, "1"))
    elif t.name == "head" and getparam(t, "1") == "ru":
      saw_head = True
      add_if(getparam(t, "head"))
  if len(heads) == 0:
    if not saw_head:
      if re.match("#redirect", page.text, re.I):
        pagemsg("Redirect without heads")
      else:
        pagemsg("WARNING: Can't find any heads: %s" % pagename)
    return term
  if len(heads) > 1:
    pagemsg("WARNING: Found multiple heads for %s: %s" % (pagename, ", ".join(heads)))
    return term
  newterm = list(heads)[0]
  if remove_diacritics(newterm) != remove_diacritics(term):
    pagemsg("WARNING: Accented term %s differs from %s in more than just accents" % (
      newterm, term))
  return newterm

def check_need_accent(text):
  for word in re.split(" +", text):
    word = blib.remove_links(word)
    if u"\u0301" in word or u"ё" in word:
      continue
    word = re.sub(not_russian_vowel_class, "", word)
    if len(word) > 1:
      return True
  return False

def find_russian_need_vowels(save, verbose, direcfile, startFrom, upTo):
  processing_lines = []
  for line in codecs.open(direcfile, "r", encoding="utf-8"):
    line = line.strip()
    m = re.match(r"^(Page [^ ]+ )(.*?)(: .*?:) Processing: (\{\{.*?\}\})( <- \{\{.*?\}\} \(\{\{.*?\}\}\))$",
        line)
    if m:
      processing_lines.append(m.groups())

  for current, index in blib.iter_pages(processing_lines, startFrom, upTo,
      # key is the page name
      key = lambda x:x[1]):

    pagenum, pagename, tempname, repltext, rest = current
    def check_template_for_missing_accent(pagetitle, index, template,
        ruparam, tr):
      saveparam = ruparam
      def pagemsg(text):
        msg("Page %s %s: %s" % (index, pagetitle, text))
      def output_line(directive):
        msg("* %s[[%s]]%s %s: <nowiki>%s%s</nowiki>" % (pagenum, pagename,
            tempname, directive, unicode(template), rest))
      if isinstance(ruparam, list):
        ruparam, saveparam = ruparam
      if ruparam == "page title":
        val = pagetitle
      else:
        val = getparam(template, ruparam)
      if check_need_accent(val):
        changed = False
        if params.find_accents:
          newval = find_vocalized(val, pagemsg)
          if newval == val:
            words = re.split(" +", val)
            # Check for "unbalanced" brackets. Can happen if the text is e.g.
            # [[торго́вец]] [[произведение искусства|произведе́ниями иску́сства]]
            # with multiple words inside a bracket -- not really unbalanced
            # but tricky to handle properly.
            unbalanced = False
            for word in words:
              if word.count("[") != word.count("]"):
                pagemsg("WARNING: Unbalanced brackets in %s" % word)
                unbalanced = True
                break
            if not unbalanced:
              newval = " ".join((find_vocalized(word, pagemsg) if
                  check_need_accent(word) else word)
                  for word in words)
          if newval != val:
            if remove_diacritics(newval) != remove_diacritics(val):
              pagemsg("WARNING: Accented page %s changed from %s in more than just accents, not changing" % (newval, val))
            else:
              changed = True
              addparam(template, saveparam, newval)
              if check_need_accent(newval):
                output_line("Need accents (changed)")
              else:
                output_line("Found accents")
        if not changed:
          output_line("Need accents")
      return False
    blib.process_links(save, verbose, "ru", "Russian", "pagetext", None,
        None, check_template_for_missing_accent,
        pages_to_do=[(pagename, repltext)], quiet=True)

pa = blib.init_argparser("Find Russian terms needing accents")
pa.add_argument("--file",
    help="File containing output from parse_log_file.py")
pa.add_argument("--find-accents", action="store_true",
    help="Look up the accents in existing pages")

params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)

find_russian_need_vowels(params.save, params.verbose, params.file, startFrom, upTo)
