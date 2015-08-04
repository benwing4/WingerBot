#!/usr/bin/env python
#coding: utf-8

#    canon_russian.py is free software: you can redistribute it and/or modify
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

import re, codecs

import blib
import ru_translit
from canon_foreign import canon_links

pa = blib.init_argparser("Canonicalize Russian and translit")
pa.add_argument("--cattype", default="borrowed",
    help="""Categories to examine ('vocab', 'borrowed', 'translation',
'links', 'pagetext', 'pages' or comma-separated list)""")
pa.add_argument("--page-file",
    help="""File containing "pages" to process when --cattype pagetext,
or list of pages when --cattype pages""")

params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)
pages_to_do = []
if params.page_file:
  for line in codecs.open(params.page_file, "r", encoding="utf-8"):
    line = line.strip()
    if params.cattype == "pages":
      pages_to_do.append(line)
    else:
      m = re.match(r"^Page [0-9]+ (.*?): [^:]*: Processing (.*?)$", line)
      if not m:
        msg("WARNING: Unable to parse line: [%s]" % line)
      else:
        pages_to_do.append(m.groups())

canon_links(params.save, params.verbose, params.cattype, "ru", "Russian",
    "Cyrl", ru_translit, startFrom, upTo, pages_to_do=pages_to_do)
