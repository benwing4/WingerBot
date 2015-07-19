#!/usr/bin/env python
#coding: utf-8

#    undo_greek_removal.py is free software: you can redistribute it and/or modify
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

def undo_greek_removal(save, verbose, direcfile, startFrom, upTo):
  template_removals = []
  for line in codecs.open(direcfile, "r", encoding="utf-8"):
    line = line.strip()
    m = re.match(r"\* \[\[(.*?)]]: Removed (.*?)=.*?: <nowiki>(.*?)</nowiki>$",
        line)
    if not m:
      msg("WARNING: Unable to parse line: [%s]" % line)
    else:
      template_removals.append(m.groups())

  for current, index in blib.iter_pages(template_removals, startFrom, upTo,
      # key is the page name
      key = lambda x: x[0]):
    pagename, removed_param, template_text = current

    def undo_one_page_greek_removal(page, index, text):
      def pagemsg(txt):
        msg("Page %s %s: %s" % (index, unicode(page.title()), txt))
      template = blib.parse_text(template_text).filter_templates()[0]
      orig_template = unicode(template)
      if getparam(template, "sc") == "polytonic":
        template.remove("sc")
      to_template = unicode(template)
      param_value = getparam(template, removed_param)
      template.remove(removed_param)
      from_template = unicode(template)
      text = unicode(text)
      found_orig_template = orig_template in text
      newtext = text.replace(from_template, to_template)
      changelog = ""
      if newtext == text:
        if not found_orig_template:
          pagemsg("WARNING: Unable to locate 'from' template when undoing Greek param removal: %s"
              % from_template)
        else:
          pagemsg("Original template found, taking no action")
      else:
        if found_orig_template:
          pagemsg("WARNING: Undid removal, but original template %s already present!" %
              orig_template)
        if len(newtext) - len(text) != len(to_template) - len(from_template):
          pagemsg("WARNING: Length mismatch when undoing Greek param removal, may have matched multiple templates: from=%s, to=%s" % (
            from_template, to_template))
        changelog = "Undid removal of %s=%s in %s" % (removed_param,
            param_value, to_template)
        pagemsg("Change log = %s" % changelog)
      return newtext, changelog

    page = pywikibot.Page(site, pagename)
    if not page.exists():
      msg("Page %s %s: WARNING, something wrong, does not exist" % (
        index, pagename))
    else:
      blib.do_edit(page, index, undo_one_page_greek_removal, save=save,
          verbose=verbose)

pa = blib.init_argparser("Undo Greek transliteration removal")
pa.add_argument("--file",
    help="File containing templates and removal directives to undo")

params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)

undo_greek_removal(params.save, params.verbose, params.file, startFrom, upTo)
