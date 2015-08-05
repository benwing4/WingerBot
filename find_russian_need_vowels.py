#!/usr/bin/env python
#coding: utf-8

#    push_manual_changes.py is free software: you can redistribute it and/or modify
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

templates = ["ru-noun", "ru-proper noun", "ru-verb", "ru-adj", "ru-adv"]

def find_vocalized(term, pagemsg):
  if "[" in term:
    pagemsg("Can't handle links: %s" % term)
    return term
  pagename = remove_diacritics(term)
  page = pywikibot.Page(site, pagename)
  if not page.exists():
    return term
  heads = set()
  for t in blib.parse(page).find_templates():
    if t.name in templates:
      heads.add(getparam(t, "1"))
    elif t.name == "head" and getparam(t, "1") == "ru":
      heads.add(getparam(t, "head"))
  if len(heads) == 0:
    pagemsg("WARNING: Can't find any heads: %s" % pagename)
    return term
  if len(heads) > 1:
    pagemsg("WARNING: Found multiple heads for %s: %s" % (pagename, ", ".join(heads)))
    return term
  return list(heads)[0]

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
  for line in codecs.open(direcfile, "r", encoding="utf-8"):
    line = line.strip()
    m = re.match(r"^(Page [^ ]+ )(.*?)(: .*?:) Processing: (\{\{.*?\}\})( <- \{\{.*?\}\} \(\{\{.*?\}\}\))$",
        line)
    if m:
      pagenum, pagename, tempname, repltext, rest = m.groups()
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
              newval = " ".join(find_vocalized(word)
                  for word in re.split(" +", val))
            if newval != val:
              addparam(template, saveparam, newval)
              if check_need_accent(newval):
                output_line("Need accents (changed)")
              else:
                output_line("Found accents")
            else:
              output_line("Need accents")
          else:
            output_line("Need accents")
        return False
      blib.process_links(save, verbose, "ru", "Russian", "pagetext", None,
          None, check_template_for_missing_accent,
          pages_to_do=[(pagename, repltext)])

pa = blib.init_argparser("Find Russian terms needing accents")
pa.add_argument("--file",
    help="File containing output from parse_log_file.py")
pa.add_argument("--find-accents", action="store_true",
    help="Look up the accents in existing pages")

params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)

find_russian_need_vowels(params.save, params.verbose, params.file, startFrom, upTo)
