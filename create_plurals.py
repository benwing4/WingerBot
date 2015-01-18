#!/usr/bin/env python
#coding: utf-8

#    create_plurals.py is free software: you can redistribute it and/or modify
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

singular_plural_counts = {}

# Create or insert a section describing the plural or similar inflection
# of a given word. PLURAL is the vocalized lemma of the inflection (e.g.
# the plural or feminine form); SINGULAR is the vocalized lemma of the base
# form (e.g. the singular or masculine); PLTR and SINGTR are the associated
# manual transliterations (if any). POS is the part of speech of the word
# (capitalized, e.g. "Noun"). Only save the changed page if SAVE is true.
# PLWORD is e.g. "plural" or "feminine", and is used in messages and to
# check specifically for plural in some special-case code. SINGWORD is
# e.g. "singular" or "masculine" and is used in messages. PLTEMP is the
# headword template for the inflected-word entry (e.g. "ar-noun-pl",
# "ar-adj-pl" or "ar-adj-fem"). SINGTEMP is the definitional template that
# points to the base form (e.g. "plural of", "masculine plural of" or
# "feminine of"). Optional SINGTEMP_PARAM is a parameter or parameters to
# add to the created SINGTEMP template, and should be either empty or of
# the form "|foo=bar" (or e.g. "|foo=bar|baz=bat" for more than one
# parameter); default is "|lang=ar".
def create_inflection(save, plural, pltr, singular, singtr, pos,
    plword, singword, pltemp, singtemp, singtemp_param = "|lang=ar"):

  # Remove any links that may esp. appear in the base form, since the
  # vocalized version of the base form as it appears in the headword
  # template often has links in it when the form is multiword.
  singular = remove_links(singular)
  plural = remove_links(plural)

  # Fetch pagename, create pagemsg() fn to output msg with page name included
  pagename = remove_diacritics(plural)
  def pagemsg(text):
    msg("Page %s: %s" % (pagename, text))

  # Remove trailing -un/-u i3rab from inflected and base form

  def remove_i3rab(singpl, word, nowarn=False):
    def mymsg(text):
      if not nowarn:
        pagemsg(text)
    word = reorder_shadda(word)
    if word.endswith(UN):
      mymsg("Removing i3rab (UN) from %s %s" % (singpl, word))
      return re.sub(UN + "$", "", word)
    if word.endswith(U):
      mymsg("Removing i3rab (U) from %s %s" % (singpl, word))
      return re.sub(U + "$", "", word)
    if word and word[-1] in [A, I, U, AN]:
      mymsg("FIXME: Strange diacritic at end of %s %s" % (singpl, word))
    if word[0] == ALIF_WASLA:
      mymsg("Changing alif wasla to plain alif for %s %s" % (singpl, word))
      word = ALIF + word[1:]
    return word

  singular = remove_i3rab(singword, singular)
  plural = remove_i3rab(plword, plural)

  if plural == "-":
    pagemsg("Not creating %s entry - for %s %s%s" % (
      plword, singword, singular, " (%s)" % singtr if singtr else ""))
    return

  # Prepare to create page
  pagemsg("Creating %s entry %s%s for %s %s%s" % (
    plword, plural, " (%s)" % pltr if pltr else "",
    singword, singular, " (%s)" % singtr if singtr else ""))
  pl_no_vowels = pagename
  sing_no_vowels = remove_diacritics(singular)
  page = pywikibot.Page(site, pagename)

  # For singular قطعة and plural قطع, three different possible
  # sets of vocalizations. For this case, require that the
  # existing versions match exactly, rather than matching with
  # removed diacritics.
  must_match_exactly = plword == "plural" and pl_no_vowels == u"قطع" and sing_no_vowels == u"قطعة"

  sp_no_vowels = (sing_no_vowels, pl_no_vowels)
  singular_plural_counts[sp_no_vowels] = \
      singular_plural_counts.get(sp_no_vowels, 0) + 1
  if singular_plural_counts[sp_no_vowels] > 1:
    pagemsg("Found multiple (%s) vocalized possibilities for %s %s, %s %s" % (
      singular_plural_counts[sp_no_vowels], singword, sing_no_vowels, plword,
      pl_no_vowels))
    must_match_exactly = True
  if plword == "verbal noun":
    must_match_exactly = True

  # Prepare parts of new entry to insert
  newposbody = u"""{{%s|%s%s%s}}

# {{%s|%s%s%s}}
""" % (pltemp, plural,
    "", #"|m-p" if pos == "Adjective" and plword == "plural" else "",
    "|tr=%s" % pltr if pltr else "",
    singtemp, singular,
    "|tr=%s" % singtr if singtr else "",
    singtemp_param)
  newpos = "===%s===\n" % pos + newposbody
  newposl4 = "====%s====\n" % pos + newposbody
  newsection = "==Arabic==\n\n" + newpos

  comment = None
  notes = []
  existing_text = page.text

  if not page.exists():
    # Page doesn't exist. Create it.
    pagemsg("creating")
    comment = "Create page for Arabic %s %s of %s, pos=%s" % (
        plword, plural, singular, pos)
    page.text = newsection
    if verbose:
      pagemsg("New text is [[%s]]" % page.text)
  else: # Page does exist
    # Split off interwiki links at end
    m = re.match(r"^(.*?\n)(\n*(\[\[[a-z0-9_\-]+:[^\]]+\]\]\n*)*)$",
        page.text, re.S)
    if m:
      body = m.group(1)
      tail = m.group(2)
    else:
      body = page.text
      tail = ""

    # Split into sections
    splitsections = re.split("(^==[^=\n]+==\n)", body, 0, re.M)
    # Extract off head and recombine section headers with following text
    head = splitsections[0]
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

        # Go through each subsection in turn, looking for subsection
        # matching the POS
        subsections = re.split("(^===+[^=\n]+===+\n)", sections[i], 0, re.M)
        for j in xrange(len(subsections)):
          match_pos = False
          vn_match_noun = False
          if j > 0 and (j % 2) == 0:
            if re.match("^===+%s===+\n" % pos, subsections[j - 1]):
              match_pos = True
            if plword == "verbal noun" and re.match("^===+Noun===+\n" % pos,
                subsections[j - 1]):
              vn_match_noun = True

          # Found a POS match
          if match_pos or vn_match_noun:
            parsed = blib.parse_text(subsections[j])

            def compare_param(template, param, value):
              # In place of unknown we should put plword or singword but it
              # doesn't matter because of nowarn.
              paramval = remove_i3rab("unknown",
                  blib.getparam(template, param), nowarn=True)
              if must_match_exactly:
                return paramval == value
              else:
                return remove_diacritics(paramval) == remove_diacritics(value)

            def check_remove_i3rab(template, sgplword):
              # Check for i3rab in existing sg or pl and remove it if so
              existing = blib.getparam(template, "1")
              existing_no_i3rab = remove_i3rab(sgplword, existing)
              if existing != existing_no_i3rab:
                notes.append("removed %s i3rab" % sgplword)
                template.add("1", existing_no_i3rab)
                existing_tr = blib.getparam(template, "tr")
                if existing_tr:
                  pagemsg("WARNING: Removed i3rab from existing %s %s and manual translit %s exists" %
                      (sgplword, existing, existing_tr))
                existing = existing_no_i3rab
              return existing

            # Find the inflection headword (e.g. 'ar-noun-pl') and
            # inflection-of (e.g. 'plural of') templates. We require that
            # they match, either exactly (apart from i3rab) or only in the
            # consonants.
            infl_headword_templates = [t for t in parsed.filter_templates()
                if t.name == pltemp and compare_param(t, "1", plural)]
            infl_of_templates = [t for t in parsed.filter_templates()
                if t.name == singtemp and compare_param(t, "1", singular)]
            # Special-case handling for actual noun plurals. We expect an
            # ar-noun but if we encounter an ar-coll-noun with the plural as
            # the (collective) head and the singular as the singulative, we
            # output a message and skip. FIXME: Why?
            if plword == "plural" and pos == "Noun":
              headword_collective_templates = [t for t in parsed.filter_templates()
                  if t.name == "ar-coll-noun" and compare_param(t, "1", plural)
                  and compare_param(t, "sing", singular)]
              if headword_collective_templates:
                pagemsg("exists and has Arabic section and found collective noun with %s %s already in it; taking no action"
                    % (plword, plural))
                break

            def vn_noun_check():
              if vn_match_noun:
                pagemsg("WARNING: Found match for %s %s but in ===Noun=== section rather than ===Verbal noun==="
                    % (plword, plural))

            # We found both templates and their heads matched; inflection
            # entry is already present.
            if infl_of_templates and infl_headword_templates:
              pagemsg("exists and has Arabic section and found %s %s already in it"
                  % (plword, plural))

              vn_noun_check()

              # Make sure there's exactly one.
              if len(infl_of_templates) > 1:
                pagemsg("found multiple inflection-of templates for %s %s; taking no action"
                    % (plword, plural))
                break
              if len(infl_headword_templates) > 1:
                pagemsg("found multiple inflection headword templates for %s %s; taking no action"
                    % (plword, plural))
                break
              infl_of_template = infl_of_templates[0]
              infl_headword_template = infl_headword_templates[0]

              # Check for i3rab in existing pl and remove it if so
              existing_pl = check_remove_i3rab(infl_headword_template, plword)

              # Check for i3rab in existing sing and remove it if so
              existing_sing = check_remove_i3rab(infl_of_template, singword)

              # Replace existing pl with new one
              if len(plural) > len(existing_pl):
                pagemsg("updating existing %s %s with %s" %
                    (pltemp, existing_pl, plural))
                infl_headword_template.add("1", plural)
                if pltr:
                  infl_headword_template.add("tr", pltr)
              #if pos == "Adjective" and plword == "plural":
              #  infl_headword_template.add("2", "m-p")

              # Replace existing sg with new one
              if len(singular) > len(existing_sing):
                pagemsg("updating existing '%s' %s with %s" %
                    (singtemp, existing_sing, singular))
                infl_of_template.add("1", singular)
                if singtr:
                  infl_of_template.add("tr", singtr)

              subsections[j] = unicode(parsed)
              sections[i] = ''.join(subsections)
              comment = "Update Arabic with better vocalized versions: %s %s, %s %s, pos=%s" % (
                  plword, plural, singword, singular, pos)
              break

            elif plword == "verbal noun":
              # Found inflection headword template. Wrap definition with
              # a {{ar-verbal noun of}} declaration.
              if infl_headword_templates:
                if len(infl_headword_templates) > 1:
                  pagemsg("found multiple inflection headword templates for %s %s; taking no action"
                      % (plword, plural))
                  break
                infl_headword_template = infl_headword_templates[0]

                # Check for i3rab in existing pl and remove it if so
                check_remove_i3rab(infl_headword_template, plword)

                # Now actually wrap with {{ar-verbal noun of}}.
                subsections[j] = unicode(parsed)
                subsections[j] = re.sub("^#", r"##", subsections[j], 0, re.M)
                subsections[j] = re.sub("^##",
                    "# {{ar-verbal noun of|%s}}:\n##" % singword,
                    subsections[j], 1, re.M)
                sections[i] = ''.join(subsections)
                comment = "Wrap existing defn with {{ar-verbal noun of}}: %s %s, %s %s" % (
                    plword, plural, singword, singular)
                break

              else:
                noun_headword_templates = [t for t in parsed.filter_templates()
                    if t.name == "ar-noun" and compare_param(t, "1", plural)]
                if noun_headword_templates:
                  pagemsg("WARNING: found ar-noun matching %s %s" %
                      (plword, plural))
                  # FIXME: Should we break here?

        else: # else of for loop, i.e. no break out of loop
          pagemsg("exists and has Arabic section, appending to end of section")
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
            pagemsg("found multiple etymologies, adding new section \"Etymology %s\"" % (j))
            comment = "Append entry (Etymology %s) for %s %s of %s, pos=%s in existing Arabic section" % (
              j, plword, plural, singular, pos)
            sections[i] += "\n===Etymology %s===\n\n" % j + newposl4
          else:
            pagemsg("wrapping existing text in \"Etymology 1\" and adding \"Etymology 2\"")
            comment = "Wrap existing Arabic section in Etymology 1, append entry (Etymology 2) for %s %s of %s, pos=%s" % (
                plword, plural, singular, pos)
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
        pagemsg("exists; inserting before %s section" % (m.group(1)))
        comment = "Create Arabic section and entry for %s %s of %s, pos=%s; insert before %s section" % (
            plword, plural, singular, pos, m.group(1))
        sections[i:i] = [newsection, "\n----\n\n"]
        break
    else:
      pagemsg("exists; adding section to end")
      comment = "Create Arabic section and entry for %s %s of %s, pos=%s; append at end" % (
          plword, plural, singular, pos)
      # Make sure there are two trailing newlines
      if sections[-1].endswith("\n\n"):
        pass
      elif sections[-1].endswith("\n"):
        sections[-1] += "\n"
      else:
        sections[-1] += "\n\n"
      sections += ["----\n\n", newsection]
    newtext = head + ''.join(sections) + tail
    if page.text == newtext:
      pagemsg("No change in text")
    elif verbose:
      pagemsg("Replacing [[%s]] with [[%s]]" % (page.text, newtext))
    else:
      pagemsg("Text has changed")
    page.text = newtext
  if comment and page.text != existing_text:
    if notes:
      comment += " (%s)" % '; '.join(notes)
    pagemsg("comment = %s" % comment)
    if save:
      page.save(comment = comment)

def create_noun_plural(save, plural, pltr, singular, singtr, pos):
  return create_inflection(save, plural, pltr, singular, singtr, pos,
      "plural", "singular", "ar-noun-pl", "plural of")

def create_adj_plural(save, plural, pltr, singular, singtr, pos):
  return create_inflection(save, plural, pltr, singular, singtr, pos,
      "plural", "singular", "ar-adj-pl", "masculine plural of")

def create_noun_feminine(save, plural, pltr, singular, singtr, pos):
  return create_inflection(save, plural, pltr, singular, singtr, pos,
      "feminine", "masculine", None, "feminine of")

def create_adj_feminine(save, plural, pltr, singular, singtr, pos):
  return create_inflection(save, plural, pltr, singular, singtr, pos,
      "feminine", "masculine", "ar-adj-fem", "feminine of")

def create_inflections(save, pos, tempname, startFrom, upTo, createfn, param):
  for cat in [u"Arabic %ss" % pos.lower()]:
    for page in blib.cat_articles(cat, startFrom, upTo):
      for template in blib.parse(page).filter_templates():
        if template.name == tempname:
          sing = blib.getparam(template, "1")
          singtr = blib.getparam(template, "tr")
          # Handle blank head; use page title
          if sing == "":
            sing = page.title()
            msg("Page %s: blank head in template %s (tr=%s)" % (sing, tempname, singtr))
          pl = blib.getparam(template, param)
          pltr = blib.getparam(template, param + "tr")
          if pl:
            createfn(save, pl, pltr, sing, singtr, pos)
          i = 2
          while pl:
            pl = blib.getparam(template, param + str(i))
            pltr = blib.getparam(template, param + str(i) + "tr")
            if pl:
              otherhead = blib.getparam(template, "head" + str(i))
              otherheadtr = blib.getparam(template, "tr" + str(i))
              if otherhead:
                msg("Page %s: Using head%s %s (tr=%s) as lemma for %s (tr=%s)" % (
                  sing, i, otherhead, otherheadtr, pl, pltr))
                createfn(save, pl, pltr, otherhead, otherheadtr, pos)
              else:
                createfn(save, pl, pltr, sing, singtr, pos)
            i += 1

def create_plurals(save, pos, tempname, startFrom, upTo):
  return create_inflections(save, pos, tempname, startFrom, upTo,
      create_noun_plural if pos == "Noun" else create_adj_plural, "pl")

def create_feminines(save, pos, tempname, startFrom, upTo):
  return create_inflections(save, pos, tempname, startFrom, upTo,
      create_noun_feminine if pos == "Noun" else create_adj_feminine, "f")

# Create a verbal noun entry, either creating a new page or adding to an
# existing page. Do nothing if entry is already present. Only save changes
# if SAVE is true. VN is the vocalized verbal noun; VERBPAGE is the Page
# object representing the dictionary-form verb of this verbal noun;
# TEMPLATE is the conjugation template for the verb, i.e. {{ar-conj|...}};
# UNCERTAIN is true if the verbal noun is uncertain (indicated with a ? at
# the end of the vn=... parameter in the conjugation template).
def create_verbal_noun(save, vn, page, template, uncertain):
  # Make an expand-template call to convert the conjugation template to
  # the dictionary form. The code here is based on the expand_text()
  # function of the Page object.
  req = pywikibot.data.api.Request(action="expandtemplates",
      text = unicode(template).replace("{{ar-conj|", "{{ar-past3sm|"),
      title = page.title(withSection=False),
      site = page.site)
  dicform = req.submit()["expandtemplates"]["*"]

  return create_inflection(save, vn, None, dicform, None, "Verbal noun",
    "verbal noun", "dictionary form", "ar-verbal noun", "ar-verbal noun of",
    uncertain and "|uncertain=yes" or "")

def create_verbal_nouns(save, startFrom, upTo):
  for page in blib.cat_articles("Arabic verbs", startFrom, upTo):
    for template in blib.parse(page).filter_templates():
      if template.name == "ar-conj":
        vnvalue = blib.getparam(template, "vn")
        uncertain = False
        if vnvalue.endswith("?"):
          vnvalue = vnvalue[:-1]
          uncertain = True
        if not vnvalue:
          continue
        vns = re.split(u"[,،]", vnvalue)
        for vn in vns:
          create_verbal_noun(save, vn, page, template, uncertain)

pa = blib.init_argparser("Create Arabic inflections")
pa.add_argument("-p", "--plural", action='store_true',
    help="Do plural inflections")
pa.add_argument("-f", "--feminine", action='store_true',
    help="Do feminine inflections")
pa.add_argument("--verbal-noun", action='store_true',
    help="Do verbal noun inflections")

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
