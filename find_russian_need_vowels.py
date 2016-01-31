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

# Despite its name, this is actually a script to auto-accent Russian text
# by looking up unaccented multisyllabic words in the dictionary and fetching
# the accented headwords, and if there's only one, using it in place of the
# original unaccented word. We're somewhat smarter than this, e.g. we first
# try looking up the whole phrase before partitioning it into individual
# words.
#
# FIXME:
#
# 1. (DONE AS PART OF SMARTER WORD SPLITTING) Handle '''FOO''', matched up
#    against blank tr, TR or '''TR'''. Cf. '''спасти''' in 23865 спасти.
# 2. (DONE) Handle multiword expressions *inside* of find_accented so we
#    can handle e.g. the multiword linked expressions in 24195 стан, such
#    as [[нотный стан]] and [[передвижной полевой стан]].
# 3. (DONE) Handle single-word two-part links [[FOO|BAR]].
# 4. Consider implementing support for [[FOO BAR]] [[BAZ]]. To do this
#    we need to keep [[FOO BAR]] together when word-splitting. We can
#    do this by splitting on the expression we want to keep together,
#    with a capturing split, something like "(\[\[.*?\]\]|[^ ,.!?\-]+)".
#    It's tricky to handle treating ''' as punctuation when doing this,
#    and even trickier if there is manual translit; probably in the latter
#    case we just want to refuse to do it.
# 5. (DONE) When splitting on spaces, don't split on hyphens at first, but
#    then split on hyphens the second time around.
# 6. (DONE) Implement a cache in find_accented_2().
# 7. (DONE, NO, ACCENTED TEXT CAN'T BE PUT INTO WIKIPEDIA PAGE LINKS)
#    Should probably skip {{wikipedia|lang=ru|...}} links. First check
#    whether accented text can even be put into the page link.
# 8. (DONE) Skip {{temp|head}}.
# 9. (DONE) Don't try to accent multisyllable particles that should be
#    accentless (либо, нибудь, надо, обо, ото, перед, передо, подо, предо,
#    через).
# 10. (DONE) Message "changed from ... in more than just accents": Handle
#    grave accent on е and и, handle case where accented text ends with extra
#    ! or ?.
# 11. (DONE) Turn off splitting of templates on translit with comma in it.
# 12. (DONE) When doing word splitting and looking up individual words,
#    if the lookup result has a comma in translit, chop off everything
#    after the comma and issue a warning. Occurs e.g. in 6661 детектив,
#    with {{l|ru|частный детектив}}. (FIXME: Even better would be to
#    duplicate the entire translit.)
# 13. (DONE) When fetching the result of ru-noun+, if there are multiple
#    lemmas, combine the ones with the same Russian by separating the translits
#    with a comma. Occurs e.g. in 6810 динамика with {{l|ru|термодинамика}}.
# 14. If we repeat this script, we should handle words that occur directly
#    after a stressed monosyllabic preposition and not auto-acent them.
#    The list of such prepositions is без, близ, во, да, до, за, из, ко,
#    меж, на, над, не, ни, об, от, по, под, пред, при, про, со, у. I don't
#    think multisyllabic unstressed prepositions can steal accent from a
#    following word; need to ask Anatoli/Wikitiki89 about this.

import re, codecs

import blib, pywikibot
from blib import msg, getparam, addparam
import rulib as ru

site = pywikibot.Site()
semi_verbose = False # Set by --semi-verbose or --verbose

# List of accentless multisyllabic words. FIXME: We include было because of
# the expression не́ было, but we should maybe check for this expression
# rather than never accenting было.
accentless_multisyllable = [u"либо", u"нибудь", u"надо", u"обо", u"ото",
  u"перед", u"передо", u"подо", u"предо", u"через", u"было"]

ru_head_templates = ["ru-noun", "ru-proper noun", "ru-verb", "ru-adj", "ru-adv",
  "ru-phrase", "ru-noun form"]

