#!/usr/bin/env python
#coding: utf-8

#    rewrite_ar_plural.py is free software: you can redistribute it and/or modify
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

import blib
from blib import getparam, addparam

def rewrite_one_page_ar_nisba(page, index, text):
  for template in text.filter_templates():
    if template.name == "ar-nisba":
      if template.has("head") and not template.has(1):
        head = unicode(template.get("head").value)
        template.remove("head")
        addparam(template, "1", head, before=template.params[0].name if len(template.params) > 0 else None)
      if template.has("plhead"):
        blib.msg("%s has plhead=" % page.title())
  return text, "ar-nisba: head= -> 1="

def rewrite_ar_nisba(save, verbose, startFrom, upTo):
  for page, index in blib.references("Template:ar-nisba", startFrom, upTo):
    blib.do_edit(page, index, rewrite_one_page_ar_nisba, save=save, verbose=verbose)

pa = blib.init_argparser("Rewrite ar-nisba, changing head= to 1=")
params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)

rewrite_ar_nisba(params.save, params.verbose, startFrom, upTo)
