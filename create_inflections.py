#!/usr/bin/env python
#coding: utf-8

#    create_inflections.py is free software: you can redistribute it and/or modify
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
from blib import msg

site = pywikibot.Site()

verbose = True

# hamza
HAMZA = u"ء"

# diacritics
A  = u"\u064E" # fatḥa
AN = u"\u064B" # fatḥatān (fatḥa tanwīn)
U  = u"\u064F" # ḍamma
UN = u"\u064C" # ḍammatān (ḍamma tanwīn)
I  = u"\u0650" # kasra
IN = u"\u064D" # kasratān (kasra tanwīn)
SK = u"\u0652" # sukūn = no vowel
SH = u"\u0651" # šadda = gemination of consonants
DAGGER_ALIF = u"\u0670"
DIACRITIC_ANY_BUT_SH = "[" + A + I + U + AN + IN + UN + SK + DAGGER_ALIF + "]"
DIACRITIC_ANY = "[" + A + I + U + AN + IN + UN + SK + SH + DAGGER_ALIF + "]"

# various letters
ALIF = u"ا"
ALIF_WASLA = u"ٱ"
ALIF_ANY = "[" + ALIF + ALIF_WASLA + "]"
AMAQ = u"ى"
AMAD = u"آ"
TAM = u"ة"
Y = u"ي"

# combinations
UUN = U + u"ون"
UUNA = UUN + A
UNU = "[" + UN + U + "]"

def remove_diacritics(word):
  return re.sub(DIACRITIC_ANY, "", word)

def remove_links(text):
  text = re.sub(r"\[\[[^|\]]*?\|", "", text)
  text = re.sub(r"\[\[", "", text)
  text = re.sub(r"\]\]", "", text)
  return text

def reorder_shadda(text):
  # shadda+short-vowel (including tanwīn vowels, i.e. -an -in -un) gets
  # replaced with short-vowel+shadda during NFC normalisation, which
  # MediaWiki does for all Unicode strings; however, it makes the
  # detection process inconvenient, so undo it.
  return re.sub("(" + DIACRITIC_ANY_BUT_SH + ")" + SH, SH + r"\1", text)

def get_vn_gender(word, form):
  # Remove -un or -u i3rab
  word = re.sub(UNU + "$", "", reorder_shadda(word))
  if word.endswith(TAM):
    return "f"
  elif word.endswith(AN + AMAQ) or word.endswith(AN + ALIF):
    return "m"
  elif word.endswith(ALIF + HAMZA):
    if form != "I":
      return "m"
    elif re.match("^.[" + A + I + U + "]." + A + ALIF + HAMZA + "$", word):
      # only 3 consonants including hamza, which subs for a final-weak
      # consonant
      return "m"
    else:
      return "?"
  elif (word.endswith(AMAQ) or word.endswith(AMAD) or word.endswith(ALIF)):
    return "?"
  else:
    return "m"

# Make sure there are two trailing newlines
def ensure_two_trailing_nl(text):
  return re.sub(r"\n*$", r"\n\n", text)

lemma_inflection_counts = {}

