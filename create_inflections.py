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
ALIF = u"ا"
ALIF_WASLA = u"ٱ"
ALIF_ANY = "[" + ALIF + ALIF_WASLA + "]"

UUN = U + u"ون"
UUNA = UUN + A

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
# "ar-noun-pl", "ar-adj-pl" or "ar-adj-fem"). DEFTEMP is the definitional
# template that points to the base form (e.g. "plural of",
# "masculine plural of" or "feminine of"). Optional DEFTEMP_PARAM is a
# parameter or parameters to add to the created DEFTEMP template, and
# should be either empty or of the form "|foo=bar" (or e.g. "|foo=bar|baz=bat"
# for more than one parameter); default is "|lang=ar".
def create_inflection_entry(save, index, inflection, infltr, lemma, lemmatr, pos,
    infltype, lemmatype, infltemp, deftemp, deftemp_param = "|lang=ar"):

  # Remove any links that may esp. appear in the lemma, since the
  # vocalized version of the lemma as it appears in the lemma's headword
  # template often has links in it when the form is multiword.
  lemma = remove_links(lemma)
  inflection = remove_links(inflection)

  # Fetch pagename, create pagemsg() fn to output msg with page name included
  pagename = remove_diacritics(inflection)
  def pagemsg(text, simple = False):
    if simple:
      msg("Page %s (%s): %s" % (pagename, index, text))
    else:
      msg("Page %s (%s): %s: %s %s%s, %s %s%s" % (pagename, index, text,
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
    if word[0] == ALIF_WASLA:
      mymsg("Changing alif wasla to plain alif for %s %s" % (wordtype, word))
      word = ALIF + word[1:]
    return word

  is_participle = infltype.endswith("participle")
  is_vn = infltype == "verbal noun"
  is_verb_part = pos == "Verb"
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
      lemma_inflection_counts[li_no_vowels], lemmatype, lemma_no_vowels, infltype,
      infl_no_vowels))
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
  new_headword_template = "{{%s|%s%s}}" % (infltemp, inflection,
    "|tr=%s" % infltr if infltr else "")
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
                notes.append("Converted 'Verbal noun' section header to 'Noun'")
              parsed = blib.parse_text(subsections[j])
              for t in parsed.filter_templates():
                if t.name == "ar-verbal noun":
                  t.name = "ar-noun"
                  pagemsg("Converting 'ar-verbal noun' template into 'ar-noun'")
                  notes.append("Converted 'ar-verbal noun' template into 'ar-noun'")
              subsections[j] = unicode(parsed)
              sections[i] = ''.join(subsections)

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
                  noremove=is_verb_part)
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
            # consonants.
            infl_headword_templates = [t for t in parsed.filter_templates()
                if t.name == infltemp and compare_param(t, "1", inflection)]
            defn_templates = [t for t in parsed.filter_templates()
                if t.name == deftemp and compare_param(t, "1", lemma)]
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

              # Make sure there's exactly one headword template.
              if len(infl_headword_templates) > 1:
                pagemsg("WARNING: Found multiple inflection headword templates for %s; taking no action"
                    % (infltype))
                break
              infl_headword_template = infl_headword_templates[0]

              # For verb forms check for an exactly matching definitional
              # template; if not, insert one at end of definition.
              if is_verb_part:
                for d_t in defn_templates:
                  if (reorder_shadda(unicode(d_t)) ==
                      reorder_shadda(new_defn_template)):
                    pagemsg("Found exact-matching definitional template for %s; taking no action"
                        % (infltype))
                    break
                else: # No break
                  subsections[j] = unicode(parsed)
                  subsections[j] = re.sub(r"^(.*\n#[^\n]*\n)",
                      r"\1%s\n" % new_defn_template, subsections[j], 1, re.S)
                  sections[i] = ''.join(subsections)
                  pagemsg("Adding new definitional template to existing defn for pos = %s" % (pos))
                  comment = "Add new definitional template to existing defn: %s %s, %s %s, pos=%s" % (
                      infltype, inflection, lemmatype, lemma, pos)
                break

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
                    "# {{%s|%s}}\n#" % (deftemp, lemma),
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
                if len(infl_headword_templates) > 1:
                  pagemsg("WARNING: Found multiple inflection headword templates for %s; taking no action"
                      % (infltype))
                  break
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

        else: # else of for loop over subsections, i.e. no break out of loop
          # At this point we couldn't find an existing subsection with
          # matching POS and appropriate headword template whose head matches
          # the the inflected form.
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
            sections[i] += "\n===Etymology %s===\n\n" % j + newposl4
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
                re.sub("^==(.*?)==$", r"===\1===", sections[i], 0, re.M) +
                "\n===Etymology 2===\n\n" + newposl4)
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
      # Make sure there are two trailing newlines
      if sections[-1].endswith("\n\n"):
        pass
      elif sections[-1].endswith("\n"):
        sections[-1] += "\n"
      else:
        sections[-1] += "\n\n"
      sections += ["----\n\n", newsection]

    # End of loop over sections in existing page; rejoin sections
    newtext = pagehead + ''.join(sections) + pagetail
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
      "plural", "singular", "ar-noun-pl", "plural of")

