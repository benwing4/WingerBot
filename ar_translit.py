#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Authors: Benwing, ZxxZxxZ, Atitarev

#    ar_translit.py is free software: you can redistribute it and/or modify
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

def error(msg):
    raise RuntimeError(msg)

zwnj = u"\u200c" # zero-width non-joiner
zwj  = u"\u200d" # zero-width joiner
#lrm = u"\u200e" # left-to-right mark
#rlm = u"\u200f" # right-to-left mark

tt = {
    # consonants
    u"ب":u"b", u"ت":u"t", u"ث":u"ṯ", u"ج":u"j", u"ح":u"ḥ", u"خ":u"ḵ",
    u"د":u"d", u"ذ":u"ḏ", u"ر":u"r", u"ز":u"z", u"س":u"s", u"ش":u"š",
    u"ص":u"ṣ", u"ض":u"ḍ", u"ط":u"ṭ", u"ظ":u"ẓ", u"ع":u"ʿ", u"غ":u"ḡ",
    u"ف":u"f", u"ق":u"q", u"ك":u"k", u"ل":u"l", u"م":u"m", u"ن":u"n",
    u"ه":u"h",
    # tāʾ marbūṭa (special) - always after a fátḥa (a), silent at the end of
    # an utterance, "t" in ʾiḍāfa or with pronounced tanwīn. We catch
    # most instances of tāʾ marbūṭa before we get to this stage.
    u"\u0629":"t", # tāʾ marbūṭa = ة
    # control characters
    zwnj:"-", # ZWNJ (zero-width non-joiner)
    zwj:"-", # ZWJ (zero-width joiner)
    # rare letters
    u"پ":u"p", u"چ":u"č", u"ڤ":u"v", u"گ":u"g", u"ڨ":u"g", u"ڧ":u"q",
    # semivowels or long vowels, alif, hamza, special letters
    u"ا":u"ā", # ʾalif = \u0627
    # hamzated letters
    u"أ":u"ʾ", u"إ":u"ʾ", u"ؤ":u"ʾ", u"ئ":u"ʾ", u"ء":u"ʾ",
    u"و":u"w", #"ū" after ḍamma (u) and not before diacritic = \u0648
    u"ي":u"y", #"ī" after kasra (i) and not before diacritic = \u064A
    u"ى":u"ā", # ʾalif maqṣūra = \u0649
    u"آ":u"ʾā", # ʾalif madda = \u0622
    u"ٱ":u"", # hamzatu l-waṣl = \u0671
    u"\u0670":u"ā", # ʾalif xanjariyya = dagger ʾalif (Koranic diacritic)
    # short vowels, šádda and sukūn
    u"\u064B":u"an", # fatḥatan
    u"\u064C":u"un", # ḍammatan
    u"\u064D":u"in", # kasratan
    u"\u064E":u"a", # fatḥa
    u"\u064F":u"u", # ḍamma
    u"\u0650":u"i", # kasra
    # \u0651 = šadda - doubled consonant
    u"\u0652":u"", #sukūn - no vowel
    # ligatures
    u"ﻻ":u"lā",
    u"ﷲ":u"llāh",
    # taṭwīl
    u"ـ":u"", # taṭwīl, no sound
    # numerals
    u"١":u"1", u"٢":u"2", u"٣":u"3", u"٤":u"4", u"٥":u"5",
    u"٦":u"6", u"٧":u"7", u"٨":u"8", u"٩":u"9", u"٠":u"0",
    # punctuation (leave on separate lines)
    u"؟":u"?", # question mark
    u"،":u",", # comma
    u"؛":u";" # semicolon
}

sun_letters = u"تثدذرزسشصضطظلن"
# For use in implementing sun-letter assimilation of ال (al-)
ttsun1 = {}
ttsun2 = {}
for ch in sun_letters:
    ttsun1[ch] = tt[ch]
    ttsun2["l-" + ch] = tt[ch] + "-" + ch
# For use in implementing elision of al-
sun_letters_tr = ''.join(ttsun1.values())

consonants_needing_vowels = u"بتثجحخدذرزسشصضطظعغفقكلمنهپچڤگڨڧأإؤئءةﷲ"
# consonants on the right side; includes alif madda
rconsonants = consonants_needing_vowels + u"ويآ"
# consonants on the left side; does not include alif madda
lconsonants = consonants_needing_vowels + u"وي"
punctuation = (u"؟،؛" # Arabic semicolon, comma, question mark
               + u"ـ" # taṭwīl
               + u".!'" # period, exclamation point, single quote for bold/italic
               )
numbers = u"١٢٣٤٥٦٧٨٩٠"

