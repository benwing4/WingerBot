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

# This works by modifying lines that end with a template (which is the {{FROM}}
# template, i.e. the template as it stood in Wiktionary before modification)
# to instead end in "{{TO}} <- {{FROM}} ({{TO}})", where TO is the resulting
# modified template currently in Wiktionary. This is done so that the first
# instance of the TO template can be manually edited to make further changes,
# and the previous version of the TO template (as it's actually found in
# Wiktionary) is still present in the second instance so we can update it.
# The TO template comes from "Replaced {{FOO}} with {{BAR}}" statements later
# on in log messages for the same page. Alternatively, there may be no such
# "Replaced ..." messages if nothing changed (e.g. we were unable to vocalize
# and there was no cross-canonicalization or self-canonicalization). We
# become aware of such situations by looking for two successive
# "Processing {{FOO}}" statements with different FOO and without an intervening
# "Replaced ..." message. In this case, FROM == TO.

# Note also that we don't do the template fixups immediately when a
# "Replaced {{FOO}} with {{BAR}}" log message is found, because there may be
# a later "Replaced {{BAR}} with {{BAZ}}" message for the same template, and
# possibly another following "Replaced {{BAZ}} with {{BAT}}", etc. Instead, we
# keep a pointer 'PREV_LINE_REPLACE' to the first line needing replacement
# before the first "Replace ..." line in a series (in this case, the
# "Replaced FOO with BAR" line), and another pointer 'LAST_LINE_REPLACE' to
# the most recent "Replaced ..." line (in this case, "Replaced BAZ with BAT"
# after we have encountered it). When we encounter e.g. "Replaced QUX with FLOX"
# where QUX isn't the same as BAT (the TO-template in the previous replace
# line), we process the lines between those two pointers. (Note that the above
# description is slightly off in that 'PREV_LINE_REPLACE' actually points to
# the line before the first line needing replacement.) In order to facilitate
# this processing, we keep both the latest TO-template (in this case, BAT) as
# well as all the FROM templates (FOO, BAR and BAZ), since any of them may
# occur as the FROM template in one of the lines to be processed.

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
  prev_replace_line = -1
  last_replace_line = -1
  # Last "Processing ... {{FOO}}" template since we encountered a
  # "Replaced {{FOO}} with {{BAR}}" line. This is used to handle the case where
  # we didn't make any replacements (we might have "Unable to vocalize" lines
  # in this section, for example). The first time (at the beginning of the page
  # or after a "Replaced ..." line) that we hit a "Processing ..." line,
  # 'last_processing_template' will be empty and we set it. Next time we hit a
  # "Processing ..." line without an intervening "Replaced ..." line, if the
  # template is the same as before we don't do anything, else we fix up the
  # intervening lines with FROM/TO templates where FROM==TO.
  last_processing_template = None
  # Used to fix up the templates in lines ending with templates.
  # 'REPLACE_FROM_TEMPLATES' is all the possible templates that might appear
  # in a line ending with a template, with the actual template on the line
  # serving as the FROM template, and 'REPLACE_TO_TEMPLATE' is the TO template;
  # we change the FROM template to an annotation TO <- FROM (TO), so that the
  # TO template can be manually edited to make further changes, and the
  # previous version of the TO template (as it's actually found in Wiktionary)
  # is still present so we can update it.
  replace_from_templates = []
  replace_to_template = None

  def pagemsg(text):
    msg("Page %s %s: %s" % (index, pagename, text))

  def fix_page_line(line):
    if not replace_from_templates:
      pagemsg("Can't find replacement template???")
      return line
    #m = re.match(r"(^Page [0-9/.-]+ .*?: (?:Match-canoning|Vocalizing|Self-canoning|Cross-canoning) .*?: )(\{\{.*?\}\}$)",
    #    line)
    # Match any line with a template at the end, after a colon. Includes
    # "Processing {{FOO}}" lines because early on we change them into
    # "Processing: {{FOO}}" lines.
    m = re.match(r"(^Page [0-9/.-]+ .*?: .*?: .*?: )(\{\{.*?\}\}$)", line)
    if not m:
      return line
    linepref = m.group(1)
    old_template = m.group(2)
    if old_template not in replace_from_templates:
      pagemsg("WARNING: Old template %s has no 'Replaced {{FOO}} with {{BAR}}' line"
          % (old_template))
      return line
    return "%s%s <- %s (%s)" % (linepref, replace_to_template, old_template,
        replace_to_template)

  # Fix page lines in the range [FRM+1,TO), where FRM and TO are the indices
  # of the bracketing "Replaced {{FOO}} with {{BAR}}" lines.
  def fix_page_lines(frm, to):
    for i in xrange(frm+1, to):
      page_lines[i] = fix_page_line(page_lines[i])

  for line in codecs.open(fn, "r", encoding="utf-8"):
    line = line.strip()
    # Add a colon after Processing to match other lines
    m = re.match(r"^(Page [^{}]*: )Processing (\{\{.*?\}\})$", line)
    if m:
      line = "%sProcessing: %s" % (m.groups())
    m = re.match(r"^Page ([0-9/.-]+) (.*?): (.*)$", line)
    if not m:
      pagemsg("Can't parse line, skipping: [%s]" % line)
    else:
      newindex = m.group(1)
      newpagename = m.group(2)
      # We're at the end of a page, starting a new one.
      if newindex != index or newpagename != pagename:
        if index != None:
          # Add FROM/TO templates up through the last set of "Replaced"
          # statements.
          fix_page_lines(prev_replace_line, last_replace_line)
          # If there was a "Processing ..." after the last "Replaced" line,
          # it means there was another template processed that we didn't make
          # any changes to; annotate appropriate lines in this section with
          # FROM/TO templates where FROM==TO.
          if last_processing_template:
            replace_from_templates = [last_processing_template]
            replace_to_template = last_processing_template
            fix_page_lines(last_replace_line, len(page_lines))
          yield index, pagename, page_lines
        index = newindex
        pagename = newpagename
        page_lines = []
        prev_replace_line = -1
        last_replace_line = -1
        last_processing_template = None
        replace_from_templates = []
        replace_to_template = None
      mm = re.match(r"Replaced (\{\{.*?\}\}) with (\{\{.*?\}\})$", m.group(3))
      if mm:
        # We found a "Replaced {{FOO}} with {{BAR}} line.
        from_template = mm.group(1)
        to_template = mm.group(2)
        if replace_to_template == from_template:
          replace_from_templates.append(from_template)
          replace_to_template = to_template
        else:
          fix_page_lines(prev_replace_line, last_replace_line)
          prev_replace_line = last_replace_line
          last_replace_line = len(page_lines)
          last_processing_template = None
          replace_from_templates = [from_template]
          replace_to_template = to_template
      else:
        mm = re.match(r".*?: Processing: (\{\{.*?\}\})$", m.group(3))
        if mm:
          processing_template = mm.group(1)
          if last_processing_template and (last_processing_template !=
              processing_template):
            if last_processing_template:
              fix_page_lines(prev_replace_line, last_replace_line)
              replace_from_templates = [last_processing_template]
              replace_to_template = last_processing_template
              fix_page_lines(last_replace_line, len(page_lines))
              replace_from_templates = []
              replace_to_template = None
              # Include the current "Processing" line in the next batch of
              # lines to be processed but set no current lines needing
              # processing.
              last_replace_line = len(page_lines) - 1
              prev_replace_line = last_replace_line
          last_processing_template = processing_template
      page_lines.append(line)
  if index != None:
    fix_page_lines(prev_replace_line, last_replace_line)
    if last_processing_template:
      replace_from_templates = [last_processing_template]
      replace_to_template = last_processing_template
      fix_page_lines(last_replace_line, len(page_lines))
    yield index, pagename, page_lines

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