# List of heads found during lookup of a page. Value is None if the page
# doesn't exist. Value is the string "redirect" if page is a redirect.
# Otherwise, value is a tuple (HEADS, SAW_HEAD) where HEADS is all heads
# found on the page, and SAW_HEAD is True if we saw any headword templates
# on the page (we might have found headword templates but no heads, e.g.
# in a template call like {{ru-phrase}}).
accented_cache = {}
num_cache_lookups = 0
num_cache_hits = 0
global_disable_cache = False

def output_stats(pagemsg):
  if global_disable_cache:
    return
  pagemsg("Cache size = %s" % len(accented_cache))
  pagemsg("Cache lookups = %s, hits = %s, %0.2f%% hit rate" % (
    num_cache_lookups, num_cache_hits,
    float(num_cache_hits)*100/num_cache_lookups if num_cache_lookups else 0.0))

def split_ru_tr(form):
  if "//" in form:
    rutr = re.split("//", form)
    assert len(rutr) == 2
    ru, tr = rutr
    return (ru, tr)
  else:
    return (form, "")

# Look up a single term (which may be multi-word); if the page exists,
# retrieve the headword(s), and if there's only one, return its
# (presumably accented) text and any manual translit; otherwise, return
# the term and translit passed in.
def find_accented_2(term, termtr, verbose, pagemsg):
  if term in accentless_multisyllable:
    pagemsg("Not accenting unaccented multisyllabic particle %s" % term)
    return term, termtr
  # This can happen if e.g. we're passed "[[FOO|BAR]] BAZ"; we will reject it,
  # but it will then be word-split and handled correctly ("[[FOO|BAR]]" is
  # special-cased in find_accented_1()).
  if "|" in term:
    #pagemsg("Can't handle links with vertical bars: %s" % term)
    return term, termtr
  # This can happen if e.g. we're passed "[[FOO]] [[BAR]]"; we will reject it,
  # but it will then be word-split and handled correctly ("[[FOO]]" is
  # special-cased in find_accented_1()).
  if "[" in term or "]" in term:
    #pagemsg("Can't handle stray bracket in %s" % term)
    return term, termtr
  if "<" in term or ">" in term:
    pagemsg("Can't handle stray < or >: %s" % term)
    return term, termtr
  if u"\u0301" in term or u"ё" in term:
    pagemsg(u"Term has accent or ё, not looking up accents: %s" % term)
    return term, termtr
  if ru.is_monosyllabic(term):
    pagemsg("Term is monosyllabic, not looking up accents: %s" % term)
    return term, termtr
  pagename = ru.remove_accents(term)
  # We can't use expand_text() from find_accented_1() because it has a
  # different value for PAGENAME, and the proper value is important in
  # expanding ru-noun+ and ru-proper noun+.
  def expand_text(tempcall):
    return blib.expand_text(tempcall, pagename, pagemsg, semi_verbose)

  # Look up the page
  if semi_verbose:
    pagemsg("find_accented: Finding heads on page %s" % pagename)

  cached_redirect = False
  global num_cache_lookups
  num_cache_lookups += 1
  if pagename in accented_cache:
    global num_cache_hits
    num_cache_hits += 1
    result = accented_cache[pagename]
    cached = True
    if result is None:
      if semi_verbose:
        pagemsg("find_accented: Page %s doesn't exist (cached)" % pagename)
      return term, termtr
    elif result == "redirect":
      cached_redirect = True
      heads = set()
      saw_head = False
    else:
      heads, saw_head = result
  else:
    cached = False
    page = pywikibot.Page(site, pagename)
    try:
      if not page.exists():
        if semi_verbose:
          pagemsg("find_accented: Page %s doesn't exist" % pagename)
        if not global_disable_cache:
          accented_cache[pagename] = None
        return term, termtr
    except Exception as e:
      pagemsg("WARNING: Error checking page existence: %s" % unicode(e))
      if not global_disable_cache:
        accented_cache[pagename] = None
      return term, termtr

    # Page exists, find the heads
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
        lemmas = re.split(",", lemma)
        lemmas = [split_ru_tr(lemma) for lemma in lemmas]
        # Group lemmas by Russian, to group multiple translits
        lemmas = ru.group_translits(lemmas, pagemsg, expand_text)
        for val, tr in lemmas:
          add(val, tr)
      if saw_head:
        for i in xrange(2, 10):
          headn = getparam(t, "head" + str(i))
          if headn:
            add(headn, getparam(t, "tr" + str(i)))
    if not global_disable_cache:
      accented_cache[pagename] = (heads, saw_head)

  # We have the heads
  cached_msg = " (cached)" if cached else ""
  if len(heads) == 0:
    if not saw_head:
      if cached_redirect:
        pagemsg("Redirect without heads (cached)")
      elif not cached and re.match("#redirect", page.text, re.I):
        if not global_disable_cache:
          accented_cache[pagename] = "redirect"
        pagemsg("Redirect without heads")
      else:
        pagemsg("WARNING: Can't find any heads: %s%s" % (pagename, cached_msg))
    return term, termtr
  if len(heads) > 1:
    pagemsg("WARNING: Found multiple heads for %s%s: %s" % (pagename, cached_msg, ",".join("%s%s" % (ru, "//%s" % tr if tr else "") for ru, tr in heads)))
    return term, termtr
  newterm, newtr = list(heads)[0]
  if semi_verbose:
    pagemsg("find_accented: Found head %s%s%s" % (newterm, "//%s" % newtr if newtr else "", cached_msg))
  if re.search("[!?]$", newterm) and not re.search("[!?]$", term):
    newterm_wo_punc = re.sub("[!?]$", "", newterm)
    if ru.remove_accents(newterm_wo_punc) == ru.remove_accents(term):
      pagemsg("Removing punctuation from %s when matching against %s" % (
        newterm, term))
      newterm = newterm_wo_punc
  if ru.remove_accents(newterm) != ru.remove_accents(term):
    pagemsg("WARNING: Accented term %s differs from %s in more than just accents%s" % (
      newterm, term, cached_msg))
  return newterm, newtr