# Create or insert a section describing a given inflection of a given lemma.
# INFLECTION is the vocalized inflectional form (e.g. the
# plural, feminine, verbal noun, participle, etc.); LEMMA is the vocalized
# lemma (e.g. the singular, masculine or dictionary form of a verb); INFLTR
# and LEMMATR are the associated manual transliterations (if any). POS is the
# part of speech of the word (capitalized, e.g. "Noun"). Only save the changed
# page if SAVE is true. INDEX is the numeric index of the lemma page, for
# ID purposes and to aid restarting. INFLTYPE is e.g. "plural", "feminine",
# "verbal noun", "active participle" or "passive participle", and is used in
# messages; both POS and INFLTYPE are used in special-case code that is
# appropriate to only certain inflectional types. LEMMATYPE is e.g.
# "singular", "masculine" or "dictionary form" and is used in messages.
# INFLTEMP is the headword template for the inflected-word entry (e.g.
# "ar-noun-pl", "ar-adj-pl" or "ar-adj-fem"). INFLTEMP_PARAM is a parameter
# or parameters to add to the created INFLTEMP template, and should be either
# empty or of the form "|foo=bar" (or e.g. "|foo=bar|baz=bat" for more than
# one parameter). DEFTEMP is the definitional template that points to the
# base form (e.g. "plural of", "masculine plural of" or "feminine of").
# DEFTEMP_PARAM is a parameter or parameters to add to the created DEFTEMP
# template, similar to INFLTEMP_PARAM.
def create_inflection_entry(save, index, inflection, infltr, lemma, lemmatr,
    pos, infltype, lemmatype, infltemp, infltemp_param, deftemp,
    deftemp_param):

  # Did we insert an entry or find an existing one? If not, we need to
  # add a new one. If we break out of the loop through subsections of the
  # Arabic section, we also don't need an entry; but we have this flag
  # because in some cases we need to continue checking subsections after
  # we've inserted an entry, to delete duplicate ones.
  need_new_entry = True

  # Remove any links that may esp. appear in the lemma, since the
  # vocalized version of the lemma as it appears in the lemma's headword
  # template often has links in it when the form is multiword.
  lemma = remove_links(lemma)
  inflection = remove_links(inflection)

  # Fetch pagename, create pagemsg() fn to output msg with page name included
  pagename = remove_diacritics(inflection)
  def pagemsg(text, simple = False):
    if simple:
      msg("Page %s %s: %s" % (index, pagename, text))
    else:
      msg("Page %s %s: %s: %s %s%s, %s %s%s" % (index, pagename, text,
        infltype, inflection, " (%s)" % infltr if infltr else "",
        lemmatype, lemma, " (%s)" % lemmatr if lemmatr else ""))

  # Remove trailing -un/-u i3rab from inflected form and lemma

  def maybe_remove_i3rab(wordtype, word, nowarn=False, noremove=False):
    if noremove:
      return word
    def mymsg(text):
      if not nowarn:
        pagemsg(text)
    word = reorder_shadda(word)
    if word.endswith(UN):
      mymsg("Removing i3rab (UN) from %s" % wordtype)
      return re.sub(UN + "$", "", word)
    if word.endswith(U):
      mymsg("Removing i3rab (U) from %s" % wordtype)
      return re.sub(U + "$", "", word)
    if word.endswith(UUNA):
      mymsg("Removing i3rab (UUNA -> UUN) from %s" % wordtype)
      return re.sub(UUNA + "$", UUN, word)
    if word and word[-1] in [A, I, U, AN]:
      mymsg("FIXME: Strange diacritic at end of %s %s" % (wordtype, word))
    if word and word[0] == ALIF_WASLA:
      mymsg("Changing alif wasla to plain alif for %s %s" % (wordtype, word))
      word = ALIF + word[1:]
    return word

  is_participle = infltype.endswith("participle")
  is_vn = infltype == "verbal noun"
  is_verb_part = pos == "Verb"
  if is_verb_part:
    # Make sure infltemp_param is '|' + FORM, as we expect
    assert(len(infltemp_param) >= 2 and infltemp_param[0] == '|'
        and infltemp_param[1] in ["I", "V", "X"])
    verb_part_form = infltemp_param[1:]
    verb_part_inserted_defn = False
  is_plural_noun = infltype == "plural" and pos == "Noun"
  vn_or_participle = is_vn or is_participle
  lemma_is_verb = is_verb_part or vn_or_participle

  lemma = maybe_remove_i3rab(lemmatype, lemma, noremove=lemma_is_verb)
  inflection = maybe_remove_i3rab(infltype, inflection, noremove=is_verb_part)

  if inflection == "-":
    pagemsg("Not creating %s entry - for %s %s%s" % (
      infltype, lemmatype, lemma, " (%s)" % lemmatr if lemmatr else ""))
    return

  # Prepare to create page
  pagemsg("Creating entry")
  infl_no_vowels = pagename
  lemma_no_vowels = remove_diacritics(lemma)
  page = pywikibot.Page(site, pagename)

  # For singular قطعة and plural قطع, three different possible
  # sets of vocalizations. For this case, require that the
  # existing versions match exactly, rather than matching with
  # removed diacritics.
  #
  # This should now be handled by the general code to detect cases
  # where multiple lemmas that are the same when unvocalized have
  # inflections that are the same when unvocalized.
  # must_match_exactly = is_plural_noun and infl_no_vowels == u"قطع" and lemma_no_vowels == u"قطعة"
  must_match_exactly = False

  li_no_vowels = (lemma_no_vowels, infl_no_vowels)
  lemma_inflection_counts[li_no_vowels] = (
      lemma_inflection_counts.get(li_no_vowels, 0) + 1)
  if lemma_inflection_counts[li_no_vowels] > 1:
    pagemsg("Found multiple (%s) vocalized possibilities for %s %s, %s %s" % (
      lemma_inflection_counts[li_no_vowels], lemmatype, lemma_no_vowels,
      infltype, infl_no_vowels))
    must_match_exactly = True
  if vn_or_participle or is_verb_part:
    must_match_exactly = True

  def compare_param(template, param, value):
    # In place of unknown we should put infltype or lemmatype but it
    # doesn't matter because of nowarn.
    paramval = blib.getparam(template, param)
    paramval = maybe_remove_i3rab("unknown", paramval, nowarn=True,
        noremove=is_verb_part)
    if must_match_exactly:
      return reorder_shadda(paramval) == reorder_shadda(value)
    else:
      return remove_diacritics(paramval) == remove_diacritics(value)

  # Prepare parts of new entry to insert
  new_headword_template_prefix = "%s|%s" % (infltemp, inflection)
  new_headword_template = "{{%s%s%s}}" % (new_headword_template_prefix,
      infltemp_param, "|tr=%s" % infltr if infltr else "")
  new_defn_template = "{{%s|%s%s%s}}" % (
    deftemp, lemma,
    "|tr=%s" % lemmatr if lemmatr else "",
    deftemp_param)
  newposbody = """%s

# %s
""" % (new_headword_template, new_defn_template)
  newpos = "===%s===\n" % pos + newposbody
  newposl4 = "====%s====\n" % pos + newposbody
  newsection = "==Arabic==\n\n" + newpos

  comment = None
  notes = []
  existing_text = page.text

  if not page.exists():
    # Page doesn't exist. Create it.
    pagemsg("Creating page")
    comment = "Create page for Arabic %s %s of %s, pos=%s" % (
        infltype, inflection, lemma, pos)
    page.text = newsection
    if verbose:
      pagemsg("New text is [[%s]]" % page.text)
  else: # Page does exist
    # Split off interwiki links at end
    m = re.match(r"^(.*?\n)(\n*(\[\[[a-z0-9_\-]+:[^\]]+\]\]\n*)*)$",
        page.text, re.S)
    if m:
      pagebody = m.group(1)
      pagetail = m.group(2)
    else:
      pagebody = page.text
      pagetail = ""

    # Split into sections
    splitsections = re.split("(^==[^=\n]+==\n)", pagebody, 0, re.M)
    # Extract off pagehead and recombine section headers with following text
    pagehead = splitsections[0]
    sections = []
    for i in xrange(1, len(splitsections)):
      if (i % 2) == 1:
        sections.append("")
      sections[-1] += splitsections[i]

    # Go through each section in turn, looking for existing Arabic section
    for i in xrange(len(sections)):
      m = re.match("^==([^=\n]+)==$", sections[i], re.M)
      if not m:
        pagemsg("Can't find language name in text: [[%s]]" % (sections[i]))
      elif m.group(1) == "Arabic":
        # Extract off trailing separator
        mm = re.match(r"^(.*?\n)(\n*--+\n*)$", sections[i], re.S)
        if mm:
          sections[i:i+1] = [mm.group(1), mm.group(2)]

        # If verb part, correct mistaken indent from a previous run,
        # where level-3 entries were inserted instead of level 4.
        if is_verb_part and "\n===Etymology 1===\n" in sections[i]:
          oldsectionsi = sections[i]
          sections[i] = re.sub("\n===Verb===\n", "\n====Verb====\n",
              sections[i])
          if oldsectionsi != sections[i]:
            notes.append("corrected verb-part indent level")

        subsections = re.split("(^===+[^=\n]+===+\n)", sections[i], 0, re.M)

        # If verbal noun, count how many matching noun entries; if exactly
        # one, we will insert a verbal noun defn into it if necessary.
        # If more than one, punt because we don't know which one, or more
        # than one, to insert the verbal noun defn into.
        if is_vn:
          matching_vn_noun_templates = []
          for j in xrange(len(subsections)):
            if j > 0 and (j % 2) == 0:
              if re.match("^===+Noun===+", subsections[j - 1]):
                parsed = blib.parse_text(subsections[j])
                matching_vn_noun_templates += [
                    t for t in parsed.filter_templates()
                    if t.name == "ar-noun" and compare_param(t, "1", inflection)]
          if len(matching_vn_noun_templates) > 1:
            pagemsg("WARNING: Found multiple matching subsections, don't know which one to insert VN defn into")
            break

        # If verbal noun, convert existing ===Verbal noun=== headers into
        # ===Noun===, and existing {{ar-verbal noun}} templates into
        # {{ar-noun}}
        if is_vn:
          for j in xrange(len(subsections)):
            if j > 0 and (j % 2) == 0:
              if re.match("^===+Verbal noun===+", subsections[j - 1]):
                subsections[j - 1] = re.sub("(===+)Verbal noun(===+)",
                    r"\1Noun\2", subsections[j - 1])
                pagemsg("Converting 'Verbal noun' section header to 'Noun'")
                notes.append("converted 'Verbal noun' section header to 'Noun'")
              parsed = blib.parse_text(subsections[j])
              for t in parsed.filter_templates():
                if t.name == "ar-verbal noun":
                  t.name = "ar-noun"
                  pagemsg("Converting 'ar-verbal noun' template into 'ar-noun'")
                  notes.append("converted 'ar-verbal noun' template into 'ar-noun'")
              subsections[j] = unicode(parsed)
              sections[i] = ''.join(subsections)

        def sort_verb_part_sections():
          def sort_one_section(start, end):
            #msg("sort_one_section called with [%s,%s]" % (start, end))
            if end == start:
              return
            assert(start > 0 and (start % 2) == 0)
            assert((end % 2) == 0 and end > start)
            assert(end < len(subsections))
            header1 = subsections[start - 1]
            for j in xrange(start + 1, end + 1, 2):
              if subsections[j] != header1:
                pagemsg("Header [[%s]] doesn't match prior header [[%s]], not sorting"
                    % (subsections[j], header1))
                return
            subsecs = []
            for j in xrange(start, end + 2, 2):
              subsecs.append(subsections[j])
            def keyfunc(subsec):
              parsed = blib.parse_text(subsec)
              vf_person = 13
              vf_last_vowel = "u"
              vf_voice = "pasv"
              vf_mood = "c"

              for t in parsed.filter_templates():
                if t.name == "ar-verb-form":
                  vf_vowels = re.sub("[^" + A + I + U + "]", "",
                      blib.getparam(t, "1")[0:-1])
                  if len(vf_vowels) > 0:
                    if vf_vowels[-1] == A:
                      vf_last_vowel = "a"
                    elif vf_vowels[-1] == I:
                      vf_last_vowel = "i"
                    else:
                      vf_last_vowel = "u"
                if t.name == "inflection of":
                  tstr = unicode(t)
                  if "|actv" in tstr:
                    vf_voice = "actv"
                  if "|indc" in tstr:
                    vf_mood = "a"
                  if "|subj" in tstr:
                    vf_mood = "b"
                  persons = persons_infl_entry.values()
                  for k in xrange(len(persons)):
                    if "|" + persons[k] in tstr:
                      vf_person = k
              #msg("Sort key: %s" % ((vf_person, vf_voice, vf_last_vowel, vf_mood),))
              return (vf_person, vf_voice, vf_last_vowel, vf_mood)
            newsubsecs = sorted(subsecs, key=keyfunc)
            if newsubsecs != subsecs:
              for k, j in zip(xrange(len(subsecs)), xrange(start, end + 2, 2)):
                subsections[j] = ensure_two_trailing_nl(newsubsecs[k])
          subsections_sentinel = subsections + ["", ""]
          start = None
          for j in xrange(len(subsections_sentinel)):
            if j > 0 and (j % 2) == 0:
              is_verb_form = "{{ar-verb-form|" in subsections_sentinel[j]
              if start == None and is_verb_form:
                start = j
              if start != None and not is_verb_form:
                end = j - 2
                sort_one_section(start, end)
                start = None
          newtext = ''.join(subsections)
          if newtext != sections[i]:
            sections[i] = newtext
            pagemsg("Sorted verb part sections")
            notes.append("sorted verb part sections")

        # If verb part, go through and sort adjoining verb form sections
        if is_verb_part:
          sort_verb_part_sections()

        # Go through each subsection in turn, looking for subsection
        # matching the POS with an appropriate headword template whose
        # head matches the inflected form
        for j in xrange(len(subsections)):
          match_pos = False
          particip_pos_mismatch = False
          if j > 0 and (j % 2) == 0:
            if re.match("^===+%s===+\n" % pos, subsections[j - 1]):
              match_pos = True
            if is_participle:
              for mismatch_pos in ["Noun", "Adjective"]:
                if re.match("^===+%s===+\n" % mismatch_pos, subsections[j - 1]):
                  particip_pos_mismatch = True
                  particip_mismatch_pos = mismatch_pos
                  break

          # Found a POS match
          if match_pos or particip_pos_mismatch:
            parsed = blib.parse_text(subsections[j])

            def check_maybe_remove_i3rab(template, wordtype):
              # Check for i3rab in existing lemma or infl and remove it if so
              existing = blib.getparam(template, "1")
              existing_no_i3rab = maybe_remove_i3rab(wordtype, existing,
                  noremove=is_verb_part or wordtype == "dictionary form")
              if reorder_shadda(existing) != reorder_shadda(existing_no_i3rab):
                notes.append("removed %s i3rab" % wordtype)
                template.add("1", existing_no_i3rab)
                existing_tr = blib.getparam(template, "tr")
                if existing_tr:
                  pagemsg("WARNING: Removed i3rab from existing %s %s and manual translit %s exists" %
                      (wordtype, existing, existing_tr))
                existing = existing_no_i3rab
              return existing

            # Find the inflection headword (e.g. 'ar-noun-pl') and
            # definitional (e.g. 'plural of') templates. We require that
            # they match, either exactly (apart from i3rab) or only in the
            # consonants. If verb part, also require that the conj form match
            # in the inflection headword template, but don't require that
            # the lemma match in the definitional template.
            infl_headword_templates = [t for t in parsed.filter_templates()
                if t.name == infltemp and compare_param(t, "1", inflection)
                and (not is_verb_part or compare_param(t, "2", verb_part_form))]
            defn_templates = [t for t in parsed.filter_templates()
                if t.name == deftemp and (is_verb_part or
                compare_param(t, "1", lemma))]
            # Special-case handling for actual noun plurals. We expect an
            # ar-noun but if we encounter an ar-coll-noun with the plural as
            # the (collective) head and the singular as the singulative, we
            # output a message and skip so we don't end up creating a
            # duplicate entry.
            if is_plural_noun:
              headword_collective_templates = [t for t in parsed.filter_templates()
                  if t.name == "ar-coll-noun" and compare_param(t, "1", inflection)
                  and compare_param(t, "sing", lemma)]
              if headword_collective_templates:
                pagemsg("WARNING: Exists and has Arabic section and found collective noun with %s already in it; taking no action"
                    % (infltype))
                break

            def particip_mismatch_check():
              if particip_pos_mismatch:
                pagemsg("WARNING: Found match for %s but in ===%s=== section rather than ===%s==="
                    % (infltype, particip_mismatch_pos, pos))

            # Make sure there's exactly one headword template.
            if len(infl_headword_templates) > 1:
              pagemsg("WARNING: Found multiple inflection headword templates for %s; taking no action"
                  % (infltype))
              break

            # We found both templates and their heads matched; inflection
            # entry is probably already present. For verb forms, however,
            # check all the parameters of the definitional template,
            # because there may be multiple definitional templates
            # corresponding to different inflections that have the same form
            # for the same lemma (e.g. يَكْتُنُو yaktubū is both subjunctive and
            # jussive, and يَكْتُبْنَ yaktubna is all 3 of indicative, subjunctive
            # and jussive).
            if defn_templates and infl_headword_templates:
              pagemsg("Exists and has Arabic section and found %s already in it"
                  % (infltype))

              particip_mismatch_check()

              infl_headword_template = infl_headword_templates[0]

              # For verb forms check for an exactly matching definitional
              # template; if not, insert one at end of definition.
              if is_verb_part:
                def compare_verb_part_defn_templates(code1, code2):
                  pagemsg("Comparing %s with %s" % (code1, code2))
                  def canonicalize_defn_template(code):
                    code = reorder_shadda(code)
                    code = re.sub(r"\[\[.*?\]\]", "", code)
                    code = re.sub(r"\|gloss=[^|}]*", "", code)
                    code = re.sub(r"\|lang=ar", "", code)
                    return code
                  return (canonicalize_defn_template(code1) ==
                      canonicalize_defn_template(code2))
                found_exact_matching = False
                for d_t in defn_templates:
                  if compare_verb_part_defn_templates(unicode(d_t),
                      new_defn_template):
                    pagemsg("Found exact-matching definitional template for %s; taking no action"
                        % (infltype))
                    found_exact_matching = True
                  else:
                    pagemsg("Found non-matching definitional template for %s: %s"
                        % (infltype, unicode(d_t)))

                if verb_part_inserted_defn:
                  # If we already inserted an entry or found an exact-matching
                  # entry, check for duplicate entries. Currently we combine
                  # entries with the same inflection and conjugational form
                  # and separate lemmas, but previously created separate
                  # entries. We will add the new definition to the existing
                  # section but need to check for the previously added separate
                  # sections.
                  if found_exact_matching and len(defn_templates) == 1:
                    pagemsg("Found duplicate definition, deleting")
                    subsections[j - 1] = ""
                    subsections[j] = ""
                    sections[i] = ''.join(subsections)
                    notes.append("delete duplicate definition for %s %s, form %s"
                        % (infltype, inflection, verb_part_form))
                elif not found_exact_matching:
                  subsections[j] = unicode(parsed)
                  if subsections[j][-1] != '\n':
                    subsections[j] += '\n'
                  subsections[j] = re.sub(r"^(.*\n#[^\n]*\n)",
                      r"\1# %s\n" % new_defn_template, subsections[j], 1, re.S)
                  sections[i] = ''.join(subsections)
                  pagemsg("Adding new definitional template to existing defn for pos = %s" % (pos))
                  comment = "Add new definitional template to existing defn: %s %s, %s %s, pos=%s" % (
                      infltype, inflection, lemmatype, lemma, pos)

                # Don't break, so we can check for duplicate entries.
                # We set need_new_entry to false so we won't insert a new
                # one down below.
                verb_part_inserted_defn = True
                need_new_entry = False

              # Else, not verb form. Remove i3rab from existing headword and
              # definitional template, and maybe update the template heads
              # with better-vocalized versions.
              else:
                if len(defn_templates) > 1:
                  pagemsg("WARNING: Found multiple definitional templates for %s; taking no action"
                      % (infltype))
                  break
                defn_template = defn_templates[0]

                #### Rest of this code primarily for plurals and feminines,
                #### which may be partly vocalized and may have existing i3rab.
                #### For verbal nouns and participles, we require exact match
                #### so conditions like 'len(inflection) > len(existing_infl)'
                #### won't apply, and there generally isn't existing i3rab.
                
                # Check for i3rab in existing infl and remove it if so
                existing_infl = \
                    check_maybe_remove_i3rab(infl_headword_template, infltype)

                # Check for i3rab in existing lemma and remove it if so
                existing_lemma = \
                    check_maybe_remove_i3rab(defn_template, lemmatype)

                # Replace existing infl with new one
                if len(inflection) > len(existing_infl):
                  pagemsg("Updating existing %s %s with %s" %
                      (infltemp, existing_infl, inflection))
                  infl_headword_template.add("1", inflection)
                  if infltr:
                    infl_headword_template.add("tr", infltr)

                # Replace existing lemma with new one
                if len(lemma) > len(existing_lemma):
                  pagemsg("Updating existing '%s' %s with %s" %
                      (deftemp, existing_lemma, lemma))
                  defn_template.add("1", lemma)
                  if lemmatr:
                    defn_template.add("tr", lemmatr)

                #### End of code primarily for plurals and feminines.

                subsections[j] = unicode(parsed)
                sections[i] = ''.join(subsections)
                comment = "Update Arabic with better vocalized versions: %s %s, %s %s, pos=%s" % (
                    infltype, inflection, lemmatype, lemma, pos)
                break

            # At this point, didn't find either headword or definitional
            # template, or both.
            elif vn_or_participle:
              # Insert {{ar-verbal noun of}} (or equivalent for participles).
              # Return comment (can't set it inside of fn).
              def insert_vn_defn():
                subsections[j] = unicode(parsed)
                subsections[j] = re.sub("^#",
                    "# %s\n#" % new_defn_template,
                    subsections[j], 1, re.M)
                sections[i] = ''.join(subsections)
                pagemsg("Insert existing defn with {{%s}} at beginning" % (
                    deftemp))
                return "Insert existing defn with {{%s}} at beginning: %s %s, %s %s" % (
                    deftemp, infltype, inflection, lemmatype, lemma)

              # If verb or participle, see if we found inflection headword
              # template at least. If so, add definition to beginning as
              # {{ar-verbal noun of}} (or equivalent for participles).
              if infl_headword_templates:
                infl_headword_template = infl_headword_templates[0]

                # Check for i3rab in existing infl and remove it if so
                check_maybe_remove_i3rab(infl_headword_template, infltype)

                # Now actually add {{ar-verbal noun of}} (or equivalent
                # for participles).
                comment = insert_vn_defn()
                break

              elif is_participle:
                # Couldn't find headword template; if we're a participle,
                # see if there's a generic noun or adjective template
                # with the same head.
                for other_template in ["ar-noun", "ar-adj"]:
                  other_headword_templates = [
                      t for t in parsed.filter_templates()
                      if t.name == other_template and compare_param(t, "1", inflection)]
                  if other_headword_templates:
                      pagemsg("WARNING: Found %s matching %s" %
                          (other_template, infltype))
                      # FIXME: Should we break here? Should we insert
                      # a participle defn?

        # else of for loop over subsections, i.e. no break out of loop
        else:
          if not need_new_entry:
            break
          # At this point we couldn't find an existing subsection with
          # matching POS and appropriate headword template whose head matches
          # the the inflected form.

          # If verb part, try to find an existing verb section corresponding
          # to the same verb or another verb of the same conjugation form
          # (either the lemma of the verb or another non-lemma form).
          # When looking at the lemma of the verb, make sure both the
          # conjugation form and the consonants match so we don't end up
          # e.g. matching non-past yasurr (from sarra) with yasara, but
          # we do match up forms from faʿala and faʿila.
          # Insert after the last such one.
          if is_verb_part:
            insert_at = None
            for j in xrange(len(subsections)):
              if j > 0 and (j % 2) == 0:
                if re.match("^===+Verb===+", subsections[j - 1]):
                  parsed = blib.parse_text(subsections[j])
                  for t in parsed.filter_templates():
                    if (t.name == deftemp and compare_param(t, "1", lemma) or
                        t.name == infltemp and (not t.has("2") or compare_param(t, "2", verb_part_form)) or
                        t.name == "ar-verb" and re.sub("-.*$", "", blib.getparam(t, "1")) == verb_part_form and remove_diacritics(get_dicform(page, t)) == remove_diacritics(lemma)):
                      insert_at = j + 1
            if insert_at:
              pagemsg("Found section to insert verb part after: [[%s]]" %
                  subsections[insert_at - 1])

              # Determine indent level and skip past sections at higher indent
              m = re.match("^(==+)", subsections[insert_at - 2])
              indentlevel = len(m.group(1))
              while insert_at < len(subsections):
                if (insert_at % 2) == 0:
                  insert_at += 1
                  continue
                m = re.match("^(==+)", subsections[insert_at])
                newindent = len(m.group(1))
                if newindent <= indentlevel:
                  break
                pagemsg("Skipped past higher-indented subsection: [[%s]]" %
                    subsections[insert_at])
                insert_at += 1

              pagemsg("Inserting after verb section for same lemma")
              comment = "Insert entry for %s %s of %s after verb section for same lemma" % (
                infltype, inflection, lemma)
              subsections[insert_at - 1] = ensure_two_trailing_nl(
                  subsections[insert_at - 1])
              if indentlevel == 3:
                subsections[insert_at:insert_at] = [newpos + "\n"]
              else:
                assert(indentlevel == 4)
                subsections[insert_at:insert_at] = [newposl4 + "\n"]
              sections[i] = ''.join(subsections)
              sort_verb_part_sections()
              break

          # If participle, try to find an existing noun or adjective with the
          # same lemma to insert before. Insert before the first such one.
          if is_participle:
            insert_at = None
            for j in xrange(len(subsections)):
              if j > 0 and (j % 2) == 0:
                if re.match("^===+(Noun|Adjective)===+", subsections[j - 1]):
                  parsed = blib.parse_text(subsections[j])
                  for t in parsed.filter_templates():
                    if (t.name in ["ar-noun", "ar-adj"] and
                        compare_param(t, "1", inflection) and insert_at is None):
                      insert_at = j - 1

            if insert_at is not None:
              pagemsg("Found section to insert participle before: [[%s]]" %
                  subsections[insert_at + 1])

              comment = "Insert entry for %s %s of %s before section for same lemma" % (
                infltype, inflection, lemma)
              if insert_at > 0:
                subsections[insert_at - 1] = ensure_two_trailing_nl(
                    subsections[insert_at - 1])
              subsections[insert_at:insert_at] = [newpos + "\n"]
              sections[i] = ''.join(subsections)
              break

          pagemsg("Exists and has Arabic section, appending to end of section")
          # FIXME! Conceivably instead of inserting at end we should insert
          # next to any existing ===Noun=== (or corresponding POS, whatever
          # it is), in particular after the last one. However, this makes less
          # sense when we create separate etymologies, as we do. Conceivably
          # this would mean inserting after the last etymology section
          # containing an entry of the same part of speech.
          #
          # (Perhaps for now we should just skip creating entries if we find
          # an existing Arabic entry?)
          if "\n===Etymology 1===\n" in sections[i]:
            j = 2
            while ("\n===Etymology %s===\n" % j) in sections[i]:
              j += 1
            pagemsg("Found multiple etymologies, adding new section \"Etymology %s\"" % (j))
            comment = "Append entry (Etymology %s) for %s %s of %s, pos=%s in existing Arabic section" % (
              j, infltype, inflection, lemma, pos)
            sections[i] = ensure_two_trailing_nl(sections[i])
            sections[i] += "===Etymology %s===\n\n" % j + newposl4
          else:
            pagemsg("Wrapping existing text in \"Etymology 1\" and adding \"Etymology 2\"")
            comment = "Wrap existing Arabic section in Etymology 1, append entry (Etymology 2) for %s %s of %s, pos=%s" % (
                infltype, inflection, lemma, pos)
            # Wrap existing text in "Etymology 1" and increase the indent level
            # by one of all headers
            sections[i] = re.sub("^\n*==Arabic==\n+", "", sections[i])
            wikilink_re = r"^(\{\{wikipedia\|.*?\}\})\n*"
            mmm = re.match(wikilink_re, sections[i])
            wikilink = (mmm.group(1) + "\n") if mmm else ""
            if mmm:
              sections[i] = re.sub(wikilink_re, "", sections[i])
            sections[i] = re.sub("^===Etymology===\n", "", sections[i])
            sections[i] = ("==Arabic==\n" + wikilink + "\n===Etymology 1===\n" +
                ("\n" if sections[i].startswith("==") else "") +
                ensure_two_trailing_nl(re.sub("^==(.*?)==$", r"===\1===",
                  sections[i], 0, re.M)) +
                "===Etymology 2===\n\n" + newposl4)
        break
      elif m.group(1) > "Arabic":
        pagemsg("Exists; inserting before %s section" % (m.group(1)))
        comment = "Create Arabic section and entry for %s %s of %s, pos=%s; insert before %s section" % (
            infltype, inflection, lemma, pos, m.group(1))
        sections[i:i] = [newsection, "\n----\n\n"]
        break

    else: # else of for loop over sections, i.e. no break out of loop
      pagemsg("Exists; adding section to end")
      comment = "Create Arabic section and entry for %s %s of %s, pos=%s; append at end" % (
          infltype, inflection, lemma, pos)

      sections[-1] = ensure_two_trailing_nl(sections[-1])
      sections += ["----\n\n", newsection]

    # End of loop over sections in existing page; rejoin sections
    newtext = pagehead + ''.join(sections) + pagetail

    # If participle, remove [[Category:Arabic participles]]
    if is_participle:
      oldnewtext = newtext
      newtext = re.sub(r"\n+\[\[Category:Arabic participles]]\n+", r"\n\n",
          newtext)
      if newtext != oldnewtext:
        pagemsg("Removed [[Category:Arabic participles]]")

    if page.text == newtext:
      pagemsg("No change in text")
    elif verbose:
      pagemsg("Replacing [[%s]] with [[%s]]" % (page.text, newtext),
          simple = True)
    else:
      pagemsg("Text has changed")
    page.text = newtext

  # Executed whether creating new page or modifying existing page.
  # Check for changed text and save if so.
  notestext = '; '.join(notes)
  if notestext:
    if comment:
      comment += " (%s)" % notestext
    else:
      comment = notestext
  if page.text != existing_text:
    assert(comment)
    pagemsg("comment = %s" % comment, simple = True)
    if save:
      page.save(comment = comment)

