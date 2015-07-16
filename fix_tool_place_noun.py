#!/usr/bin/env python
#coding: utf-8

#    fix_tool_place_noun.py is free software: you can redistribute it and/or modify
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
from blib import msg, getparam, addparam

def fix_tool_place_noun(save, verbose, startFrom, upTo):
  for template in ["ar-tool noun", "ar-noun of place", "ar-instance noun"]:

    # Fix the template refs. If cap= is present, remove it; else, add lc=.
    def fix_one_page_tool_place_noun(page, index, text):
      pagetitle = page.title()
      for t in text.filter_templates():
        if t.name == template:
          if getparam(t, "cap"):
            msg("Page %s %s: Template %s: Remove cap=" %
                (index, pagetitle, template))
            t.remove("cap")
          else:
            msg("Page %s %s: Template %s: Add lc=1" %
                (index, pagetitle, template))
            addparam(t, "lc", "1")
      changelog = "%s: If cap= is present, remove it, else add lc=" % template
      msg("Page %s %s: Change log = %s" % (index, pagetitle, changelog))
      return text, changelog

    for page, index in blib.references("Template:" + template, startFrom, upTo):
      blib.do_edit(page, index, fix_one_page_tool_place_noun, save=save,
          verbose=verbose)

pa = blib.init_argparser("Fix lc vs. cap in tool/place noun etym templates")
params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)

fix_tool_place_noun(params.save, params.verbose, startFrom, upTo)