before_diacritic_checking_subs = [
    ########### transformations prior to checking for diacritics ##############
    # remove the first part of [[foo|bar]] links
    [ur"\[\[[^]]*\|", u""],
    # remove brackets in [[foo]] links
    [ur"[\[\]]", u""],
    # convert llh for allāh into ll+shadda+dagger-alif+h
    [u"لله", u"للّٰه"],
    # shadda+short-vowel (including tanwīn vowels, i.e. -an -in -un) gets
    # replaced with short-vowel+shadda during NFC normalisation, which
    # MediaWiki does for all Unicode strings; however, it makes the
    # transliteration process inconvenient, so undo it.
    [u"([\u064B\u064C\u064D\u064E\u064F\u0650\u0670])\u0651", u"\u0651\\1"],
    # ignore alif jamīla (otiose alif in 3pl verb forms)
    #     #1: handle ḍamma + wāw + alif (final -ū)
    [u"\u064F\u0648\u0627", u"\u064F\u0648"],
    #     #2: handle wāw + sukūn + alif (final -w in -aw in defective verbs)
    #     this must go before the generation of w, which removes the waw here.
    [u"\u0648\u0652\u0627", u"\u0648\u0652"],
    # ignore final alif or alif maqṣūra following fatḥatan (e.g. in accusative
    # singular or words like عَصًا "stick" or هُذًى "guidance"; this is called
    # tanwin nasb)
    [u"\u064B[\u0627\u0649]", u"\u064B"],
    # same but with the fatḥatan placed over the alif or alif maqṣūra
    # instead of over the previous letter (considered a misspelling but
    # common)
    [u"[\u0627\u0649]\u064B", u"\u064B"],
    # tāʾ marbūṭa should always be preceded by fatḥa, alif, alif madda or
    # dagger alif; infer fatḥa if not
    [u"([^\u064E\u0627\u0622\u0670])\u0629", u"\\1\u064E\u0629"],
    # similarly for alif between consonants, possibly marked with shadda
    # (does not apply to initial alif, which is silent when not marked with
    # hamza, or final alif, which might be pronounced as -an)
    [u"([" + lconsonants + u"]\u0651?)\u0627([" + rconsonants + u"])",
        u"\\1\u064E\u0627\\2"],
    # infer fatḥa in case of non-fatḥa + alif/alif-maqṣūra + dagger alif
    [u"([^\u064E])([\u0627\u0649]\u0670)", u"\\1\u064E\\2"],
    # infer kasra in case of hamza-under-alif not + kasra
    [u"\u0625([^\u0650])", u"\u0625\u0650\\1"],
    # ignore dagger alif placed over regular alif or alif maqṣūra
    [u"([\u0627\u0649])\u0670", u"\\1"],

    # al + consonant + shadda (only recognize word-initially if regular alif): remove shadda
    [u"(^|\\s)(\u0627\u064E?\u0644[" + lconsonants + u"])\u0651", u"\\1\\2"],
    [u"(\u0671\u064E?\u0644[" + lconsonants + u"])\u0651", u"\\1"],
    # handle l- hamzatu l-waṣl or word-initial al-
    [u"(^|\\s)\u0627\u064E?\u0644", u"\\1al-"],
    [u"\u0671\u064E?\u0644", "l-"],
    # implement assimilation of sun letters
    [u"l-[" + sun_letters + "]", ttsun2]
]

# Transliterate any words or phrases. OMIT_I3RAAB means leave out final
# short vowels (ʾiʿrāb). FORCE_TRANSLATE causes even non-vocalized text to
# be transliterated (normally the function checks for non-vocalized text and
# returns None, since such text is ambiguous in transliteration).
def tr(text, lang=None, sc=None, omit_i3raab=False, gray_i3raab=True,
        force_translate=False):
    for sub in before_diacritic_checking_subs:
        text = rsub(text, sub[0], sub[1])

    if not force_translate and not has_diacritics(text):
        return None

    ############# transformations after checking for diacritics ##############
    # Replace plain alif with hamzatu l-waṣl when followed by fatḥa/ḍamma/kasra.
    # Must go after handling of initial al-, which distinguishes alif-fatḥa
    # from alif w/hamzatu l-waṣl. Must go before generation of ū and ī, which
    # eliminate the ḍamma/kasra.
    text = rsub(text, u"\u0627([\u064E\u064F\u0650])", u"\u0671\\1")
    # ḍamma + waw not followed by a diacritic is ū, otherwise w
    text = rsub(text, u"\u064F\u0648([^\u064B\u064C\u064D\u064E\u064F\u0650\u0651\u0652\u0670])", u"ū\\1")
    text = rsub(text, u"\u064F\u0648$", u"ū")
    # kasra + yaa not followed by a diacritic (or ū from prev step) is ī, otherwise y
    text = rsub(text, u"\u0650\u064A([^\u064B\u064C\u064D\u064E\u064F\u0650\u0651\u0652\u0670ū])", u"ī\\1")
    text = rsub(text, u"\u0650\u064A$", u"ī")
    # convert shadda to double letter.
    text = rsub(text, u"(.)\u0651", u"\\1\\1")
    if not omit_i3raab and gray_i3raab: # show ʾiʿrāb grayed in transliteration
        # decide whether to gray out the t in ة. If word begins with al-, yes.
        # Otherwise, no if word ends in a/i/u, yes if ends in an/in/un.
        text = rsub(text, u"((?:^|\\s)a?l-[^\\s]+)\u0629([\u064B\u064C\u064D\u064E\u064F\u0650])",
            u"\\1<span style=\"color: #888888\">t</span>\\2")
        text = rsub(text, u"\u0629([\u064E\u064F\u0650])", u"t\\1")
        text = rsub(text, u"\u0629([\u064B\u064C\u064D])",
            u"<span style=\"color: #888888\">t</span>\\1")
        text = rsub(text, u".", {
            u"\u064B":u"<span style=\"color: #888888\">an</span>",
            u"\u064D":u"<span style=\"color: #888888\">in</span>",
            u"\u064C":u"<span style=\"color: #888888\">un</span>"
        })
        text = rsub(text, u"([\u064E\u064F\u0650])\\s", {
            u"\u064E":u"<span style=\"color: #888888\">a</span> ",
            u"\u0650":u"<span style=\"color: #888888\">i</span> ",
            u"\u064F":u"<span style=\"color: #888888\">u</span> "
        })
        text = rsub(text, u"[\u064E\u064F\u0650]$", {
            u"\u064E":u"<span style=\"color: #888888\">a</span>",
            u"\u0650":u"<span style=\"color: #888888\">i</span>",
            u"\u064F":u"<span style=\"color: #888888\">u</span>"
        })
        text = rsub(text, u"</span><span style=\"color: #888888\">", u"")
    elif omit_i3raab: # omit ʾiʿrāb in transliteration
        text = rsub(text, u"[\u064B\u064C\u064D]", u"")
        text = rsub(text, u"[\u064E\u064F\u0650]\\s", u" ")
        text = rsub(text, u"[\u064E\u064F\u0650]$", u"")
    # tāʾ marbūṭa should not be rendered by -t if word-final even when
    # ʾiʿrāb (desinential inflection) is shown; instead, use (t) before
    # whitespace, nothing when final; but render final -اة and -آة as -āh,
    # consistent with Wehr's dictionary
    text = rsub(text, u"([\u0627\u0622])\u0629$", u"\\1h")
    # Need to do the following after graying or omitting word-final ʾiʿrāb.
    text = rsub(text, u"\u0629$", u"")
    if not omit_i3raab: # show ʾiʿrāb in transliteration
        text = rsub(text, u"\u0629\\s", u"(t) ")
    else:
        # When omitting ʾiʿrāb, show all non-absolutely-final instances of
        # tāʾ marbūṭa as (t), with trailing ʾiʿrāb omitted.
        text = rsub(text, u"\u0629", u"(t)")
    text = rsub(text, u".", tt)
    text = rsub(text, u"aā", u"ā")
    # Implement elision of al- after a final vowel. We do this
    # conservatively, only handling elision of the definite article rather
    # than elision in other cases of hamzat al-waṣl (e.g. form-I imperatives
    # or form-VII and above verbal nouns) partly because elision in
    # these cases isn't so common in MSA and partly to avoid excessive
    # elision in case of words written with initial bare alif instead of
    # properly with hamzated alif. Possibly we should reconsider.
    # At the very least we currently don't handle elision of الَّذِي (allaḏi)
    # correctly because we special-case it to appear without the hyphen;
    # perhaps we should reconsider that.
    text = rsub(text, u"([aiuāīū](?:</span>)?) a([" + sun_letters_tr + "]-)",
        u"\\1 \\2")

    return text

