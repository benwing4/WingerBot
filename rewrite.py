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

import blib, re, codecs
import pywikibot
from arabiclib import reorder_shadda

def rewrite_pages(refrom, reto, refs, cat, pagefile, comment, save, verbose, startFrom,
    upTo):
  def rewrite_one_page(page, index, text):
    #blib.msg("From: [[%s]], To: [[%s]]" % (refrom, reto))
    text = unicode(text)
    text = reorder_shadda(text)
    text = re.sub(refrom, reto, text)
    return text, comment or "replace %s -> %s" % (refrom, reto)

  if pagefile:
    lines = [x.strip() for x in codecs.open(pagefile, "r", "utf-8")]
    pages = ((pywikibot.Page(blib.site, page), index) for page, index in blib.iter_pages(lines, startFrom, upTo))
  elif refs:
    pages = blib.references(refs, startFrom, upTo, includelinks=True)
  else:
    pages = blib.cat_articles(cat, startFrom, upTo)
  for page, index in pages:
    if verbose:
      blib.msg("Processing %s" % unicode(page.title()))
    blib.do_edit(page, index, rewrite_one_page, save=save, verbose=verbose)

pa = blib.init_argparser("Search and replace on pages")
pa.add_argument("-f", "--from", help="From regex", metavar="FROM",
    dest="from_", required=True)
pa.add_argument("-t", "--to", help="To regex", required=True)
pa.add_argument("-r", "--references", "--refs",
    help="Do pages with references to this page")
pa.add_argument("-c", "--category", "--cat",
    help="Do pages in this category")
pa.add_argument("--comment", help="Specify the change comment to use")
pa.add_argument('--pagefile', help="File containing pages to fix.")
params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)

if not params.references and not params.category and not params.pagefile:
  raise ValueError("--references, --category or --pagefile must be present")

references = params.references and params.references.decode("utf-8")
category = params.category and params.category.decode("utf-8")
from_ = params.from_ and params.from_.decode("utf-8")
to = params.to and params.to.decode("utf-8")
comment = params.comment and params.comment.decode("utf-8")

blib.msg("References to %s" % references)

rewrite_pages(from_, to, references, category, params.pagefile,
    comment, params.save, params.verbose, startFrom, upTo)
