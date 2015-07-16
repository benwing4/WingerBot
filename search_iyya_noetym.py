#!/usr/bin/env python
#coding: utf-8

#    search_iyya_noetym.py is free software: you can redistribute it and/or modify
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
from blib import msg, getparam, addparam

def search_iyya_noetym(startFrom, upTo):
  for page, index in blib.cat_articles(u"Arabic nouns", startFrom, upTo):
    text = blib.parse(page)
    pagetitle = page.title()
    etym = False
    suffix = False
    if pagetitle.endswith(u"ية"):
      for t in text.filter_templates():
        if t.name in ["ar-etym-iyya", "ar-etym-nisba-a",
            "ar-etym-noun-nisba", "ar-etym-noun-nisba-linking"]:
          etym = True
        if t.name == "suffix":
          suffix = True
      if not etym:
        msg("Page %s %s: Ends with -iyya, no appropriate etym template%s" % (
          index, pagetitle, " (has suffix template)" if suffix else ""))

startFrom, upTo = blib.get_args()

search_iyya_noetym(startFrom, upTo)
