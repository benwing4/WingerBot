#!/usr/bin/env python
#coding: utf-8

#    remove_hy_translit.py is free software: you can redistribute it and/or modify
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
from blib import msg, getparam

templates_changed = {}
template_params_removed = {}
remove_tr_langs = ["hy", "xcl", "ka"]
remove_tr_long_langs = ["Armenian", "Old Armenian", "Georgian"]

def remove_translit(save, verbose, startFrom, upTo):
  # Remove redundant translits on one page.
  def remove_translit_one_page(page, index, text):
    pagetitle = page.title()
    params_removed = []
    for t in text.filter_templates():
      tname = unicode(t.name)
      def getp(param):
        return getparam(t, param)
      def doparam(param):
        val = getp(param)
        if val:
          if re.search(u"[\u0370-\u1CFF\u1F00-\u1FFF\u2C00-\u2C5F\u2C80-\uA6FF\uA800-\uAB2F\uAB70-\uFEFF]", val):
            msg("WARNING: Value %s=%s of template %s has non-Western chars in it, not removing" %
                (param, val, tname))
          else:
            tempparam = "%s.%s" % (tname, param)
            params_removed.append(tempparam)
            t.remove(param)
            msg("Removed %s=%s from %s" % (param, val, tname))
            templates_changed[tname] = templates_changed.get(tname, 0) + 1
            templates_params_removed[tempparam] = (
                templates_params_removed.get(tempparam, 0) + 1)
      # Declension templates
      for start_template in ["hy-noun-", "xcl-noun-"]:
        if tname.startswith(start_template):
          doparam("1")
      # (Old) Armenian headword templates
      # 
      # Note: The following still use the tr= parameter, but pass it to
      # {{head}}, which presumably ignores it:
      #
      # hy-particle, hy-personal_pronoun, hy-phrase, hy-postp, hy-postp-form,
      # hy-prefix, hy-proper-noun-form, hy-suffix
      #
      # xcl-adj, xcl-adj-form, xcl-adv, xcl-con, xcl-interj, xcl-noun-form,
      # xcl-numeral, xcl-particle, xcl-postp, xcl-prefix, xcl-prep, xcl-pron,
      # xcl-pron-form, xcl-proper_noun, xcl-proper-noun-form, xcl-root,
      # xcl-suffix, xcl-verb, xcl-verb-form
      if tname in ["hy-adj", "hy-adv", "hy-con", "hy-interj",
          # "hy-letter", param 1 is Armenian
          "hy-noun", "hy-noun-form", "hy-numeral", "hy-particle",
          "hy-personal_pronoun", "hy-phrase", "hy-postp", "hy-postp-form",
          "hy-prefix", "hy-prep", "hy-pronoun", "hy-proper_noun",
          "hy-proper-noun-form", "hy-proverb", "hy-suffix", "hy-verb",
          "hy-verb-form",
          # Declension templates; no xcl-decl-verb
          "hy-decl-verb",
          # Old Armenian
          "xcl-adj", "xcl-adj-form", "xcl-adv", "xcl-con", "xcl-interj",
          "xcl-noun", "xcl-noun-form", "xcl-numeral", "xcl-particle",
          "xcl-postp", "xcl-prefix", "xcl-prep", "xcl-pron", "xcl-pron-form",
          "xcl-proper_noun", "xcl-proper-noun-form", "xcl-root", "xcl-suffix",
          "xcl-verb", "xcl-verb-form"]:
        doparam("1")
        doparam("tr")
      # Georgian headword templates
      # NOTE: ka-adj, ka-adv, ka-pron, ka-proper noun, ka-verb still use the
      # tr= parameter, but pass it to {{head}}, which presumably ignores it.
      if tname in ["ka-adj", "ka-adv", "ka-con", "ka-noun", "ka-pron",
          "ka-proper noun", "ka-verb", "ka-verbal noun"]:
        doparam("tr")
      # FIXME: ka-decl-noun. All even-numbered templates (up through at least
      # 36) are translits, but are still used in the template.
      #if tname == "ka-decl-noun":
      #  for i in xrange(2, 38, 2):
      #    doparam(str(i))
      #
      # Armenian conjugation templates
      if t.startswith("hy-conj"):
        doparam("2")
        doparam("4")
        doparam("6")
      if t.startswith("xcl-conj"):
        doparam("1")
        doparam("3")
        doparam("5")
      # Suffix/prefix/affix
      if (tname in ["suffix", "prefix", "confix", "affix", "compound"] and
          getp("lang") in remove_tr_langs):
          i = 1
          while getp(str(i)):
            doparam("tr" + str(i))
            i += 1
      if (#tname in ["t", "t+", "t-", "t+check", "t-check", "l", "m",
          #"link", "mention", "head", "ux"] and
          getp("1") in remove_tr_langs):
        doparam("tr")
      if (#tname in ["term", "usex"] and
          getp("lang") in remove_tr_langs
          and tname != "borrowing"):
        doparam("tr")
      # Remove sc=Armn from (Old) Armenian, sc=Geor from Georgian
      for langs, script in [(["hy", "xcl"], "Armn"), (["ka"], "Geor")]:
        if getp("1") in langs or getp("lang") in langs and tname != "borrowing":
          if getp("sc") == script:
            t.remove("sc")
            tempparam = "%s.sc=%s" % (tname, script)
            params_removed.append(tempparam)
            templates_changed[tname] = templates_changed.get(tname, 0) + 1
            templates_params_removed[tempparam] = (
                templates_params_removed.get(tempparam, 0) + 1)

    changelog = "Remove translit (%s)" % ", ".join(params_removed)
    msg("Page %s %s: Change log = %s" % (index, pagetitle, changelog))
    return text, changelog

  def yield_cats():
    for lang in remove_tr_langs:
      for category in ["Terms with redundant transliterations/" + lang,
          "Terms with manual transliterations different from the automated ones/"
          + lang]:
        yield category
    for lang in remove_tr_long_langs:
      for category in ["%s lemmas" % lang, "%s non-lemma forms" % lang]:
        yield category

  for category in yield_cats():
    msg("Processing category %s ..." % category)
    for page, index in blib.cat_articles(category, startFrom, upTo):
      blib.do_edit(page, index, remove_translit_one_page, save=save,
          verbose=verbose)

pa = blib.init_argparser("Remove translit, sc=Armn, sc=Geor from hy, xcl, ka templates")
parms = pa.parse_args()
startFrom, upTo = blib.parse_start_end(parms.start, parms.end)

remove_translit(parms.save, parms.verbose, startFrom, upTo)

msg("Templates processed:")
for template, count in sorted(templates_changed.items(), key=lambda x:-x[1]):
  msg("  %s = %s" % (template, count))
msg("Template params removed:")
for tpar, count in sorted(template_params_removed.items(), key=lambda x:-x[1]):
  msg("  %s = %s" % (tpar, count))