def create_noun_plural(save, index, inflection, infltr, lemma, lemmatr, pos):
  create_inflection_entry(save, index, inflection, infltr, lemma, lemmatr, pos,
      "plural", "singular", "ar-noun-pl", "", "plural of", "|lang=ar")

def create_adj_plural(save, index, inflection, infltr, lemma, lemmatr, pos):
  create_inflection_entry(save, index, inflection, infltr, lemma, lemmatr, pos,
      "plural", "singular", "ar-adj-pl", "", "masculine plural of", "|lang=ar")

def create_noun_feminine_entry(save, index, inflection, infltr, lemma, lemmatr,
    pos):
  create_inflection_entry(save, index, inflection, infltr, lemma, lemmatr, pos,
      "feminine", "masculine", None, # FIXME
      "", "feminine of", "|lang=ar")

def create_adj_feminine_entry(save, index, inflection, infltr, lemma, lemmatr,
    pos):
  create_inflection_entry(save, index, inflection, infltr, lemma, lemmatr, pos,
      "feminine", "masculine", "ar-adj-fem", "", "feminine of", "|lang=ar")

def create_inflection_entries(save, pos, tempname, startFrom, upTo, createfn,
    param):
  for cat in [u"Arabic %ss" % pos.lower()]:
    for page, index in blib.cat_articles(cat, startFrom, upTo):
      for template in blib.parse(page).filter_templates():
        if template.name == tempname:
          lemma = blib.getparam(template, "1")
          lemmatr = blib.getparam(template, "tr")
          # Handle blank head; use page title
          if lemma == "":
            lemma = page.title()
            msg("Page %s: blank head in template %s (tr=%s)" % (
              lemma, tempname, lemmatr))
          infl = blib.getparam(template, param)
          infltr = blib.getparam(template, param + "tr")
          if infl:
            createfn(save, index, infl, infltr, lemma, lemmatr, pos)
          i = 2
          while infl:
            infl = blib.getparam(template, param + str(i))
            infltr = blib.getparam(template, param + str(i) + "tr")
            if infl:
              otherhead = blib.getparam(template, "head" + str(i))
              otherheadtr = blib.getparam(template, "tr" + str(i))
              if otherhead:
                msg("Page %s: Using head%s %s (tr=%s) as lemma for %s (tr=%s)" % (
                  lemma, i, otherhead, otherheadtr, infl, infltr))
                createfn(save, index, infl, infltr, otherhead, otherheadtr, pos)
              else:
                createfn(save, index, infl, infltr, lemma, lemmatr, pos)
            i += 1

