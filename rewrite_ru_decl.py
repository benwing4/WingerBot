#!/usr/bin/env python
#coding: utf-8

#    rewrite_ru_decl.py is free software: you can redistribute it and/or modify
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
from blib import msg, getparam, addparam, remove_links

ending_for_ru_adj = {
  "ru-adj1": u"ый",
  "ru-adj2": u"ий",
  "ru-adj3": u"ий",
  "ru-adj4": u"ой",
  "ru-adj5": u"ой",
  "ru-adj6": u"ий",
  "ru-adj7": u"ьий",
  "ru-adj8": u"short",
  "ru-adj9": u"mixed",
  "ru-adj10": u"ый",
  #"ru-adj11": (not yet supported)
  "ru-adj12": u"ий",
  "ru-adj13": u"ой",
}

def clean(value):
  value = remove_links(value)
  value = re.sub(", +", ",", value)
  return value

def rewrite_one_page_ru_decl_adj(page, index, text):
  oldtemps = []
  for t in text.filter_templates():
    converted = True
    origname = t.name
    if t.name == "ru-adj-table":
      t.name = "ru-decl-adj"
    else:
      if re.match("^ru-adjective[0-9]", t.name):
        t.name = t.name.replace("ru-adjective", "ru-adj")
      suffix = None
      if t.name == "ru-adj3-sja":
        suffix = u"ся"
        t.name = "ru-adj3"
      elif t.name == "ru-adj5-suffix":
        suffix = "-" + getparam(t, "8")
        t.name = "ru-adj5"
      if t.name in ending_for_ru_adj:
        addparam(t, "1", getparam(t, "2"))
        addparam(t, "2", ending_for_ru_adj[t.name])
        mshort = clean(getparam(t, "3"))
        fshort = clean(getparam(t, "4"))
        nshort = clean(getparam(t, "5"))
        pshort = clean(getparam(t, "6"))
        t.remove("8")
        t.remove("7")
        t.remove("6")
        t.remove("5")
        t.remove("4")
        t.remove("3")
        if mshort:
          addparam(t, "3", mshort)
        # Note that fshort and nshort get reversed
        if nshort:
          addparam(t, "4", nshort)
        if fshort:
          addparam(t, "5", fshort)
        if pshort:
          addparam(t, "6", pshort)
        if suffix:
          addparam(t, "suffix", suffix)
      else:
        converted = False
    if converted:
      oldtemps.append(unicode(origname))
  return text, "convert %s -> ru-decl-adj" % ", ".join(oldtemps)

def rewrite_ru_decl_adj(save, verbose, startFrom, upTo):
  for cat in [u"Russian adjectives"]:
    for page, index in blib.cat_articles(cat, startFrom, upTo):
      blib.do_edit(page, index, rewrite_one_page_ru_decl_adj, save=save, verbose=verbose)

pa = blib.init_argparser("Rewrite Russian old declension templates")
pa.add_argument("--adjectives", action='store_true',
    help="Rewrite old adjective templates")
pa.add_argument("--nouns", action='store_true',
    help="Rewrite old noun templates")
params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)

rewrite_ru_decl_adj(params.save, params.verbose, startFrom, upTo)