has_diacritics_subs = [
    # FIXME! What about lam-alif ligature?
    # remove punctuation and shadda
    # must go before removing final consonants
    [u"[" + punctuation + u"\u0651]", u""],
    # Remove consonants at end of word or utterance, so that we're OK with
    # words lacking iʿrāb (must go before removing other consonants).
    # If you want to catch places without iʿrāb, comment out the next two lines.
    [u"[" + lconsonants + u"]$", u""],
    [u"[" + lconsonants + u"]\\s", u" "],
    # remove consonants (or alif) when followed by diacritics
    # must go after removing shadda
    # do not remove the diacritics yet because we need them to handle
    # long-vowel sequences of diacritic + pseudo-consonant
    [u"[" + lconsonants + u"\u0627]([\u064B\u064C\u064D\u064E\u064F\u0650\u0652\u0670])", u"\\1"],
    # the following two must go after removing consonants w/diacritics because
    # we only want to treat vocalic wāw/yā' in them (we want to have removed
    # wāw/yā' followed by a diacritic)
    # remove ḍamma + wāw
    [u"\u064F\u0648", u""],
    # remove kasra + yā'
    [u"\u0650\u064A", u""],
    # remove fatḥa/fatḥatan + alif/alif-maqṣūra
    [u"[\u064B\u064E][\u0627\u0649]", u""],
    # remove diacritics
    [u"[\u064B\u064C\u064D\u064E\u064F\u0650\u0652\u0670]", u""],
    # remove numbers, hamzatu l-waṣl, alif madda
    [u"[" + numbers + u"ٱ" + u"آ" + "]", u""],
    # remove non-Arabic characters
    [u"[^\u0600-\u06FF\u0750-\u077F\u08A1-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]", u""]
]

def has_diacritics(text):
    for sub in has_diacritics_subs:
        text = rsub(text, sub[0], sub[1])
    return len(text) == 0


############################################################################
#                     Transliterate from Latin to Arabic                   #
############################################################################

#########       Transliterate with unvocalized Arabic to guide       #########

silent_alif_subst = u"\ufff1"
silent_alif_maqsuura_subst = u"\ufff2"
multi_single_quote_subst = u"\ufff3"
assimilating_l_subst = u"\ufff4"
hamza_match=[u"ʾ",u"’",u"'",u"`"]
hamza_match_or_empty=[u"ʾ",u"’",u"'",u"`",u""]

# Special-case matching at beginning of word. Plain alif normally corresponds
# to nothing, and hamza seats might correspond to nothing (omitted hamza
# at beginning of word). We can't allow e.g. أ to have "" as one of its
# possibilities mid-word because that will screw up a word like سألة "saʾala",
# which won't match at all because the أ will match nothing directly after
# the Latin "s", and then the ʾ will never be matched.
tt_to_arabic_matching_bow = { #beginning of word
    # put empty string in list so this entry will be recognized -- a plain
    # empty string is considered logically false
    u"ا":[u""],
    u"أ":hamza_match_or_empty,
    u"إ":hamza_match_or_empty,
    u"آ":[u"ʾaā",u"’aā",u"'aā",u"`aā",u"aā"], #ʾalif madda = \u0622
}

# Special-case matching at end of word. Some ʾiʿrāb endings may appear in
# the Arabic but not the transliteration; allow for that.
tt_to_arabic_matching_eow = { # end of word
    u"\u064C":[u"un",u""], # ḍammatan
    u"\u064E":[u"a",u""], # fatḥa (in plurals)
    u"\u064F":[u"u",u""], # ḍamma (in diptotes)
    u"\u0650":[u"i",u""], # kasra (in duals)
}

