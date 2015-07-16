#!/usr/bin/env python
#coding: utf-8

#    search_noconj.py is free software: you can redistribute it and/or modify
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

def search_noconj(startFrom, upTo):
  for page, index in blib.cat_articles(u"Arabic verbs", startFrom, upTo):
    text = unicode(blib.parse(page))
    pagetitle = page.title()
    if "{{ar-verb" not in text:
      msg("* ar-verb not in {{l|ar|%s}}" % pagetitle)
    if "{{ar-conj" not in text:
      msg("* ar-conj not in {{l|ar|%s}}" % pagetitle)

startFrom, upTo = blib.get_args()

search_noconj(startFrom, upTo)
