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

def rewrite_one_page_ar_plural(page, index, text):
  for template in text.filter_templates():
    if template.name == "ar-plural":
      template.name = "ar-noun-pl"

  return text, "rename {{temp|ar-plural}} to {{temp|ar-noun-pl}}"

def rewrite_ar_plural(save, verbose, startFrom, upTo):
  for cat in [u"Arabic plurals"]:
    for page, index in blib.cat_articles(cat, startFrom, upTo):
      blib.do_edit(page, index, rewrite_one_page_ar_plural, save=save, verbose=verbose)

pa = blib.init_argparser("Rewrite ar-plural to ar-noun-pl templates")
params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)

rewrite_ar_plural(params.save, params.verbose, startFrom, upTo)