# This dict maps Arabic characters to all the Latin characters that might
# correspond to them. The entries can be a string (equivalent to a one-entry
# list) or a list of strings or one-element lists containing strings (the latter is
# equivalent to a string but suppresses canonicalization during transliteration;
# see below). The ordering of elements in the list is important insofar as which
# element is first, because the default behavior when canonicalizing a transliteration
# is to substitute any string in the list with the first element of the list (this can
# be suppressed by making an element a one-entry list containing a string, as
# mentioned above). Each string might have multiple characters, to handle things
# like خ=kh and ث=th.
tt_to_arabic_matching = {
    # consonants
    u"ب":u"b", u"ت":u"t", u"ث":[u"ṯ",u"ŧ",u"θ",u"th"],    u"ج":[u"j",u"ǧ"],
    # allow what would normally be capital H, but we lowercase all text
    # before processing
    u"ح":[u"ḥ",u"ħ",u"h"], u"خ":[u"ḵ",u"x",u"kh"],
    u"د":u"d", u"ذ":[u"ḏ",u"đ",u"ð",u"dh"], u"ر":u"r", u"ز":u"z",
    u"س":u"s", u"ش":[u"š",u"sh"],
    # allow non-emphatic to match so we can handle uppercase S, D, T, Z;
    # we lowercase the text before processing to handle proper names and such
    u"ص":[u"ṣ",u"sʿ",u"s", u"ʂ"], u"ض":[u"ḍ",u"dʿ",u"d"],
    u"ط":[u"ṭ",u"tʿ",u"ṫ",u"t"], u"ظ":[u"ẓ",u"ðʿ",u"đ̣",u"z"],
    u"ع":[u"ʿ",u"ʕ",u"`",u"‘",u"ʻ",u"3",u"ˁ"], u"غ":[u"ḡ",u"ġ",u"ğ",u"gh"],
    u"ف":u"f", u"ق":u"q", u"ك":u"k", u"ل":u"l", u"م":u"m",    u"ن":u"n",
    u"ه":u"h",
    # We have special handling for the following in the canonicalized Latin,
    # so that we have -a but -āh and -at-.
    u"ة":[u"h",[u"t"],[u"(t)"],u""],
    # control characters
    zwnj:[u"-"],#,u""], # ZWNJ (zero-width non-joiner)
    zwj:[u"-"],#,u""], # ZWJ (zero-width joiner)
    # rare letters
    u"پ":u"p", u"چ":[u"č",u"ch"], u"ڤ":u"v", u"گ":u"g", u"ڨ":u"g", u"ڧ":u"q",
    # semivowels or long vowels, alif, hamza, special letters
    u"ا":u"ā", # ʾalif = \u0627
    silent_alif_subst:[u""],
    silent_alif_maqsuura_subst:[u""],
    # hamzated letters
    u"أ":hamza_match, u"إ":hamza_match, u"ؤ":hamza_match,
    u"ئ":hamza_match, u"ء":hamza_match,
    u"و":[[u"w"],[u"ū"],[u"ō"]],
    u"ي":[[u"y"],[u"ī"],[u"ē"]],
    u"ى":u"ā", # ʾalif maqṣūra = \u0649
    u"آ":[u"ʾaā",u"’aā",u"'aā",u"`aā"], # ʾalif madda = \u0622
    u"ٱ":[u""], # hamzatu l-waṣl = \u0671
    u"\u0670":u"aā", # ʾalif xanjariyya = dagger ʾalif (Koranic diacritic)
    # short vowels, šadda and sukūn
    u"\u064B":u"an", # fatḥatan
    u"\u064C":u"un", # ḍammatan
    u"\u064D":u"in", # kasratan
    u"\u064E":u"a", # fatḥa
    u"\u064F":[[u"u"],[u"o"]], # ḍamma
    u"\u0650":[[u"i"],[u"e"]], # kasra
    u"\u0651":u"\u0651", # šadda - doubled consonant
    u"\u0652":u"", #sukūn - no vowel
    # ligatures
    u"ﻻ":u"lā",
    u"ﷲ":u"llāh",
    # taṭwīl
    u"ـ":[u""], # taṭwīl, no sound
    # numerals
    u"١":u"1", u"٢":u"2", u"٣":u"3", u"٤":u"4", u"٥":u"5",
    u"٦":u"6", u"٧":u"7", u"٨":u"8", u"٩":u"9", u"٠":u"0",
    # punctuation (leave on separate lines)
    u"؟":u"?", # question mark
    u"،":u",", # comma
    u"؛":u";", # semicolon
    u".":u".", # period
    u"'":u"'", # single quote, for bold/italic
    u" ":u" ",
    u"[":u"",
    u"]":u""
}

build_canonicalize_latin = {}
for ch in "abcdefghijklmnopqrstuvwyz3":
    build_canonicalize_latin[ch] = "multiple"
    build_canonicalize_latin[""] = "multiple"
for arabic in tt_to_arabic_matching:
    alts = tt_to_arabic_matching[arabic]
    if isinstance(alts, basestring):
        continue
    canon = alts[0]
    if isinstance(canon, list):
        continue
    for alt in alts[1:]:
        if isinstance(alt, list):
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

tt_to_arabic_unmatching = {
    u"a":u"\u064E",
    u"u":u"\u064F",
    u"o":u"\u064F",
    u"i":u"\u0650",
    u"e":u"\u0650",
    u"\u0651":u"\u0651",
    u"-":u""
}

def pre_canonicalize_latin(text):
    text = text.lower()
    # eliminate accents
    text = rsub(text, u".",
        {u"á":u"a", u"é":u"e", u"í":u"i", u"ó":u"o", u"ú":u"u",
         u"ā́":u"ā", u"ḗ":u"ē", u"ī́":u"ī", u"ṓ":u"ō", u"ū́":u"ū"})
    # some accented macron letters have the accent as a separate Unicode char
    text = rsub(text, u".́",
        {u"ā́":u"ā", u"ḗ":u"ē", u"ī́":u"ī", u"ṓ":u"ō", u"ū́":u"ū"})
    # eliminate doubled vowels = long vowels
    text = rsub(text, u"([aeiou])\\1", {u"a":u"ā", u"e":u"ē", u"i":u"ī", u"o":u"ō", u"u":u"ū"})
    # eliminate vowels followed by colon = long vowels
    text = rsub(text, u"([aeiou])[:ː]", {u"a":u"ā", u"e":u"ē", u"i":u"ī", u"o":u"ō", u"u":u"ū"})
    # eliminate - or ' separating t-h, t'h, etc. in transliteration style
    # that uses th to indicate ث
    text = rsub(text, u"([dtgkcs])[-']h", u"\\1h")
    text = rsub(text, u"ūw", u"uww")
    text = rsub(text, u"īy", u"iyy")
    text = rsub(text, u"ai", u"ay")
    text = rsub(text, u"au", u"aw")
    text = rsub(text, u"āi", u"āy")
    text = rsub(text, u"āu", u"āw")
    #text = rsub(text, u"[-]", u"") # eliminate stray hyphens (e.g. in al-)
    # add short vowel before long vowel since corresponding Arabic has it
    text = rsub(text, u".",
        {u"ā":u"aā", u"ē":u"eē", u"ī":u"iī", u"ō":u"oō", u"ū":u"uū"})
    return text