def create_plurals(save, pos, tempname, startFrom, upTo):
  return create_inflection_entries(save, pos, tempname, startFrom, upTo,
      create_noun_plural if pos == "Noun" else create_adj_plural, "pl")

def create_feminines(save, pos, tempname, startFrom, upTo):
  return create_inflection_entries(save, pos, tempname, startFrom, upTo,
      create_noun_feminine if pos == "Noun" else create_adj_feminine, "f")

def expand_template(page, text):
  # Make an expand-template call to expand the template text.
  # The code here is based on the expand_text() function of the Page object.
  # FIXME: Use site.expand_text(text, title=page.title(withSection=False))
  req = pywikibot.data.api.Request(action="expandtemplates",
      text = text,
      title = page.title(withSection=False),
      site = page.site,
      prop = "wikitext" # "*"
      )
  #return req.submit()["expandtemplates"]["*"]
  return req.submit()["expandtemplates"]["wikitext"]

def get_part_prop(page, template, prefix):
  # Make an expand-template call to convert the conjugation template to
  # the desired form or property.
  return expand_template(page,
      re.sub("\{\{ar-(conj|verb)\|", "{{%s|" % prefix, unicode(template)))

def get_dicform(page, template):
  return get_part_prop(page, template, "ar-past3sm")

def get_passive(page, template):
  return get_part_prop(page, template, "ar-verb-prop|passive")