# After the words in TERM with translit TERMTR have been split into words
# WORDS and TRWORDS (which should be an empty list if TERMTR is empty), with
# alternating separators in the odd-numbered words, find accents for each
# individual word and then rejoin the result.
def find_accented_split_words(term, termtr, words, trwords, verbose, pagemsg,
    expand_text, origt):
  newterm = term
  newtr = termtr
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
        # If it's a word (not a separator), look it up.
        ru, tr = find_accented(word, trword, verbose, pagemsg, expand_text,
            origt)
        if tr and "," in tr:
          chopped_tr = re.sub(",.*", "", tr)
          pagemsg("WARNING: Comma in translit <%s>, chopping off text after the comma to <%s>" % (
            tr, chopped_tr))
          tr = chopped_tr
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
        newterm = "".join(newwords)
        newtr = "".join(newertrwords)
    else:
      newterm = "".join(newwords)
      newtr = ""
  return newterm, newtr

# Look up a term (and associated manual translit) and try to add accents.
# The basic algorithm is that we first look up the whole term and then
# split on words and recursively look up each word individually.
# We are currently able to handle some bracketed expressions but not all:
#
# (1) If we're passed in [[FOO]] or [[FOO BAR]], we handle it as a special
#     case by recursively looking up the text inside the link.
# (2) If we're passed in [[FOO|BAR]] or [[FOO BAR|BAZ BAT]], we handle it as
#     another special case by recursively looking up the text on the right
#     side of the vertical bar.
# (3) If we're passed in [[FOO]] [[BAR]], [[FOO]] [[BAR|BAZ]] or
#     [[FOO|BAR]] [[BAZ|BAT]], special cases (1) and (2) won't apply. We then
#     will reject it (i.e. leave it unchanged) during the first lookup but
#     then succeed during the recursive (word-split) version, because we
#     will recursively be able to handle the individual parts by cases
#     (1) and (2).
# (4) If we're passed in [[FOO BAR]] [[BAZ]], or any other expression with
#     a space inside of a link that isn't the entire term, we can't currently
#     handle it. Word splitting will leave unbalanced "words" [[FOO and BAR]],
#     which we will trigger a rejection of the whole expression (i.e. it will
#     be left unchanged).
def find_accented_1(term, termtr, verbose, pagemsg, expand_text, origt):
  # We can handle plain [[FOO]] or [[FOO BAR]]
  m = re.search(r"^\[\[([^\[\]\|]*)\]\]$", term)
  if m:
    newterm, newtr = find_accented(m.group(1), termtr, verbose, pagemsg, expand_text, origt)
    return "[[" + newterm + "]]", newtr
  # We can handle [[FOO|BAR]] or [[FOO BAR|BAZ BAT]]
  m = re.search(r"^\[\[([^\[\]\|]*)\|([^\[\]\|]*)\]\]$", term)
  if m:
    newterm, newtr = find_accented(m.group(2), termtr, verbose, pagemsg, expand_text, origt)
    return "[[" + m.group(1) + "|" + newterm + "]]", newtr

  newterm, newtr = find_accented_2(term, termtr, verbose, pagemsg)
  if newterm == term and newtr == termtr:
    words = re.split(r"((?:[ ,.?!]|''+)+)", term)
    trwords = re.split(r"((?:[ ,.?!]|''+)+)", termtr) if termtr else []
    if trwords and len(words) != len(trwords):
      pagemsg("WARNING: %s Cyrillic words but different number %s translit words: %s//%s" % (len(words), len(trwords), term, termtr))
    elif len(words) == 1:
      if term.startswith("-") or term.endswith("-"):
        # Don't separate a prefix or suffix into component parts; might
        # not be the same word.
        pass
      else:
        # Only one word, and we already looked it up; don't duplicate work.
        # But split on hyphens the second time around.
        words = re.split(r"(-)", term)
        trwords = re.split(r"(-)", termtr) if termtr else []
        if trwords and len(words) != len(trwords):
          pagemsg("WARNING: %s Cyrillic words but different number %s translit words: %s//%s" % (len(words), len(trwords), term, termtr))
          pass
        elif len(words) == 1:
          # Only one word, and we already looked it up; don't duplicate work
          # or get stuck in infinite loop.
          pass
        else:
          newterm, newtr = find_accented_split_words(term, termtr, words,
              trwords, verbose, pagemsg, expand_text, origt)
    else:
      newterm, newtr = find_accented_split_words(term, termtr, words, trwords,
          verbose, pagemsg, expand_text, origt)
  return newterm, newtr

# Outer wrapper, equivalent to find_accented_1() except outputs extra
# log messages if --semi-verbose.
def find_accented(term, termtr, verbose, pagemsg, expand_text, origt):
  if semi_verbose:
    pagemsg("find_accented: Call with term %s%s" % (term, "//%s" % termtr if termtr else ""))
  term, termtr = find_accented_1(term, termtr, verbose, pagemsg, expand_text,
      origt)
  if semi_verbose:
    pagemsg("find_accented: Return %s%s" % (term, "//%s" % termtr if termtr else ""))
  return term, termtr

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

def check_need_accent(text):
  for word in re.split(" +", text):
    word = blib.remove_links(word)
    if u"\u0301" in word or u"ё" in word:
      continue
    if not ru.is_monosyllabic(word):
      return True
  return False

def process_template(pagetitle, index, template, ruparam, trparam, output_line,
    find_accents, verbose):
  origt = unicode(template)
  saveparam = ruparam
  def pagemsg(text):
    msg("Page %s %s: %s" % (index, pagetitle, text))
  def expand_text(tempcall):
    return blib.expand_text(tempcall, pagetitle, pagemsg, semi_verbose)
  if semi_verbose:
    pagemsg("Processing template: %s" % unicode(template))
  if unicode(template.name) == "head":
    # Skip {{head}}. We don't want to mess with headwords.
    return False
  if isinstance(ruparam, list):
    ruparam, saveparam = ruparam
  if ruparam == "page title":
    val = pagetitle
  else:
    val = getparam(template, ruparam)
  valtr = getparam(template, trparam) if trparam else ""
  changed = False
  if find_accents:
    newval, newtr = find_accented(val, valtr, verbose, pagemsg, expand_text,
        origt)
    if newval != val or newtr != valtr:
      if ru.remove_accents(newval) != ru.remove_accents(val):
        pagemsg("WARNING: Accented page %s changed from %s in more than just accents, not changing" % (newval, val))
      else:
        changed = True
        addparam(template, saveparam, newval)
        if newtr:
          if not trparam:
            pagemsg("WARNING: Unable to change translit to %s because no translit param available (Cyrillic param %s): %s" %
                (newtr, saveparam, origt))
          elif unicode(template.name) in ["ru-ux"]:
            pagemsg("WARNING: Not changing or adding translit param %s=%s to ru-ux: origt=%s" % (
              trparam, newtr, origt))
          else:
            if valtr and valtr != newtr:
              pagemsg("WARNING: Changed translit param %s from %s to %s: origt=%s" %
                  (trparam, valtr, newtr, origt))
            if not valtr:
              pagemsg("NOTE: Added translit param %s=%s to template: origt=%s" %
                  (trparam, newtr, origt))
            addparam(template, trparam, newtr)
        elif valtr:
          pagemsg("WARNING: Template has translit %s but lookup result has none, leaving translit alone: origt=%s" %
              (valtr, origt))
        if check_need_accent(newval):
          output_line("Need accents (changed)")
        else:
          output_line("Found accents")
  if not changed and check_need_accent(val):
    output_line("Need accents")
  if changed:
    pagemsg("Replaced %s with %s" % (origt, unicode(template)))
  return ["auto-accent %s%s" % (newval, "//%s" % newtr if newtr else "")] if changed else False

def find_russian_need_vowels(find_accents, cattype, direcfile, save,
    verbose, startFrom, upTo):
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

      def pagemsg(text):
        msg("Page %s(%s) %s: %s" % (pagenum, index, pagetitle, text))
      def check_template_for_missing_accent(pagetitle, index, template,
          ruparam, trparam):
        def output_line(directive):
          msg("* %s[[%s]]%s %s: <nowiki>%s%s</nowiki>" % (pagenum, pagename,
              tempname, directive, unicode(template), rest))
        return process_template(pagetitle, index, template, ruparam, trparam,
            output_line, find_accents, verbose)

      blib.process_links(save, verbose, "ru", "Russian", "pagetext", None,
          None, check_template_for_missing_accent,
          join_actions=join_changelog_notes, split_templates=None,
          pages_to_do=[(pagename, repltext)], quiet=True)
      if index % 100 == 0:
        output_stats(pagemsg)
  else:
    def check_template_for_missing_accent(pagetitle, index, template,
        ruparam, trparam):
      def pagemsg(text):
        msg("Page %s %s: %s" % (index, pagetitle, text))
      def output_line(directive):
        pagemsg("%s: %s" % (directive, unicode(template)))
      result = process_template(pagetitle, index, template, ruparam, trparam,
          output_line, find_accents, verbose)
      if index % 100 == 0:
        output_stats(pagemsg)
      return result

    blib.process_links(save, verbose, "ru", "Russian", cattype, startFrom,
        upTo, check_template_for_missing_accent,
        join_actions=join_changelog_notes, split_templates=None)

pa = blib.init_argparser("Find Russian terms needing accents")
pa.add_argument("--cattype", default="vocab",
    help="Categories to examine ('vocab', 'borrowed', 'translation')")
pa.add_argument("--file",
    help="File containing output from parse_log_file.py")
pa.add_argument("--semi-verbose", action="store_true",
    help="More info but not as much as --verbose")
pa.add_argument("--find-accents", action="store_true",
    help="Look up the accents in existing pages")
pa.add_argument("--no-cache", action="store_true",
    help="Disable caching head lookup results")

params = pa.parse_args()
semi_verbose = params.semi_verbose or params.verbose
global_disable_cache = params.no_cache
startFrom, upTo = blib.parse_start_end(params.start, params.end)

find_russian_need_vowels(params.find_accents, params.cattype,
    params.file, params.save, params.verbose, startFrom, upTo)

blib.elapsed_time()
