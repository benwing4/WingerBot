#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Authors: Benwing; ??? for tr() functions, in Lua

#    grc_translit.py is free software: you can redistribute it and/or modify
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
import unicodedata

from blib import remove_links, msg

# FIXME:
#
# 1. Check case of u"ᾱῦ", whether the PERIS shouldn't be on first vowel.
#    Similarly with ACUTE (and GRAVE?).
# 2. Also check case of Latin Hāídēs. What should it be?

# Accented characters
GRAVE = u"\u0300"      # grave accent = varia
ACUTE = u"\u0301"      # acute accent = oxia, tonos
CIRC = u"\u0302"       # circumflex accent
MAC = u"\u0304"        # macron
BREVE = u"\u0306"      # breve = vrachy
DIA = u"\u0308"        # diaeresis = dialytika
CAR = u"\u030C"        # caron = haček
SMBR = u"\u0313"       # smooth breathing = comma above = psili
ROBR = u"\u0314"       # rough breathing = reversed comma above = dasia
PERIS = u"\u0342"      # perispomeni (circumflex accent)
KORO = u"\u0343"       # koronis (is this used? looks like comma above/psili)
DIATON = u"\u0344"     # dialytika tonos = diaeresis + acute, should not occur
IOBE = u"\u0345"       # iota below = ypogegrammeni

GR_ACC = ("[" + GRAVE + ACUTE + MAC + BREVE + DIA + SMBR + ROBR +
        PERIS + KORO + DIATON + IOBE + "]")
GR_ACC_NO_IOBE = ("[" + GRAVE + ACUTE + MAC + BREVE + DIA + SMBR + ROBR +
        PERIS + KORO + DIATON + "]")
GR_ACC_NO_DIA = ("[" + GRAVE + ACUTE + MAC + BREVE + SMBR + ROBR +
        PERIS + KORO + DIATON + IOBE + "]")
GR_ACC_NO_MB = ("[" + GRAVE + ACUTE + DIA + SMBR + ROBR +
        PERIS + KORO + DIATON + IOBE + "]")
LA_ACC_NO_MB = ("[" + GRAVE + ACUTE + CIRC + DIA + CAR + "]")
ONE_MB = "[" + MAC + BREVE + "]"
MBS = ONE_MB + "+"
MBSOPT = ONE_MB + "*"
RS = "[" + ROBR + SMBR + "]"
RSOPT = RS + "?"

def uniprint(x):
  print x.encode('utf-8')
def uniout(x):
  print x.encode('utf-8'),

def rsub(text, fr, to):
    if type(to) is dict:
        def rsub_replace(m):
            try:
                g = m.group(1)
            except IndexError:
                g = m.group(0)
            if g in to:
                return to[g]
            else:
                return g
        return re.sub(fr, rsub_replace, text)
    else:
        return re.sub(fr, to, text)

def error(text):
    raise RuntimeError(text)

def nfc_form(txt):
    return unicodedata.normalize("NFC", unicode(txt))

def nfd_form(txt):
    return unicodedata.normalize("NFD", unicode(txt))

tt = {
    # Plain vowels
    u"α":"a", u"Α":"A",
    u"ε":"e", u"Ε":"E",
    u"η":"e"+MAC, u"Η":"E"+MAC,
    u"ι":"i", u"Ι":"I",
    u"ο":"o", u"Ο":"O",
    u"ω":"o"+MAC, u"Ω":"O"+MAC,
    u"υ":"u", u"Υ":"U",

    # Iotated vowels
    u"ᾳ":"a"+MAC+"i", u"ᾼ":"A"+MAC+"i",
    u"ῃ":"e"+MAC+"i", u"ῌ":"E"+MAC+"i",
    u"ῳ":"o"+MAC+"i", u"ῼ":"O"+MAC+"i",

    # Consonants
    u"β":u"b", u"Β":u"B",
    u"γ":u"g", u"Γ":u"G",
    u"δ":u"d", u"Δ":u"D",
    u"ζ":u"z", u"Ζ":u"Z",
    u"θ":u"th", u"Θ":u"Th",
    u"κ":u"k", u"Κ":u"K",
    u"λ":u"l", u"Λ":u"L",
    u"μ":u"m", u"Μ":u"M",
    u"ν":u"n", u"Ν":u"N",
    u"ξ":u"ks", u"Ξ":u"Ks",
    u"π":u"p", u"Π":u"P",
    u"ρ":u"r", u"Ρ":u"R",
    u"σ":u"s", u"ς":u"s", u"Σ":u"S",
    u"τ":u"t", u"Τ":u"T",
    u"φ":u"ph", u"Φ":u"Ph",
    u"χ":u"kh", u"Χ":u"Kh",
    u"ψ":u"ps", u"Ψ":u"Ps",

    # Archaic letters
    u"ϝ":u"w", u"Ϝ":u"W",
    u"ϻ":u"s"+ACUTE, u"Ϻ":u"S"+ACUTE,
    u"ϙ":u"q", u"Ϙ":u"Q",
    u"ϡ":u"s"+CAR, u"Ϡ":u"S"+CAR,
    u"\u0377":u"v", u"\u0376":u"V",

    GRAVE:GRAVE,
    ACUTE:ACUTE,
    MAC:MAC,
    BREVE:"",
    DIA:DIA,
    SMBR:"",
    ROBR:"h", # will be canonicalized before uppercase vowel
    PERIS:CIRC,
    KORO:"", # should not occur,
    DIATON:DIA + ACUTE, # should not occur
    IOBE:"i", #should not occur
}

