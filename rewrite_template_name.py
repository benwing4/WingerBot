#!/usr/bin/env python
#coding: utf-8

#    rewrite_template_name.py is free software: you can redistribute it and/or modify
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

def rewrite_template_names(old, new, save, verbose, startFrom, upTo):
  def rewrite_one_page_template_names(page, text):
    for template in text.filter_templates():
      if template.name == old:
        template.name = new

    return text, "rename {{temp|%s}} to {{temp|%s}}" % (old, new)

  for page in blib.references("Template:%s" % old, startFrom, upTo):
    blib.do_edit(page, rewrite_one_page_template_names, save=save,
        verbose=verbose)

pa = blib.init_argparser("Rewrite old to new template names")
pa.add_argument("-o", "--old", help="Old name of template")
pa.add_argument("-n", "--new", help="new name of template")
params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)

rewrite_template_names(params.old, params.new, params.save, params.verbose,
    startFrom, upTo)
