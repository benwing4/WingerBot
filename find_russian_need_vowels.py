#!/usr/bin/env python
#coding: utf-8

#    find_russian_need_vowels.py is free software: you can redistribute it and/or modify
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

# FIXME:
#
# 1. (DONE AS PART OF SMARTER WORD SPLITTING) Handle '''FOO''', matched up
#    against blank tr, TR or '''TR'''. Cf. '''спасти''' in 23865 спасти.
# 2. Handle multiword expressions *inside* of find_vocalized so e.g. the
#    multiword linked expressions in 24101 стан.

import re, codecs

import blib, pywikibot
from blib import msg, getparam, addparam
from ru_translit import remove_diacritics
import rulib as ru

site = pywikibot.Site()
semi_verbose = False # Set by --semi-verbose or --verbose

# List of Russian vowels minus soft/hard signs
russian_vowels = u"АОУҮЫЭЯЁЮИЕІѢѴаоуүыэяёюиеіѣѵAEIOUYĚƐaeiouyěɛ"
not_russian_vowel_class = "[^%s]" % russian_vowels

ru_head_templates = ["ru-noun", "ru-proper noun", "ru-verb", "ru-adj", "ru-adv",
  "ru-phrase", "ru-noun form"]

def find_vocalized_1(term, termtr, verbose, pagemsg):
  # We can't handle [[FOO|BAR]] currently; in any case, BAR is generally
  # an inflected term that probably won't have an entry
  if "|" in term:
    pagemsg("Can't handle links with vertical bars: %s" % term)
    return term, termtr
  if "<" in term or ">" in term:
    pagemsg("Can't handle stray < or >: %s" % term)
    return term, termtr
  # But we can handle plain [[FOO]]
  m = re.search(r"^\[\[([^\[\]]*)\]\]$", term)
  if m:
    newterm, newtr = find_vocalized(m.group(1), termtr, verbose, pagemsg)
    return "[[" + newterm + "]]", newtr
  # This can happen if e.g. we're passed "[[FOO]] [[BAR]]".
  if "[" in term or "]" in term:
    pagemsg("Can't handle stray bracket in %s" % term)
    return term, termtr

  pagename = remove_diacritics(term)
  def expand_text(tempcall):
    return blib.expand_text(tempcall, pagename, pagemsg, semi_verbose)

  if semi_verbose:
    pagemsg("find_vocalized: Finding heads on page %s" % pagename)
  page = pywikibot.Page(site, pagename)
  try:
    if not page.exists():
      if semi_verbose:
        pagemsg("find_vocalized: Page %s doesn't exist" % pagename)
      return term, termtr
  except Exception as e:
    pagemsg("WARNING: Error checking page existence: %s" % unicode(e))
    return term, termtr
  heads = set()
  def add(val, tr):
    val_to_add = blib.remove_links(val)
    if val_to_add:
      heads.add((val_to_add, tr))
  saw_head = False

  for t in blib.parse(page).filter_templates():
    tname = unicode(t.name)
    if tname in ru_head_templates:
      saw_head = True
      if getparam(t, "1"):
        add(getparam(t, "1"), getparam(t, "tr"))
      elif getparam(t, "head"):
        add(getparam(t, "head"), getparam(t, "tr"))
    elif tname == "head" and getparam(t, "1") == "ru":
      saw_head = True
      add(getparam(t, "head"), getparam(t, "tr"))
    elif tname in ["ru-noun+", "ru-proper noun+"]:
      saw_head = True
      lemma = ru.fetch_noun_lemma(t, expand_text)
      for head in re.split(",", lemma):
        if "//" in head:
          head, tr = re.split("//", head)
          add(head, tr)
        else:
          add(head, "")
    if saw_head:
      for i in xrange(2, 10):
        headn = getparam(t, "head" + str(i))
        if headn:
          add(headn, getparam(t, "tr" + str(i)))

  if len(heads) == 0:
    if not saw_head:
      if re.match("#redirect", page.text, re.I):
        pagemsg("Redirect without heads")
      else:
        pagemsg("WARNING: Can't find any heads: %s" % pagename)
    return term, termtr
  if len(heads) > 1:
    pagemsg("WARNING: Found multiple heads for %s: %s" % (pagename, ",".join("%s%s" % (ru, "//%s" % tr if tr else "") for ru, tr in heads)))
    return term, termtr
  newterm, newtr = list(heads)[0]
  if semi_verbose:
    pagemsg("find_vocalized: Found head %s%s" % (newterm, "//%s" % newtr if newtr else ""))
  if remove_diacritics(newterm) != remove_diacritics(term):
    pagemsg("WARNING: Accented term %s differs from %s in more than just accents" % (
      newterm, term))
  return newterm, newtr