greek_lowercase_vowels_raw = u"αεηιοωυᾳῃῳ"
greek_lowercase_vowels = "[" + greek_lowercase_vowels_raw + "]"
greek_uppercase_vowels_raw = u"ΑΕΗΙΟΩΥᾼῌῼ"
greek_uppercase_vowels = "[" + greek_uppercase_vowels_raw + "]"
greek_vowels = ("[" + greek_lowercase_vowels_raw + greek_uppercase_vowels_raw
        + "]")
# vowels that can be the first part of a diphthong
greek_diphthong_first_vowels = u"[αεηοωΑΕΗΟΩ]"
iotate_vowel = {u"α":u"ᾳ", u"Α":u"ᾼ",
                u"η":u"ῃ", u"Ε":u"ῌ",
                u"ω":u"ῳ", u"Ω":u"ῼ",}

# Transliterates text, which should be a single word or phrase. It should
# include stress marks, which are then preserved in the transliteration.
def tr(text, lang=None, sc=None, msgfun=msg):
    text = remove_links(text)
    text = tr_canonicalize_greek(text)

    text = rsub(text, u"γ([γκξχ])", r"n\1")
    text = rsub(text, u"ρρ", "rrh")

    text = rsub(text, '.', tt)

    # compose accented characters, fix hA and similar
    text = tr_canonicalize_latin(text)

    return text

############################################################################
#                      Transliterate from Latin to Greek                   #
############################################################################

#########       Transliterate with Greek to guide       #########

multi_single_quote_subst = u"\ufff1"

# This dict maps Greek characters to all the Latin characters that
# might correspond to them. The entries can be a string (equivalent
# to a one-entry list) or a list of strings or one-element lists
# containing strings (the latter is equivalent to a string but
# suppresses canonicalization during transliteration; see below). The
# ordering of elements in the list is important insofar as which
# element is first, because the default behavior when canonicalizing
# a transliteration is to substitute any string in the list with the
# first element of the list (this can be suppressed by making an
# element a one-entry list containing a string, as mentioned above).
#
# If the element of a list is a one-element tuple, we canonicalize
# during match-canonicalization but we do not trigger the check for
# multiple possible canonicalizations during self-canonicalization;
# instead we indicate that this character occurs somewhere else and
# should be canonicalized at self-canonicalization according to that
# somewhere-else.
#
# Each string might have multiple characters, to handle things
# like θ=th.

tt_to_greek_matching = {
    # Plain vowels; allow uppercase Greek to match lowercase Latin to
    # handle vowels with rough breathing
    u"α":"a", u"Α":["A","a"],
    u"ε":"e", u"Ε":["E","e"],
    u"η":"e"+MAC, u"Η":["E"+MAC,"e"+MAC],
    u"ι":"i", u"Ι":["I","i"],
    u"ο":"o", u"Ο":["O","o"],
    u"ω":"o"+MAC, u"Ω":["O"+MAC,"o"+MAC],
    u"υ":"u", u"Υ":["U","u"],

    # Iotated vowels
    u"ᾳ":"a"+MAC+"i", u"ᾼ":["A"+MAC+"i","a"+MAC+"i"],
    u"ῃ":"e"+MAC+"i", u"ῌ":["E"+MAC+"i","e"+MAC+"i"],
    u"ῳ":"o"+MAC+"i", u"ῼ":["O"+MAC+"i","o"+MAC+"i"],

    # Consonants
    u"β":[u"b",u"β"], u"Β":[u"B",u"Β"], # second B is Greek
    # This will match n anywhere against γ and canonicalize to g, which
    # is probably OK because in post-processing we convert gk/gg to nk/ng.
    u"γ":[u"g",u"n",u"ŋ",u"γ"], u"Γ":[u"G",u"Γ"],
    u"δ":[u"d",u"δ"], u"Δ":[u"D",u"Δ"],
    # Handling of ζ/Ζ opposite zd/Zd is special-cased in
    # check_unmatching_rh_zd().
    u"ζ":u"z", u"Ζ":u"Z",
    u"θ":[u"th",u"θ"], u"Θ":[u"Th",u"Θ"],
    u"κ":[u"k",u"κ"], u"Κ":u"K",
    u"λ":u"l", u"Λ":u"L",
    u"μ":u"m", u"Μ":u"M",
    u"ν":u"n", u"Ν":u"N",
    u"ξ":[u"ks",u"x",u"ξ"], u"Ξ":[u"Ks",u"X",u"Ξ"],
    u"π":u"p", u"Π":u"P",
    # Handling of ρρ opposite rrh is special-cased in check_unmatching_rh_zd().
    u"ρ":u"r", u"Ρ":u"R",
    u"σ":u"s", u"ς":u"s", u"Σ":u"S",
    u"τ":u"t", u"Τ":u"T",
    u"φ":[u"ph",u"φ"], u"Φ":[u"Ph",u"Φ"],
    u"χ":[u"kh",u"χ",u"ch"], u"Χ":[u"Kh",u"Χ"],
    u"ψ":[u"ps",u"ψ"], u"Ψ":[u"Ps",u"Ψ"],

    # Archaic letters
    u"ϝ":u"w", u"Ϝ":u"W",
    u"ϻ":u"s"+ACUTE, u"Ϻ":u"S"+ACUTE,
    u"ϙ":u"q", u"Ϙ":u"Q",
    u"ϡ":u"s"+CAR, u"Ϡ":u"S"+CAR,
    u"\u0377":u"v", u"\u0376":u"V",

    GRAVE:[GRAVE,""],
    ACUTE:[ACUTE,""],
    MAC:[MAC,""],
    BREVE:"",
    DIA:[DIA,""],
    SMBR:"",
    ROBR:["h","H",""], # will be canonicalized before uppercase vowel
    PERIS:[CIRC,MAC,""],
    #KORO:"", # should not occur,
    #DIATON:DIA + ACUTE, # should not occur
    #IOBE:"i", #should not occur

    # numerals
    u"1":u"1", u"2":u"2", u"3":u"3", u"4":u"4", u"5":u"5",
    u"6":u"6", u"7":u"7", u"8":u"8", u"9":u"9", u"0":u"0",
    # punctuation (leave on separate lines)
    u"?":u"?", # question mark
    u",":u",", # comma
    u";":u";", # semicolon
    u".":u".", # period
    u"!":u"!", # exclamation point
    u"-":u"-", # hyphen/dash
    u"'":u"'", # single quote, for bold/italic
    u" ":u" ",
    u"[":u"",
    u"]":u"",
}

word_interrupting_chars = u"-[]"

build_canonicalize_latin = {}
# x X y Y not on list -- canoned to ks Ks u U
for ch in u"abcdefghijklmnopqrstuvwzABCDEFGHIJKLMNOPQRSTUVWZ":
    build_canonicalize_latin[ch] = "multiple"
build_canonicalize_latin[""] = "multiple"

# Make sure we don't canonicalize any canonical letter to any other one;
# e.g. could happen with ʾ, an alternative for ʿ.
for greek in tt_to_greek_matching:
    alts = tt_to_greek_matching[greek]
    if isinstance(alts, basestring):
        build_canonicalize_latin[alts] = "multiple"
    else:
        canon = alts[0]
        if isinstance(canon, tuple):
            pass
        if isinstance(canon, list):
            build_canonicalize_latin[canon[0]] = "multiple"
        else:
            build_canonicalize_latin[canon] = "multiple"

for greek in tt_to_greek_matching:
    alts = tt_to_greek_matching[greek]
    if isinstance(alts, basestring):
        continue
    canon = alts[0]
    if isinstance(canon, list):
        continue
    for alt in alts[1:]:
        if isinstance(alt, list) or isinstance(alt, tuple):
            continue
        if alt in build_canonicalize_latin and build_canonicalize_latin[alt] != canon:
            build_canonicalize_latin[alt] = "multiple"
        else:
            build_canonicalize_latin[alt] = canon
tt_canonicalize_latin = {}
for alt in build_canonicalize_latin:
    canon = build_canonicalize_latin[alt]
    if canon != "multiple":
        tt_canonicalize_latin[alt] = canon

# A list of Latin characters that are allowed to be unmatched in the
# Greek. The value is the corresponding Greek character to insert.
tt_to_greek_unmatching = {
    MAC:MAC,
    BREVE:BREVE,
}

# Pre-canonicalize Latin, and Greek if supplied. If Greek is supplied,
# it should be the corresponding Greek (after pre-pre-canonicalization),
# and is used to do extra canonicalizations.
def pre_canonicalize_latin(text, greek=None):
    # remove L2R, R2L markers
    text = rsub(text, u"[\u200E\u200F]", "")
    # remove embedded comments
    text = rsub(text, u"<!--.*?-->", "")
    # remove embedded IPAchar templates
    text = rsub(text, r"\{\{IPAchar\|(.*?)\}\}", r"\1")
    # lowercase and remove leading/trailing spaces
    text = text.strip()
    # canonicalize interior whitespace
    text = rsub(text, r"\s+", " ")
    # decompose
    text = nfd_form(text)
    text = rsub(text, "y", "u")
    # move accent on first part of diphthong to second part
    text = rsub(text, "([aeiuoAEIOU]" + MBSOPT + ")([" + CIRC + ACUTE + GRAVE +
            "])([ui])(?!" + MBSOPT + DIA + ")", r"\1\3\2")

    return text

def tr_canonicalize_latin(text):
    # Fix cases like hA to read Ha
    text = rsub(text, "h([AEIOU])",
            lambda m: "H" + m.group(1).lower())
    # Compose diacritics
    text = nfc_form(text)
    return text

def post_canonicalize_latin(text):
    # Move macron and breve to beginning after vowel.
    text = rsub(text, u"([aeiouAEIOU])(" + LA_ACC_NO_MB + "*)(" +
            MBS + ")", r"\1\3\2")
    # Convert rr to rrh
    text = rsub(text, "rr($|[^h])", r"rrh\1")
    # Convert gk, gg to nk, ng
    text = rsub(text, "g([kg])", r"n\1")
    # recompose accented letters
    text = tr_canonicalize_latin(text)

    text = text.strip()
    return text

# Canonicalize a Latin transliteration and Greek text to standard form.
# Can be done on only Latin or only Greek (with the other one None), but
# is more reliable when both aare provided. This is less reliable than
# tr_matching() and is meant when that fails. Return value is a tuple of
# (CANONLATIN, CANONARABIC).
def canonicalize_latin_greek(latin, greek, msgfun=msg):
    if greek is not None:
        greek = pre_pre_canonicalize_greek(greek)
    if latin is not None:
        latin = pre_canonicalize_latin(latin, greek)
    if greek is not None:
        greek = pre_canonicalize_greek(greek)
        greek = post_canonicalize_greek(greek, msgfun=msgfun)
    if latin is not None:
        # Protect instances of two or more single quotes in a row so they don't
        # get converted to sequences of ʹ characters.
        def quote_subst(m):
            return m.group(0).replace("'", multi_single_quote_subst)
        latin = re.sub(r"''+", quote_subst, latin)
        latin = rsub(latin, u".", tt_canonicalize_latin)
        latin = latin.replace(multi_single_quote_subst, "'")
        latin = post_canonicalize_latin(latin)
    return (latin, greek)

def canonicalize_latin_foreign(latin, greek, msgfun=msg):
    return canonicalize_latin_greek(latin, greek, msgfun=msgfun)

def tr_canonicalize_greek(text):
    # Convert to decomposed form
    text = nfd_form(text)
    # Put rough/smooth breathing before vowel. (We do this with smooth
    # breathing as well to make it easier to add missing smooth breathing
    # in post_canonicalize_greek().)
    # Repeat in case of diphthong, where rough/smooth breathing follows 2nd
    # vowel.

    # Put rough/smooth breathing before diphthong; rough breathing comes first
    # in order with multiple accents, except macron or breve. Second vowel of
    # diphthong must be υ or ι and no following diaeresis. Only do it at
    # beginning of word.
    text = rsub(text, r"(^|[ \[\]|])(" + greek_diphthong_first_vowels + MBSOPT +
            u"[υι])(" + RS + ")(?!" + GR_ACC_NO_DIA + "*" + DIA + ")",
            r"\1\3\2")
    # Put rough/smooth breathing before vowel; rough breathing comes first in
    # order with multiple accents, except macron or breve. Only do it at
    # beginning of word.
    text = rsub(text, r"(^|[ \[\]|])(" + greek_vowels + MBSOPT + ")(" +
            RS + ")", r"\1\3\2")
    # Recombine iotated vowels; iotated accent comes last in order.
    # We do this because iotated vowels have special Latin mappings that
    # aren't just sum-of-parts (i.e. with an extra macron in the case of αΑ).
    text = rsub(text, u"([αΑηΗωΩ])(" + GR_ACC_NO_IOBE + "*)" + IOBE,
            lambda m:iotate_vowel[m.group(1)] + m.group(2))
    return text

# Early pre-canonicalization of Greek, doing stuff that's safe. We split
# this from pre-canonicalization proper so we can do Latin pre-canonicalization
# between the two steps.
def pre_pre_canonicalize_greek(text):
    # remove L2R, R2L markers
    text = rsub(text, u"[\u200E\u200F]", "")
    # remove leading/trailing spaces
    text = text.strip()
    # canonicalize interior whitespace
    text = rsub(text, r"\s+", " ")

    # Do some compatibility transformations since we no longer do the
    # NFKC/NFKD transformations due to them changing Greek 1FBD (koronis) into
    # 0020 SPACE + 0313 COMBINING COMMA ABOVE.
    text = text.replace(u"\u00B5", u"μ")

    text = tr_canonicalize_greek(text)

    return text

def pre_canonicalize_greek(text):
    return text

def post_canonicalize_greek(text, msgfun=msg):
    # Move macron and breve to beginning after vowel.
    text = rsub(text, u"(" + greek_vowels + ")(" + GR_ACC_NO_MB + "*)(" +
            MBS + ")", r"\1\3\2")
    # Don't do this; the Greek should already have an iotated vowel.
    # In any case, complications arise with acute accents in the Latin and
    # Greek (should we have pā́i against παί?).
    ## Canonicalize Greek ᾱι to ᾳ. Same for uppercase. But not if ι is followed
    ## by diaeresis. IOBE goes at end of accents.
    #text = rsub(text, u"([Αα])" + MAC + "(" + GR_ACC + u"*)ι(?!" +
    #        GR_ACC_NO_DIA + "*" + DIA + ")", r"\1\2" + IOBE)
    # Don't do this; it's not always appropriate (e.g. with suffixes);
    # instead issue a warning.
    # If no rough breathing before beginning-of-word vowel, add a smooth
    # breathing sign.
    newtext = rsub(text, u"(^|[ \[\]|])(" + greek_vowels + ")",
            r"\1" + SMBR + r"\2")
    if newtext != text:
        msgfun("WARNING: Text %s may be missing a smooth-breathing sign" %
                text)
    # Put rough/smooth breathing after diphthong; rough breathing comes first
    # in order with multiple accents, except macron or breve. Second vowel of
    # diphthong must be υ or ι and no following diaeresis. Only do it at
    # beginning of word.
    text = rsub(text, r"(^|[ \[\]|])(" + RS + ")(" +
            greek_diphthong_first_vowels + MBSOPT + u"[υι])(?!" + GR_ACC_NO_DIA
            + "*" + DIA + ")", r"\1\3\2")
    # Put rough/smooth breathing after vowel; rough breathing comes first in
    # order with multiple accents, except macron or breve. Only do it at
    # beginning of word.
    text = rsub(text, r"(^|[ \[\]|])(" + RS + ")(" + greek_vowels +
            MBSOPT + ")", r"\1\3\2")
    # Eliminate breve over short vowel
    text = rsub(text, u"([οεΟΕ])" + BREVE, r"\1")
    # Eliminate macron over long vowel
    text = rsub(text, u"([ηωΗΩᾳᾼῃῌῳῼ])" + MAC, r"\1")
    # Finally, convert to composed form. Do at very end.
    text = nfc_form(text)
    return text

debug_tr_matching = False

