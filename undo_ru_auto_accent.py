#!/usr/bin/env python
#coding: utf-8

#    undo_ru_auto_accent.py is free software: you can redistribute it and/or modify
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

# Undo auto-accent changes made by (misnamed) find_russian_need_vowels
# (actually an auto-accent script), when applied to things that may be
# direct quotations; this is approximated by undoing instances of ux, usex,
# and lang. This will affect many things that are usage examples but not
# quotations; we will have to sort this out manually.
import re, codecs

import blib, pywikibot
from blib import msg, getparam, addparam

site = pywikibot.Site()

def undo_ru_auto_accent(save, verbose, direcfile, startFrom, upTo):
  template_removals = []
  for line in codecs.open(direcfile, "r", encoding="utf-8"):
    line = line.strip()
    m = re.search(r"^Page [0-9]+ (.*?): Replaced (\{\{.*?\}\}) with (\{\{.*?\}\})$",
        line)
    if not m:
      msg("WARNING: Unable to parse line: [%s]" % line)
    else:
      template_removals.append(m.groups())

  for current, index in blib.iter_pages(template_removals, startFrom, upTo,
      # key is the page name
      key = lambda x: x[0]):
    pagename, orig_template, repl_template = current
    if not re.search(r"^\{\{(ux|usex|ru-ux|lang)\|", orig_template):
      continue
    def undo_one_page_ru_auto_accent(page, index, text):
      def pagemsg(txt):
        msg("Page %s %s: %s" % (index, unicode(page.title()), txt))
      text = unicode(text)
      if not re.search("^#\*:* *%s" % re.escape(repl_template), text, re.M):
        return None, ""
      found_orig_template = orig_template in text
      newtext = text.replace(repl_template, orig_template)
      changelog = ""
      if newtext == text:
        if not found_orig_template:
          pagemsg("WARNING: Unable to locate 'repl' template when undoing Russian auto-accenting: %s"
              % repl_template)
        else:
          pagemsg("Original template found, taking no action")
      else:
        pagemsg("Replaced %s with %s" % (repl_template, orig_template))
        if found_orig_template:
          pagemsg("WARNING: Undid replacement, but original template %s already present!" %
              orig_template)
        if len(newtext) - len(text) != len(orig_template) - len(repl_template):
          pagemsg("WARNING: Length mismatch when undoing Russian auto-accenting, may have matched multiple templates: orig=%s, repl=%s" % (
            orig_template, repl_template))
        changelog = "Undid auto-accenting (per Wikitiki89) of %s" % (orig_template)
        pagemsg("Change log = %s" % changelog)
      return newtext, changelog

    page = pywikibot.Page(site, pagename)
    if not page.exists():
      msg("Page %s %s: WARNING, something wrong, does not exist" % (
        index, pagename))
    else:
      blib.do_edit(page, index, undo_one_page_ru_auto_accent, save=save,
          verbose=verbose)

pa = blib.init_argparser("Undo auto-accent changes involving ux, usex and lang templates that look like direct quotes")
pa.add_argument("--file",
    help="File containing log file from original auto-accent run")

params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)

undo_ru_auto_accent(params.save, params.verbose, params.file, startFrom, upTo)