def find_vocalized(term, termtr, verbose, pagemsg):
  if semi_verbose:
    pagemsg("find_vocalized: Call with term %s%s" % (term, "//%s" % termtr if termtr else ""))
  term, termtr = find_vocalized_1(term, termtr, verbose, pagemsg)
  if semi_verbose:
    pagemsg("find_vocalized: Return %s%s" % (term, "//%s" % termtr if termtr else ""))
  return term, termtr

def check_need_accent(text):
  for word in re.split(" +", text):
    word = blib.remove_links(word)
    if u"\u0301" in word or u"ё" in word:
      continue
    word = re.sub(not_russian_vowel_class, "", word)
    if len(word) > 1:
      return True
  return False

def join_changelog_notes(notes):
  accented_words = []
  other_notes = []
  for note in notes:
    m = re.search("^auto-accent (.*)$", note)
    if m:
      accented_words.append(m.group(1))
    else:
      other_notes.append(note)
  if accented_words:
    notes = ["auto-accent %s" % ",".join(accented_words)]
  else:
    notes = []
  notes.extend(other_notes)
  return "; ".join(notes)

def process_template(pagetitle, index, template, ruparam, trparam, output_line,
    find_accents, verbose):
  origt = unicode(template)
  saveparam = ruparam
  def pagemsg(text):
    msg("Page %s %s: %s" % (index, pagetitle, text))
  def expand_text(tempcall):
    return blib.expand_text(tempcall, pagetitle, pagemsg, semi_verbose)
  if isinstance(ruparam, list):
    ruparam, saveparam = ruparam
  if ruparam == "page title":
    val = pagetitle
  else:
    val = getparam(template, ruparam)
  valtr = getparam(template, trparam) if trparam else ""
  changed = False
  if check_need_accent(val):
    if find_accents:
      newval, newtr = find_vocalized(val, valtr, verbose, pagemsg)
      if newval == val and newtr == valtr:
        words = re.split(r"((?:[ ,.?!\-]|''+)+)", val)
        trwords = re.split(r"((?:[ ,.?!\-]|''+)+)", valtr) if valtr else []
        if trwords and len(words) != len(trwords):
          pagemsg("WARNING: %s Cyrillic words but different number %s translit words: %s//%s" % (len(words), len(trwords), val, valtr))
        elif len(words) == 1:
          # Only one word, and we already looked it up; don't duplicate work
          pass
        else:
          # Check for "unbalanced" brackets. Can happen if the text is e.g.
          # [[торго́вец]] [[произведение искусства|произведе́ниями иску́сства]]
          # with multiple words inside a bracket -- not really unbalanced
          # but tricky to handle properly.
          unbalanced = False
          for i in xrange(0, len(words), 2):
            word = words[i]
            if word.count("[") != word.count("]"):
              pagemsg("WARNING: Unbalanced brackets in word #%s %s: %s" %
                  (i//2, word, "".join(words)))
              unbalanced = True
              break
          if not unbalanced:
            newwords = []
            newtrwords = []
            # If we end up with any words with manual translit (either because
            # translit was already supplied by the existing template and we
            # preserve the translit for a given word, or because we encounter
            # manual translit when looking up a word), we will need to manually
            # transliterate all remaining words. Note, even when the existing
            # template supplies manual translit, we may need to manually
            # translit some words, because the lookup of those words may
            # (in fact, usually will) return a result without manual translit.
            sawtr = False
            # Go through each word and separator.
            for i in xrange(len(words)):
              word = words[i]
              trword = trwords[i] if trwords else ""
              if i % 2 == 0:
                # If it's a word (not a separator), look it up if necessary.
                if check_need_accent(word):
                  ru, tr = find_vocalized(word, trword, verbose, pagemsg)
                else:
                  ru, tr = word, trword
                newwords.append(ru)
                newtrwords.append(tr)
                # If we saw a manual translit word, note it (see above).
                if tr:
                  sawtr = True
              else:
                # Else, a separator. Just copy the separator. If it has
                # translit, copy that as well, else copy the separator
                # directly as the translit (all the separator tokens should
                # pass through translit unchanged). Only flag the need for
                # manual translit expansion if there's an existing manual
                # translit of the separator that's different from the
                # separator itself, i.e. different from what auto-translit
                # would produce. (FIXME: It's arguably an error if the
                # manual translit of a separator is different from the
                # separator itself. We output a warning but maybe we should
                # override the manual translit entirely.)
                newwords.append(word)
                newtrwords.append(trword or word)
                if trword and word != trword:
                  pagemsg("WARNING: Separator <%s> at index %s has manual translit <%s> that's different from it: %s" % (
                    word, i, trword, origt))
                  sawtr = True
            if sawtr:
              newertrwords = []
              got_error = False
              for ru, tr in zip(newwords, newtrwords):
                if tr:
                  pass
                elif not ru:
                  tr = ""
                else:
                  tr = expand_text("{{xlit|ru|%s}}" % ru)
                  if not tr:
                    got_error = True
                    pagemsg("WARNING: Got error during transliteration")
                    break
                newertrwords.append(tr)
              if not got_error:
                newval = "".join(newwords)
                newtr = "".join(newertrwords)
            else:
              newval = "".join(newwords)
              newtr = ""
      if newval != val or newtr != valtr:
        if remove_diacritics(newval) != remove_diacritics(val):
          pagemsg("WARNING: Accented page %s changed from %s in more than just accents, not changing" % (newval, val))
        else:
          changed = True
          addparam(template, saveparam, newval)
          if newtr:
            if not trparam:
              pagemsg("WARNING: Unable to change translit to %s because no translit param available (Cyrillic param %s): %s" %
                  (newtr, saveparam, origt))
            else:
              if valtr and valtr != newtr:
                pagemsg("WARNING: Changed translit param %s from %s to %s: origt=%s" %
                    (trparam, valtr, newtr, origt))
              addparam(template, trparam, newtr)
          elif valtr:
            pagemsg("WARNING: Template has translit %s but lookup result has none, leaving translit alone: origt=%s" %
                (valtr, origt))
          if check_need_accent(newval):
            output_line("Need accents (changed)")
          else:
            output_line("Found accents")
    if not changed:
      output_line("Need accents")
    if changed:
      pagemsg("Replaced %s with %s" % (origt, unicode(template)))
  return ["auto-accent %s%s" % (newval, "//%s" % newtr if newtr else "")] if changed else False

def find_russian_need_vowels(find_accents, cattype, direcfile, save, verbose,
    startFrom, upTo):
  if direcfile:
    processing_lines = []
    for line in codecs.open(direcfile, "r", encoding="utf-8"):
      line = line.strip()
      m = re.match(r"^(Page [^ ]+ )(.*?)(: .*?:) Processing: (\{\{.*?\}\})( <- \{\{.*?\}\} \(\{\{.*?\}\}\))$",
          line)
      if m:
        processing_lines.append(m.groups())

    for current, index in blib.iter_pages(processing_lines, startFrom, upTo,
        # key is the page name
        key = lambda x:x[1]):

      pagenum, pagename, tempname, repltext, rest = current

      def check_template_for_missing_accent(pagetitle, index, template,
          ruparam, trparam):
        def output_line(directive):
          msg("* %s[[%s]]%s %s: <nowiki>%s%s</nowiki>" % (pagenum, pagename,
              tempname, directive, unicode(template), rest))
        return process_template(pagetitle, index, template, ruparam, trparam,
            output_line, find_accents, verbose)

      blib.process_links(save, verbose, "ru", "Russian", "pagetext", None,
          None, check_template_for_missing_accent,
          join_actions=join_changelog_notes,
          pages_to_do=[(pagename, repltext)], quiet=True)
  else:
    def check_template_for_missing_accent(pagetitle, index, template,
        ruparam, trparam):
      def pagemsg(text):
        msg("Page %s %s: %s" % (index, pagetitle, text))
      def output_line(directive):
        pagemsg("%s: %s" % (directive, unicode(template)))
      return process_template(pagetitle, index, template, ruparam, trparam,
          output_line, find_accents, verbose)

    blib.process_links(save, verbose, "ru", "Russian", cattype, startFrom,
        upTo, check_template_for_missing_accent,
        join_actions=join_changelog_notes, quiet=True)

pa = blib.init_argparser("Find Russian terms needing accents")
pa.add_argument("--cattype", default="vocab",
    help="Categories to examine ('vocab', 'borrowed', 'translation')")
pa.add_argument("--file",
    help="File containing output from parse_log_file.py")
pa.add_argument("--semi-verbose", action="store_true",
    help="More info but not as much as --verbose")
pa.add_argument("--find-accents", action="store_true",
    help="Look up the accents in existing pages")

params = pa.parse_args()
semi_verbose = params.semi_verbose or params.verbose
startFrom, upTo = blib.parse_start_end(params.start, params.end)

find_russian_need_vowels(params.find_accents, params.cattype,
    params.file, params.save, params.verbose, startFrom, upTo)
