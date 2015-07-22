#!/usr/bin/env python
#coding: utf-8

#    fix_smp.py is free software: you can redistribute it and/or modify
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
from arabiclib import *

def fix_smp(save, verbose, startFrom, upTo):
  for template in arabic_decl_templates:
    # Fix the template refs. If cap= is present, remove it; else, add lc=.
    def fix_one_page_smp(page, index, text):
      pagetitle = page.title()
      for t in text.filter_templates():
        head = reorder_shadda(getparam(t, "1"))
        if t.name.startswith("ar-decl-"):
          param = "pl"
          pl = getparam(t, param)
          i = 2
          while pl:
            if pl == "smp":
              if head.endswith(TAM):
                msg("Page %s %s: WARNING: Found %s=smp with feminine ending head %s in %s: not changing" % (
                  index, pagetitle, param, head, t.name))
              else:
                msg("Page %s %s: Changing %s=smp to %s=sp in %s" % (
                  index, pagetitle, param, param, t.name))
                addparam(t, param, "sp")
            param = "pl%s" % i
            pl = getparam(t, param)
            i += 1
      changelog = "Change pl=smp to pl=sp"
      msg("Page %s %s: Change log = %s" % (index, pagetitle, changelog))
      return text, changelog

    for page, index in blib.references("Template:" + template, startFrom, upTo):
      blib.do_edit(page, index, fix_one_page_smp, save=save,
          verbose=verbose)

pa = blib.init_argparser("Change |pl=smp to |pl=sp in declension templates")
params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)

fix_smp(params.save, params.verbose, startFrom, upTo)
