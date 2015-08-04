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

site = pywikibot.Site()

# List of Russian vowels minus soft/hard signs
russian_vowels = u"АОУҮЫЭЯЁЮИЕІѢѴаоуүыэяёюиеіѣѵAEIOUYĚƐaeiouyěɛ"
not_russian_vowel_class = "[^%s]" % russian_vowels

def find_russian_need_vowels(save, verbose, direcfile, startFrom, upTo):
  for line in codecs.open(direcfile, "r", encoding="utf-8"):
    line = line.strip()
    m = re.match(r"^(Page [^ ]+ )(.*?)(: .*?: Processing: )(\{\{.*?\}\})( <- \{\{.*?\}\} \(\{\{.*?\}\}\))$",
        line)
    if m:
      pagenum, pagename, processing, repltext, rest = m.groups()
      def check_template_for_missing_accent(pagetitle, index, template,
          ruparam, tr):
        if isinstance(ruparam, list):
          ruparam, _ = ruparam
        if ruparam == "page title":
          val = pagetitle
        else:
          val = getparam(template, ruparam)
        needaccent = False
        for word in re.split(" +", val):
          word = blib.remove_links(word)
          if u"\u0301" in word or u"ё" in word:
            continue
          word = re.sub(not_russian_vowel_class, "", word)
          if len(word) > 1:
            needaccent = True
            break
        if needaccent:
          msg("* %s[[%s]]%s<nowiki>%s%s</nowiki>" % (pagenum, pagename,
            processing, repltext, rest))
        return False
      blib.process_links(save, verbose, "ru", "Russian", "pagetext", None,
          None, check_template_for_missing_accent,
          pages_to_do=[(pagename, repltext)])

pa = blib.init_argparser("Find Russian terms needing accents")
pa.add_argument("--file",
    help="File containing output from parse_log_file.py")

params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)

find_russian_need_vowels(params.save, params.verbose, params.file, startFrom, upTo)