def create_adj_plural(save, index, inflection, infltr, lemma, lemmatr, pos):
  create_inflection_entry(save, index, inflection, infltr, lemma, lemmatr, pos,
      "plural", "singular", "ar-adj-pl", "masculine plural of")

def create_noun_feminine_entry(save, index, inflection, infltr, lemma, lemmatr, pos):
  create_inflection_entry(save, index, inflection, infltr, lemma, lemmatr, pos,
      "feminine", "masculine", None, "feminine of")

def create_adj_feminine_entry(save, index, inflection, infltr, lemma, lemmatr, pos):
  create_inflection_entry(save, index, inflection, infltr, lemma, lemmatr, pos,
      "feminine", "masculine", "ar-adj-fem", "feminine of")

def create_inflection_entries(save, pos, tempname, startFrom, upTo, createfn,
    param):
  for cat in [u"Arabic %ss" % pos.lower()]:
    for page, index in blib.cat_articles(cat, startFrom, upTo,
        includeindex=True):
      for template in blib.parse(page).filter_templates():
        if template.name == tempname:
          lemma = blib.getparam(template, "1")
          lemmatr = blib.getparam(template, "tr")
          # Handle blank head; use page title
          if lemma == "":
            lemma = page.title()
            msg("Page %s: blank head in template %s (tr=%s)" % (lemma, tempname, lemmatr))
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
      unicode(template).replace("{{ar-conj|", "{{%s|" % prefix))

def get_dicform(page, template):
  return get_part_prop(page, template, "ar-past3sm")

def get_passive(page, template):
  return get_part_prop(page, template, "ar-verb-prop|passive")

# For a given value of passive= (yes, impers, no, only, only-impers), does
# the verb have an active form?
def has_active_form(passive):
  assert(passive in ["yes", "impers", "no", "only", "only-impers"])
  return passive in ["yes", "impers", "no"]

# For a given value of passive= (yes, impers, no, only, only-impers), does
# the verb have a passive form?
def has_passive_form(passive):
  assert(passive in ["yes", "impers", "no", "only", "only-impers"])
  return passive != "no"

# Create a verbal noun entry, either creating a new page or adding to an
# existing page. Do nothing if entry is already present. SAVE, INDEX are as in
# create_inflection_entry(). VN is the vocalized verbal noun; VERBPAGE is the
# Page object representing the dictionary-form verb of this verbal noun;
# TEMPLATE is the conjugation template for the verb, i.e. {{ar-conj|...}};
# UNCERTAIN is true if the verbal noun is uncertain (indicated with a ? at
# the end of the vn=... parameter in the conjugation template).
def create_verbal_noun(save, index, vn, page, template, uncertain):
  dicform = get_dicform(page, template)

  create_inflection_entry(save, index, vn, None, dicform, None, "Noun",
    "verbal noun", "dictionary form", "ar-noun", "ar-verbal noun of",
    uncertain and "|uncertain=yes" or "")

def create_verbal_nouns(save, startFrom, upTo):
  for page, index in blib.references("Template:ar-conj", startFrom, upTo,
      includeindex=True):
    for template in blib.parse(page).filter_templates():
      if template.name == "ar-conj":
        vnvalue = blib.getparam(template, "vn")
        uncertain = False
        if vnvalue.endswith("?"):
          vnvalue = vnvalue[:-1]
          uncertain = True
        if not vnvalue:
          if not re.match("^[1I](-|$)", blib.getparam(template, "1")):
            # Augmented verb. Fetch auto-generated verbal noun(s).
            vnvalue = get_part_prop(page, template, "ar-verb-part-all|vn")
          else:
            continue
        vns = re.split(u"[,،]", vnvalue)
        for vn in vns:
          create_verbal_noun(save, index, vn, page, template, uncertain)

def create_participle(save, index, part, page, template, actpass):
  dicform = get_dicform(page, template)

  create_inflection_entry(save, index, part, None, dicform, None, "Participle",
    "%s participle" % actpass, "dictionary form", "ar-%s participle" % actpass,
    "ar-%s participle of", "")

def create_participles(save, startFrom, upTo):
  for page, index in blib.references("Template:ar-conj", startFrom, upTo,
      includeindex=True):
    for template in blib.parse(page).filter_templates():
      if template.name == "ar-conj":
        passive = get_passive(page, template)
        if has_active_form(passive):
          apvalue = get_part_prop(page, template, "ar-verb-part-all|ap")
          if apvalue:
            aps = re.split(",", apvalue)
            for ap in aps:
              create_participle(save, index, ap, page, template, "active")
        if has_passive_form(passive):
          ppvalue = get_part_prop(page, template, "ar-verb-part-all|pp")
          if ppvalue:
            pps = re.split(",", ppvalue)
            for pp in pps:
              create_participle(save, index, pp, page, template, "passive")

# List of all person/number/gender combinations, using the ID's in
# {{ar-verb-part-all|...}}
persons = [
    "1s", "2sm", "2sf", "3sm", "3sf",
    "2d", "3dm", "3df",
    "1p", "2pm", "2pf", "3pm", "3pf"
    ]
# Corresponding part of {{inflection of|...}} template, e.g. 3|s|m for 3sm
persons_infl_entry = dict([x, re.sub("([sdpmf])", r"|\1", x)] for x in persons)
# List of all tense/mood combinations, using the ID's in
# {{ar-verb-part-all|...}}
tenses = ["perf", "impf", "subj", "juss"]
# Corresponding part of {{inflection of|...}} template, with %s where
# "active" or "passive" goes
tenses_infl_entry = {
    "perf":"past|%s",
    "impf":"non-past|%s|ind",
    "subj":"non-past|%s|sub",
    "juss":"non-past|%s|juss"
    }

# Create a single verb part. SAVE, INDEX are as in create_inflection_entry().
# PAGE is the page of the lemma, and TEMPLATE is the {{ar-conj|...}}
# template indicating the lemma's conjugation. DICFORM is the vocalized form
# of the lemma, ACTPASS is either "active" or "passive", and PERSON and TENSE
# indicate the particular person/number/gender/tense/mood combination, using
# the codes passed to {{ar-verb-part-all|...}}.
def create_one_verb_part(save, index, page, template, dicform, actpass, person,
    tense):
  infl_person = persons_infl_entry[person]
  infl_tense = tenses_infl_entry[tense] % actpass
  partid = actpass == ("active" and "%s-%s" % (person, tense) or
      "%s-ps-%s" % (person, tense))
  value = get_part_prop(page, template, "ar-verb-part-all|%s" % partid)
  if value:
    parts = re.split(",", value)
    for part in parts:
      create_inflection_entry(save, index, part, None, dicform, None, "Verb",
        partid, "dictionary form", "ar-verb form",
        "inflection of", "||lang=ar|%s|%s" % (infl_person, infl_tense))

# Create the active and passive versions (as appropriate) of a single verb
# part. SAVE, INDEX are as in create_inflection_entry(). PAGE is the page of
# the lemma, and TEMPLATE is the {{ar-conj|...}} template indicating the
# lemma's conjugation. DICFORM is the vocalized form of the lemma. PASSIVE is
# the value of the 'passive' property as returned by
# {{ar-verb-prop|passive|...}}. PERSON and TENSE indicate the particular
# person/number/gender/tense/mood combination, using the codes passed to
# {{ar-verb-part-all|...}}.
def create_verb_part(save, index, page, template, dicform, passive, person,
    tense):
  if has_active_form(passive):
    create_one_verb_part(save, index, page, template, dicform, "active", person,
        tense)
  if has_passive_form(passive):
    create_one_verb_part(save, index, page, template, dicform, "passive", person,
        tense)

# Create all required verb parts for all verbs. If ALLFORMS is true, do *all*
# verb parts (other than 3sm-perf, the dictionary form); otherwise, only do
# only 3sm-impf, the corresponding non-past dictionary form. SAVE, INDEX are as
# in create_inflection_entry(). STARTFROM and UPTO, if not None, delimit the
# range of pages to process.
def create_verb_parts(save, startFrom, upTo, allforms=False):
  for page, index in blib.references("Template:ar-conj", startFrom, upTo,
      includeindex=True):
    for template in blib.parse(page).filter_templates():
      if template.name == "ar-conj":
        dicform = get_dicform(page, template)
        passive = get_passive(page, template)
        if allforms:
          for person in persons:
            for tense in tenses:
              if not (person == "3sm" and tense == "perf"):
                create_verb_part(save, index, page, template, dicform, passive,
                    person, tense)
        else:
          create_verb_part(save, index, page, template, dicform, passive,
            "3sm", "impf")

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
    help="Do non-past dictionary-form inflections")
pa.add_argument("--all-verb-part", action='store_true',
    help="Do all verb part inflections")

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
if params.non_past:
  create_verb_parts(params.save, startFrom, upTo, allforms=False)
if params.all_verb_part:
  create_verb_parts(params.save, startFrom, upTo, allforms=True)