# For a given value of passive= (yes, impers, no, only, only-impers), does
# the verb have an active form?
def has_active_form(passive):
  assert(passive in ["yes", "impers", "no", "only", "only-impers"])
  return passive in ["yes", "impers", "no"]

# For a given value of passive= (yes, impers, no, only, only-impers) and a
# given person/number/gender combination, does the verb have a passive form?
# Supply None for PERS for non-finite verb parts (participles).
def has_passive_form(passive, pers):
  assert(passive in ["yes", "impers", "no", "only", "only-impers"])
  # If no person or it's 3sm, then impersonal passives have it. Otherwise no.
  if not pers or pers == "3sm":
    return passive != "no"
  return passive == "yes" or passive =="only"

# Create a verbal noun entry, either creating a new page or adding to an
# existing page. Do nothing if entry is already present. SAVE, INDEX are as in
# create_inflection_entry(). VN is the vocalized verbal noun; VERBPAGE is the
# Page object representing the dictionary-form verb of this verbal noun;
# TEMPLATE is the conjugation template for the verb, i.e. {{ar-conj|...}};
# UNCERTAIN is true if the verbal noun is uncertain (indicated with a ? at
# the end of the vn=... parameter in the conjugation template).
def create_verbal_noun(save, index, vn, form, page, template, uncertain):
  dicform = get_dicform(page, template)

  gender = get_vn_gender(vn, form)
  if gender == "?":
    msg("Page %s %s: WARNING: Unable to determine gender: verbal noun %s, dictionary form %s"
        % (index, remove_diacritics(vn), vn, dicform))
    genderparam = ""
  else:
    genderparam = "|%s" % gender

  defparam = "|form=%s%s" % (form, uncertain and "|uncertain=yes" or "")
  create_inflection_entry(save, index, vn, None, dicform, None, "Noun",
    "verbal noun", "dictionary form", "ar-noun", genderparam,
    "ar-verbal noun of", defparam)

def create_verbal_nouns(save, startFrom, upTo):
  for page, index in blib.cat_articles("Arabic verbs", startFrom, upTo):
    for template in blib.parse(page).filter_templates():
      if template.name == "ar-conj":
        form = re.sub("-.*$", "", blib.getparam(template, "1"))
        vnvalue = blib.getparam(template, "vn")
        uncertain = False
        if vnvalue.endswith("?"):
          vnvalue = vnvalue[:-1]
          uncertain = True
        if not vnvalue:
          if form != "I":
            # Augmented verb. Fetch auto-generated verbal noun(s).
            vnvalue = get_part_prop(page, template, "ar-verb-part-all|vn")
          else:
            continue
        vns = re.split(u"[,،]", vnvalue)
        for vn in vns:
          create_verbal_noun(save, index, vn, form, page, template, uncertain)

def create_participle(save, index, part, page, template, actpass, apshort):
  dicform = get_dicform(page, template)

  # Retrieve form, eliminate any weakness value (e.g. "I" from "I-sound")
  form = re.sub("-.*$", "", blib.getparam(template, "1"))
  create_inflection_entry(save, index, part, None, dicform, None, "Participle",
    "%s participle" % actpass, "dictionary form",
    "ar-%s-participle" % apshort, "|" + form,
    "%s participle of" % actpass, "|lang=ar")

