#!/usr/bin/env python
#coding: utf-8

#    rewrite_ar_part.py is free software: you can redistribute it and/or modify
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

def rewrite_one_page_ar_part(page, text):
  for template in text.filter_templates():
    if template.name == "ar-part":
      template.name = "ar-particle"

  return text, "rename {{temp|ar-part}} to {{temp|ar-particle}}"

def rewrite_ar_part(save, verbose, startFrom, upTo):
  for page in blib.references("Template:ar-part", startFrom, upTo):
    blib.do_edit(page, rewrite_one_page_ar_part, save=save, verbose=verbose)

pa = blib.init_argparser("Rewrite ar-part to ar-particle templates")
params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)

rewrite_ar_part(params.save, params.verbose, startFrom, upTo)