def post_canonicalize_latin(text):
    text = rsub(text, u"aā", u"ā")
    text = rsub(text, u"eē", u"ē")
    text = rsub(text, u"iī", u"ī")
    text = rsub(text, u"oō", u"ō")
    text = rsub(text, u"uū", u"ū")
    # Convert shadda back to double letter
    text = rsub(text, u"(.)\u0651", u"\\1\\1")
    # Implement elision of al- after a word-final vowel. See comments above
    # in tr().
    text = rsub(text, u"([aiuāīū](?:</span>)?) a([" + sun_letters_tr + "]-)",
        u"\\1 \\2")
    return text

# Canonicalize a Latin transliteration to standard form, as much as is
# possible without access to the Arabic (which can be done using
# tr_matching()).
def canonicalize_latin(text):
    text = pre_canonicalize_latin(text)
    # Protect instances of two or more single quotes in a row so they don't
    # get converted to sequences of hamza half-rings.
    def quote_subst(m):
        return m.group(0).replace("'", multi_single_quote_subst)
    text = re.sub(r"''+", quote_subst, text)
    text = rsub(text, u".", tt_canonicalize_latin)
    latin_chars = u"[a-zA-Zāēīōūčḍḏḡḥḵṣšṭṯẓžʿʾ]"
    # Convert 3 to ʿ if next to a letter or letter symbol. This tries
    # to avoid converting 3 in numbers.
    text = rsub(text, u"(%s)3" % latin_chars, u"\\1ʿ")
    text = rsub(text, u"3(%s)" % latin_chars, u"ʿ\\1")
    text = text.replace(multi_single_quote_subst, "'")
    text = post_canonicalize_latin(text)
    return text

def pre_canonicalize_arabic(unvoc):
    # print "unvoc enter: %s" % unvoc
    # shadda+short-vowel (including tanwīn vowels, i.e. -an -in -un) gets
    # replaced with short-vowel+shadda during NFC normalisation, which
    # MediaWiki does for all Unicode strings; however, it makes the
    # transliteration process inconvenient, so undo it.
    unvoc = rsub(unvoc,
        u"([\u064B\u064C\u064D\u064E\u064F\u0650\u0670])\u0651", u"\u0651\\1")
    # tāʾ marbūṭa should always be preceded by fatḥa, alif, alif madda or
    # dagger alif; infer fatḥa if not. This fatḥa will force a match to an "a"
    # in the Latin, so we can safely have tāʾ marbūṭa itself match "h", "t"
    # or "", making it work correctly with alif + tāʾ marbūṭa where
    # e.g. اة = ā and still correctly allow e.g. رة = ra but disallow رة = r.
    unvoc = rsub(unvoc, u"([^\u064E\u0627\u0622\u0670])\u0629",
        u"\\1\u064E\u0629")
    # Final alif or alif maqṣūra following fatḥatan is silent (e.g. in
    # accusative singular or words like عَصًا "stick" or هُذًى "guidance"; this is
    # called tanwin nasb). So substitute special silent versions of these
    # vowels. Will convert back during post-canonicalization.
    unvoc = rsub(unvoc, u"\u064B\u0627", u"\u064B" + silent_alif_subst)
    unvoc = rsub(unvoc, u"\u064B\u0649", u"\u064B" + silent_alif_maqsuura_subst)
    # same but with the fatḥatan placed over the alif or alif maqṣūra
    # instead of over the previous letter (considered a misspelling but
    # common)
    unvoc = rsub(unvoc, u"\u0627\u064B", silent_alif_subst + u"\u064B")
    unvoc = rsub(unvoc, u"\u0649\u064B", silent_alif_maqsuura_subst + u"\u064B")
    # initial al + consonant + shadda: remove shadda
    unvoc = rsub(unvoc, u"(^|\\s|\[\[|\|)([\u0627\u0671]\u064E?\u0644[" + lconsonants + u"])\u0651",
        u"\\1\\2")
    # word-initial al- + sun letter: convert l to assimilating_l_subst; will
    # convert back during post-canonicalization; during tr_matching(),
    # assimilating_l_subst will match the appropriate character, or "l"
    unvoc = rsub(unvoc, u"(^|\\s)(\u0627\u064E?)\u0644([" + sun_letters + "])",
        u"\\1\\2" + assimilating_l_subst + u"\\3")
    unvoc = rsub(unvoc, u"(\u0671\u064E?)\u0644([" + sun_letters + "])",
        u"\\1" + assimilating_l_subst + u"\\2")
    return unvoc

def post_canonicalize_arabic(text):
    text = rsub(text, silent_alif_subst, u"ا")
    text = rsub(text, silent_alif_maqsuura_subst, u"ى")
    text = rsub(text, assimilating_l_subst, u"ل")

    # add sukūn between adjacent consonants, but not in the first part of
    # a link of the sort [[foo|bar]], which we don't vocalize
    splitparts = []
    index = 0
    for part in re.split(r'(\[\[[^]]*\|)', text):
        if (index % 2) == 0:
            part = rsub(part, u"([" + lconsonants + u"])([" + rconsonants + u"])", u"\\1\u0652\\2")
        splitparts.append(part)
        index += 1
    text = ''.join(splitparts)

    # remove sukūn after ḍamma + wāw
    text = rsub(text, u"\u064F\u0648\u0652", u"\u064F\u0648")
    # remove sukūn after kasra + yā'
    text = rsub(text, u"\u0650\u064A\u0652", u"\u0650\u064A")
    # initial al + consonant + sukūn + sun letter: convert to shadda
    text = rsub(text, u"(^|\\s|\[\[|\|)([\u0627\u0671]\u064E?\u0644)\u0652([" + sun_letters + "])",
         u"\\1\\2\\3\u0651")
    return text