def create_participles(save, startFrom, upTo):
  for page, index in blib.cat_articles("Arabic verbs", startFrom, upTo):
    for template in blib.parse(page).filter_templates():
      if template.name == "ar-conj":
        passive = get_passive(page, template)
        if has_active_form(passive):
          apvalue = get_part_prop(page, template, "ar-verb-part-all|ap")
          if apvalue:
            aps = re.split(",", apvalue)
            for ap in aps:
              create_participle(save, index, ap, page, template, "active",
                  "act")
        if has_passive_form(passive, None):
          ppvalue = get_part_prop(page, template, "ar-verb-part-all|pp")
          if ppvalue:
            pps = re.split(",", ppvalue)
            for pp in pps:
              create_participle(save, index, pp, page, template, "passive",
                  "pass")

# List of all person/number/gender combinations, using the ID's in
# {{ar-verb-part-all|...}}
all_persons = [
    "1s", "2sm", "2sf", "3sm", "3sf",
    "2d", "3dm", "3df",
    "1p", "2pm", "2pf", "3pm", "3pf"
    ]
# Corresponding part of {{inflection of|...}} template, e.g. 3|m|s for 3sm
persons_infl_entry = dict([x,
  re.sub("([sdpmf])", r"|\1", re.sub("([sdp])([mf])", r"\2\1", x))]
  for x in all_persons)
# List of all tense/mood combinations, using the ID's in
# {{ar-verb-part-all|...}}
all_tenses = ["perf", "impf", "subj", "juss", "impr"]
# Corresponding part of {{inflection of|...}} template, with %s where
# "active" or "passive" goes
tenses_infl_entry = {
    "perf":"past|%s",
    "impf":"non-past|%s|indc",
    "subj":"non-past|%s|subj",
    "juss":"non-past|%s|jussive",
    "impr":"%s|impr" # FIXME, figure out what this really is
    }
all_voices = ["active", "passive"]
voices_infl_entry = {
    "active":"actv",
    "passive":"pasv"
    }

# Create a single verb part. SAVE, INDEX are as in create_inflection_entry().
# PAGE is the page of the lemma, and TEMPLATE is the {{ar-conj|...}}
# template indicating the lemma's conjugation. DICFORM is the vocalized form
# of the lemma, PASSIVE is the value of the 'passive' property of the lemma.
# VOICE is either "active" or "passive", and PERSON and TENSE
# indicate the particular person/number/gender/tense/mood combination, using
# the codes passed to {{ar-verb-part-all|...}}. We refuse to do combinations
# not compatible with the value of PASSIVE, and we refuse to do the
# dictionary form (3sm-perf, or 3sm-ps-perf for passive-only verbs).
# We assume that impossible parts (passive and non-2nd-person imperatives)
# have already been filtered.
def create_verb_part(save, index, page, template, dicform, passive,
    voice, person, tense):
  if voice == "active" and not has_active_form(passive):
    return
  if voice == "passive" and not has_passive_form(passive, person):
    return
  # Refuse to do the dictionary form.
  if person == "3sm" and tense == "perf" and (voice == "active" or
      voice == "passive" and not has_active_form(passive)):
    return
  infl_person = persons_infl_entry[person]
  infl_tense = tenses_infl_entry[tense] % voices_infl_entry[voice]
  partid = (voice == "active" and "%s-%s" % (person, tense) or
      "%s-ps-%s" % (person, tense))
  # Retrieve form, eliminate any weakness value (e.g. "I" from "I-sound")
  form = re.sub("-.*$", "", blib.getparam(template, "1"))
  value = get_part_prop(page, template, "ar-verb-part-all|%s" % partid)
  if value:
    parts = re.split(",", value)
    for part in parts:
      create_inflection_entry(save, index, part, None, dicform, None, "Verb",
        "verb part %s" % partid, "dictionary form",
        "ar-verb-form", "|" + form,
        "inflection of", "||lang=ar|%s|%s" % (infl_person, infl_tense))

