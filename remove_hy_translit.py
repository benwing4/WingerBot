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
from blib import msg, errmsg, getparam

templates_changed = {}
template_params_removed = {}
langs_with_override_translit = [
  ("hy", "Armenian"),
  ("xcl", "Old Armenian"),
  ("axm", "Middle Armenian"),
  ("ka", "Georgian"),
  ("el", "Greek"),
  ("grc", "Ancient Greek"),
#  ("ab", "Abkhaz"),
#  ("abq", "Abaza"),
#  ("ady", "Adyghe"),
#  ("av", "Avar"),
#  ("ba", "Bashkir"),
#  ("bo", "Tibetan"),
#  ("bua", "Buryat"),
#  ("ce", "Chechen"),
#  "chm":"Eastern Mari":
#  ("cv", "Chuvash"),
#  ("dar", "Dargwa"),
#  ("dv", "Dhivehi"),
#  ("dz", "Dzongkha"),
#  ("inh", "Ingush"),
#  ("iu", "Inuktitut"),
#  ("kk", "Kazakh"),
#  ("kbd", "Kabardian"),
#  ("kca", "Khanty"),
#  ("kjh", "Khakas"),
#  ("kn", "Kannada"),
#  ("koi", "Komi-Permyak"),
#  ("kpv", "Komi-Zyrian"),
#  ("ky", "Kyrgyz"),
##  ("kv", ""), # Apparently was Komi
#  ("lo", "Lao"),
#  ("lbe", "Lak"),
#  ("lez", "Lezgi"),
#  ("lzz", "Laz"),
#  ("mdf", "Moksha"),
#  ("ml", "Malayalam"),
#  ("mn", "Mongolian"),
#  ("my", "Burmese"),
#  ("myv", "Erzya"),
#  ("oge", "Old Georgian"),
#  ("os", "Ossetian"),
#  ("sah", "Yakut"),
#  ("si", "Sinhalese"),
#  ("sva", "Svan"),
#  ("ta", "Tamil"),
#  ("tab", "Tabasaran"),
#  ("te", "Telugu"),
#  ("tg", "Tajik"),
#  ("tt", "Tatar"),
#  ("tyv", "Tuvan"),
#  ("ug", "Uyghur"),
#  ("udi", "Udi"),
#  ("udm", "Udmurt"),
#  ("xal", "Kalmyk"),
#  ("xmf", "Mingrelian"),
]
langs_with_override_translit_map = dict(langs_with_override_translit)

remove_tr_langs = [x for x, y in langs_with_override_translit]
remove_tr_long_langs = [y for x, y in langs_with_override_translit]

def has_non_western_chars(val):
  # Some Greek translits contain the following chars mixed in with
  # the Latin chars, so ignore them. Note that these are all
  # consonants and pretty much all real Greek words will have vowels
  # in them, so this is unlikely to lead to missing actual Greek
  # text.
  checkval = re.sub(u"[χφθβγδ]", "", val)
  return re.search(u"[\u0370-\u1CFF\u1F00-\u1FFF\u2C00-\u2C5F\u2C80-\uA6FF\uA800-\uAB2F\uAB70-\uFEFF]", checkval)

ignore_prefixes = ["User:", "Talk:",
    "Wiktionary:Beer parlour", "Wiktionary:Translation requests",
    "Wiktionary:Grease pit", "Wiktionary:Etymology scriptorium",
    "Wiktionary:Information desk"]

def remove_translit(params, startFrom, upTo):
  # Remove redundant translits on one page.
  def remove_translit_one_page(page, index, text):
    pagetitle = page.title()
    def pagemsg(text):
      msg("Page %s %s: %s" % (index, pagetitle, text))

    # Hack for grc pages where we don't want to remove the translit
    if u"Ͷ" in pagetitle or u"ͷ" in pagetitle:
      pagemsg(u"Page has Ͷ or ͷ in it, not doing")
      return text, ""

    params_removed = []
    for t in text.filter_templates():
      tname = unicode(t.name)
      def getp(param):
        return getparam(t, param)
      def doparam(param, value=None):
        val = getp(param)
        if value is None:
          matches_value = not not val
        else:
          matches_value = val == value
        if matches_value:
          is_ignore_prefix = False
          for ip in ignore_prefixes:
            if pagetitle.startswith(ip):
              is_ignore_prefix = True
          if " talk:" in pagetitle:
            is_ignore_prefix = True
          is_grc = (tname.startswith("grc-") or getp("lang") == "grc" or
              getp("1") == "grc")
          has_nwc = has_non_western_chars(val)
          if val == "-":
            pagemsg("Not removing %s=-: %s" % (param, unicode(t)))
          elif has_nwc and not param.startswith("tr"):
            pagemsg("WARNING: Value %s=%s has non-Western chars in it, not removing: %s" %
                (param, val, unicode(t)))
          elif is_ignore_prefix:
            pagemsg("Not removing %s=%s from page in to-ignore category: %s" % (
              param, val, unicode(t)))
          # We don't need to do accented chars because they are normalized into
          # char with macron + combining accent; the only combined macro/accent
          # single chars are ḗ and ṓ
          elif is_grc and re.search(ur"[āīūĀĪŪ]", val):
            pagemsg("WARNING: grc and value %s=%s has long a/i/u in it, not removing: %s" %
                (param, val, unicode(t)))
          elif is_grc and re.search(ur"[ăĭŭĂĬŬ]", val):
            pagemsg("WARNING: grc and value %s=%s has a/i/u with breve in it, not removing: %s" %
                (param, val, unicode(t)))
          else:
            if has_nwc:
              pagemsg("NOTE: Value %s=%s has non-Western chars but removing anyway because starts with 'tr': %s" %
                  (param, val, unicode(t)))
            pagemsg("Removed %s=%s: %s" % (param, val, unicode(t)))
            if value is None:
              tempparam = "%s.%s" % (tname, param)
            else:
              tempparam = "%s.%s=%s" % (tname, param, value)
            params_removed.append(tempparam)
            t.remove(param)
            templates_changed[tname] = templates_changed.get(tname, 0) + 1
            template_params_removed[tempparam] = (
                template_params_removed.get(tempparam, 0) + 1)
      def remove_even(upto=10):
        for i in xrange(2, upto, 2):
          doparam(str(i))
      def remove_odd(upto=9):
        for i in xrange(1, upto, 2):
          doparam(str(i))
      # (Old) Armenian declension templates
      if re.match("^xcl-noun-.*pl", tname) and tname not in [
          u"xcl-noun-ն-pl", u"xcl-noun-ն-2-pl", u"xcl-noun-ն-3-pl",
          u"xcl-noun-ո-ա-pl"]:
        remove_even()
      elif tname.startswith("xcl-noun-collnum"):
        remove_even()
      elif tname in [u"xcl-noun-հայր", u"xcl-noun-տէր", u"xcl-noun-այր",
          u"xcl-noun-կին"]:
        remove_even()
      else:
        for start_template in ["hy-noun-", "xcl-noun-"]:
          if tname.startswith(start_template):
            remove_odd()
      if tname in ["xcl-noun", "xcl-adj"]:
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
          "hy-personal_pronoun", "hy-personal pronoun", "hy-phrase",
          "hy-postp", "hy-postp-form", "hy-prefix", "hy-prep", "hy-pronoun",
          "hy-proper_noun", "hy-proper noun", "hy-proper-noun-form",
          "hy-proverb", "hy-suffix", "hy-verb", "hy-verb-form",
          # Declension templates; no xcl-decl-verb
          "hy-decl-verb",
          # Old Armenian
          # "xcl-adj" uses param 3 and 4
          "xcl-adj-form", "xcl-adv", "xcl-con", "xcl-interj",
          # xcl-noun uses param 3 and 4
          "xcl-noun-form", "xcl-numeral", "xcl-particle",
          "xcl-postp", "xcl-prefix", "xcl-prep", "xcl-pron", "xcl-pron-form",
          "xcl-proper_noun", "xcl-proper-noun-form", "xcl-root", "xcl-suffix",
          "xcl-verb", "xcl-verb-form"]:
        remove_odd()
      # Armenian conjugation templates
      if tname.startswith("hy-conj"):
        remove_even()
      if tname.startswith("xcl-conj"):
        remove_odd()
      # Middle Armenian headword templates handled further below.
      # NOTE: axm-adj, axm-adv, axm-interj, axm-noun, axm-prefix, axm-suffix,
      # axm-verb still use the tr= parameter, but pass it to {{head}}, which
      # presumably ignores it.
      #
      # Georgian headword templates handled further below.
      # NOTE: ka-adj, ka-adv, ka-pron, ka-proper noun, ka-verb still use the
      # tr= parameter, but pass it to {{head}}, which presumably ignores it.
      #
      # Old Georgian headword templates handled further below.
      # NOTE: oge-noun and perhaps others still use the tr= parameter, but
      # pass it to {{head}}, which presumably ignores it.
      #
      # FIXME: ka-decl-noun. All even-numbered parameters (up through at least
      # 36) are translits, but are still used in the template.
      #if tname == "ka-decl-noun":
      #  remove_even(upto=38)
      #
      # Ancient Greek templates with numbered translit params
      if tname in ["grc-noun-con"]:
        doparam("5")
      if tname in ["grc-proper noun", "grc-noun"]:
        doparam("4")
      if tname in ["grc-adj-1&2", "grc-adj-1&3", "grc-part-1&3"]:
        doparam("3")
      if tname in ["grc-adj-2nd", "grc-adj-3rd", "grc-adj-2&3"]:
        doparam("2")
      if tname in ["grc-num"]:
        doparam("1")
      #
      # Handle any template beginning with hy-, xcl-, ka-, el-, grc-, etc.
      # that has a tr parameter. But don't do el-p, which uses the tr param.
      for lang in remove_tr_langs:
        if tname.startswith(lang + "-") and tname not in ["el-p"]:
          doparam("tr")
      # Suffix/prefix/affix
      if (tname in ["suffix", "suffix2", "prefix", "confix", "affix",
          "circumfix", "infix", "compound"] and
          getp("lang") in remove_tr_langs):
        # Don't just do cases up through where there's a numbered param
        # because there may be holes.
        for i in xrange(1, 11):
          doparam("tr" + str(i))
      if (#tname in ["t", "t+", "t-", "t+check", "t-check", "l", "m",
          #"link", "mention", "head", "ux"] and
          getp("1") in remove_tr_langs):
        if tname == "head" and not params.do_head:
          pagemsg("Not removing tr= from {{head|...}}: %s" % unicode(t))
        else:
          doparam("tr")
      if (#tname in ["term", "usex"] and
          getp("lang") in remove_tr_langs
          and tname != "borrowing"):
        doparam("tr")
      # Remove sc=Armn from (Old) Armenian, sc=Grek from Greek
      for langs, script in [
          (["hy", "xcl", "axm"], "Armn"),
          (["ka"], "Geor"),
          (["el"], "Grek"),
          (["grc"], "polytonic"),
          (["grc"], "Grek"),
          ]:
        if getp("1") in langs or getp("lang") in langs and tname != "borrowing":
          doparam("sc", script)

    reduced_pr = []
    for pr in params_removed:
      if reduced_pr:
        last_pr, num = reduced_pr[-1]
        if pr == last_pr:
          reduced_pr[-1] = (pr, num + 1)
          continue
      reduced_pr.append((pr, 1))
    pr_msg = ", ".join("%s(x%s)" % (pr, num) if num > 1 else pr
        for pr, num in reduced_pr)

    changelog = ""
    if pr_msg:
      changelog = "Remove translit/sc (%s)" % pr_msg
      pagemsg("Change log = %s" % changelog)
    return text, changelog

  def get_langs_to_do():
    if params.langs == "all":
      langs2do = remove_tr_langs
    else:
      langs2do = params.langs.split(",")
      for lang in langs2do:
        assert lang in remove_tr_langs
    long_langs2do = [langs_with_override_translit_map[x] for x in
        langs2do]
    return (langs2do, long_langs2do)

  def yield_cats(cattype=params.cattype):
    if cattype == "all":
      cats = ["translit", "lemma", "non-lemma"]
    else:
      cats = cattype.split(",")

    langs2do, long_langs2do = get_langs_to_do()

    if "translit" in cats:
      for lang in langs2do:
        for category in ["Terms with redundant transliterations/" + lang,
            "Terms with manual transliterations different from the automated ones/"
            + lang]:
          yield category
    if "lemma" in cats:
      for lang in long_langs2do:
        for category in ["%s lemmas" % lang]:
          yield category
    if "non-lemma" in cats:
      for lang in long_langs2do:
        for category in ["%s non-lemma forms" % lang]:
          yield category

  def yield_lemma_non_lemma_page_titles():
    for cat in yield_cats("lemma,non-lemma"):
      msg("Retrieving pages from %s ..." % cat)
      errmsg("Retrieving pages from %s ..." % cat)
      for page, index in blib.cat_articles(cat, None, None):
        yield page.title()

  if params.ignore_lemma_non_lemma:
    pages_to_ignore = set(yield_lemma_non_lemma_page_titles())
  else:
    pages_to_ignore = set()

  for category in yield_cats():
    msg("Processing category %s ..." % category)
    errmsg("Processing category %s ..." % category)
    for page, index in blib.cat_articles(category, startFrom, upTo):
      if page.title() not in pages_to_ignore:
        blib.do_edit(page, index, remove_translit_one_page, save=params.save,
            verbose=params.verbose)

pa = blib.init_argparser("Remove translit, sc= from hy, xcl, ka, el, grc templates")
pa.add_argument("--langs", default="all",
    help="Languages to do, a comma-separated list or 'all'")
pa.add_argument("--cattype", default="all",
    help="""Categories to examine ('all' or comma-separated list of
'translit', 'lemma', 'non-lemma'; default 'all')""")
pa.add_argument("--ignore-lemma-non-lemma", action="store_true",
    help="""Ignore lemma and non-lemma pages (useful with '--cattype translit').""")
pa.add_argument("--do-head", action="store_true",
    help="""Remove tr= in {{head|..}}""")
params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)

remove_translit(params, startFrom, upTo)

msg("Templates processed:")
for template, count in sorted(templates_changed.items(), key=lambda x:-x[1]):
  msg("  %s = %s" % (template, count))
msg("Template params removed:")
for tpar, count in sorted(template_params_removed.items(), key=lambda x:-x[1]):
  msg("  %s = %s" % (tpar, count))
