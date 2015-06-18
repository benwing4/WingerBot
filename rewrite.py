#!/usr/bin/env python
#coding: utf-8

#    rewrite.py is free software: you can redistribute it and/or modify
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

import blib, re
from arabiclib import *

def rewrite_pages(refrom, reto, refs, cat, save, verbose, fix_shadda,
    startFrom, upTo):
  def rewrite_one_page(page, index, text):
    #blib.msg("From: [[%s]], To: [[%s]]" % (refrom, reto))
    text = unicode(text)
    if fix_shadda:
      text = reorder_shadda(text)
    text = re.sub(refrom, reto, text)
    return text, "replace %s -> %s" % (refrom, reto)

  if refs:
    pages = blib.references(refs, startFrom, upTo)
  else:
    pages = blib.cat_articles(cat, startFrom, upTo)
  for page, index in pages:
    blib.do_edit(page, index, rewrite_one_page, save=save, verbose=verbose)

pa = blib.init_argparser("Search and replace on pages")
pa.add_argument("-f", "--from", help="From regex", metavar="FROM",
    dest="from_", required=True)
pa.add_argument("-t", "--to", help="To regex", required=True)
pa.add_argument("-r", "--references", "--refs",
    help="Do pages with references to this page")
pa.add_argument("-c", "--category", "--cat",
    help="Do pages in this category")
pa.add_argument("--reorder-shadda",
    help="""Reorder shadda before search/replace. Generally useful when
doing operations with Arabic text but may trigger unnecessary saves, so not
default.""")
params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)

if not params.references and not params.category:
  raise ValueError("--references or --category must be present")

rewrite_pages(params.from_, params.to, params.references,
    params.category, params.save, params.verbose, params.reorder_shadda,
    startFrom, upTo)