# Parse a part spec, one or more parts separated by commas. Each part spec
# is either PERSON-TENSE (active), PERSON-ps-TENSE (passive) or
# PERSON-all-TENSE (both), where PERSON is either 'all' or one of the values
# of all_persons (actually specifies person, number and gender), and TENSE is
# either 'all', 'nonpast' (= 'impf', 'subj', 'juss') or one of the values of
# all_tenses. Return a list of all the actual parts required, where each list
# element is a list [VOICE, PERSON, TENSE] where VOICE is either "active" or
# "passive" and PERSON and TENSE are the same as above. Skip passive and
# non-2nd-person imperatives, even if explicitly specified.
def parse_part_spec(partspec):
  def check(variable, value, possible):
    if not value in possible:
      raise ValueError("Invalid value '%s' for %s, expected one of %s" % (
        value, variable, '/'.join(possible)))

  parts = []
  for part in re.split(",", partspec):
    if part == "all":
      part = "all-all-all"
    partparts = re.split("-", part)
    if len(partparts) == 2:
      person = partparts[0]
      tense = partparts[1]
      voice = "active"
    elif len(partparts) == 3:
      person = partparts[0]
      tense = partparts[2]
      if partparts[1] == "ps":
        voice = "passive"
      elif partparts[1] == "all":
        voice = "all"
      else:
        raise ValueError("Expected PERSON-TENSE or PERSON-VOICE-TENSE where VOICE is 'ps' or 'all', but found '%s'"
            % partparts[1])
    if person == "all":
      persons = all_persons
    else:
      check("person-number-gender", person, all_persons)
      persons = [person]
    if tense == "all":
      tenses = all_tenses
    elif tense == "nonpast":
      tenses = ["impf", "subj", "juss"]
    else:
      check("tense/mood", tense, all_tenses)
      tenses = [tense]
    if voice == "all":
      voices = all_voices
    else:
      assert(voice in all_voices)
      voices = [voice]

  msg("Doing the following verb parts:")
  for voice in voices:
    for person in persons:
      for tense in tenses:
        # Refuse to do passive and non-2nd-person imperatives.
        if tense == "impr" and (voice == "passive" or person[0] != "2"):
          continue
        msg("  %s %s %s" % (person, tense, voice))
        parts.append([voice, person, tense])
  return parts

# Create required verb parts for all verbs. PART specifies the part(s) to do.
# If "all", do all parts (other than 3sm-perf, the dictionary form);
# otherwise, only do the specified part(s).
# SAVE is as in create_inflection_entry(). STARTFROM and UPTO, if not None,
# delimit the range of pages to process (inclusive on both ends).
def create_verb_parts(save, startFrom, upTo, partspec):
  parts_desired = parse_part_spec(partspec)
  for page, index in blib.cat_articles("Arabic verbs", startFrom, upTo):
    for template in blib.parse(page).filter_templates():
      if template.name == "ar-conj":
        dicform = get_dicform(page, template)
        passive = get_passive(page, template)
        for voice, person, tense in parts_desired:
          create_verb_part(save, index, page, template, dicform, passive,
              voice, person, tense)

pa = blib.init_argparser("Create Arabic inflection entries")
pa.add_argument("-p", "--plural", action='store_true',
    help="Do plural inflections")
pa.add_argument("-f", "--feminine", action='store_true',
    help="Do feminine inflections")
pa.add_argument("--verbal-noun", action='store_true',
    help="Do verbal noun inflections")
pa.add_argument("--participle", action='store_true',
    help="Do participle inflections")
pa.add_argument("--non-past", action='store_true',
    help="""Do non-past dictionary-form inflections; equivalent to
'--verb-part 3sm-all-impf'.""")
pa.add_argument("--verb-part",
    help="""Do specified verb-part inflections, a comma-separated list.
Each element is compatible with the specifications used in {{ar-verb-part}}
with the addition of 'all' specs, i.e. either 'all' or PERSON-TENSE (active
voice), PERSON-ps-TENSE (passive voice) or PERSON-all-TENSE (both), where
PERSON (which actually specifies person, number and gender) is either 'all' or
one of the values '1s/2sm/2sf/3sm/3sf/2d/3dm/3df/1p/2pm/2pf/3pm/3pf' and TENSE
(which actually specifies tense and mood) is either 'all' or 'nonpast' or
one of the values 'perf/impf/subj/juss/impr' where perf = past, impf = non-past
indicative, impr = imperative, 'nonpast' = 'impf' and 'subj' and 'juss'.
The special case part spec 'all' is equivalent to 'all-all-all'. Silently
ignored are the following: the dictionary form (active 3sm-perf);
non-second-person or passive imperatives; active and/or passive inflections
if in disagreement with the 'passive' property of the lemma (i.e. passive=no
means no passive, passive=impers or passive=only-impers means passive only
in participles and the third singular masculine, and passive=only or
passive=only-impers means no active).""")

params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)

if params.plural:
  create_plurals(params.save, "Noun", "ar-noun", startFrom, upTo)
  create_plurals(params.save, "Adjective", "ar-adj", startFrom, upTo)
if params.feminine:
  #create_feminines(params.save, "Noun", "ar-noun", startFrom, upTo)
  create_feminines(params.save, "Adjective", "ar-adj", startFrom, upTo)
if params.verbal_noun:
  create_verbal_nouns(params.save, startFrom, upTo)
if params.participle:
  create_participles(params.save, startFrom, upTo)
if params.verb_part:
  create_verb_parts(params.save, startFrom, upTo, params.verb_part)
if params.non_past:
  create_verb_parts(params.save, startFrom, upTo, '3sm-all-impf')
