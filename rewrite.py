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

def rewrite_pages(refrom, reto, refs, cat, pages, pagefile, pagetitle_sub,
    comment, filter_pages, save, verbose, startFrom, upTo):
  def rewrite_one_page(page, index, text):
    #blib.msg("From: [[%s]], To: [[%s]]" % (refrom, reto))
    text = unicode(text)
    text = reorder_shadda(text)
    zipped_fromto = zip(refrom, reto)
    for fromval, toval in zipped_fromto:
      if pagetitle_sub:
        pagetitle = unicode(page.title())
        fromval = fromval.replace(pagetitle_sub, re.escape(pagetitle))
        toval = toval.replace(pagetitle_sub, pagetitle)
      text = re.sub(fromval, toval, text)
    return text, comment or "replace %s" % (", ".join("%s -> %s" % (f, t) for f, t in zipped_fromto))

  if pages:
    pages = ((pywikibot.Page(blib.site, page), index) for page, index in blib.iter_pages(pages, startFrom, upTo))
  elif pagefile:
    lines = [x.strip() for x in codecs.open(pagefile, "r", "utf-8")]
    pages = ((pywikibot.Page(blib.site, page), index) for page, index in blib.iter_pages(lines, startFrom, upTo))
  elif refs:
    pages = blib.references(refs, startFrom, upTo, includelinks=True)
  else:
    pages = blib.cat_articles(cat, startFrom, upTo)
  for page, index in pages:
    pagetitle = unicode(page.title())
    if filter_pages and not re.search(filter_pages, pagetitle):
      blib.msg("Skipping %s because doesn't match --filter-pages regex %s" %
          (pagetitle, filter_pages))
    else:
      if verbose:
        blib.msg("Processing %s" % pagetitle)
      blib.do_edit(page, index, rewrite_one_page, save=save, verbose=verbose)

pa = blib.init_argparser("Search and replace on pages")
pa.add_argument("-f", "--from", help="From regex, can be specified multiple times",
    metavar="FROM", dest="from_", required=True, action="append")
pa.add_argument("-t", "--to", help="To regex, can be specified multiple times",
    required=True, action="append")
pa.add_argument("-r", "--references", "--refs",
    help="Do pages with references to this page")
pa.add_argument("-c", "--category", "--cat",
    help="Do pages in this category")
pa.add_argument("--comment", help="Specify the change comment to use")
pa.add_argument('--filter-pages', help="Regex to use to filter page names.")
pa.add_argument('--pages', help="List of pages to fix, comma-separated.")
pa.add_argument('--pagefile', help="File containing pages to fix.")
pa.add_argument('--pagetitle', help="Value to substitute page title with.")
params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)

if not params.references and not params.category and not params.pages and not params.pagefile:
  raise ValueError("--references, --category, --pages or --pagefile must be present")

references = params.references and params.references.decode("utf-8")
category = params.category and params.category.decode("utf-8")
from_ = [x.decode("utf-8") for x in params.from_]
to = [x.decode("utf-8") for x in params.to]
pages = params.pages and re.split(",", params.pages.decode("utf-8"))
pagetitle_sub = params.pagetitle and params.pagetitle.decode("utf-8")
comment = params.comment and params.comment.decode("utf-8")
filter_pages = params.filter_pages and params.filter_pages.decode("utf-8")

if len(from_) != len(to):
  raise ValueError("Same number of --from and --to arguments must be specified")

rewrite_pages(from_, to, references, category, pages, params.pagefile,
    pagetitle_sub, comment, filter_pages, params.save, params.verbose,
    startFrom, upTo)
