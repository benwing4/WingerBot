#!/usr/bin/env python
#coding: utf-8

#    parse_log_file.py is free software: you can redistribute it and/or modify
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

# FIXME!!!
#
# 1. Should output the templates in the order replacement <- original (replacement)
#    so that the replacement is easily available to further modify, and a copy of
#    the replacement remains, while the original is also present
# 2. Needs to handle multiple changes to a given template. All changes to a
#    template should happen in order, but we may have "Replaced FOO with BAR"
#    and then "Replaced BAR with BAZ" and then "Replaced BAZ with BAT" and
#    then "Replaced QUX with FLOX" etc. indicating a new template being processed.
#    All the lines preceding the last "Replaced with" statement need to be
#    processed for Vocalizing/Cross-canoning/etc. statements, all of which list the
#    "ORIGINAL" template at the time, which theoretically could e.g. in the above
#    example be any of FOO, BAR or BAZ. We should check this and use BAT as the
#    replacement.

import re, codecs, argparse

import blib
from blib import msg

pa = argparse.ArgumentParser(description="Parse log files from canon_arabic etc.")
pa.add_argument("-f", "--file", help="Log file")
pa.add_argument("start", nargs="?", help="First page to work on")
pa.add_argument("end", nargs="?", help="Last page to work on")

def yield_page_lines(fn):
  index = None
  pagename = None
  page_lines = []
  replacement_template = None

  def pagemsg(text):
    msg("Page %s %s: %s" % (index, pagename, text))

  def fix_page_line(line):
    if not replacement_template:
      # pagemsg("Can't find replacement template???")
      return line
    m = re.match(r"(^Page [0-9/.-]+ .*?: )((?:Match-canoning|Vocalizing|Self-canoning|Cross-canoning) .*$)",
        line)
    if not m:
      return line
    return "%s%s -> %s" % (m.group(1), m.group(2), replacement_template)

  def spit_out_lines():
    if index != None:
      for line in page_lines:
        yield fix_page_line(line)
      index = None
      pagename = None
      page_lines = []
      replacement_template = None

  for line in codecs.open(fn, "r", encoding="utf-8"):
    line = line.strip()
    m = re.match(r"^Page ([0-9/.-]+) (.*?): (.*)$", line)
    if not m:
      pagemsg("Can't parse line, skipping: [%s]" % line)
    else:
      newindex = m.group(1)
      newpagename = m.group(2)
      if newindex != index or newpagename != pagename:
        if index != None:
          yield index, pagename, [fix_page_line(l) for l in page_lines]
        index = newindex
        pagename = newpagename
        page_lines = []
        replacement_template = None
      mm = re.match(r"Replaced (\{\{.*?\}\}) with (\{\{.*?\}\})$", m.group(3))
      if mm:
        replacement_template = mm.group(2)
      page_lines.append(line)
  if index != None:
    yield index, pagename, [fix_page_line(l) for l in page_lines]

def parse_log_file(fn, startFrom, upTo):
  for current, index in blib.iter_pages(yield_page_lines(fn), startFrom, upTo,
      key=lambda x:x[1]):
    pageindex, pagename, lines = current
    for line in lines:
      m = re.match(r"^Page ([0-9/.-]+) (.*)$", line)
      if m:
        msg("Page %s/%s %s" % (pageindex, m.group(1), m.group(2)))
      else:
        msg(line)

params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)

parse_log_file(params.file, startFrom, upTo)
