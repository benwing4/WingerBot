#!/usr/bin/env python
#coding: utf-8

#    push_manual_changes.py is free software: you can redistribute it and/or modify
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

import blib, pywikibot
from blib import msg, getparam, addparam

site = pywikibot.Site()

def push_manual_changes(save, verbose, direcfile, annotation, startFrom, upTo):
  template_changes = []
  for line in codecs.open(direcfile, "r", encoding="utf-8"):
    line = line.strip()
    m = re.match(r"^Page [^ ]+ (.*?): .*?: (\{\{.*?\}\}) <- \{\{.*?\}\} \((\{\{.*?\}\})\)$",
        line)
    if not m:
      m = re.match(r"^\* (?:Page [^ ]+ )?\[\[(.*?)\]\]: .*?: <nowiki>(\{\{.*?\}\}) <- \{\{.*?\}\} \((\{\{.*?\}\})\)</nowiki>.*$",
          line)
      if not m:
        msg("WARNING: Unable to parse line: [%s]" % line)
        continue
    if m.group(2) != m.group(3):
      # If the current template is the same as the current template of the
      # previous entry, ignore the previous entry; otherwise we won't be
      # able to locate the current template the second time around. This
      # happens e.g. in the output of find_russian_need_vowels.py when
      # processing a template such as cardinalbox or compound that has
      # more than one foreign-language parameter in it.
      if len(template_changes) > 0 and template_changes[-1][2] == m.group(3):
        msg("Ignoring change for pagename %s, %s -> %s" % template_changes[-1])
        template_changes.pop()
      template_changes.append(m.groups())

  for current, index in blib.iter_pages(template_changes, startFrom, upTo,
      # key is the page name
      key = lambda x: x[0]):
    pagename, repl_template, curr_template = current

    def push_one_manual_change(page, index, text):
      def pagemsg(txt):
        msg("Page %s %s: %s" % (index, unicode(page.title()), txt))
      #template = blib.parse_text(template_text).filter_templates()[0]
      #orig_template = unicode(template)
      #if getparam(template, "sc") == "polytonic":
      #  template.remove("sc")
      #to_template = unicode(template)
      #param_value = getparam(template, removed_param)
      #template.remove(removed_param)
      #from_template = unicode(template)
      text = unicode(text)
      found_repl_template = repl_template in text
      newtext = text.replace(curr_template, repl_template)
      changelog = ""
      if newtext == text:
        if not found_repl_template:
          pagemsg("WARNING: Unable to locate current template: %s"
              % curr_template)
        else:
          pagemsg("Replacement template already found, taking no action")
      else:
        if found_repl_template:
          pagemsg("WARNING: Made change, but replacement template %s already present!" %
              repl_template)
        repl_curr_diff = len(repl_template) - len(curr_template)
        newtext_text_diff = len(newtext) - len(text)
        if newtext_text_diff == repl_curr_diff:
          pass
        else:
          ratio = float(newtext_text_diff) / repl_curr_diff
          if ratio == int(ratio):
            pagemsg("WARNING: Replaced %s occurrences of curr=%s with repl=%s"
                % (int(ratio), curr_template, repl_template))
          else:
            pagemsg("WARNING: Something wrong, length mismatch during replacement: Expected length change=%s, actual=%s, ratio=%.2f, curr=%s, repl=%s"
                % (repl_curr_diff, newtext_text_diff, ratio, curr_template,
                  repl_template))
        changelog = "Replaced %s with %s (%s)" % (curr_template, repl_template,
            annotation)
        pagemsg("Change log = %s" % changelog)
      return newtext, changelog

    page = pywikibot.Page(site, pagename)
    if not page.exists():
      msg("Page %s %s: WARNING, something wrong, does not exist" % (
        index, pagename))
    else:
      blib.do_edit(page, index, push_one_manual_change, save=save,
          verbose=verbose)

pa = blib.init_argparser("Push manual changes to Wiktionary")
pa.add_argument("--file",
    help="File containing templates to change, as output by parse_log_file.py")
pa.add_argument("--annotation", default="manually",
    help="Annotation in change log message used to indicate source of changes (default 'manually')")

params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)

push_manual_changes(params.save, params.verbose, params.file, params.annotation, startFrom, upTo)