# Vocalize Arabic based on transliterated Latin, and canonicalize the
# transliteration based on the Arabic.  This works by matching the Latin
# to the unvocalized Arabic and inserting the appropriate diacritics in
# the right places, so that ambiguities of Latin transliteration can be
# correctly handled. Returns a tuple of Arabic, Latin. If unable to match,
# throw an error if ERR, else return None.
def tr_matching(arabic, latin, err=False):
    latin = pre_canonicalize_latin(latin)
    # convert double consonant to consonant + shadda, but not multiple quotes
    latin = rsub(latin, u"([^'])\\1", u"\\1\u0651")
    arabic = pre_canonicalize_arabic(arabic)

    ar = [] # exploded Arabic characters
    la = [] # exploded Latin characters
    res = [] # result Arabic characters
    lres = [] # result Latin characters
    for cp in arabic:
        ar.append(cp)
    for cp in latin:
        la.append(cp)
    aind = [0] # index of next Arabic character
    alen = len(ar)
    lind = [0] # index of next Latin character
    llen = len(la)

    # attempt to match the current Arabic character against the current
    # Latin character(s). If no match, return False; else, increment the
    # Arabic and Latin pointers over the matched characters, add the Arabic
    # character to the result characters and return True.
    def match():
        ac = ar[aind[0]]
        # uniprint("ac is %s" % ac)
        bow = aind[0] == 0 or ar[aind[0] - 1] in [u" ", u"[", u"|"]
        eow = aind[0] == alen - 1 or ar[aind[0] + 1] in [u" ", u"]", u"|"]

        # Check for link of the form [[foo|bar]] and skip over the part
        # up through the vertical bar, copying it
        if ac == '[':
            newpos = aind[0]
            while newpos < alen and ar[newpos] != ']':
                if ar[newpos] == '|':
                    newpos += 1
                    while aind[0] < newpos:
                        res.append(ar[aind[0]])
                        aind[0] += 1
                    return True
                newpos += 1

        # Special-case handling of the lām that gets assimilated to a sun
        # letter in transliteration. We build up the list of possible
        # matches on the fly according to the following character, which
        # should be a sun letter. We put "l" as a secondary match so that
        # something like al-nūr will get recognized and converted to an-nūr.
        if ac == assimilating_l_subst:
            assert aind[0] < alen - 1
            sunlet = ar[aind[0] + 1]
            assert sunlet in sun_letters
            matches = [ttsun1[sunlet], "l"]
        else:
            matches = (
                bow and tt_to_arabic_matching_bow.get(ac) or
                eow and tt_to_arabic_matching_eow.get(ac) or
                tt_to_arabic_matching.get(ac))
        # uniprint("matches is %s" % matches)
        if matches == None:
            if True:
                error("Encountered non-Arabic (?) character " + ac +
                    " at index " + str(aind[0]))
            else:
                matches = [ac]
        if type(matches) is not list:
            matches = [matches]
        for m in matches:
            preserve_latin = False
            if type(m) is list:
                preserve_latin = True
                m = m[0]
            l = lind[0]
            matched = True
            # uniprint("m: %s" % m)
            for cp in m:
                # uniprint("cp: %s" % cp)
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
                elif ac == u"ة":
                    if not eow:
                        lres.append(u"t")
                    elif aind[0] > 0 and (ar[aind[0] - 1] == u"ا" or
                            ar[aind[0] - 1] == u"آ"):
                        lres.append(u"h")
                    # else do nothing
                else:
                    subst = matches[0]
                    if type(subst) is list:
                        subst = subst[0]
                    for cp in subst:
                        lres.append(cp)
                lind[0] = l
                aind[0] = aind[0] + 1
                # uniprint("matched; lind is %s" % lind[0])
                return True
        return False

    def cant_match():
        if aind[0] < alen and lind[0] < llen:
            error("Unable to match Arabic character %s at index %s, Latin character %s at index %s" %
                (ar[aind[0]], aind[0], la[lind[0]], lind[0]))
        elif aind[0] < alen:
            error("Unable to match trailing Arabic character %s at index %s" %
                (ar[aind[0]], aind[0]))
        else:
            error("Unable to match trailing Latin character %s at index %s" %
                (la[lind[0]], lind[0]))

    # Here we go through the unvocalized Arabic letter for letter, matching
    # up the consonants we encounter with the corresponding Latin consonants
    # using the dict in tt_to_arabic_matching and copying the Arabic
    # consonants into a destination array. When we don't match, we check for
    # allowed unmatching Latin characters in tt_to_arabic_unmatching, which
    # handles short vowels and shadda. If this doesn't match either, and we
    # have left-over Arabic or Latin characters, we reject the whole match,
    # either returning False or signaling an error.

    while aind[0] < alen or lind[0] < llen:
        matched = False
        if aind[0] < alen and match():
            matched = True
        elif lind[0] < llen:
            # uniprint("Unmatched Latin: %s at %s" % (la[lind[0]], lind[0]))
            unmatched = tt_to_arabic_unmatching.get(la[lind[0]])
            if unmatched != None:
                res.append(unmatched)
                lres.append(la[lind[0]])
                lind[0] = lind[0] + 1
                matched = True
        if not matched:
            if err:
                cant_match()
            else:
                return False

    arabic = "".join(res)
    latin = "".join(lres)
    arabic = post_canonicalize_arabic(arabic)
    latin = post_canonicalize_latin(latin)
    return arabic, latin

def tr_matching_arabic(arabic, latin, err=False):
    arabic, latin = tr_matching(arabic, latin, err)
    return arabic

def tr_matching_latin(arabic, latin, err=False):
    arabic, latin = tr_matching(arabic, latin, err)
    return latin