# Vocalize Greek based on transliterated Latin, and canonicalize the
# transliteration based on the Greek.  This works by matching the Latin
# to the Greek and transferring Latin stress marks to the Greek as
# appropriate, so that ambiguities of Latin transliteration can be
# correctly handled. Returns a tuple of Greek, Latin. If unable to match,
# throw an error if ERR, else return None.
def tr_matching(greek, latin, err=False, msgfun=msg):
    origgreek = greek
    origlatin = latin
    def debprint(x):
        if debug_tr_matching:
            uniprint(x)
    greek = pre_pre_canonicalize_greek(greek)
    latin = pre_canonicalize_latin(latin, greek)
    greek = pre_canonicalize_greek(greek)

    gr = [] # exploded Greek characters
    la = [] # exploded Latin characters
    res = [] # result Greek characters
    lres = [] # result Latin characters
    for cp in greek:
        gr.append(cp)
    for cp in latin:
        la.append(cp)
    gind = [0] # index of next Greek character
    glen = len(gr)
    lind = [0] # index of next Latin character
    llen = len(la)

    def is_bow(pos=None):
        if pos is None:
            pos = gind[0]
        return pos == 0 or gr[pos - 1] in [u" ", u"[", u"|", u"-"]

    # True if we are at the last character in a word.
    def is_eow(pos=None):
        if pos is None:
            pos = gind[0]
        return pos == glen - 1 or gr[pos + 1] in [u" ", u"]", u"|", u"-"]

    def get_matches(delete_blank_matches=False):
        ac = gr[gind[0]]
        debprint("get_matches: ac is %s" % ac)
        bow = is_bow()
        eow = is_eow()

        matches = tt_to_greek_matching.get(ac)
        debprint("get_matches: matches is %s" % matches)
        if matches == None:
            if True:
                error("Encountered non-Greek (?) character " + ac +
                    " at index " + str(gind[0]))
            else:
                matches = [ac]
        if type(matches) is not list:
            matches = [matches]
        if delete_blank_matches:
            # Don't delete blank matches if first match is blank, otherwise
            # we run into problems with ἆθλον vs. āthlon.
            if matches[0]:
                matches = [x for x in matches if x]
                debprint("get_matches: deleted blanks, matches is now %s" % matches)
        return matches

    # attempt to match the current Greek character against the current
    # Latin character(s). If no match, return False; else, increment the
    # Greek and Latin pointers over the matched characters, add the Greek
    # character to the result characters and return True.
    def match():
        # The reason for delete_blank_matches here is to deal with the case
        # of Greek βλάξ vs. Latin blā́ks. We want the Greek acute accent to
        # match nothing so it gets transfered to the Latin, but if we do
        # this naively we get a problem in these two words: the Greek contains
        # an acute accent, while the Latin contains a macron + acute, and
        # so the Greek acute accent matches against nothing in the Latin,
        # then the Latin macron matches against nothing in the Greek
        # through check_unmatching(), then we can't match Greek ξ against
        # Latin acute accent. Instead, disallow matching Greek stuff against
        # nothing if check_unmatching() would trigger. That way we don't
        # match Greek acute against nothing, but instead handle the macron
        # first, then the acute accents match against each other. We can't
        # fix this by simply doing check_unmatching() before match() because
        # then we wouldn't match Greek macron with Latin macron.
        delete_blank_matches = (
                lind[0] < llen and la[lind[0]] in tt_to_greek_unmatching)
        matches = get_matches(delete_blank_matches)

        ac = gr[gind[0]]

        # Check for link of the form [[foo|bar]] and skip over the part
        # up through the vertical bar, copying it
        if ac == '[':
            newpos = gind[0]
            while newpos < glen and gr[newpos] != ']':
                if gr[newpos] == '|':
                    newpos += 1
                    while gind[0] < newpos:
                        res.append(gr[gind[0]])
                        gind[0] += 1
                    return True
                newpos += 1

        for m in matches:
            preserve_latin = False
            # If an element of the match list is a list, it means
            # "don't canonicalize".
            if type(m) is list:
                preserve_latin = True
                m = m[0]
            # A one-element tuple is a signal for use in self-canonicalization,
            # not here.
            elif type(m) is tuple:
                m = m[0]
            l = lind[0]
            matched = True
            debprint("m: %s" % m)
            for cp in m:
                debprint("cp: %s" % cp)
                if l < llen and la[l] == cp:
                    l = l + 1
                else:
                    matched = False
                    break
            if matched:
                res.append(ac)
                if preserve_latin:
                    for cp in m:
                        lres.append(cp)
                else:
                    subst = matches[0]
                    if type(subst) is list or type(subst) is tuple:
                        subst = subst[0]
                    for cp in subst:
                        lres.append(cp)
                lind[0] = l
                gind[0] = gind[0] + 1
                debprint("matched; lind is %s" % lind[0])
                return True
        return False

    def cant_match():
        if gind[0] < glen and lind[0] < llen:
            error("Unable to match Greek character %s at index %s, Latin character %s at index %s" %
                (gr[gind[0]], gind[0], la[lind[0]], lind[0]))
        elif gind[0] < glen:
            error("Unable to match trailing Greek character %s at index %s" %
                (gr[gind[0]], gind[0]))
        else:
            error("Unable to match trailing Latin character %s at index %s" %
                (la[lind[0]], lind[0]))

    # Check for an unmatched Latin short vowel or similar; if so, insert
    # corresponding Greek diacritic.
    def check_unmatching():
        if not (lind[0] < llen):
            return False
        debprint("Unmatched Latin: %s at %s" % (la[lind[0]], lind[0]))
        unmatched = tt_to_greek_unmatching.get(la[lind[0]])
        if unmatched != None:
            res.append(unmatched)
            lres.append(la[lind[0]])
            lind[0] = lind[0] + 1
            return True
        return False

    def check_unmatching_rh_zd():
        # Check for rh corresponding to ρ, which will occur especially
        # in a sequence ρρ. We can't handle this in tt_to_greek_matching[]
        # because canonical "r" is a subsequence of "rh".
        if not (lind[0] < llen and gind[0] > 0):
            return False
        if la[lind[0]] == "h" and gr[gind[0] - 1] == u"ρ":
            lres.append("h")
            lind[0] += 1
            return True
        # Exact same thing here for zd/Zd corresponding to ζ/Ζ.
        if la[lind[0]] == "d" and gr[gind[0] - 1] in [u"ζ", u"Ζ"]:
            lres.append("d")
            lind[0] += 1
            return True
        return False

    # Here we go through the Greek letter for letter, matching
    # up the consonants we encounter with the corresponding Latin consonants
    # using the dict in tt_to_greek_matching and copying the Greek
    # consonants into a destination array. When we don't match, we check for
    # allowed unmatching Latin characters in tt_to_greek_unmatching, which
    # handles acute accents. If this doesn't match either, and we have
    # left-over Greek or Latin characters, we reject the whole match,
    # either returning False or signaling an error.

    while gind[0] < glen or lind[0] < llen:
        matched = False
        # The effect of the next clause is to handle cases where the
        # Greek has a right bracket or similar character and the Latin has
        # an acute accent that doesn't match and needs to go before
        # the right bracket. The is_bow() check is necessary for reasons
        # described in ar_translit.py, where this check comes from.
        #
        # FIXME: Is this still necessary here? Is there a better way?
        # E.g. splitting the Greek string on occurrences of left/right
        # brackets and handling the remaining occurrences piece-by-piece?
        if (not is_bow() and gind[0] < glen and
                gr[gind[0]] in word_interrupting_chars and
                check_unmatching()):
            debprint("Matched: Clause 1")
            matched = True
        elif gind[0] < glen and match():
            debprint("Matched: Clause match()")
            matched = True
        elif check_unmatching():
            debprint("Matched: Clause check_unmatching()")
            matched = True
        elif check_unmatching_rh_zd():
            debprint("Matched: Clause check_unmatching_rh_zd()")
            matched = True
        if not matched:
            if err:
                cant_match()
            else:
                return False

    greek = "".join(res)
    latin = "".join(lres)
    greek = post_canonicalize_greek(greek, msgfun=msgfun)
    latin = post_canonicalize_latin(latin)
    return greek, latin

def remove_diacritics(text):
    text = rsub(text, u"[ᾸᾹᾰᾱῘῙῐῑῨῩῠῡ]",
            {u"Ᾰ":u"Α", u"Ᾱ":u"Α", u"ᾰ":u"α", u"ᾱ":u"α", u"Ῐ":u"Ι", u"Ῑ":u"Ι",
             u"ῐ":u"ι", u"ῑ":u"ι", u"Ῠ":u"Υ", u"Ῡ":u"Υ", u"ῠ":u"υ", u"ῡ":u"υ"})
    text = rsub(text, ONE_MB, "")
    text = nfc_form(text)
    return text

################################ Test code ##########################

num_failed = 0
num_succeeded = 0

def test(latin, greek, should_outcome, expectedgreek=None):
    global num_succeeded, num_failed
    if not expectedgreek:
        expectedgreek = greek
    try:
        result = tr_matching(greek, latin, True)
    except RuntimeError as e:
        uniprint(u"%s" % e)
        result = False
    if result == False:
        uniprint("tr_matching(%s, %s) = %s" % (greek, latin, result))
        outcome = "failed"
        canongreek = expectedgreek
    else:
        canongreek, canonlatin = result
        trlatin = tr(canongreek)
        uniout("tr_matching(%s, %s) = %s %s," %
                (greek, latin, canongreek, canonlatin))
        if trlatin == canonlatin:
            uniprint("tr() MATCHED")
            outcome = "matched"
        else:
            uniprint("tr() UNMATCHED (= %s)" % trlatin)
            outcome = "unmatched"
    if canongreek != expectedgreek:
        uniprint("Canon Greek FAILED, expected %s got %s"% (
            expectedgreek, canongreek))
    canonlatin, _ = canonicalize_latin_greek(latin, None)
    uniprint("canonicalize_latin(%s) = %s" %
            (latin, canonlatin))
    if outcome == should_outcome and canongreek == expectedgreek:
        uniprint("TEST SUCCEEDED.")
        num_succeeded += 1
    else:
        uniprint("TEST FAILED.")
        num_failed += 1

def run_tests():
    global num_succeeded, num_failed
    num_succeeded = 0
    num_failed = 0

    # Test inferring accents in both Cyrillic and Latin
    test(u"Khristoû", u"Χριστοῦ", "matched")
    test(u"Khrīstoû", u"Χριστοῦ", "matched", u"Χρῑστοῦ")
    test(u"Khristoû", u"Χρῑστοῦ", "matched")
    test(u"Khrīstoû", u"Χρῑστοῦ", "matched")
    test(u"hioû", u"ἱοῦ", "matched")
    test(u"huioû", u"υἱοῦ", "matched")
    test(u"huiou", u"υἱοῦ", "matched")
    test(u"huiôu", u"υἱοῦ", "matched")
    #test(u"pāi", u"παι", "matched", u"πᾳ")
    #test(u"pā́i", u"παί", "matched", u"πᾴ")
    #test(u"pāï", u"παϊ", "matched", u"πᾱϊ")
    #test(u"pā́ï", u"πάϊ", "matched", u"πᾱ́ϊ")
    # Should add smooth breathing
    test(u"ā̂u", u"αῦ", "matched", u"ᾱὖ") # FIXME!! Check this

    test(u"huiôu", u"ὑϊοῦ", "matched")

    # Various real tests from the long-vowel warnings
    test(u"krīnō", u"κρίνω", "matched", u"κρῑ́νω")
    # Should add smooth breathing
    test(u"aŋkýlā", u"αγκύλα", "matched", u"ἀγκύλᾱ")
    test(u"baptīzō", u"βαπτίζω", "matched", u"βαπτῑ́ζω")
    test(u"stūlos", u"στῦλος", "matched")
    test(u"hūlē", u"ὕλη", "matched", u"ῡ̔́λη")
    test(u"Hamilkās", u"Ἀμίλκας", "failed")
    test(u"Dānīēl", u"Δανιήλ", "matched", u"Δᾱνῑήλ")
    test(u"hēmerā", u"ἡμέρα", "matched", u"ἡμέρᾱ")
    test(u"sbénnūmi", u"σβέννυμι", "matched", u"σβέννῡμι")
    test(u"Īberniā", u"Ἱβερνία", "matched", u"Ῑ̔βερνίᾱ")
    # FIXME: Produces Hāídēs. What should it produce?
    test(u"Hāidēs", u"ᾍδης", "matched")
    test(u"blā́ks", u"βλάξ", "matched", u"βλᾱ́ξ")
    test(u"blā́x", u"βλάξ", "matched", u"βλᾱ́ξ")
    # FIXME: Think about this. We currently transliterate Greek breve with
    # nothing, so the translit of the Greek won't match the Latin.
    test(u"krūŏn", u"κρύον", "unmatched", u"κρῡ́ον")
    test(u"āthlon", u"ἆθλον", "matched")
    test(u"rhādix", u"ῥάδιξ", "matched", u"ῥᾱ́διξ")
    test(u"Murrhā", u"Μύῤῥα", "matched", u"Μύῤῥᾱ")
    # Smooth breathing not at beginning of word; should not be moved
    test(u"tautologiā", u"ταὐτολογία", "matched", u"ταὐτολογίᾱ")
    # # Things that should fail
    test(u"stúlos", u"στῦλος", "failed")
    test(u"stilos", u"στῦλος", "failed")

    # Test handling of embedded links, including unmatched macron
    # directly before right bracket on Greek side
    test(u"pala bolu", u"παλα [[βολα|βολυ]]", "matched")
    test(u"pala bolū", u"παλα [[βολα|βολυ]]", "matched", u"παλα [[βολα|βολῡ]]")
    test(u"bolu pala", u"[[βολα|βολυ]] παλα", "matched")
    test(u"bolū pala", u"[[βολα|βολυ]] παλα", "matched", u"[[βολα|βολῡ]] παλα")
    test(u"bolupala", u"[[βολα|βολυ]]παλα", "matched")
    test(u"pala bolu", u"παλα [[βολυ]]", "matched")
    test(u"pala bolū", u"παλα [[βολυ]]", "matched", u"παλα [[βολῡ]]")
    test(u"bolu pala", u"[[βολυ]] παλα", "matched")
    test(u"bolū pala", u"[[βολυ]] παλα", "matched", u"[[βολῡ]] παλα")
    test(u"bolūpala", u"[[βολυ]]παλα", "matched", u"[[βολῡ]]παλα")

    # # Single quotes in Greek
    test(u"bolu '''pala'''", u"βολυ '''παλα'''", "matched")
    test(u"bolu '''palā'''", u"βολυ '''παλα'''", "matched", u"βολυ '''παλᾱ'''")

    # Final results
    uniprint("RESULTS: %s SUCCEEDED, %s FAILED." % (num_succeeded, num_failed))

if __name__ == "__main__":
    run_tests()

# For Vim, so we get 4-space indent
# vim: set sw=4:
