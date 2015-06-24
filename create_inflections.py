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
import codecs

import blib, pywikibot
from blib import msg, getparam
from arabiclib import *

site = pywikibot.Site()

verbose = True

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
# template, similar to INFLTEMP_PARAM. If ENTRYTEXT is given, this is the
# text to use for the entry, starting directly after the "==Etymology==" line,
# which is assumed to be necessary. If not given, this text is synthesized
# from the other parameters. GENDER is used for noun plurals.
def create_inflection_entry(save, index, inflection, infltr, lemma, lemmatr,
    pos, infltype, lemmatype, infltemp, infltemp_param, deftemp,
    deftemp_param, entrytext=None, gender=None):

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
      mymsg("WARNING: Strange diacritic at end of %s %s" % (wordtype, word))
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
  is_plural = infltype == "plural"
  is_feminine = infltype == "feminine"
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

  # Compare parameter PARAM (e.g. "1", "head2", etc.) of template TEMPLATE
  # with value VALUE. If REQUIRE_EXACT_MATCH, match must be exact (after
  # canonicalizing shadda); otherwise, match on non-vocalized text.
  def compare_param(template, param, value, require_exact_match=False):
    # In place of unknown we should put infltype or lemmatype but it
    # doesn't matter because of nowarn.
    paramval = getparam(template, param)
    paramval = maybe_remove_i3rab("unknown", paramval, nowarn=True,
        noremove=is_verb_part)
    if must_match_exactly or require_exact_match:
      return reorder_shadda(paramval) == reorder_shadda(value)
    else:
      return remove_diacritics(paramval) == remove_diacritics(value)

  # First, for each template, return a tuple of
  # (template, param, matches), where MATCHES is true if any head
  # matches FORM and PARAM is the (first) matching head param.
  def template_head_match_info(template, form,
      require_exact_match=False):
    # Look at all heads
    if compare_param(template, "1", form, require_exact_match):
      return (template, "1", True)
    i = 2
    while True:
      param = "head" + str(i)
      if not getparam(template, param):
        return (template, None, False)
      if compare_param(template, param, form, require_exact_match):
        return (template, param, True)
      i += 1
  # True if any head in the template matches FORM.
  def template_head_matches(template, form,
      require_exact_match=False):
    return template_head_match_info(template, form,
        require_exact_match)[2]

  # Prepare parts of new entry to insert
  if entrytext:
    entrytextl4 = re.sub("^==(.*?)==$", r"===\1===", entrytext, 0, re.M)
    newsection = "==Arabic==\n\n===Etymology===\n" + entrytext
  else:
    # Synthesize new entry. Some of the parts here besides 'entrytext',
    # 'entrytextl4' and 'newsection' are used down below when creating
    # verb parts and participles; these parts don't exist when 'entrytext'
    # was passed in, but that isn't a problem because it isn't passed in
    # when creating verb parts or participles.
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
    entrytext = "\n" + newpos
    entrytextl4 = "\n" + newposl4
    newsection = "==Arabic==\n" + entrytext

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
        pagemsg("WARNING: Can't find language name in text: [[%s]]" % (sections[i]))
      elif m.group(1) == "Arabic":
        # Extract off trailing separator
        mm = re.match(r"^(.*?\n)(\n*--+\n*)$", sections[i], re.S)
        if mm:
          sections[i:i+1] = [mm.group(1), mm.group(2)]
        elif i < len(sections) - 1:
          pagemsg("WARNING: Arabic language section %s is non-final and missing trailing separator" % i)

        # If verb part, correct mistaken indent from a previous run,
        # where level-3 entries were inserted instead of level 4.
        if is_verb_part and "\n===Etymology 1===\n" in sections[i]:
          oldsectionsi = sections[i]
          sections[i] = re.sub("\n===Verb===\n", "\n====Verb====\n",
              sections[i])
          if oldsectionsi != sections[i]:
            notes.append("corrected verb-part indent level")

        subsections = re.split("(^===+[^=\n]+===+\n)", sections[i], 0, re.M)

        # If verbal noun, convert existing ===Verbal noun=== headers into
        # ===Noun===.
        if is_vn:
          for j in xrange(len(subsections)):
            if j > 0 and (j % 2) == 0:
              if re.match("^===+Verbal noun===+", subsections[j - 1]):
                subsections[j - 1] = re.sub("(===+)Verbal noun(===+)",
                    r"\1Noun\2", subsections[j - 1])
                pagemsg("Converting 'Verbal noun' section header to 'Noun'")
                notes.append("converted 'Verbal noun' section header to 'Noun'")
              sections[i] = ''.join(subsections)

        # If verbal noun or participle, check for an existing entry matching
        # the headword and defn. If so, don't do anything. We need to do this
        # because otherwise we might have a situation with two entries for a
        # given noun (or participle) and the second one having an appropriate
        # defn, and when we encounter the first one we see it doesn't have a
        # defn and go ahead and insert it, which we don't want to do.
        #
        # Also count number of entries for given noun (or participle). If
        # none have a defn and there's more than one, we don't know which one
        # to insert the defn into, so issue a warning and punt.
        if vn_or_participle:
          num_matching_headword_templates = 0
          found_matching_headword_and_defn_templates = False
          for j in xrange(len(subsections)):
            if j > 0 and (j % 2) == 0:
              if re.match("^===+%s===+" % pos, subsections[j - 1]):
                parsed = blib.parse_text(subsections[j])

                # While we're at it, check for verbal noun defn templates
                # missing form=
                if is_vn:
                  for t in parsed.filter_templates():
                    if t.name == deftemp and not getparam(t, "form"):
                      pagemsg("WARNING: Verbal noun template %s missing form= param" % unicode(t))

                matching_headword_templates = [
                    t for t in parsed.filter_templates()
                    if t.name == infltemp and
                    template_head_matches(t, inflection)]
                matching_defn_templates = [
                    t for t in parsed.filter_templates()
                    if t.name == deftemp and compare_param(t, "1", lemma,
                      require_exact_match=True)]
                num_matching_headword_templates += len(
                    matching_headword_templates)
                if matching_headword_templates and matching_defn_templates:
                  found_matching_headword_and_defn_templates = True
          if found_matching_headword_and_defn_templates:
            pagemsg("Exists and has Arabic section and found %s already in it"
                % infltype)
            break
          if num_matching_headword_templates > 1:
            pagemsg("WARNING: Found multiple matching subsections, don't know which one to insert %s defn into" % infltype)
            break

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
                      getparam(t, "1")[0:-1])
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

            def check_maybe_remove_i3rab(template, param, wordtype):
              # Check for i3rab in existing lemma or infl and remove it if so
              existing = getparam(template, param)
              existing_no_i3rab = maybe_remove_i3rab(wordtype, existing,
                  noremove=is_verb_part or wordtype == "dictionary form")
              if reorder_shadda(existing) != reorder_shadda(existing_no_i3rab):
                notes.append("removed %s i3rab" % wordtype)
                template.add(param, existing_no_i3rab)
                trparam = "tr" if param == "1" else param.replace("head", "tr")
                existing_tr = getparam(template, trparam)
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

            head_matches_tuples = [template_head_match_info(t, inflection)
                for t in parsed.filter_templates()]
            # Now get a list of (TEMPLATE, PARAM) for all matching templates,
            # where PARAM is the matching head param, as above.
            infl_headword_templates = (
                [(t, param) for t, param, matches in head_matches_tuples
                 if t.name == infltemp and matches
                 and (not is_verb_part or compare_param(t, "2", verb_part_form))])

            # Special-case handling for actual noun plurals. We expect an
            # ar-noun but if we encounter an ar-coll-noun with the plural as
            # the (collective) head and the singular as the singulative, we
            # output a message and skip so we don't end up creating a
            # duplicate entry.
            if is_plural_noun:
              headword_collective_templates = [t for t in parsed.filter_templates()
                  if t.name == "ar-coll-noun" and template_head_matches(t, inflection)
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

            # Get list of definition templates that match. We may or may
            # not be matching in a way that ignores vowels (see
            # must_match_exactly above).
            approx_defn_templates = [t for t in parsed.filter_templates()
                if t.name == deftemp and (is_verb_part or
                compare_param(t, "1", lemma))]
            # Get list of definition templates that match, checking vowels.
            defn_templates = [t for t in parsed.filter_templates()
                if t.name == deftemp and (is_verb_part or
                compare_param(t, "1", lemma, require_exact_match=True))]

            # Check the existing gender of the given headword template
            # (assumed to be "p" if non-existent) and attempt to make sure
            # it matches the given gender or can be compatibly modified to
            # the new gender. Return False if genders incompatible (and
            # issue a warning if WARNING_ON_FALSE), else modify existing
            # gender if needed. (E.g. existing "p" matches new "m-p" and will
            # be modified; existing "m-p" matches new "p" and will be left
            # alone; existing "p-pe" matches new "m-p" and will be modified
            # to "m-p-pe". Similar checks are done for the second gender.
            # We don't currently handle the situation where e.g. the existing
            # gender is both "m-p" and "f-p" and the new gender is "f-p" and
            # "m-p" in reverse order. To handle that, we would need to
            # sort both sets of genders by some criterion.)
            def check_fix_gender(headword_template, gender, warning_on_false):
              def gender_compatible(existing, new):
                if not re.match(r"\bp\b", existing):
                  pagemsg("WARNING: Something wrong, existing gender %s does not have 'p' in it" % existing)
                  return False
                if not re.match(r"\bp\b", new):
                  pagemsg("WARNING: Something wrong, new gender %s does not have 'p' in it" % new)
                  return False
                m = re.match(r"\b([mf])\b", existing)
                existing_mf = m and m.group(1)
                m = re.match(r"\b([mf])\b", new)
                new_mf = m and m.group(1)
                if existing_mf and new_mf and existing_mf != new_mf:
                  if warning_on_false:
                    pagemsg("WARNING: Can't modify mf gender from %s to %s" % (
                        existing, new))
                    return False
                new_mf = new_mf or existing_mf
                m = re.match(r"\b(pe|np)\b", existing)
                existing_pe = m and m.group(1)
                m = re.match(r"\b(pe|np)\b", new)
                new_pe = m and m.group(1)
                if existing_pe and new_pe and existing_pe != new_pe:
                  if warning_on_false:
                    pagemsg("WARNING: Can't modify personalness from %s to %s" % (
                        existing, new))
                    return False
                new_pe = new_pe or existing_pe
                return '-'.join([x for x in [new_mf, "p", new_pe]])
              existing_gender = getparam(headword_template, "2")
              existing_gender2 = getparam(headword_template, "g2")
              assert(len(gender) == 1 or len(gender) == 2)
              new_gender = gender_compatible(existing_gender or "p", gender[0])
              if not new_gender:
                return False
              new_gender2 = len(gender) == 2 and gender[1] or ""
              if existing_gender2 or new_gender2:
                new_gender2 = gender_compatible(existing_gender2 or "p",
                    new_gender2 or "p")
                if not new_gender2:
                  return False
              if new_gender != existing_gender:
                pagemsg("Modifying first gender from '%s' to '%s'" % (
                  existing_gender, new_gender))
                headword_template.add("2", new_gender)
              if (new_gender2 != existing_gender2 and new_gender2 and
                  new_gender2 != "p"):
                pagemsg("Modifying second gender from '%s' to '%s'" % (
                  existing_gender2, new_gender2))
                headword_template.add("g2", new_gender2)
              return True

            if (infl_headword_templates and len(approx_defn_templates) == 1
                and not must_match_exactly):

              #### Code for plurals and feminines, which may be partly
              #### vocalized and may have existing i3rab.

              infl_headword_template, infl_headword_matching_param = \
                  infl_headword_templates[0]
              defn_template = approx_defn_templates[0]
                
              # Check for i3rab in existing infl and remove it if so.
              existing_infl = \
                  check_maybe_remove_i3rab(infl_headword_template,
                      infl_headword_matching_param, infltype)

              # Check for i3rab in existing lemma and remove it if so
              existing_lemma = \
                  check_maybe_remove_i3rab(defn_template, "1", lemmatype)

              # Check that new inflection is the same as or longer then
              # existing inflection, and same for the lemma. In such a
              # case we assume that the existing lemma/inflection represents
              # a possibly partly vocalized version of new lemma/inflection.
              if ((len(inflection) > len(existing_infl) or
                   inflection == existing_infl) and
                  (len(lemma) > len(existing_lemma) or
                   lemma == existing_lemma)):
                if inflection != existing_infl or lemma != existing_lemma:
                  pagemsg("Approximate match to partly vocalized: Exists and has Arabic section and found %s already in it"
                      % (infltype))
                else:
                  pagemsg("Exists and has Arabic section and found %s already in it"
                      % (infltype))

                # First, if we're a plural noun, update gender and make sure
                # we can do it
                if (not is_plural_noun or
                    check_fix_gender(infl_headword_template, gender, True)):
                  # Replace existing infl with new one
                  if len(inflection) > len(existing_infl):
                    pagemsg("Updating existing %s %s with %s" %
                        (infltemp, existing_infl, inflection))
                    infl_headword_template.add(infl_headword_matching_param,
                      inflection)
                    if infltr:
                      trparam = "tr" if infl_headword_matching_param == "1" \
                          else infl_headword_matching_param.replace("head", "tr")
                      infl_headword_template.add(trparam, infltr)

                  # Replace existing lemma with new one
                  if len(lemma) > len(existing_lemma):
                    pagemsg("Updating existing '%s' %s with %s" %
                        (deftemp, existing_lemma, lemma))
                    defn_template.add("1", lemma)
                    if lemmatr:
                      defn_template.add("tr", lemmatr)

                  subsections[j] = unicode(parsed)
                  sections[i] = ''.join(subsections)
                  comment = "Update Arabic with better %svocalized versions: %s %s, %s %s, pos=%s" % (
                      is_plural_noun and "gender and " or "",
                      infltype, inflection, lemmatype, lemma, pos)
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

              infl_headword_template, infl_headword_matching_param = \
                  infl_headword_templates[0]

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

              # Else, not verb form. If plural noun, set the gender
              # appropriately.
              elif is_plural_noun:
                check_fix_gender(infl_headword_template, gender, True)
                subsections[j] = unicode(parsed)
                sections[i] = ''.join(subsections)
                comment = "Update gender of plural noun to %s: %s %s, %s %s" % (
                    gender, infltype, inflection, lemmatype, lemma)
                break

              # Else, not verb form and not plural noun. Already have
              # defn so do nothing.
              else:
                break

            # At this point, didn't find either headword or definitional
            # template, or both.
            elif vn_or_participle:
              # Insert {{ar-verbal noun of}} (or equivalent for participles).
              # Return comment (can't set it inside of fn).
              def insert_vn_defn():
                subsections[j] = unicode(parsed)
                # If there's already a defn line present, insert after
                # any such defn lines. Else, insert at beginning.
                if re.search(r"^# \{\{%s\|" % deftemp, subsections[j], re.M):
                  if not subsections[j].endswith("\n"):
                    subsections[j] += "\n"
                  subsections[j] = re.sub(r"(^(# \{\{%s\|.*\n)+)" % deftemp,
                      r"\1# %s\n" % new_defn_template, subsections[j],
                      1, re.M)
                else:
                  subsections[j] = re.sub(r"^#", "# %s\n#" % new_defn_template,
                      subsections[j], 1, re.M)
                sections[i] = ''.join(subsections)
                pagemsg("Insert existing defn with {{%s}} at beginning after any existing such defns" % (
                    deftemp))
                return "Insert existing defn with {{%s}} at beginning after any existing such defns: %s %s, %s %s" % (
                    deftemp, infltype, inflection, lemmatype, lemma)

              # If verb or participle, see if we found inflection headword
              # template at least. If so, add definition to beginning as
              # {{ar-verbal noun of}} (or equivalent for participles).
              if infl_headword_templates:
                infl_headword_template, infl_headword_matching_param = \
                    infl_headword_templates[0]

                # Check for i3rab in existing infl and remove it if so
                check_maybe_remove_i3rab(infl_headword_template,
                    infl_headword_matching_param, infltype)

                # Don't insert defn when there are multiple heads because
                # we don't know that all heads are actually legit verbal noun
                # (or participle) alternants.
                if getparam(infl_headword_template, "head2"):
                  pagemsg("Inflection template has multiple heads, not inserting %s defn into it" % (infltype))
                else:
                  # Now actually add {{ar-verbal noun of}} (or equivalent
                  # for participles).
                  comment = insert_vn_defn()
                  break

              elif is_participle:
                # Couldn't find headword template; if we're a participle,
                # see if there's a generic noun or adjective template
                # with the same head.
                for other_template in ["ar-noun", "ar-adj", "ar-adj-sound",
                    "ar-adj-in", "ar-adj-an"]:
                  other_headword_templates = [
                      t for t in parsed.filter_templates()
                      if t.name == other_template and template_head_matches(t, inflection)]
                  if other_headword_templates:
                      pagemsg("WARNING: Found %s matching %s" %
                          (other_template, infltype))
                      # FIXME: Should we break here? Should we insert
                      # a participle defn?

            # At this point, didn't find either headword or definitional
            # template, or both, and not vn or participle. If we found
            # headword template, insert new definition in same section.
            elif infl_headword_templates:
              # Previously, when looking for a matching headword template,
              # we may not have required the vowels to match exactly
              # (e.g. when creating plurals). But now we want to make sure
              # they do, or we will put the new definition under a wrong
              # headword.
              infl_headword_template, infl_headword_matching_param = \
                  infl_headword_templates[0]
              if compare_param(infl_headword_template, infl_headword_matching_param, inflection, require_exact_match=True):
                # Also make sure manual translit matches
                trparam = "tr" if infl_headword_matching_param == "1" \
                    else infl_headword_matching_param.replace("head", "tr")
                existing_tr = getparam(infl_headword_template, trparam)
                # infltr may be None and existing_tr may be "", but
                # they should match
                if (infltr or None) == (existing_tr or None):
                  # If plural noun, also make sure we can set the gender
                  # appropriately. If not, we will end up adding an entirely
                  # new entry.
                  if (not is_plural_noun or
                      check_fix_gender(infl_headword_template, gender, False)):
                    subsections[j] = unicode(parsed)
                    if subsections[j][-1] != '\n':
                      subsections[j] += '\n'
                    subsections[j] = re.sub(r"^(.*\n#[^\n]*\n)",
                        r"\1# %s\n" % new_defn_template, subsections[j], 1,
                        re.S)
                    sections[i] = ''.join(subsections)
                    pagemsg("Adding new definitional template to existing defn for pos = %s" % (pos))
                    comment = "Add new definitional template to existing defn: %s %s, %s %s, pos=%s" % (
                        infltype, inflection, lemmatype, lemma, pos)
                    break

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
                        t.name == "ar-verb" and re.sub("-.*$", "", getparam(t, "1")) == verb_part_form and remove_diacritics(lemma) in [remove_diacritics(dicform) for dicform in get_dicform_all(page, t)]):
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
                    if (t.name in ["ar-noun", "ar-adj", "ar-adj-sound",
                      "ar-adj-in", "ar-adj-an"] and
                        template_head_matches(t, inflection) and insert_at is None):
                      insert_at = j - 1

            if insert_at is not None:
              pagemsg("Found section to insert participle before: [[%s]]" %
                  subsections[insert_at + 1])

              comment = "Insert entry for %s %s of %s before section for same lemma" % (
                infltype, inflection, lemma)
              if insert_at > 0:
                subsections[insert_at - 1] = ensure_two_trailing_nl(
                    subsections[insert_at - 1])
              # Determine indent level
              m = re.match("^(==+)", subsections[insert_at])
              indentlevel = len(m.group(1))
              if indentlevel == 3:
                subsections[insert_at:insert_at] = [newpos + "\n"]
              else:
                assert(indentlevel == 4)
                subsections[insert_at:insert_at] = [newposl4 + "\n"]
              sections[i] = ''.join(subsections)
              break

          # If plural or feminine, try to find an existing noun or adjective
          # form with the same headword to insert after. Insert after the
          # last such one.
          if is_plural or is_feminine:
            insert_at = None
            for j in xrange(len(subsections)):
              if j > 0 and (j % 2) == 0:
                if re.match("^===+(Noun|Adjective)===+", subsections[j - 1]):
                  parsed = blib.parse_text(subsections[j])
                  for t in parsed.filter_templates():
                    if (t.name in ["ar-noun-pl", "ar-adj-pl", "ar-noun-fem",
                        "ar-adj-fem", "ar-coll-noun"] and
                        template_head_matches(t, inflection,
                          require_exact_match=True)):
                      insert_at = j + 1
            if insert_at:
              pagemsg("Found section to insert %s after: [[%s]]" %
                  (infltype, subsections[insert_at - 1]))

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

              pagemsg("Inserting after noun/adjective section for same inflection")
              comment = "Insert entry for %s %s of %s after noun/adjective section for same inflection" % (
                infltype, inflection, lemma)
              subsections[insert_at - 1] = ensure_two_trailing_nl(
                  subsections[insert_at - 1])
              if indentlevel == 3:
                subsections[insert_at:insert_at] = [newpos + "\n"]
              else:
                assert(indentlevel == 4)
                subsections[insert_at:insert_at] = [newposl4 + "\n"]
              sections[i] = ''.join(subsections)
              break

          # At this point, couldn't find an existing section to insert
          # next to.
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
            sections[i] += "===Etymology %s===\n" % j + entrytextl4
          else:
            pagemsg("Wrapping existing text in \"Etymology 1\" and adding \"Etymology 2\"")
            comment = "Wrap existing Arabic section in Etymology 1, append entry (Etymology 2) for %s %s of %s, pos=%s" % (
                infltype, inflection, lemma, pos)
            # Wrap existing text in "Etymology 1" and increase the indent level
            # by one of all headers
            sections[i] = re.sub("^\n*==Arabic==\n+", "", sections[i])
            # Peel off stuff we expect before the first header; it will be
            # put back later
            wikilink_re = r"^((\{\{wikipedia\|.*?\}\}\n|\[\[File:.*?\]\]\n)+)\n*"
            mmm = re.match(wikilink_re, sections[i])
            wikilink = mmm.group(1) if mmm else ""
            if mmm:
              sections[i] = re.sub(wikilink_re, "", sections[i])
            # Check for any other stuff before the first header
            if not re.match("^=", sections[i]):
              mmm = re.match("^(.*?\n)=", sections[i], re.S)
              if not mmm:
                pagemsg("WARNING: Strange section lacking headers: [[%s]]" %
                    sections[i])
              else:
                pagemsg("WARNING: Stuff before first header: [[%s]]" %
                    mmm.group(1))
            # Stuff like "===Alternative forms===" that goes before the
            # etymology section should be moved after.
            sections[i] = re.sub(r"^(.*\n)(===Etymology===\n([^=\n]*\n)*)",
                r"\2\1", sections[i], 0, re.S)
            sections[i] = re.sub("^===Etymology===\n", "", sections[i])
            sections[i] = ("==Arabic==\n" + wikilink + "\n===Etymology 1===\n" +
                ("\n" if sections[i].startswith("==") else "") +
                ensure_two_trailing_nl(re.sub("^==(.*?)==$", r"===\1===",
                  sections[i], 0, re.M)) +
                "===Etymology 2===\n" + entrytextl4)
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

def create_noun_plural(save, index, inflection, infltr, lemma, lemmatr,
    template, pos):
  pagename = remove_diacritics(inflection)
  def pagemsg(text, simple = False):
    if simple:
      msg("Page %s %s: %s" % (index, pagename, text))
    else:
      msg("Page %s %s: %s: plural %s%s, singular %s%s" % (index, pagename, text,
        inflection, " (%s)" % infltr if infltr else "",
        lemma, " (%s)" % lemmatr if lemmatr else ""))
  def pluralize_gender(g):
    plural_gender = {
        "m":"m-p", "m-pe":"m-p-pe", "m-np":"m-p-np",
        "f":"f-p", "f-pe":"f-p-pe", "f-np":"f-p-np",
        "pe":"p-pe", "np":"p-np"
    }
    if re.match(g, r"\bp\b"):
      pagemsg("WARNING: Trying to pluralize already plural gender %s" % g)
      return g
    if g in plural_gender:
      return plural_gender[g]
    pagemsg("WARNING: Trying to pluralize unrecognizable gender %s" % g)
    return g
  # Figure out plural gender
  if template.name == "ar-noun-nisba":
    gender = ["m-p-pe"]
  else:
    # If plural ends in -ūn we are almost certainly dealing with a masculine
    # personal noun, unless it's a short plural like قُرُون plural
    # of وَرْن "horn" or سِنُون plural of سَنَة "hour".
    singgender = getparam(template, "2")
    inflection = reorder_shadda(inflection)
    if inflection.endswith(UUN) and len(inflection) <= 6:
      pagemsg(u"Short -ūn plural, not treating as personal plural")
    elif inflection.endswith(UUN) or inflection.endswith(UUNA):
      pagemsg(u"Long -ūn plural, treating as personal")
      if singgender in ["", "m", "m-pe"]:
        singgender = "m-pe"
      else:
        pagemsg(u"WARNING: Long -ūn plural but strange gender %s" % singgender)
    if not singgender:
      gender = ["p"]
    else:
      gender = [pluralize_gender(singgender)]
      singgender2 = getparam(template, "g2")
      if singgender2:
          gender.append(pluralize_gender(singgender2))
  if not gender:
    genderparam = ""
  elif len(gender) == 1:
    genderparam = "|%s" % gender[0]
  else:
    assert(len(gender) == 2)
    genderparam = "|%s|g2=%s" % (gender[0], gender[1])

  create_inflection_entry(save, index, inflection, infltr, lemma, lemmatr, pos,
      "plural", "singular", "ar-noun-pl", genderparam, "plural of", "|lang=ar",
      gender=gender)

def create_adj_plural(save, index, inflection, infltr, lemma, lemmatr,
    template, pos):
  create_inflection_entry(save, index, inflection, infltr, lemma, lemmatr, pos,
      "plural", "singular", "ar-adj-pl", "", "masculine plural of", "|lang=ar")

def create_noun_feminine(save, index, inflection, infltr, lemma, lemmatr,
    template, pos):
  create_inflection_entry(save, index, inflection, infltr, lemma, lemmatr, pos,
      "feminine", "masculine", None, # FIXME
      "", "feminine of", "|lang=ar")

def create_adj_feminine(save, index, inflection, infltr, lemma, lemmatr,
    template, pos):
  create_inflection_entry(save, index, inflection, infltr, lemma, lemmatr, pos,
      "feminine", "masculine", "ar-adj-fem", "", "feminine of", "|lang=ar")

# Create inflection entries for POS (the part of speech, which should be
# capitalized, e.g "Noun") by looking for inflections in the parameter
# PARAM (e.g. "pl") of templates named TEMPNAME (e.g. "ar-noun"). Entries
# created are limited by STARTFROM and UPTO (which are typically numbers
# but may be strings, and are the same as the START and END parameters
# passed on the command line), and only saved if SAVE is true (which is
# specified by --save on the command line). CREATEFN is the actual function
# called to the creation, and is passed seven parameters; see
# 'create_noun_plural' for an example. INFLECTFN is used to create the
# actual inflected form given the form specified in the template; the default
# is to use the template form unmodified. This function is always
# called even if no inflected form is found, and hence can be used in cases
# where the inflection is auto-generated by the template (e.g. in 'ar-nisba').
def create_inflection_entries(save, pos, tempname, param, startFrom, upTo,
    createfn, inflectfn=None):
  if not inflectfn:
    inflectfn = default_inflection
  if type(tempname) is not list:
    tempname = [tempname]
  # FIXME!! If there are multiple heads, we should consider iterating over
  # them and creating plural entries for each, esp. if there is only one
  # plural. When multiple heads and multiple plurals, unclear what to do.
  # Need to think through this.
  for cat in [u"Arabic %ss" % pos.lower()]:
    for page, index in blib.cat_articles(cat, startFrom, upTo):
      for template in blib.parse(page).filter_templates():
        if template.name in tempname:
          lemma = getparam(template, "1")
          lemmatr = getparam(template, "tr")
          # Handle blank head; use page title
          if lemma == "":
            lemma = page.title()
            msg("Page %s: blank head in template %s (tr=%s)" % (
              lemma, template.name, lemmatr))
          infl = getparam(template, param)
          infltr = getparam(template, param + "tr")
          infl, infltr = inflectfn(infl, infltr, lemma, lemmatr,
              template, param)
          if infl:
            createfn(save, index, infl, infltr, lemma, lemmatr, template, pos)
          i = 2
          while infl:
            infl = getparam(template, param + str(i))
            infltr = getparam(template, param + str(i) + "tr")
            otherhead = getparam(template, "head" + str(i))
            otherheadtr = getparam(template, "tr" + str(i))
            if otherhead:
              infl, infltr = inflectfn(infl, infltr, otherhead, otherheadtr,
                  template, param + str(i))
            else:
              infl, infltr = inflectfn(infl, infltr, lemma, lemmatr,
                  template, param + str(i))
            if infl:
              if otherhead:
                msg("Page %s: Using head%s %s (tr=%s) as lemma for %s (tr=%s)" % (
                  lemma, i, otherhead, otherheadtr, infl, infltr))
                createfn(save, index, infl, infltr, otherhead, otherheadtr,
                    template, pos)
              else:
                createfn(save, index, infl, infltr, lemma, lemmatr,
                    template, pos)
            i += 1

# Inflection function when we default pl= to the sound masculine plural.
# A value of + also indicates the sound masculine plural in any inflection
# param.
def sound_pl_inflection(infl, infltr, lemma, lemmatr, template, param):
  if infl == "+" or (not infl and param == "pl"):
    return (lemma + UUN, lemmatr and lemmatr + u"ūn" or "")
  return (infl, infltr)

# Inflection function for -in plurals when a value of + indicates the sound
# masculine plural.
def in_pl_inflection(infl, infltr, lemma, lemmatr, template, param):
  if infl == "+":
    lemma = reorder_shadda(lemma)
    if lemma.endswith(IN):
      lemma = re.sub(IN + "$", "", lemma)
      lemmatr = re.sub("in$", "", lemmatr)
    return (lemma + UUN, lemmatr and lemmatr + u"ūn" or "")
  return (infl, infltr)

# Inflection function for -an plurals when we default pl= to the sound
# masculine -awn plural. A value of + also indicates the sound masculine
# -awn plural in any inflection param.
def an_pl_inflection(infl, infltr, lemma, lemmatr, template, param):
  if infl == "+" or (not infl and param == "pl"):
    lemma = reorder_shadda(lemma)
    if lemma.endswith(AN + AMAQ):
      lemma = re.sub(AN + AMAQ + "$", "", lemma)
      lemmatr = re.sub("an$", "", lemmatr)
    return (lemma + AWN, lemmatr and lemmatr + u"awn" or "")
  return (infl, infltr)

def pl_inflection(infl, infltr, lemma, lemmatr, template, param):
  if template.name in ["ar-noun-nisba", "ar-nisba", "ar-adj-sound"]:
    return sound_pl_inflection(infl, infltr, lemma, lemmatr, template, param)
  elif template.name == "ar-adj-in":
    return in_pl_inflection(infl, infltr, lemma, lemmatr, template, param)
  elif template.name == "ar-adj-an":
    return an_pl_inflection(infl, infltr, lemma, lemmatr, template, param)
  else:
    return (infl, infltr)

# Inflection function when we default f= to the regular feminine for
# certain templates. A value of + also indicates the feminine in any
# inflection param for these templates. We also handle -an and -in
# lemmas here.
def fem_inflection(infl, infltr, lemma, lemmatr, template, param):
  if template.name in ["ar-noun-nisba", "ar-nisba", "ar-adj-sound",
      "ar-adj-in", "ar-adj-an"]:
    if infl == "+" or (not infl and param == "f"):
      lemma = reorder_shadda(lemma)
      if lemma.endswith(AN + AMAQ):
        lemma = re.sub(AN + AMAQ + "$", "", lemma)
        lemmatr = re.sub("an$", "", lemmatr)
        return (lemma + AAH, lemmatr and lemmatr + u"āh" or "")
      if lemma.endswith(IN):
        lemma = re.sub(IN + "$", "", lemma)
        lemmatr = re.sub("in$", "", lemmatr)
        return (lemma + IYAH, lemmatr and lemmatr + u"iya" or "")
      return (lemma + AH, lemmatr and lemmatr + u"a" or "")
    return (infl, infltr)
  else:
    return (infl, infltr)

def create_plurals(save, pos, tempname, startFrom, upTo):
  return create_inflection_entries(save, pos, tempname, "pl", startFrom, upTo,
      create_noun_plural if pos == "Noun" else create_adj_plural,
      pl_inflection)

def create_feminines(save, pos, tempname, startFrom, upTo):
  return create_inflection_entries(save, pos, tempname, "f", startFrom, upTo,
      create_noun_feminine if pos == "Noun" else create_adj_feminine,
      fem_inflection)

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

#def get_dicform(page, template):
#  return get_part_prop(page, template, "ar-past3sm")

def get_dicform_all(page, template):
  return get_part_prop(page, template, "ar-past3sm-all").split(",")

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
  for dicform in get_dicform_all(page, template):

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
        form = re.sub("-.*$", "", getparam(template, "1"))
        vnvalue = getparam(template, "vn")
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
  for dicform in get_dicform_all(page, template):

    # Retrieve form, eliminate any weakness value (e.g. "I" from "I-sound")
    form = re.sub("-.*$", "", getparam(template, "1"))
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
  form = re.sub("-.*$", "", getparam(template, "1"))
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
        passive = get_passive(page, template)
        for dicform in get_dicform_all(page, template):
          for voice, person, tense in parts_desired:
            create_verb_part(save, index, page, template, dicform, passive,
                voice, person, tense)

def add_bracketing(defn):
  return " ".join(["[[%s]]" % word for word in defn.split(" ")])

def parse_elative_defn(spec):
  m = re.match(ur"(.*?) ([\u0600-\u07FF]+)(?: .*?)? from (.*?) from (.*?)(?: ref (.*?))?$", spec)
  if not m:
    msg("Unable to match spec: %s" % spec)
  else:
    defnstext, elative, arpositivetext, roottext, reftext = m.groups()
    defns = []
    for defn in defnstext.split(" / "):
      m = re.match(r"\((.*)\)$", defn)
      if m:
        defns.append(m.group(1))
      else:
        synonyms = []
        for synonym in defn.split(", "):
          m = re.match(r"(.*) \[\]$", synonym)
          if m:
            synonyms.append([add_bracketing(m.group(1)), None, None])
            continue
          m = re.match(r"(.*) \[(.*); (.*)\]$", synonym)
          if m:
            synonyms.append([add_bracketing(m.group(1)),
                add_bracketing(m.group(2)),
                add_bracketing(m.group(3))])
            continue
          m = re.match(r"(.*) \[(.*)\]$", synonym)
          if m:
            if not re.match(".*er$", m.group(2)):
              msg("Synonym comparative does not end in -er: %s" % m.group(2))
            else:
              synonyms.append([add_bracketing(m.group(1)),
                  add_bracketing(m.group(2)),
                  add_bracketing(re.sub("er$", "est", m.group(2)))])
            continue
          synonym = add_bracketing(synonym)
          synonyms.append([synonym, "more " + synonym, "most " + synonym])
        defns.append(synonyms)
    arpositives = arpositivetext.split(" and ")
    roots = roottext.split(" and ")
    refs = reftext and reftext.split(" and ") or []
    # msg("Found entry: %s" % spec)
    # msg("  elative: %s" % elative)
    # msg("  arpositive: %s" % arpositives)
    # msg("  roots: %s" % roots)
    # msg("  defns: %s" % defns)
    # msg("  refs: %s" % refs)

    # Create the etymology line
    etymlinedefns = []
    for defn in defns:
      if type(defn) is not list: # literal text in parens
        continue
      etymlinedefns.append(", ".join([synonym[0] for synonym in defn]))
    etymlinedefntext = "; ".join(etymlinedefns)
    etymlinepos = "{{m|ar|%s||%s}}" % (arpositives[0], etymlinedefntext)
    if len(arpositives) > 1:
      etymlinepos += " and " + " and ".join(["{{m|ar|%s||(same)}}" % arpositive for arpositive in arpositives[1:]])
    etymlineroottext = " and ".join(["{{ar-root|%s}}" % root for root in roots])
    if len(roots) > 1:
      etymlineroottext = "roots " + etymlineroottext
    else:
      etymlineroottext = "root " + etymlineroottext
    etymline = "{{ar-elative}} of %s, from the %s." % (
        etymlinepos, etymlineroottext)

    # Create the "elative of" line
    elative_of_line = "# " + ", ".join([
      "{{elative of|%s|lang=ar}}" % pos for pos in arpositives]) + ":"

    # Create the definition lines
    defn_lines = []
    for defn in defns:
      if type(defn) is not list: # literal text in parens
        defn_lines.append("## %s" % defn)
      else:
        comparatives = [synonym[1] for synonym in defn if synonym[1]]
        superlatives = [synonym[2] for synonym in defn if synonym[2]]
        defn_lines.append("## %s; %s" % (", ".join(comparatives), ", ".join(superlatives)))

    # Create the references, if any
    if not refs:
      reftext = ""
    else:
      ref_lines = []
      for ref in refs:
        if "|" in ref:
          ref_lines.append("* {{R:ar:%s}}" % ref)
        else:
          if ref == "Steingass" or ref == "GT" or ref == "Almaany":
            ref_root = remove_diacritics(elative)
          else:
            ref_root = roots[0].replace(" ", "")
            if ref_root[-1] == ref_root[-2]:
              ref_root = ref_root[0:-1]
            elif ref_root[-1] == u'ي':
              ref_root = ref_root[0:-1] + u'ى'
            elif ref_root[-1] == u'ء':
              ref_root = ref_root[0:-1] + u'أ'
          ref_lines.append("* {{R:ar:%s|%s}}" % (ref, ref_root))
      reftext = "\n\n====References====\n" + "\n".join(ref_lines)

    # Create the definition text
    defn_text = """%s

===Adjective===
{{ar-adj|%s}}

%s
%s

====Declension====
{{ar-decl-adj|%s}}%s
""" % (etymline, elative, elative_of_line, "\n".join(defn_lines), elative,
    reftext)

    msg("Found entry: %s" % spec)
    msg(defn_text)
    return [defn_text, elative, arpositives]

def create_elatives(save, elfile, startFrom, upTo):
  elative_defns = []
  for line in codecs.open(elfile, "r", encoding="utf-8"):
    line = line.strip()
    elative_defns.append(parse_elative_defn(line))
  for current, index in blib.iter_pages(elative_defns, startFrom, upTo,
      # key is the elative
      key = lambda x: x[1]):
    defn_text, elative, arpositives = current
    create_inflection_entry(save, index, elative, None, arpositives[0], None,
      "Adjective", "elative", "positive", "ar-adj", "", "elative of",
      "|lang=ar", entrytext=defn_text)
    for arpositive in arpositives:
      def add_elative_param(page, index, text):
        pagetitle = page.title()
        if not page.exists:
          msg("Page %s %s: WARNING, positive %s not found for elative %s (page nonexistent)" % (
            index, pagetitle, arpositive, elative))
          return None, "skipped positive %s elative %s" % (arpositive, elative)
        found_positive = False
        for template in text.filter_templates():
          if template.name in ["ar-adj", "ar-adj-sound", "ar-adj-in", "ar-adj-an"]:
            if reorder_shadda(getparam(template, "1")) != reorder_shadda(arpositive):
              msg("Page %s %s: Skipping, found adjective template with wrong positive, expecting %s: %s" % (
                  index, pagetitle, arpositive, template))
              continue
            found_positive = True
            existingel = getparam(template, "el")
            if existingel:
              if reorder_shadda(existingel) == reorder_shadda(elative):
                msg("Page %s %s: Skipping template with elative already in it: %s" % (
                    index, pagetitle, template))
              else:
                msg("Page %s %s: Strange, template has elative already in it but not expected %s: %s" % (
                    index, pagetitle, elative, template))
            else:
              msg("Page %s %s: Adding elative %s to template: %s" % (
                index, pagetitle, elative, template))
              template.add("el", elative)
        if not found_positive:
          msg("Page %s %s: WARNING, positive %s not found for elative %s (page exists but couldn't find appropriate template)" % (
            index, pagetitle, arpositive, elative))
        return text, "Add el=%s to adjective %s" % (elative, arpositive)

      page = pywikibot.Page(site, remove_diacritics(arpositive))
      blib.do_edit(page, index, add_elative_param, save=save)

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
pa.add_argument("--elative-list",
    help="File containing elative directives")
pa.add_argument("--elative", action='store_true',
    help="Do elatives")

params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)

if params.plural:
  #create_plurals(params.save, "Noun", ["ar-noun", "ar-noun-nisba"],
  #    startFrom, upTo)
  create_plurals(params.save, "Adjective",
      ["ar-adj", "ar-nisba", "ar-adj-sound", "ar-adj-in", "ar-adj-an"],
      startFrom, upTo)

if params.feminine:
  #create_feminines(params.save, "Noun", ["ar-noun", "ar-noun-nisba"],
  #    startFrom, upTo, fem_inflection)
  create_feminines(params.save, "Adjective",
      ["ar-adj", "ar-nisba", "ar-adj-sound", "ar-adj-in", "ar-adj-an"],
      startFrom, upTo)

if params.verbal_noun:
  create_verbal_nouns(params.save, startFrom, upTo)
if params.participle:
  create_participles(params.save, startFrom, upTo)
if params.verb_part:
  create_verb_parts(params.save, startFrom, upTo, params.verb_part)
if params.non_past:
  create_verb_parts(params.save, startFrom, upTo, '3sm-all-impf')
if params.elative:
  create_elatives(params.save, params.elative_list, startFrom, upTo)