######### Transliterate directly, without unvocalized Arabic to guide #########
#########                         (NEEDS WORK)                        #########

tt_to_arabic_direct = {
    # consonants
    u"b":u"ب", u"t":u"ت", u"ṯ":u"ث", u"θ":u"ث", # u"th":u"ث",
    u"j":u"ج",
    u"ḥ":u"ح", u"ħ":u"ح", u"ḵ":u"خ", u"x":u"خ", # u"kh":u"خ",
    u"d":u"د", u"ḏ":u"ذ", u"ð":u"ذ", u"đ":u"ذ", # u"dh":u"ذ",
    u"r":u"ر", u"z":u"ز", u"s":u"س", u"š":u"ش", # u"sh":u"ش",
    u"ṣ":u"ص", u"ḍ":u"ض", u"ṭ":u"ط", u"ẓ":u"ظ",
    u"ʿ":u"ع", u"ʕ":u"ع",
    u"`":u"ع",
    u"3":u"ع",
    u"ḡ":u"غ", u"ġ":u"غ", u"ğ":u"غ",  # u"gh":u"غ",
    u"f":u"ف", u"q":u"ق", u"k":u"ك", u"l":u"ل", u"m":u"م", u"n":u"ن",
    u"h":u"ه",
    # u"a":u"ة", u"ah":u"ة"
    # tāʾ marbūṭa (special) - always after a fátḥa (a), silent at the end of
    # an utterance, "t" in ʾiḍāfa or with pronounced tanwīn
    # \u0629 = tāʾ marbūṭa = ة
    # control characters
    # zwj:u"", # ZWJ (zero-width joiner)
    # rare letters
    u"p":u"پ", u"č":u"چ", u"v":u"ڤ", u"g":u"گ",
    # semivowels or long vowels, alif, hamza, special letters
    u"ā":u"\u064Eا", # ʾalif = \u0627
    # u"aa":u"\u064Eا", u"a:":u"\u064Eا"
    # hamzated letters
    u"ʾ":u"ء",
    u"’":u"ء",
    u"'":u"ء",
    u"w":u"و",
    u"y":u"ي",
    u"ū":u"\u064Fو", # u"uu":u"\u064Fو", u"u:":u"\u064Fو"
    u"ī":u"\u0650ي", # u"ii":u"\u0650ي", u"i:":u"\u0650ي"
    # u"ā":u"ى", # ʾalif maqṣūra = \u0649
    # u"an":u"\u064B" = fatḥatan
    # u"un":u"\u064C" = ḍammatan
    # u"in":u"\u064D" = kasratan
    u"a":u"\u064E", # fatḥa
    u"u":u"\u064F", # ḍamma
    u"i":u"\u0650", # kasra
    # \u0651 = šadda - doubled consonant
    # u"\u0652":u"", #sukūn - no vowel
    # ligatures
    # u"ﻻ":u"lā",
    # u"ﷲ":u"llāh",
    # taṭwīl
    # numerals
    u"1":u"١", u"2":u"٢",# u"3":u"٣",
    u"4":u"٤", u"5":u"٥",
    u"6":u"٦", u"7":u"٧", u"8":u"٨", u"9":u"٩", u"0":u"٠",
    # punctuation (leave on separate lines)
    u"?":u"؟", # question mark
    u",":u"،", # comma
    u";":u"؛" # semicolon
}

# Transliterate any words or phrases from Latin into Arabic script.
# POS, if not None, is e.g. "noun" or "verb", controlling how to handle
# final -a.
#
# FIXME: NEEDS WORK. Works but ignores POS. Doesn't yet generate the correct
# seat for hamza (need to reuse code in Module:ar-verb to do this). Always
# transliterates final -a as fatḥa, never as tāʾ marbūṭa (should make use of
# POS for this). Doesn't (and can't) know about cases where sh, th, etc.
# stand for single letters rather than combinations.
def tr_latin_direct(text, pos):
    text = pre_canonicalize_latin(text)
    text = rsub(text, u"ah$", u"\u064Eة")
    text = rsub(text, u"āh$", u"\u064Eاة")
    text = rsub(text, u".", tt_to_arabic_direct)
    # convert double consonant to consonant + shadda
    text = rsub(text, u"([" + lconsonants + u"])\\1", u"\\1\u0651")
    text = post_canonicalize_arabic(text)

    return text

num_failed = 0
num_succeeded = 0

def test(latin, arabic, should_outcome):
    global num_succeeded, num_failed
    try:
        result = tr_matching(arabic, latin, True)
    except RuntimeError as e:
        uniprint(u"%s" % e)
        result = False
    if result == False:
        uniprint("tr_matching(%s, %s) = %s" % (arabic, latin, result))
        outcome = "failed"
    else:
        vocarabic, canonlatin = result
        trlatin = tr(vocarabic)
        uniout("tr_matching(%s, %s) = %s %s," %
                (arabic, latin, vocarabic, canonlatin))
        if trlatin == canonlatin:
            uniprint("tr() MATCHED")
            outcome = "matched"
        else:
            uniprint("tr() UNMATCHED (= %s)" % trlatin)
            outcome = "unmatched"
    uniprint("canonicalize_latin(%s) = %s" %
            (latin, canonicalize_latin(latin)))
    if outcome == should_outcome:
        uniprint("TEST SUCCEEDED.")
        num_succeeded += 1
    else:
        uniprint("TEST FAILED.")
        num_failed += 1

