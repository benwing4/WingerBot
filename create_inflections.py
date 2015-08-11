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
import time

import blib, pywikibot
from blib import msg, errmsg, getparam, addparam, remove_links
from arabiclib import *

site = pywikibot.Site()

verbose = True
personal = False

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

# Remove trailing -un/-u i3rab from inflected form and lemma
def remove_i3rab(wordtype, word, nowarn=False, noremove=False,
    pagemsg=msg):
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
  if word.endswith(AWNA):
    mymsg("Removing i3rab (AWNA -> AWN) from %s" % wordtype)
    return re.sub(AWNA + "$", AWN, word)
  if word and word[-1] in [A, I, U, AN]:
    mymsg("WARNING: Strange diacritic at end of %s %s" % (wordtype, word))
  if word and word[0] == ALIF_WASLA:
    mymsg("Changing alif wasla to plain alif for %s %s" % (wordtype, word))
    word = ALIF + word[1:]
  return word

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
# "ar-noun-pl", "ar-adj-pl" or "ar-adj-fem"). INFLTEMP_PARAMS is a parameter
# or parameters to add to the created INFLTEMP template, and should be a list
# of (PARAM, VALUE) tuples, e.g. '[("2", "f"), ("pl", "sfp")]', in the order
# they should appear in the newly created inflection template. DEFTEMP is
# the definitional template that points to the base form (e.g. "plural of",
# "masculine plural of" or "feminine of"). DEFTEMP_PARAM is a parameter or
# parameters to add to the created DEFTEMP template, and is currently a
# string, either empty of or of the form "|foo=bar" (or e.g. "|foo=bar|baz=bat"
# for more than one parameter). If ENTRYTEXT is given, this is the text to
# use for the entry, starting directly after the "==Etymology==" line, which
# is assumed to be necessary. If not given, this text is synthesized from the
# other parameters. GENDER is used for noun plurals and verbal nouns. (When
# GENDER is specified, the gender parameters should also be present in
# ِINFLTEMP_PARAM. GENDER is used to update the gender in existing entries.)
def create_inflection_entry(save, index, inflection, infltr, lemma, lemmatr,
    pos, infltype, lemmatype, infltemp, infltemp_params, deftemp,
    deftemp_params, entrytext=None, gender=None):

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

  def maybe_remove_i3rab(wordtype, word, nowarn=False, noremove=False):
    return remove_i3rab(wordtype, word, nowarn=nowarn, noremove=noremove,
        pagemsg=pagemsg)

  is_participle = infltype.endswith("participle")
  is_vn = infltype == "verbal noun"
  is_verb_part = infltype.startswith("verb part")
  is_plural = infltype == "plural"
  is_feminine = infltype == "feminine"
  is_plural_noun = is_plural and pos == "Noun"
  is_feminine_noun = is_feminine and pos == "Noun"
  is_plural_or_fem = is_plural or is_feminine
  lemma_is_verb = is_verb_part or is_vn or is_participle

  infltemp_params_str = ''.join([
    "|%s" % value if re.match("^[0-9]+$", param) else "|%s=%s" % (param, value)
    for param, value in infltemp_params])

  if is_verb_part:
    # assert infltemp_params is as we expect, 2=FORM
    assert(len(infltemp_params) == 1 and infltemp_params[0][0] == "2")
    verb_part_form = infltemp_params[0][1]
    assert(len(verb_part_form) > 0 and verb_part_form[0] in ["I", "V", "X"])
    verb_part_inserted_defn = False

  lemma = maybe_remove_i3rab(lemmatype, lemma, noremove=lemma_is_verb)
  inflection = maybe_remove_i3rab(infltype, inflection, noremove=is_verb_part)

  if inflection == "-":
    pagemsg("Not creating entry '-'")
    return

  # This can happen e.g. with words like جَرِيح "wounded" where the feminine
  # is the same as the masculine.
  if reorder_shadda(lemma) == reorder_shadda(inflection):
    pagemsg("WARNING: Inflection same as lemma, not creating entry")
    return

  # Prepare to create page
  pagemsg("Creating entry")
  page = pywikibot.Page(site, pagename)

  must_match_exactly = not is_plural_or_fem

  # Detect cases where multiple lemmas that are the same when unvocalized
  # have inflections that are the same when unvocalized. For example, for
  # singular قطعة and plural قطع, there are three different possible
  # vocalizations. If so, require the existing versions match exactly
  # rather than matching with removed diacritics. (The first time around
  # this won't happen and we may change the vowels to match the first set,
  # but when processing the later sets, we'll add new entries and the first
  # set's entry will stand.)
  if not must_match_exactly:
    infl_no_vowels = pagename
    lemma_no_vowels = remove_diacritics(lemma)
    li_no_vowels = (lemma_no_vowels, infl_no_vowels)
    lemma_inflection_counts[li_no_vowels] = (
        lemma_inflection_counts.get(li_no_vowels, 0) + 1)
    if lemma_inflection_counts[li_no_vowels] > 1:
      pagemsg("Found multiple (%s) vocalized possibilities for %s %s, %s %s" % (
        lemma_inflection_counts[li_no_vowels], lemmatype, lemma_no_vowels,
        infltype, infl_no_vowels))
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

  custom_entrytext = entrytext

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
        infltemp_params_str, "|tr=%s" % infltr if infltr else "")
    new_defn_template = "{{%s|%s%s%s}}" % (
      deftemp, lemma,
      "|tr=%s" % lemmatr if lemmatr else "",
      deftemp_params)
    newposbody = """%s

# %s
""" % (new_headword_template, new_defn_template)
    newposheader = "===%s===\n" % pos
    newpos = newposheader + newposbody
    newposheaderl4 = "====%s====\n" % pos
    newposl4 = newposheaderl4 + newposbody
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
    m = re.match(r"^(.*?\n)((\[\[[a-z0-9_\-]+:[^\]]+\]\]\n*)*)$",
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
        mm = re.match(r"^(.*?\n)(--+\n*)$", sections[i], re.S)
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

        # Convert existing ===Verbal noun=== headers into ===Noun===,
        # ===Adjective form=== into ===Adjective=== and
        # ===Noun form=== into ===Noun===.
        for j in xrange(1, len(subsections), 2):
          for frompos, topos in [("Verbal noun", "Noun"),
              ("Adjective form", "Adjective"), ("Noun form", "Noun")]:
            if re.match("^===+%s===+" % frompos, subsections[j]):
              subsections[j] = re.sub("(===+)%s(===+)" % frompos,
                  r"\1%s\2" % topos, subsections[j])
              pagemsg("Converting '%s' section header to '%s'" %
                  (frompos, topos))
              notes.append("converted '%s' section header to '%s'" %
                  (frompos, topos))
            sections[i] = ''.join(subsections)

        # If verbal noun or participle or feminine noun, check for an existing
        # entry matching the headword and defn. If so, don't do anything. We
        # need to do this because otherwise we might have a situation with two
        # entries for a given noun (or participle) and the second one having
        # an appropriate defn, and when we encounter the first one we see it
        # doesn't have a defn and go ahead and insert it, which we don't want
        # to do.
        #
        # Also count number of entries for given noun (or participle). If
        # none have a defn and there's more than one, we don't know which one
        # to insert the defn into, so issue a warning and punt.
        #
        # FIXME: Should we do this check for all lemma/inflection types?
        if is_vn or is_participle or is_feminine_noun:
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

        # Derive a sort key from the text of an inflection-of template.
        def inflection_of_sort_key(tstr):
          vf_person = 13
          vf_voice = "pasv"
          vf_mood = "e"
          if "|actv" in tstr:
            vf_voice = "actv"
          if "|past" in tstr:
            vf_mood = "a"
          if "|indc" in tstr:
            vf_mood = "b"
          if "|subj" in tstr:
            vf_mood = "c"
          if "|juss" in tstr:
            vf_mood = "d"
          persons = all_person_infls
          for k in xrange(len(persons)):
            if "|" + persons[k] in tstr:
              vf_person = k
          return (vf_person, vf_voice, vf_mood)

        # Sort the definition templates in the verb part subsection indexed
        # by INDEX. Return True if anything changed.
        def sort_defns_in_one_verb_part_subsection(index):
          assert index > 0 and (index % 2) == 0
          subsec = subsections[index]
          if not subsec.endswith("\n"):
            subsec += "\n"
          mm = re.match(r"^(.*?\n)((?:# \{\{inflection of\|[^\n}]*\}\}\n)+)(.*)$",
              subsec, re.S)
          if not mm:
            pagemsg("WARNING: Strange subsection without inflection-of template: [[%s]]" %
                subsec)
          else:
            before, defntext, after = mm.groups()
            if defntext:
              assert defntext.endswith("\n")
              # Ignore last split defn, which will be empty
              defns = re.split("\n", defntext)[0:-1]
              new_defns = sorted(defns, key=inflection_of_sort_key)
              if defns != new_defns:
                subsections[index] = (before + "\n".join(new_defns) + "\n" +
                    after)
                return True
          return False

        # Sort the definitions in an individual verb-part subsection.
        # Return True if text was changed.
        def sort_defns_in_verb_part_subsections():
          sorted_any = False
          for j in xrange(2, len(subsections), 2):
            is_verb_form = "{{ar-verb-form|" in subsections[j]
            if is_verb_form:
              sorted_this = sort_defns_in_one_verb_part_subsection(j)
              sorted_any = sorted_any or sorted_this
          if sorted_any:
            sections[i] = ''.join(subsections)
          return sorted_any

        # Sort the run of individual verb-part subsections from START to
        # END, inclusive on both sides.
        def sort_verb_part_subsection_run(start, end):
          #pagemsg("sort_one_section called with [%s,%s]" % (start, end))
          if end == start:
            return
          assert(start > 0 and (start % 2) == 0)
          assert((end % 2) == 0 and end > start)
          assert(end < len(subsections))
          header1 = subsections[start - 1]
          for j in xrange(start + 1, end + 1, 2):
            if subsections[j] != header1:
              pagemsg("WARNING: Header [[%s]] doesn't match prior header [[%s]], not sorting"
                  % (subsections[j], header1))
              return
          subsecs = []
          for j in xrange(start, end + 2, 2):
            subsecs.append(subsections[j])
          def keyfunc(subsec):
            parsed = blib.parse_text(subsec)
            vf_last_vowel = "u"
            vf_person = 13
            vf_voice = "pasv"
            vf_mood = "e"
            seen_inflection_of = False

            for t in parsed.filter_templates():
              if t.name == "ar-verb-form":
                vf_vowels = re.sub("[^" + A + I + U + "]", "",
                    reorder_shadda(getparam(t, "1"))[0:-1])
                if len(vf_vowels) > 0:
                  if vf_vowels[-1] == A:
                    vf_last_vowel = "a"
                  elif vf_vowels[-1] == I:
                    vf_last_vowel = "i"
                  else:
                    vf_last_vowel = "u"
              # Only use first inflection-of template
              if t.name == "inflection of" and not seen_inflection_of:
                vf_person, vf_voice, vf_mood = (
                    inflection_of_sort_key(unicode(t)))
                seen_inflection_of = True
            sort_key = (vf_person, vf_voice, vf_last_vowel, vf_mood)
            #pagemsg("Sort key: %s" % (sort_key,))
            return sort_key
          newsubsecs = sorted(subsecs, key=keyfunc)
          if newsubsecs != subsecs:
            for k, j in zip(xrange(len(subsecs)), xrange(start, end + 2, 2)):
              subsections[j] = ensure_two_trailing_nl(newsubsecs[k])

        # Sort the order of individual verb-part subsections. Return True
        # if text was changed.
        def sort_verb_part_subsections():
          subsections_sentinel = subsections + ["", ""]
          #for jj in xrange(len(subsections_sentinel)):
            #pagemsg("Subsection %s: [[%s]]" % (jj, subsections_sentinel[jj]))
          start = None
          for j in xrange(len(subsections_sentinel)):
            if j > 0 and (j % 2) == 0:
              is_verb_form = "{{ar-verb-form|" in subsections_sentinel[j]
              if start == None and is_verb_form:
                start = j
              if start != None and not is_verb_form:
                end = j - 2
                sort_verb_part_subsection_run(start, end)
                start = None
          newtext = ''.join(subsections)

          if newtext != sections[i]:
            #pagemsg("old sections[i]: [[%s]]\nnew sections[i]: [[%s]]\n" % (
            #  sections[i], newtext))
            sections[i] = newtext
            return True
          else:
            return False

        # Return False is ===Etymology N=== section doesn't contain only
        # verb parts. Else, return a key of (FORM, LEMMA) where LEMMA
        # doesn't contain diacritics.
        def verb_part_etym_group_key(text, warn=False):
          # Issue a warning only if WARN is True. We do this first time
          # around, but not when functioning as a sort key to avoid getting
          # a zillion warnings.
          def warning(txt):
            if warn:
              pagemsg("WARNING: %s" % txt)

          subsecs = re.split("(^===+[^=\n]+===+\n)", text, 0, re.M)
          if len(subsecs) < 2:
            warning("Etym section has no subsections: [[%s]]" % text)
            return False
          form = None
          lemma = None
          # Keep track of lemmas seen to reduce warnings
          lemmas_seen = []
          for j in xrange(1, len(subsecs), 2):
            if not re.match("^=+Verb=+\n", subsecs[j]):
              return False
            parsed = blib.parse_text(subsecs[j + 1])
            for t in parsed.filter_templates():
              if t.name == "ar-verb-form":
                newform = getparam(t, "2")
                if not form:
                  form = newform
                elif form != newform:
                  warning("Same etym section, two different forms, %s and %s" % (
                    form, newform))
              elif t.name == "inflection of":
                newlemma = remove_diacritics(getparam(t, "1"))
                if not lemma:
                  lemma = newlemma
                  lemmas_seen.append(lemma)
                elif lemma != newlemma:
                  if newlemma not in lemmas_seen:
                    warning("Same etym section, two different vowelless lemmas, %s and %s" % (
                      lemma, newlemma))
                    lemmas_seen.append(newlemma)
              else:
                return False
          if not form or not lemma:
            warning("Verb etym section has missing templates: [[%s]]" % text)
          if not form:
            form = 100
          elif form not in form_classes_to_number:
            warning("Strange verb form class %s" % form)
            form = 100
          else:
            form = form_classes_to_number[form]
          if not lemma:
            lemma = u"يييييييييييييييي"
          return (form, lemma)

        # Sort the groups of subsections under ===Etymology N=== headers.
        # Return True if text was changed.
        def sort_verb_part_etym_groups():
          etym_groups = re.split("(^===Etymology [0-9]+===\n)", sections[i],
              0, re.M)
          if len(etym_groups) > 1:
            # Save the header
            etym_header = etym_groups[0]
            # Separate verb-part and non-verb-part etyms
            non_verb_part_etyms = []
            verb_part_etyms = []
            for j in xrange(2, len(etym_groups), 2):
              is_verb_part_etym = verb_part_etym_group_key(
                  etym_groups[j], warn=True)
              if is_verb_part_etym:
                verb_part_etyms.append(etym_groups[j])
              else:
                non_verb_part_etyms.append(etym_groups[j])
            # Sort verb-part etyms
            new_vpes = sorted(verb_part_etyms, key=verb_part_etym_group_key)
            # Put non-verb-part etyms before sorted verb-part etyms
            new_etym_groups = [etym_header]
            sorted_etyms = non_verb_part_etyms + new_vpes
            for index, etym_group in zip(
                xrange(len(sorted_etyms)), sorted_etyms):
              new_etym_groups.append("===Etymology %s===\n" % (index + 1))
              new_etym_groups.append(etym_group)
            if new_etym_groups != etym_groups:
              for j in xrange(2, len(new_etym_groups), 2):
                new_etym_groups[j] = ensure_two_trailing_nl(
                    new_etym_groups[j])
              sections[i] = ''.join(new_etym_groups)
              # Recompute subsections[] based on new ordering; use
              # subsections[:] to overwrite existing subsections list (can't
              # just assign to subsections because variable will be local)
              subsections[:] = (
                  re.split("(^===+[^=\n]+===+\n)", sections[i], 0, re.M))
              return True
          return False

        # Sort adjoining verb form subsections, as well as defns in the
        # subsections and etym groups of subsections. However, if
        # ETYM_GROUPS_ONLY, only sort the etym groups; we do this when
        # we have added a new etym group, because this invalidates
        # subsections[], which we rely on in the other two kinds of sorting.
        def sort_verb_part_sections(etym_groups_only=False):
          sorted1 = not etym_groups_only and sort_defns_in_verb_part_subsections()
          sorted2 = not etym_groups_only and sort_verb_part_subsections()
          sorted3 = sort_verb_part_etym_groups()
          sortmsgs = []
          if sorted1:
            sortmsgs.append("defns")
          if sorted2:
            sortmsgs.append("subsecs")
          if sorted3:
            sortmsgs.append("etym groups")
          if sortmsgs:
            pagemsg("Sorted verb part sections (%s)" % ",".join(sortmsgs))
            notes.append("sorted verb part sections (%s)" % ",".join(sortmsgs))

        # If verb part, go through and sort adjoining verb form subsections,
        # as well as defns in the subsections and etym groups of subsections
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
            # Get a parsed representation of the text of subsections[j].
            # NOTE: Any time you modify a template coming from this parsed,
            # representation, you need to execute the following:
            #
            # subsections[j] = unicode(parsed)
            # sections[i] = ''.join(subsections)
            parsed = blib.parse_text(subsections[j])

            def check_maybe_remove_i3rab(template, param, wordtype):
              # Check for i3rab in existing lemma or infl and remove it if so
              existing = getparam(template, param)
              existing_no_i3rab = maybe_remove_i3rab(wordtype, existing,
                  noremove=is_verb_part or wordtype == "dictionary form")
              if reorder_shadda(existing) != reorder_shadda(existing_no_i3rab):
                notes.append("removed %s i3rab" % wordtype)
                addparam(template, param, existing_no_i3rab)
                subsections[j] = unicode(parsed)
                sections[i] = ''.join(subsections)
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
            # duplicate entry. Require exact match because there are cases like
            # collective noun صَدَف (singulative صَدَفَة) and plural صُدَف
            # (singular صُدْفَة) where we don't want this special case to trigger.
            if is_plural_noun:
              headword_collective_templates = [t for t in parsed.filter_templates()
                  if t.name == "ar-coll-noun" and
                  template_head_matches(t, inflection, require_exact_match=True)
                  and compare_param(t, "sing", lemma, require_exact_match=True)]
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
            # gender if needed, and return True. (E.g. existing "p" matches
            # new "m-p" and will be modified; existing "m-p" matches new "p"
            # and will be left alone; existing "p-pr" matches new "m-p" and
            # will be modified to "m-p-pr". Similar checks are done for the
            # second gender. We don't currently handle the situation where
            # e.g. the existing gender is both "m-p" and "f-p" and the new
            # gender is "f-p" and "m-p" in reverse order. To handle that,
            # we would need to sort both sets of genders by some criterion.)
            def check_fix_gender(headword_template, gender, warning_on_false):
              defgender = is_plural and "p" or ""
              def gender_compatible(existing, new):
                if is_plural:
                  if not re.search(r"\bp\b", existing):
                    pagemsg("WARNING: Something wrong, existing plural gender %s does not have 'p' in it" % existing)
                    return False
                  if not re.search(r"\bp\b", new):
                    pagemsg("WARNING: Something wrong, new plural gender %s does not have 'p' in it" % new)
                    return False
                else:
                  assert is_vn or is_feminine
                  if re.search(r"\bp\b", existing):
                    pagemsg("WARNING: Something wrong, existing vn/fem gender %s has 'p' in it" % existing)
                    return False
                  if re.search(r"\bp\b", new):
                    pagemsg("WARNING: Something wrong, new vn/fem gender %s has 'p' in it" % new)
                    return False
                m = re.search(r"\b([mf])\b", existing)
                existing_mf = m and m.group(1)
                m = re.search(r"\b([mf])\b", new)
                new_mf = m and m.group(1)
                if existing_mf and new_mf and existing_mf != new_mf:
                  pagemsg("%sCan't modify mf gender from %s to %s" % (
                      "WARNING: " if warning_on_false else "",
                      existing_mf, new_mf))
                  return False
                new_mf = new_mf or existing_mf
                m = re.search(r"\b(pr|np)\b", existing)
                existing_pr = m and m.group(1)
                m = re.search(r"\b(pr|np)\b", new)
                new_pr = m and m.group(1)
                if existing_pr and new_pr and existing_pr != new_pr:
                  pagemsg("%sCan't modify personalness from %s to %s" % (
                      "WARNING: " if warning_on_false else "",
                      existing_pr, new_pr))
                  return False
                new_pr = new_pr or existing_pr
                return '-'.join([x for x in [new_mf, defgender, new_pr] if x])

              if len(gender) == 0:
                return True # "nochange"
              existing_gender = getparam(headword_template, "2")
              existing_gender2 = getparam(headword_template, "g2")
              assert(len(gender) == 1 or len(gender) == 2)
              new_gender = gender_compatible(
                  existing_gender or defgender, gender[0])
              if new_gender == False:
                return False
              new_gender2 = len(gender) == 2 and gender[1] or ""
              if existing_gender2 or new_gender2:
                new_gender2 = gender_compatible(existing_gender2 or defgender,
                    new_gender2 or defgender)
                if new_gender2 == False:
                  return False
              changed = False
              if (new_gender != existing_gender and new_gender and
                  new_gender != defgender):
                pagemsg("Modifying first gender from '%s' to '%s'" % (
                  existing_gender, new_gender))
                addparam(headword_template, "2", new_gender)
                changed = True
              if (new_gender2 != existing_gender2 and new_gender2 and
                  new_gender2 != defgender):
                pagemsg("Modifying second gender from '%s' to '%s'" % (
                  existing_gender2, new_gender2))
                addparam(headword_template, "g2", new_gender2)
                changed = True
              if changed:
                subsections[j] = unicode(parsed)
                sections[i] = ''.join(subsections)
                notes.append("updated gender")
              return True # changed and "changed" or "nochange"

            # Update the gender in HEADWORD_TEMPLATE according to GENDER
            # (which might be empty, meaning no updating) using
            # check_fix_gender(). Also update any other parameters in
            # HEADWORD_TEMPLATE according to PARAMS. Return False and issue
            # a warning if we're unable to update (meaning a parameter
            # we wanted to set already existed in HEADWORD_TEMPLATE with a
            # different value); else return True. If changes were made,
            # an appropriate note will be added to 'notes' and the
            # section and subsection text updated.
            def check_fix_infl_params(headword_template, params, gender,
                warning_on_false):
              if gender:
                if not check_fix_gender(headword_template, gender,
                    warning_on_false):
                  return False
                # Don't try to further process the gender params that we
                # already processed.
                params = [(param, value) for param, value in params
                    if param not in ["2", "g2"]]
              # First check that we can update params before changing anything
              for param, value in params:
                existing = reorder_shadda(getparam(headword_template, param))
                value = reorder_shadda(value)
                assert(value)
                if existing == value:
                  pass
                elif existing:
                  pagemsg("%sCan't modify %s from %s to %s" % (
                      "WARNING: " if warning_on_false else "",
                      param, existing, value))
                  return False
              # Now update params
              changed = False
              for param, value in params:
                existing = reorder_shadda(getparam(headword_template, param))
                value = reorder_shadda(value)
                assert(value)
                if existing:
                  assert(existing == value)
                else:
                  addparam(headword_template, param, value)
                  changed = True
                  notes.append("updated %s=%s" % (param, value))
              if changed:
                subsections[j] = unicode(parsed)
                sections[i] = ''.join(subsections)
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

                # First, make sure we can update infl params as needed.
                if check_fix_infl_params(infl_headword_template,
                    infltemp_params, gender, True):
                  # Replace existing infl with new one
                  if len(inflection) > len(existing_infl):
                    pagemsg("Updating existing %s %s with %s" %
                        (infltemp, existing_infl, inflection))
                    addparam(infl_headword_template, infl_headword_matching_param,
                      inflection)
                    if infltr:
                      trparam = "tr" if infl_headword_matching_param == "1" \
                          else infl_headword_matching_param.replace("head", "tr")
                      addparam(infl_headword_template, trparam, infltr)

                  # Replace existing lemma with new one
                  if len(lemma) > len(existing_lemma):
                    pagemsg("Updating existing '%s' %s with %s" %
                        (deftemp, existing_lemma, lemma))
                    addparam(defn_template, "1", lemma)
                    if lemmatr:
                      addparam(defn_template, "tr", lemmatr)

                  subsections[j] = unicode(parsed)
                  sections[i] = ''.join(subsections)
                  comment = "Update Arabic with better vocalized versions: %s %s, %s %s, pos=%s" % (
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

              # Check for i3rab in existing infl and remove it if so
              check_maybe_remove_i3rab(infl_headword_template,
                  infl_headword_matching_param, infltype)

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

              # Else, not verb form.
              else:
                # Fix gender and other inflection params. Even if we can't
                # set them appropriately, do nothing since we already have
                # found an entry with same inflection and definition; but we
                # will output a warning.
                check_fix_infl_params(infl_headword_template,
                    infltemp_params, gender, True)
                # "Do nothing", but set a comment, in case we made a template
                # change like updating i3rab or changing gender.
                comment = "Already found entry: %s %s, %s %s" % (
                    infltype, inflection, lemmatype, lemma)
                break

            # At this point, didn't find both headword and definitional
            # template. If we found headword template, insert new definition
            # in same section.
            elif infl_headword_templates:
              infl_headword_template, infl_headword_matching_param = \
                  infl_headword_templates[0]
              # Check for i3rab in existing infl and remove it if so
              check_maybe_remove_i3rab(infl_headword_template,
                  infl_headword_matching_param, infltype)
              # Previously, when looking for a matching headword template,
              # we may not have required the vowels to match exactly
              # (e.g. when creating plurals). But now we want to make sure
              # they do, or we will put the new definition under a wrong
              # headword.
              if compare_param(infl_headword_template, infl_headword_matching_param, inflection, require_exact_match=True):
                # Also make sure manual translit matches
                trparam = "tr" if infl_headword_matching_param == "1" \
                    else infl_headword_matching_param.replace("head", "tr")
                existing_tr = getparam(infl_headword_template, trparam)
                # infltr may be None and existing_tr may be "", but
                # they should match
                if (infltr or None) == (existing_tr or None):

                  # Don't insert defn when there are multiple heads because
                  # we don't know that all heads are actually legit verbal noun
                  # (or participle) alternants.
                  if getparam(infl_headword_template, "head2"):
                    pagemsg("Inflection template has multiple heads, not inserting %s defn into it" % (infltype))
                  # Don't insert defn in feminine nouns that end in -iyya,
                  # because they're probably abstract nouns with different
                  # etymology.
                  elif is_feminine_noun and reorder_shadda(getparam(
                      infl_headword_template, infl_headword_matching_param
                      )).endswith(IYYAH):
                    pagemsg("Not inserting %s defn into noun ending in -iyya, probably an abstract noun" % infltype)
                  # If there's custom entry text (for elatives), we can't
                  # just insert a definition because the entry is more
                  # complicated.
                  elif custom_entrytext:
                    pagemsg("Custom entry supplied, not inserting %s defn into existing entry" % infltype)
                  else:
                    # Make sure we can set the gender and other inflection
                    # parameters appropriately. If not, we will end up
                    # checking for more entries and maybe adding an entirely
                    # new entry.
                    if check_fix_infl_params(infl_headword_template,
                        infltemp_params, gender, False):
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
                      comment = "Insert existing defn with {{%s}} at beginning after any existing such defns: %s %s, %s %s" % (
                          deftemp, infltype, inflection, lemmatype, lemma)
                      if is_verb_part:
                        sort_verb_part_sections()
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

        # else of for loop over subsections, i.e. no break out of loop
        else:
          # Under certain circumstances with verb parts, we inserted a
          # new defn in an existing section but didn't break. We break now,
          # but first sort verb part sections if necessary.
          if not need_new_entry:
            if is_verb_part:
              sort_verb_part_sections()
            break

          # At this point we couldn't find an existing subsection with
          # matching POS and appropriate headword template whose head matches
          # the the inflected form.

          # If verb part, try to find an existing verb section corresponding
          # to the same verb or another verb of the same conjugation form
          # (either the lemma of the verb or another non-lemma form) whose
          # lemma has the same consonants as the lemma of the verb part in
          # question. That way we do match up e.g. passive kutiba with active
          # kataba (or kutiba passive of kataba with katiba, if necessary),
          # but we don't match up non-past yasurru (from form I sarra) with
          # lemma verb entry (ar-verb) form I yasara, or match up non-past
          # yaruddu (from form I radda) with non-past verb part (ar-verb-form)
          # yaridu (from form I warada).) When looking at ar-verb, do a
          # template call to fetch the dictionary forms (lemma forms). When
          # looking at ar-verb-form, only the conjugation class is in the
          # template; the lemma is contained in a definition template, which
          # we check for.
          #
          # Insert after the last such verb section.
          #
          # Similarly, if plural or feminine, try to find a section with an
          # existing noun or noun form or adjective form with the same
          # headword to insert after. Insert after the last such one.

          if is_verb_part or is_plural_or_fem:
            def is_section_to_insert_after(t, defn_templates):
              if is_verb_part:
                # Check for ar-verb whose dictionary form matches the
                # verb part's lemma in its consonants. See above.
                if (t.name == "ar-verb" and
                    re.sub("-.*$", "", getparam(t, "1")) == verb_part_form and
                    remove_diacritics(lemma) in [remove_diacritics(dicform)
                      for dicform in get_dicform_all(page, t)]):
                  return True
                # Similar check for ar-verb-form; in this case we need to
                # look at the associated defn templates.
                return (t.name == infltemp and
                    compare_param(t, "2", verb_part_form) and
                    [d for d in defn_templates if
                      remove_diacritics(lemma) == remove_diacritics(getparam(d,
                        "1"))])
              else:
                assert is_plural_or_fem
                # For feminine nouns and adjectives, don't insert after section
                # for nouns that ends in -iyya, because they're probably
                # abstract nouns with different etymology -- unless there's
                # a defn, in which case it's probably a feminine noun
                # inflection.
                if (is_feminine and t.name == "ar-noun" and
                    reorder_shadda(getparam(t, "1")).endswith(IYYAH) and
                    not [d for d in defn_templates
                      # Unclear if we need this comparison.
                      if compare_param(d, "1", lemma)]):
                  return False
                # Require that the head exactly matches the new inflection;
                # but that may not be enough.
                if not template_head_matches(t, inflection,
                    require_exact_match=True):
                  return False
                # FIXME: Rest of this logic is a bit questionable.
                # If the template is for a pl or fem inflected form, OK.
                if t.name in ["ar-noun-pl", "ar-adj-pl", "ar-noun-fem",
                    "ar-adj-fem"]:
                  return True
                # For feminines, also OK if template is for any noun.
                if is_feminine:
                  return t.name in ["ar-noun", "ar-coll-noun", "ar-sing-noun"]
                # For plurals, OK to go next to collective nouns, but
                # otherwise we should only go next to nouns that are plural,
                # so we don't end up putting plural inflections next to
                # verbal nouns, e.g. plural صُلُوح of singular صَالِِح next to
                # verbal noun صُلُوح of verb صَلَحَ.
                assert is_plural
                if t.name == "ar-coll-noun":
                  return True
                if (t.name == "ar-noun" and
                    re.match(r"\bp\b", getparam(t, "2"))):
                  return True
                return False

            def section_to_insert_after():
              insert_at = None
              for j in xrange(2, len(subsections), 2):
                if re.match("^===+Verb===+" if is_verb_part else
                    "^===+(Noun|Adjective)===+", subsections[j - 1]):
                  parsed = blib.parse_text(subsections[j])
                  defn_templates = [t for t in parsed.filter_templates()
                      if t.name == deftemp]
                  for t in parsed.filter_templates():
                    if is_section_to_insert_after(t, defn_templates):
                      insert_at = j + 1
              return insert_at

            insert_at = section_to_insert_after()
            if insert_at:
              pagemsg("Found section to insert %s after: [[%s]]" % (
                  infltype, subsections[insert_at - 1]))

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

              if is_verb_part:
                secmsg = "verb section for same lemma"
              else:
                assert is_plural_or_fem
                secmsg = "noun/adjective section for same inflection"

              pagemsg("Inserting after %s" % secmsg)
              comment = "Insert entry for %s %s of %s after %s" % (
                infltype, inflection, lemma, secmsg)
              subsections[insert_at - 1] = ensure_two_trailing_nl(
                  subsections[insert_at - 1])
              if indentlevel == 3:
                subsections[insert_at:insert_at] = [
                    newposheader, newposbody + "\n"]
              else:
                assert(indentlevel == 4)
                subsections[insert_at:insert_at] = [
                    newposheaderl4, newposbody + "\n"]
              sections[i] = ''.join(subsections)

              if is_verb_part:
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
            sections[i] += "===Etymology %s===\n" % j + entrytextl4 + "\n"
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
            newsectionsi = re.sub(r"^(.*?\n)(===Etymology===\n(\n|[^=\n].*?\n)*)",
                r"\2\1", sections[i], 0, re.S)
            if newsectionsi != sections[i]:
              pagemsg("Moved ===Alternative forms=== and such after Etymology")
              sections[i] = newsectionsi
            sections[i] = re.sub("^===Etymology===\n", "", sections[i])
            sections[i] = ("==Arabic==\n" + wikilink + "\n===Etymology 1===\n" +
                ("\n" if sections[i].startswith("==") else "") +
                ensure_two_trailing_nl(re.sub("^==(.*?)==$", r"===\1===",
                  sections[i], 0, re.M)) +
                "===Etymology 2===\n" + entrytextl4 + "\n")
          if is_verb_part:
            sort_verb_part_sections(etym_groups_only=True)
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

      if sections:
        sections[-1] = ensure_two_trailing_nl(sections[-1])
        sections += ["----\n\n", newsection]
      else:
        pagemsg("WARNING: No language sections in current page")
        notes.append("formerly empty")
        if pagehead.lower().startswith("#redirect"):
          pagemsg("WARNING: Page is redirect, overwriting")
          notes.append("overwriting redirect")
          pagehead = re.sub(r"#redirect *\[\[(.*?)\]\] *(<!--.*?--> *)*\n*",
              r"{{also|\1}}\n", pagehead, 0, re.I)
        sections += [newsection]

    # End of loop over sections in existing page; rejoin sections
    newtext = pagehead + ''.join(sections)
    if pagetail:
      newtext = ensure_two_trailing_nl(newtext) + pagetail
      if not comment and not notes:
        notes.append("fixed up spacing")

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
      num_tries = 0
      while True:
        try:
          page.save(comment = comment)
          break
        except KeyboardInterrupt as e:
          raise
        except Exception as e:
          #except (pywikibot.exceptions.Error, StandardError) as e:
          pagemsg("WARNING: Error saving: %s" % unicode(e))
          errmsg("WARNING: Error saving: %s" % unicode(e))
          num_tries += 1
          if num_tries >= 5:
            pagemsg("WARNING: Can't save!!!!!!!")
            errmsg("WARNING: Can't save!!!!!!!")
            raise
          errmsg("Sleeping for 5 seconds")
          time.sleep(5)

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

  def do_remove_i3rab(wordtype, word):
    return remove_i3rab(wordtype, word, pagemsg=pagemsg)

  def pluralize_gender(g):
    plural_gender = {
        "m":"m-p", "m-pr":"m-p-pr", "m-np":"m-p-np",
        "f":"f-p", "f-pr":"f-p-pr", "f-np":"f-p-np",
        "pr":"p-pr", "np":"p-np"
    }
    if re.search(g, r"\bp\b"):
      pagemsg("WARNING: Trying to pluralize already plural gender %s" % g)
      return g
    if g in plural_gender:
      return plural_gender[g]
    pagemsg("WARNING: Trying to pluralize unrecognizable gender %s" % g)
    return g

  def fem_pl_noun(noun):
    if noun.endswith(AAH):
      return re.sub(AAH + "$", AYAAT, noun)
    if noun.endswith(AH):
      return re.sub(AH + "$", AAT, noun)
    if noun.endswith(IN):
      return re.sub(IN + "$", IYAAT, noun)
    regex = "((" + AN + "|" + A + ")(" + ALIF + "|" + AMAQ + ")|" + A + "?(" + ALIF + "|" + AMAQ + ")" + AN + ")$"
    if re.search(regex, noun):
      return re.sub(regex, AYAAT, noun)
    return noun + AAT

  # Figure out plural gender
  if template.name == "ar-noun-nisba":
    if personal:
      gender = ["m-p-pr"]
    else:
      gender = ["m-p"]
  else:
    # If plural ends in -ūn we are almost certainly dealing with a masculine
    # personal noun, unless it's a short plural like قُرُون plural
    # of وَرْن "horn" or سِنُون plural of سَنَة "hour".
    singgender = getparam(template, "2")
    lemma = do_remove_i3rab("singular", reorder_shadda(lemma))
    inflection = do_remove_i3rab("plural", reorder_shadda(inflection))
    if inflection.endswith(UUN) and len(inflection) <= 6:
      pagemsg(u"Short -ūn plural, not treating as personal plural")
    elif inflection.endswith(UUN) or inflection.endswith(UUNA):
      if personal:
        pagemsg(u"Long -ūn plural, treating as personal")
      else:
        pagemsg(u"Long -ūn plural, would treat as personal")
      if singgender == "m-pr":
        pass
      elif singgender in ["", "m"]:
        singgender = "m-pr" if personal else "m"
      else:
        pagemsg(u"WARNING: Long -ūn plural but strange gender %s" % singgender)
    elif (singgender == "m" and not lemma.endswith(TAM) and
        fem_pl_noun(lemma) == inflection):
      if personal:
        pagemsg(u"Masculine noun with -āt plural, treating as non-personal")
        singgender = "m-np"
      else:
        pagemsg(u"Masculine noun with -āt plural, would treat as non-personal")
    if not singgender:
      gender = ["p"]
    else:
      gender = [pluralize_gender(singgender)]
      singgender2 = getparam(template, "g2")
      if singgender2:
          gender.append(pluralize_gender(singgender2))
  if not gender:
    genderparam = []
  elif len(gender) == 1:
    genderparam = [("2", gender[0])]
  else:
    assert(len(gender) == 2)
    genderparam = [("2", gender[0]), ("g2", gender[1])]

  create_inflection_entry(save, index, inflection, infltr, lemma, lemmatr, pos,
      "plural", "singular", "ar-noun-pl", genderparam, "plural of", "|lang=ar",
      gender=gender)

def create_adj_plural(save, index, inflection, infltr, lemma, lemmatr,
    template, pos):
  create_inflection_entry(save, index, inflection, infltr, lemma, lemmatr, pos,
      "plural", "singular", "ar-adj-pl", [], "masculine plural of", "|lang=ar")

def create_noun_feminine(save, index, inflection, infltr, lemma, lemmatr,
    template, pos):

  plparams = []

  # Output a message include page name and inflection/lemma
  def pagemsg(text):
    msg("Page %s %s: %s: feminine %s%s, masculine %s%s" % (
      index, remove_diacritics(inflection), text,
      inflection, infltr and " (%s)" % infltr,
      lemma, lemmatr and " (%s)" % lemmatr))

  # Set plural, based on either explicitly specified feminine plural(s) in
  # lemma template, or inferred from the inflection by substituting -a with
  # -āt.
  if getparam(template, "fpl"):
    plparams.append(("pl", getparam(template, "fpl")))
    fpltr = getparam(template, "fpltr")
    if fpltr:
      plparams.append(("pltr", fpltr))
    i = 2
    while True:
      fplparam = "fpl%s" % i
      plparam = "pl%s" % i
      fpl = getparam(template, fplparam)
      if not fpl:
        break
      plparams.append((plparam, fpl))
      fpltr = getparam(template, fplparam + "tr")
      if fpltr:
        plparams.append((plparam + "tr", fpltr))
      i += 1
  else:
    inflection = reorder_shadda(inflection)
    if reorder_shadda(lemma) + AH != inflection:
      pagemsg("WARNING: Feminine is not simply masculine plus -a, auto-plural may be wrong")
    if not inflection.endswith(AH):
      pagemsg("WARNING: Arabic feminine does not end in -a")
    elif infltr and not infltr.endswith("a"):
      pagemsg("WARNING: Translit feminine does not end in -a")
    else:
      fpl = re.sub(AH + "$", AAT, inflection)
      plparams.append(("pl", fpl))
      if infltr:
        fpltr = re.sub("a$", u"āt", infltr)
        plparams.append(("pltr", fpltr))

  # Now construct gender and inflection params
  gender = ["f-pr" if personal else "f"]
  inflparams = [("2", gender[0])]
  inflparams.append(("m", lemma))
  if lemmatr:
    inflparams.append(("mtr", lemmatr))
  inflparams += plparams

  create_inflection_entry(save, index, inflection, infltr, lemma, lemmatr, pos,
      "feminine", "masculine", "ar-noun", inflparams,
      "feminine of", "|lang=ar", gender=gender)

def create_adj_feminine(save, index, inflection, infltr, lemma, lemmatr,
    template, pos):
  create_inflection_entry(save, index, inflection, infltr, lemma, lemmatr, pos,
      "feminine", "masculine", "ar-adj-fem", [], "feminine of", "|lang=ar")

# Should we match a single head to a given inflection? If so,
# return a number indicating which head. If not, return None and
# we iterate over all heads.
def should_match_head(heads, inflindex, originfl, originfltr, is_plural):
  headnv = remove_diacritics(heads[0][0])
  # Special cases
  if headnv == u"مدية":
    if inflindex < len(heads):
      return inflindex
    else:
      return 0
  if headnv in [u"بنية"]:
    assert inflindex < len(heads)
    return inflindex
  if headnv in [u"عرس"]:
    return None
  for i in xrange(len(heads)):
    head, headtr = heads[i]
    head = reorder_shadda(head)
    originfl = reorder_shadda(originfl)
    for suffix in (is_plural and [UUN, UUNA, AAT, AATUN, AWN, AWNA] or [AH]):
      if head + suffix == originfl:
        return i
      if re.sub(AH + "$", "", head) + suffix == originfl:
        return i
      # E.g. بَبَغَاء plural بَبَغَاوَات
      if re.sub(HAMZA + "$", W, head) + suffix == originfl:
        return i
  return None

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
    is_plural, createfn, inflectfn=None):
  if not inflectfn:
    inflectfn = default_inflection
  if type(tempname) is not list:
    tempname = [tempname]
  for cat in [u"Arabic %ss" % pos.lower()]:
    for page, index in blib.cat_articles(cat, startFrom, upTo):
      for template in blib.parse(page).filter_templates():
        if template.name in tempname:
          # Get first head and list of heads
          heads = []
          lemma = getparam(template, "1")
          lemmatr = getparam(template, "tr")
          # Handle blank head; use page title
          if lemma == "":
            lemma = page.title()
            msg("Page %s %s(lemma): blank head in template %s (tr=%s)" % (
              index, remove_diacritics(lemma), template.name, lemmatr))
          heads.append([lemma, lemmatr])
          i = 2
          while True:
            head = getparam(template, "head" + str(i))
            headtr = getparam(template, "tr" + str(i))
            if not head:
              break
            heads.append([head, headtr])
            i += 1

          # Figure out how many inflection entries (we don't get the list
          # of entries here because the entries might be generated based
          # on the head)
          numinfls = 0
          infl = getparam(template, param)
          infltr = getparam(template, param + "tr")
          infl, infltr = inflectfn(infl, infltr, lemma, lemmatr,
              template, param)
          i = 2
          while infl:
            numinfls += 1
            infl = getparam(template, param + str(i))
            infltr = getparam(template, param + str(i) + "tr")
            infl, infltr = inflectfn(infl, infltr, lemma, lemmatr,
                template, param + str(i))
            i += 1

          if len(heads) > 1 and numinfls > 1:
            msg("Page %s %s(lemma): WARNING: More than one head and inflection: %s" % (
              index, remove_diacritics(heads[0][0]), unicode(template)))

          for i in xrange(numinfls):
            if i == 0:
              originfl = getparam(template, param)
              originfltr = getparam(template, param + "tr")
            else:
              originfl = getparam(template, param + str(i + 1))
              originfltr = getparam(template, param + str(i + 1) + "tr")
            headind = should_match_head(heads, i, originfl, originfltr,
                is_plural)
            if headind is not None:
              head, headtr = heads[headind]
              infl, infltr = inflectfn(originfl, originfltr, head, headtr,
                  template, param)
              if infl:
                if len(heads) > 1 and numinfls > 1:
                  msg("Page %s %s: Using head#%s %s%s as lemma for inflection %s%s" % (
                      index, remove_diacritics(infl), headind + 1, head,
                      headtr and " (tr=%s)" % headtr or "", infl,
                      infltr and " (tr=%s)" % infltr or ""))
                createfn(save, index, infl, infltr, head, headtr, template,
                    pos)
            else:
              if len(heads) > 1 and numinfls > 1:
                msg("Page %s %s: Looping over all heads for inflection %s%s" % (
                    index, remove_diacritics(infl), originfl or "(empty)",
                    originfltr and " (tr=%s)" % originfltr or ""))
              for head, headtr in heads:
                infl, infltr = inflectfn(originfl, originfltr, head, headtr,
                    template, param)
                if infl:
                  createfn(save, index, infl, infltr, head, headtr, template,
                      pos)

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
      True, create_noun_plural if pos == "Noun" else create_adj_plural,
      pl_inflection)

def create_feminines(save, pos, tempname, startFrom, upTo):
  return create_inflection_entries(save, pos, tempname, "f", startFrom, upTo,
      False, create_noun_feminine if pos == "Noun" else create_adj_feminine,
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
      if personal:
        gender = "np"
      else:
        gender = ""
    elif personal:
      gender += "-np"
    genderparam = [("2", gender)] if gender else []

    defparam = "|form=%s%s" % (form, uncertain and "|uncertain=yes" or "")
    create_inflection_entry(save, index, vn, None, dicform, None, "Noun",
      "verbal noun", "dictionary form", "ar-noun", genderparam,
      "ar-verbal noun of", defparam, gender=gender and [gender] or [])

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
      "ar-%s-participle" % apshort, [("2", form)],
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

# List of all verb form classes
all_form_classes = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX",
    "X", "XI", "XII", "XIII", "XIV", "XV", "Iq", "IIq", "IIIq", "IVq"]
form_classes_to_number = dict(
    zip(all_form_classes, xrange(1, len(all_form_classes) + 1)))

# List of all person/number/gender combinations, using the ID's in
# {{ar-verb-part-all|...}}
all_persons = [
    "1s", "2sm", "2sf", "3sm", "3sf",
    "2d", "3dm", "3df",
    "1p", "2pm", "2pf", "3pm", "3pf"
    ]
# Corresponding part of {{inflection of|...}} template, e.g. 3|m|s for 3sm
all_person_infls = [re.sub("([sdpmf])", r"|\1",
  re.sub("([sdp])([mf])", r"\2\1", x))
  for x in all_persons]
persons_infl_entry = dict(zip(all_persons, all_person_infls))
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
# PAGE is the page of the lemma, and TEMPLATE is the {{ar-conj|...}} template
# indicating the lemma's conjugation. DICFORMS is an array of possible
# vocalized forms of the lemma, PASSIVE is the value of the 'passive' property
# of the lemma. VOICE is either "active" or "passive", and PERSON and TENSE
# indicate the particular person/number/gender/tense/mood combination, using
# the codes passed to {{ar-verb-part-all|...}}. We refuse to do combinations
# not compatible with the value of PASSIVE, and we refuse to do the
# dictionary form (3sm-perf, or 3sm-ps-perf for passive-only verbs).
# We assume that impossible parts (passive and non-2nd-person imperatives)
# have already been filtered.
def create_verb_part(save, index, page, template, dicforms, passive,
    voice, person, tense):
  if voice == "active" and not has_active_form(passive):
    return
  if voice == "passive" and not has_passive_form(passive, person):
    return
  dicformsnv = [remove_diacritics(x) for x in dicforms]
  distinct_dicformsnv = list(set(dicformsnv))
  # This should be subsumed below.
  # Refuse to do the dictionary form.
  #if person == "3sm" and tense == "perf" and (voice == "active" or
  #    voice == "passive" and not has_active_form(passive)):
  #  return
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
      # Refuse to do any part that will go on any dictionary-form page.
      # This typically includes 3sm active and passive. Checking all
      # dictionary-form pages ensures that we don't end up with 3sm active
      # tarādda going on the page for tarādada (alternative dictionary form
      # of the same verb) or vice-versa.
      if remove_diacritics(part) in distinct_dicformsnv:
        msg("Page %s %s: Skipping form %s, would go on same page as dictionary form(s) %s" % (
          index, remove_diacritics(part), part, ",".join(dicforms)))
        if len(distinct_dicformsnv) > 1:
          msg("Page %s %s: NOTE: Skipping form %s when there are multiple dictionary-form pages %s" % (
            index, remove_diacritics(part), part, ",".join(distinct_dicformsnv)))

      else:
        for dicform in dicforms:
          create_inflection_entry(save, index, part, None, dicform, None,
            "Verb", "verb part %s" % partid, "dictionary form",
            "ar-verb-form", [("2", form)],
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
    else:
      raise ValueError("Expected PERSON-TENSE or PERSON-ps-TENSE or PERSON-all-TENSE, but found '%s'"
          % partspec)
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
        dicforms = get_dicform_all(page, template)
        for voice, person, tense in parts_desired:
          create_verb_part(save, index, page, template, dicforms, passive,
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
      "Adjective", "elative", "positive", "ar-adj", [], "elative of",
      "|lang=ar", entrytext=defn_text)
    for arpositive in arpositives:
      def add_elative_param(page, index, text):
        pagetitle = page.title()
        def pagemsg(text):
          msg("Page %s %s: %s" % (index, pagetitle, text))
        if not page.exists():
          pagemsg("WARNING, positive %s not found for elative %s (page nonexistent)" % (
            arpositive, elative))
          return None, "skipped positive %s elative %s" % (arpositive, elative)
        found_positive = False
        for template in text.filter_templates():
          if template.name in ["ar-adj", "ar-adj-sound", "ar-adj-in", "ar-adj-an"]:
            if reorder_shadda(getparam(template, "1")) != reorder_shadda(arpositive):
              pagemsg("Skipping, found adjective template with wrong positive, expecting %s: %s" % (
                  arpositive, unicode(template)))
              continue
            found_positive = True
            existingel = getparam(template, "el")
            if existingel:
              if reorder_shadda(existingel) == reorder_shadda(elative):
                pagemsg("Skipping template with elative already in it: %s" % (
                    unicode(template)))
              else:
                pagemsg("Strange, template has elative already in it but not expected %s: %s" % (
                    elative, unicode(template)))
            else:
              pagemsg("Adding elative %s to template: %s" % (
                elative, unicode(template)))
              addparam(template, "el", elative)
        if not found_positive:
          pagemsg("WARNING, positive %s not found for elative %s (page exists but couldn't find appropriate template)" % (
            arpositive, elative))
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
pa.add_argument("--personal", action='store_true',
    help="Predict and store personal/non-personalness when possible")

params = pa.parse_args()
startFrom, upTo = blib.parse_start_end(params.start, params.end)
personal = params.personal

if params.plural:
  create_plurals(params.save, "Noun", ["ar-noun", "ar-noun-nisba"],
      startFrom, upTo)
  create_plurals(params.save, "Adjective",
      ["ar-adj", "ar-nisba", "ar-adj-sound", "ar-adj-in", "ar-adj-an"],
      startFrom, upTo)

if params.feminine:
  # FIXME: Feminine noun creation not tested yet
  create_feminines(params.save, "Noun", ["ar-noun", "ar-noun-nisba"],
      startFrom, upTo)
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
