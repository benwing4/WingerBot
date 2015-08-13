#!/usr/bin/env python
#coding: utf-8

#    rewrite_ru_decl.py is free software: you can redistribute it and/or modify
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
from blib import msg, getparam, addparam, rmparam, getrmparam, remove_links

ru_noun_transl = [
  [u"ru-noun-([12])", "", "stem-bare"],
  [u"ru-noun-(2)-а", u"-а", "stem-bare"],
  [u"ru-noun-(3)", "", "u-stem-bare-pagename"],
  [u"ru-noun-(3)-а", u"-а", "u-stem-bare-pagename"],
  [u"ru-noun-(5)", "", "u-stem-pagename"],
  [u"ru-noun-а-([12])", u"а", "u-stem-u-bare"],
  [u"ru-noun-а-(4)", u"а", "u-stem-u-bare-irregpl-irregaccsg"],
  [u"ru-noun-а-(6)", u"а", "u-stem-bare"],
  #u"ru-noun-ин", This needs to be special-cased,
  [u"ru-noun-о-([123])", u"о", "u-stem-u-bare"],
  [u"ru-noun-о-(4)", u"о", "u-stem-u-bare-irregpl"],
  [u"ru-noun-е-(1)", u"е", "u-stem-u-bare"],
  [u"ru-noun-е-(3)", u"е", "u-stem"],
  [u"ru-noun-я-([12])", u"я", "u-stem-u-bare"],
  [u"ru-noun-я-(4)", u"я", "u-stem-u-bare-irregpl-irregaccsg"],
  [u"ru-noun-я-([56])", u"я", "u-stem"],
  [u"ru-noun-ь-([1256])-m", u"ь-m", "u-stem-bare-pagename"],
  [u"ru-noun-ь-(3)-m", u"ь-m", "u-stem"],
  [u"ru-noun-vel-([124])", "", "u-stem-bare-pagename"],
  #u"ru-noun-vel-3", This needs to be special-cased,
  [u"ru-noun-vel-(5)", "", "u-stem"],
  [u"ru-noun-vel-а-([12])", u"а", "u-stem-u-bare"],
  [u"ru-noun-vel-а-(4)", u"а", "u-stem-u-bare-irregpl-irregaccsg"],
  [u"ru-noun-vel-а-(6)", u"а", "u-stem-bare"],
  [u"ru-noun-vel-о-([12])-и", u"о-и", "u-stem-u-bare"],
  [u"ru-noun-sib-([123])", "", "u-stem-bare-pagename"],
  [u"ru-noun-sib-(3)-а", "-а", "u-stem-bare-pagename"],
  [u"ru-noun-sib-(5)", "", "u-stem-pagename"],
  [u"ru-noun-sib-а-(1)", u"а", "u-stem-u-bare"],
  [u"ru-noun-sib-а-(2)", u"а", "stem"],
  [u"ru-noun-sib-а-(4)", u"а", "u-stem-u-bare-irregpl"],
  [u"ru-noun-sib-а-(6)", u"а", "u-stem"],
  [u"ru-noun-sib-е-(1)", u"о", "u-stem-u-bare"],
  [u"ru-noun-ц-([12])", "", "u-stem-bare-pagename"],
  [u"ru-noun-ца-(1)", u"а", "u-stem-u-bare"],
  [u"ru-noun-це-([13])", u"о", "u-stem-u-bare"],
  [u"ru-noun-й-([123])", u"й", "u-stem-bare"],
  [u"ru-noun-ье-(1)", u"ье", "u-stem-u-bare"],
  [u"ru-noun-ьё-([24])", u"ьё", "u-stem-u-bare"],
  [u"ru-noun-ь-([15])-f", u"ь-f", "u-stem"],
  [u"ru-noun-sib-ь-([15])-f", u"ь-f", "u-stem"],
  [u"ru-noun-мя-(1)", u"мя-1", "u-stem"],
  [u"ru-noun-мя-(3)", u"мя", "u-stem-u-bare"],
  [u"ru-noun-ий", u"ий", "u-stem-minus-i", "1"],
  [u"ru-noun-ия", u"ия", "u-stem-u-bare-minus-i", "1"],
  [u"ru-noun-ие", u"ие", "u-stem-u-bare-minus-i", "1"],
  [u"ru-noun-ие-2", u"ие", "u-stem-minus-i", "2"],
  [u"ru-noun-иё", u"иё", "u-stem-u-minus-i", "1"],
  #u"ru-noun-нок", This needs to be special-cased,
]

ending_for_ru_adj = {
  "ru-adj1": u"ый",
  "ru-adj2": u"ий",
  "ru-adj3": u"ий",
  "ru-adj4": u"ой",
  "ru-adj5": u"ой",
  "ru-adj6": u"ий",
  "ru-adj7": u"ьий",
  "ru-adj8": u"short",
  "ru-adj9": u"mixed",
  "ru-adj10": u"ый",
  #"ru-adj11": (not yet supported)
  "ru-adj12": u"ий",
  "ru-adj13": u"ой",
}

def clean(value):
  value = value.strip()
  value = remove_links(value)
  value = re.sub(", +", ",", value)
  if value == "-":
    value = ""
  return value

AC = u"\u0301"
GR = u"\u0300"
def remove_diacritics(text):
  text = text.replace(AC, "")
  text = text.replace(GR, "")
  return text

def rewrite_one_page_ru_decl_adj(page, index, text):
  oldtemps = []
  pagename = unicode(page.title())
  def pagemsg(txt):
    msg("Page %s %s: %s" % (index, pagename, txt))
  for t in text.filter_templates():
    converted = True
    def tname():
      return unicode(t.name).strip()
    origname = tname()
    origtemplate = unicode(t)
    if tname() == "ru-adj-table":
      t.name = "ru-decl-adj"
    else:
      if re.match("^ru-adjective[0-9]", tname()):
        t.name = tname().replace("ru-adjective", "ru-adj")
      if tname() == "ru-passive participle decl":
        t.name = "ru-adj1"
      suffix = None
      if tname() == "ru-adj3-sja":
        suffix = u"ся"
        t.name = "ru-adj3"
      elif tname() == "ru-adj5-suffix":
        suffix = "-" + getparam(t, "8")
        t.name = "ru-adj5"
      if tname() in ending_for_ru_adj:
        if tname() == "ru-adj13":
          addparam(t, "2", ending_for_ru_adj[tname()])
          rmparam(t, "8")
          rmparam(t, "7")
          rmparam(t, "6")
          rmparam(t, "5")
          rmparam(t, "4")
          rmparam(t, "3")
        elif tname() in ["ru-adj7", "ru-adj8", "ru-adj9", "ru-adj12"]:
          addparam(t, "1", getparam(t, "2").strip())
          addparam(t, "2", ending_for_ru_adj[tname()])
          rmparam(t, "8")
          rmparam(t, "7")
          rmparam(t, "6")
          rmparam(t, "5")
          rmparam(t, "4")
          rmparam(t, "3")
        else:
          addparam(t, "1", getparam(t, "2").strip())
          addparam(t, "2", ending_for_ru_adj[tname()])
          mshort = clean(getparam(t, "3"))
          if mshort and re.search(u"[аяоеыи]$", remove_diacritics(mshort)):
            pagemsg("WARNING: short masculine %s doesn't have right ending" %
                mshort)
          fshort = clean(getparam(t, "4"))
          if fshort and not re.search(u"[ая]$", remove_diacritics(fshort)):
            pagemsg("WARNING: short feminine %s doesn't have right ending" %
                fshort)
          nshort = clean(getparam(t, "5"))
          if nshort and not re.search(u"[ое]$", remove_diacritics(nshort)):
            pagemsg("WARNING: short neuter %s doesn't have right ending" %
                nshort)
          pshort = clean(getparam(t, "6"))
          if pshort and not re.search(u"[ыи]$", remove_diacritics(pshort)):
            pagemsg("WARNING: short plural %s doesn't have right ending" %
                pshort)
          rmparam(t, "8")
          rmparam(t, "7")
          rmparam(t, "6")
          rmparam(t, "5")
          rmparam(t, "4")
          rmparam(t, "3")
          if mshort:
            addparam(t, "3", mshort)
          # Note that fshort and nshort get reversed
          if nshort:
            addparam(t, "4", nshort)
          if fshort:
            addparam(t, "5", fshort)
          if pshort:
            addparam(t, "6", pshort)
        if suffix:
          addparam(t, "suffix", suffix)
        t.name = "ru-decl-adj"
        pagemsg("Rewrote %s as %s" % (origtemplate, unicode(t)))
      else:
        converted = False
    if converted:
      oldtemps.append(origname)
  if oldtemps:
    comment = "convert %s -> ru-decl-adj" % ", ".join(oldtemps)
  else:
    comment = None
  return text, comment

def rewrite_one_page_ru_decl_noun(page, index, text):
  oldtemps = []
  pagename = unicode(page.title())
  def pagemsg(txt):
    msg("Page %s %s: %s" % (index, pagename, txt))
  nochange = False
  change = False
  for t in text.filter_templates():
    converted = True
    def tname():
      return unicode(t.name).strip()
    origname = tname()
    origtemplate = unicode(t)
    if tname() in ["ru-noun-table", "ru-noun-old"]:
      continue
    stem = ""
    bare = ""
    accsg = ""
    locsg = ""
    if tname() == u"ru-noun-ин":
      ustem = getrmparam(t, "1")
      stem = getrmparam(t, "2")
      full = getrmparam(t, "3")
      stem = stem or ustem
      declclass = u"ин"
      if stem + u"ин" == full:
        accentclass = "1"
      elif remove_diacritics(stem) + u"и́н" == full:
        accentclass = "4"
      elif stem == full:
        accentclass = "1"
        declclass = u"-е"
      else:
        pagemsg("WARNING: Can't locate accent class for template: %s" %
            origtemplate)
        nochange = True
        break
      change = True
    elif tname() == u"ru-noun-нок":
      ustem = getrmparam(t, "1")
      stem = getrmparam(t, "2")
      uplural = getrmparam(t, "3")
      plural = getrmparam(t, "4")
      stem = stem or ustem
      plural = plural or uplural
      accentclass = "2"
      if stem.endswith(u"ё"):
        declclass = u"ёнок"
        stem = re.sub(u"ё$", "", stem)
      elif stem.endswith(u"о́"):
        declclass = u"онок"
        stem = re.sub(u"о́$", "", stem)
      else:
        pagemsg("WARNING: Template stem ends weirdly: %s" % origtemplate)
        nochange = True
        break
      if stem != re.sub(u"(я́|а́)$", "", plural):
        pagemsg("WARNING: Strange plural: %s" % origtemplate)
        nochange = True
        break
      if (declclass == u"ёнок" and not plural.endswith(u"я́") or
          declclass == u"онок" and not plural.endswith(u"а́")):
        pagemsg("WARNING: Unexpected plural ending for stem: %s" % origtemplate)
        nochange = True
        break
      change = True
    elif tname() == u"ru-noun-vel-3":
      ustem = getrmparam(t, "1")
      stem = getrmparam(t, "2")
      bare = getrmparam(t, "3")
      locsg = getrmparam(t, "13")
      locpl = getrmparam(t, "14")
      stem = stem or ustem or bare or pagename
      declclass = ""
      accentclass = "3"
      if locpl and locpl != remove_diacritics(stem) + u"а́х":
        pagemsg("WARNING: Unexpected locative plural %s: %s" % (locpl,
          origtemplate))
        nochange = True
        break
      change = True
    else:
      for entry in ru_noun_transl:
        if len(entry) == 3:
          regex, declclass, directive = entry
          m = re.match(regex, tname())
          if not m:
            continue
          assert len(m.groups()) == 1
          accentclass = m.group(1)
        else:
          assert len(entry) == 4
          regex, declclass, directive, accentclass = entry
          m = re.match(regex, tname())
          if not m:
            continue
          assert len(m.groups()) == 0
        if directive == "stem":
          stem = getrmparam(t, "1")
        elif directive == "stem-bare":
          stem = getrmparam(t, "1")
          bare = getrmparam(t, "2")
        elif directive == "u-stem":
          ustem = getrmparam(t, "1")
          stem = getrmparam(t, "2")
          stem = stem or ustem
        elif directive == "u-stem-bare":
          ustem = getrmparam(t, "1")
          stem = getrmparam(t, "2")
          bare = getrmparam(t, "3")
          stem = stem or ustem or bare
        elif directive == "u-stem-pagename":
          ustem = getrmparam(t, "1")
          stem = getrmparam(t, "2")
          stem = stem or ustem or pagename
        elif directive == "u-stem-bare-pagename":
          ustem = getrmparam(t, "1")
          stem = getrmparam(t, "2")
          bare = getrmparam(t, "3")
          stem = stem or ustem or bare or pagename
        elif directive == "u-stem-u-bare":
          ustem = getrmparam(t, "1")
          stem = getrmparam(t, "2")
          ubare = getrmparam(t, "3")
          bare = getrmparam(t, "4")
          stem = stem or ustem
          bare = bare or ubare
        elif directive in ["u-stem-u-bare-irregpl", "u-stem-u-bare-irregpl-irregaccsg"]:
          ustem = getrmparam(t, "1")
          stem = getrmparam(t, "2")
          ubare = getrmparam(t, "3")
          bare = getrmparam(t, "4")
          irregpl = getrmparam(t, "5")
          stem = irregpl or stem or ustem
          bare = bare or ubare
          if directive == "u-stem-u-bare-irregpl-irregaccsg":
            accsg = getrmparam(t, "6")
        elif directive in ["u-stem-minus-i", "u-stem-u-bare-minus-i"]:
          ustem = getrmparam(t, "1")
          stem = getrmparam(t, "2")
          stem = stem or ustem
          unstressedi = u"и"
          stressedi = u"и́"
          assert len(stressedi) == 2
          if stem.endswith(unstressedi):
            stem = stem[0:-1]
          elif stem.endswith(stressedi):
            stem = stem[0:-2]
          else:
            pagemsg(u"WARNING: Stem %s doesn't end in и in %s, skipping" %
                (stem, unicode(t)))
            nochange = True
            break
        else:
          pagemsg("WARNING: Unknown directive %s, skipping" % directive)
          nochange = True
          break

        change = True
        break
      else:
        if re.match("^ru-noun-", tname()):
          pagemsg("Encountered unknown noun decl template %s" % unicode(t))
    if change:
      if not stem:
        pagemsg("WARNING: Can't locate stem in %s, skipping" % origtemplate)
        nochange = True
        break
      anim = getrmparam(t, "anim")
      if anim:
        anim = "an"
      n = getrmparam(t, "n")
      notes = getrmparam(t, "note")
      if len(t.params) > 0:
        pagemsg("WARNING: Extraneous parameters in %s, skipping" % unicode(t))
        nochange = True
        break
      addparam(t, "1", accentclass)
      addparam(t, "2", stem)
      addparam(t, "3", declclass)
      if bare:
        addparam(t, "4", bare)
      if acc_sg:
        addparam(t, "acc_sg", acc_sg)
      if loc_sg:
        addparam(t, "loc", loc_sg)
      if anim:
        addparam(t, "a", anim)
      if n:
        addparam(t, "n", n)
      if notes:
        addparam(t, "notes", notes)
      t.name = "ru-noun-table"
      pagemsg("Rewrote %s as %s" % (origtemplate, unicode(t)))
      oldtemps.append(origname)
  if nochange:
    return None, ""
  if oldtemps:
    comment = "convert %s -> ru-noun-table" % ", ".join(oldtemps)
  else:
    comment = None
  return text, comment

def rewrite_ru_decl_noun(save, verbose, startFrom, upTo):
  for cat in [u"Russian nouns"]:
    for page, index in blib.cat_articles(cat, startFrom, upTo):
      blib.do_edit(page, index, rewrite_one_page_ru_decl_noun, save=save, verbose=verbose)
def rewrite_ru_decl_adj(save, verbose, startFrom, upTo):
  for cat in [u"Russian adjectives"]:
    for page, index in blib.cat_articles(cat, startFrom, upTo):
      blib.do_edit(page, index, rewrite_one_page_ru_decl_adj, save=save, verbose=verbose)

pa = blib.init_argparser("Rewrite Russian old declension templates")
pa.add_argument("--adjectives", action='store_true',
    help="Rewrite old adjective templates")
pa.add_argument("--nouns", action='store_true',
    help="Rewrite old noun templates")
params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)

if params.adjectives:
  rewrite_ru_decl_adj(params.save, params.verbose, startFrom, upTo)
if params.nouns:
  rewrite_ru_decl_noun(params.save, params.verbose, startFrom, upTo)