def run_tests():
    global num_succeeded, num_failed
    num_succeeded = 0
    num_failed = 0
    test("katab", u"كتب", "matched")
    test("kattab", u"كتب", "matched")
    test(u"kátab", u"كتب", "matched")
    test("katab", u"كتبٌ", "matched")
    test("kat", u"كتب", "failed") # should fail
    test("kataban", u"كتب", "failed") # should fail?
    test("dakhala", u"دخل", "matched")
    test("al-dakhala", u"الدخل", "matched")
    test("ad-dakhala", u"الدخل", "matched")
    test("al-la:zim", u"اللازم", "matched")
    test("al-bait", u"البيت", "matched")
    test("wa-dakhala", u"ودخل", "unmatched")
    # The Arabic of the following consists of wāw + fatḥa + ZWJ + dāl + ḵāʾ + lām.
    test("wa-dakhala", u"وَ‍دخل", "matched")
    # The Arabic of the following two consists of wāw + ZWJ + dāl + ḵāʾ + lām.
    test("wa-dakhala", u"و‍دخل", "matched")
    test("wadakhala", u"و‍دخل", "failed") # should fail, ZWJ must match hyphen
    test("wadakhala", u"ودخل", "matched")
    # Six different ways of spelling a long ū. uw should be preserved, others
    # mapped to ū. (We could avoid preserving uw if we were more sophisticated in
    # distinguishing uw+vowel (to be left alone), uww (currently to be left alone,
    # but could reasonably be argued to be normalized to ūw), uw+consonant
    # (to be normalized) and final uw (to be normalized).
    test("duuba", u"دوبة", "matched")
    test(u"dúuba", u"دوبة", "matched")
    test("duwba", u"دوبة", "unmatched")
    test("du:ba", u"دوبة", "matched")
    test(u"dūba", u"دوبة", "matched")
    test(u"dū́ba", u"دوبة", "matched")
    # w definitely as a consonant, should be preserved
    test("duwaba", u"دوبة", "matched")

    # Similar but for ī and y
    test("diiba", u"ديبة", "matched")
    test(u"díiba", u"ديبة", "matched")
    test("diyba", u"ديبة", "unmatched")
    test("di:ba", u"ديبة", "matched")
    test(u"dība", u"ديبة", "matched")
    test(u"dī́ba", u"ديبة", "matched")
    test("diyaba", u"ديبة", "matched")

    # Test o's and e's
    test(u"dōba", u"دوبة", "unmatched")
    test(u"dōba", u"دُوبة", "unmatched")
    test(u"telefōn", u"تلفون", "unmatched")

    # Test handling of tāʾ marbūṭa
    # test of "duuba" already done above.
    test("duubah", u"دوبة", "matched") # should be reduced to -a
    test("duubaa", u"دوباة", "matched") # should become -āh
    test("duubaah", u"دوباة", "matched") # should become -āh
    test("mir'aah", u"مرآة", "matched") # should become -āh

    # Test the definite article and its rendering in Arabic
    test("al-duuba", u"اَلدّوبة", "matched")
    test("al-duuba", u"الدّوبة", "matched")
    test("al-duuba", u"الدوبة", "matched")
    test("ad-duuba", u"اَلدّوبة", "matched")
    test("ad-duuba", u"الدّوبة", "matched")
    test("ad-duuba", u"الدوبة", "matched")
    test("al-kuuba", u"اَلْكوبة", "matched")
    test("al-kuuba", u"الكوبة", "matched")
    test("baitu l-kuuba", u"بيت الكوبة", "matched")
    test("baitu al-kuuba", u"بيت الكوبة", "matched")
    test("baitu d-duuba", u"بيت الدوبة", "matched")
    test("baitu ad-duuba", u"بيت الدوبة", "matched")
    test("baitu l-duuba", u"بيت الدوبة", "matched")
    test("baitu al-duuba", u"بيت الدوبة", "matched")
    test("bait al-kuuba", u"بيت الكوبة", "matched")
    test("baitu l-kuuba", u"بيت ٱلكوبة", "matched")

    # Test handling of tāʾ marbūṭa when non-final
    test("ghurfatu l-kuuba", u"غرفة الكوبة", "matched")
    test("ghurfatun al-kuuba", u"غرفةٌ الكوبة", "matched")
    test("al-ghurfatu l-kuuba", u"الغرفة الكوبة", "matched")
    test("ghurfat al-kuuba", u"غرفة الكوبة", "unmatched")
    test("ghurfa l-kuuba", u"غرفة الكوبة", "unmatched")
    test("ghurfa(t) al-kuuba", u"غرفة الكوبة", "matched")
    test("ghurfatu l-kuuba", u"غرفة ٱلكوبة", "matched")
    test("ghurfa l-kuuba", u"غرفة ٱلكوبة", "unmatched")
    test("ghurfa", u"غرفةٌ", "matched")

    # Test handling of embedded links
    test(u"’ālati l-fam", u"[[آلة]] [[فم|الفم]]", "matched")
    test(u"arqām hindiyya", u"[[أرقام]] [[هندية]]", "matched")
    test(u"ʾufuq al-ħadaŧ", u"[[أفق]] [[حادثة|الحدث]]", "matched")

    # Test transliteration that omits initial hamza (should be inferrable)
    test(u"aṣdiqaa'", u"أَصدقاء", "matched")
    test(u"aṣdiqā́'", u"أَصدقاء", "matched")
    # Test random hamzas
    test(u"'aṣdiqā́'", u"أَصدقاء", "matched")
    # Test capital letters for emphatics
    test(u"aSdiqaa'", u"أَصدقاء", "matched")
    # Test final otiose alif maqṣūra after fatḥatan
    test("hudan", u"هُدًى", "matched")
    # Check that final short Latin letter doesn't match to final
    # long vowel (this check is already present) and that an error doesn't
    # occur
    test("'animi", u"أنمي", "failed") # should fail and return None

    # Single quotes in Arabic
    test("man '''huwa'''", u"من '''هو'''", "matched")

    # Alif madda
    test("'aabaa'", u"آباء", "matched")
    test("mir'aah", u"مرآة", "matched")

    # Bugs: This gets tr-matched into qiṭunn instead of qiṭṭun.
    test(u"qiṭṭ", u"قِطٌ", "unmatched")

    # Final results
    uniprint("RESULTS: %s SUCCEEDED, %s FAILED." % (num_succeeded, num_failed))

if __name__ == "__main__":
    run_tests()

# For Vim, so we get 4-space indent
# vim: set sw=4:
