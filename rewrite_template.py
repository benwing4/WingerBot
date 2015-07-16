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
from blib import getparam, addparam

def rewrite_template_names(old, new, removelist, save, verbose,
    startFrom, upTo):
  def rewrite_one_page_template_names(page, index, text):
    actions = []
    for template in text.filter_templates():
      if template.name == old:
        actions.append("rename {{temp|%s}} to {{temp|%s}}" % (old, new))
        template.name = new
      for remove in removelist:
        if template.has(remove):
          template.remove(remove)
          actions.append("remove %s=" % remove)

    return text, '; '.join(actions)

  for page, index in blib.references("Template:%s" % old, startFrom, upTo):
    blib.do_edit(page, index, rewrite_one_page_template_names, save=save,
        verbose=verbose)

pa = blib.init_argparser("Rewrite old to new template names")
pa.add_argument("-o", "--old", help="Old name of template")
pa.add_argument("-n", "--new", help="New name of template")
pa.add_argument("-r", "--remove", help="Comma-separated template params to remove")
params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)
removelist = []
if params.remove:
  removelist = re.split(",", params.remove)

rewrite_template_names(params.old, params.new, removelist, params.save,
    params.verbose, startFrom, upTo)
