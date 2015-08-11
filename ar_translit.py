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

import re, unicodedata
import arabiclib
from arabiclib import *
from blib import remove_links, msg

# FIXME!! To do:
#
# 1. Modify Module:ar-translit to convert – (long dash) into regular -;
#    also need extra clause in has_diacritics_subs (2nd one)
# 2. alif madda should match against 'a with short a

# STATUS:
#
# OK to run. We actually did a run saving the results, using a page file,
# like this:
#
# python canon_arabic.py --cattype pages --page-file canon_arabic.4+14.saved-pages.out --save >! canon_arabic.15.saved-pages.save.out
#
# But it was interrupted partway through.
#
# Wrote parse_log_file.py to create a modified log file suitable for editing
# to allow manual changes to be saved rapidly (using a not-yet-written script,
# presumably modeled on undo_greek_removal.py).

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

def nfkc_form(txt):
    return unicodedata.normalize("NFKC", unicode(txt))

def nfc_form(txt):
    return unicodedata.normalize("NFC", unicode(txt))

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
    # tāʾ marbūṭa (special) - always after a fatḥa (a), silent at the end of
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
    u"\u064B":u"an", # fatḥatān
    u"\u064C":u"un", # ḍammatān
    u"\u064D":u"in", # kasratān
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
    u"؛":u";", # semicolon
    u"–":u"-", # long dash
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
    # ignore final alif or alif maqṣūra following fatḥatān (e.g. in accusative
    # singular or words like عَصًا "stick" or هُذًى "guidance"; this is called
    # tanwīn nasb)
    [u"\u064B[\u0627\u0649]", u"\u064B"],
    # same but with the fatḥatān placed over the alif or alif maqṣūra
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

# Transliterate the word(s) in TEXT. LANG (the language) and SC (the script)
# are ignored. OMIT_I3RAAB means leave out final short vowels (ʾiʿrāb).
# GRAY_I3RAAB means render transliterate short vowels (ʾiʿrāb) in gray.
# FORCE_TRANSLATE causes even non-vocalized text to be transliterated
# (normally the function checks for non-vocalized text and returns nil,
# since such text is ambiguous in transliteration).
def tr(text, lang=None, sc=None, omit_i3raab=False, gray_i3raab=False,
        force_translate=False, msgfun=msg):
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
    # Ignore final tāʾ marbūṭa (it appears as "a" due to the preceding
    # short vowel). Need to do this after graying or omitting word-final
    # ʾiʿrāb.
    text = rsub(text, u"\u0629$", u"")
    if not omit_i3raab: # show ʾiʿrāb in transliteration
        text = rsub(text, u"\u0629\\s", u"(t) ")
    else:
        # When omitting ʾiʿrāb, show all non-absolutely-final instances of
        # tāʾ marbūṭa as (t), with trailing ʾiʿrāb omitted.
        text = rsub(text, u"\u0629", u"(t)")
    # tatwīl should be rendered as - at beginning or end of word. It will
    # be rendered as nothing in the middle of a word (FIXME, do we want
    # this?)
    text = rsub(text, u"^ـ", "-")
    text = rsub(text, u"\\sـ", " -")
    text = rsub(text, u"ـ$", "-")
    text = rsub(text, u"ـ\\s", "- ")
    # Now convert remaining Arabic chars according to table.
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
    # Special-case the transliteration of allāh, without the hyphen
    text = rsub(text, u"(^|\\s)(a?)l-lāh", u"\\1\\2llāh")

    return text

has_diacritics_subs = [
    # FIXME! What about lam-alif ligature?
    # remove punctuation and shadda
    # must go before removing final consonants
    [u"[" + punctuation + u"\u0651]", u""],
    # Convert dash/hyphen to space so we can handle cases like وَيْد–جَيْلْز
    # "wayd-jaylz" (Wade-Giles).
    [u"[-–]", u" "],
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
    # remove fatḥa/fatḥatān + alif/alif-maqṣūra
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
double_l_subst = u"\ufff5"
dagger_alif_subst = u"\ufff6"

hamza_match = [u"ʾ",u"ʼ",u"'",u"´",(u"`",),u"ʔ",u"’",(u"‘",),u"ˀ",
        (u"ʕ",),(u"ʿ",),u"2"]
hamza_match_or_empty = hamza_match + [u""]
hamza_match_chars = [x[0] if isinstance(x, list) or isinstance(x, tuple) else x
        for x in hamza_match]

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
    UN:[u"un",u""], # ḍammatān
    IN:[u"in",u""], # kasratān
    A:[u"a",u""], # fatḥa (in plurals)
    U:[u"u",u""], # ḍamma (in diptotes)
    I:[u"i",u""], # kasra (in duals)
}

# This dict maps Arabic characters to all the Latin characters that
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
# somewhere-else. (For example, ` occurs as a match for both ʿ and ʾ;
# in the latter's list, it is a one-element tuple, meaning during
# self-canonicalization it will get canonicalized into ʿ and not left
# alone, as it otherwise would due to occurring as a match for multiple
# characters.)
#
# Each string might have multiple characters, to handle things
# like خ=kh and ث=th.

tt_to_arabic_matching = {
    # consonants
    u"ب":[u"b",[u"p"]], u"ت":u"t",
    u"ث":[u"ṯ",u"ŧ",u"θ",u"th"],
    # FIXME! We should canonicalize ʒ to ž
    u"ج":[u"j",u"ǧ",u"ğ",u"ǰ",u"dj",u"dǧ",u"dğ",u"dǰ",u"dž",u"dʒ",[u"ʒ"],
        [u"ž"],[u"g"]],
    # Allow what would normally be capital H, but we lowercase all text
    # before processing; always put the plain letters last so previous longer
    # sequences match (which may be letter + combining char).
    # I feel a bit uncomfortable allowing kh to match against ح like this,
    # but generally I trust the Arabic more.
    u"ح":[u"ḥ",u"ħ",u"ẖ",u"ḩ",u"7",(u"kh",),u"h"],
    # I feel a bit uncomfortable allowing ḥ to match against خ like this,
    # but generally I trust the Arabic more.
    u"خ":[u"ḵ",u"kh",u"ḫ",u"ḳ",u"ẖ",u"χ",(u"ḥ",),u"x"],
    u"د":u"d",
    u"ذ":[u"ḏ",u"đ",u"ð",u"dh",u"ḍ",u"ẕ",u"d"],
    u"ر":u"r",
    u"ز":u"z",
    # I feel a bit uncomfortable allowing emphatic variants of s to match
    # against س like this, but generally I trust the Arabic more.
    u"س":[u"s",(u"ṣ",),(u"sʿ",),(u"sˤ",),(u"sˁ",),(u"sʕ",),(u"ʂ",),(u"ṡ",)],
    u"ش":[u"š",u"sh",u"ʃ"],
    # allow non-emphatic to match so we can handle uppercase S, D, T, Z;
    # we lowercase the text before processing to handle proper names and such;
    # always put the plain letters last so previous longer sequences match
    # (which may be letter + combining char)
    u"ص":[u"ṣ",u"sʿ",u"sˤ",u"sˁ",u"sʕ",u"ʂ",u"ṡ",u"s"],
    u"ض":[u"ḍ",u"dʿ",u"dˤ"u"dˁ",u"dʕ",u"ẓ",u"ɖ",u"ḋ",u"d"],
    u"ط":[u"ṭ",u"tʿ",u"tˤ",u"tˁ",u"tʕ",u"ṫ",u"ţ",u"ŧ",u"ʈ",u"t̤",u"t"],
    u"ظ":[u"ẓ",u"ðʿ",u"ðˤ",u"ðˁ",u"ðʕ",u"ð̣",u"đʿ",u"đˤ",u"đˁ",u"đʕ",u"đ̣",
        u"ż",u"ʐ",u"dh",u"z"],
    u"ع":[u"ʿ",u"ʕ",u"`",u"‘",u"ʻ",u"3",u"ˤ",u"ˁ",(u"'",),(u"ʾ",),u"῾",(u"’",)],
    u"غ":[u"ḡ",u"ġ",u"ğ",u"gh",[u"g"],(u"`",)],
    u"ف":[u"f",[u"v"]],
    # I feel a bit uncomfortable allowing k to match against q like this,
    # but generally I trust the Arabic more
    u"ق":[u"q",u"ḳ",[u"g"],u"k"],
    u"ك":[u"k",[u"g"]],
    u"ل":u"l",
    u"م":u"m",
    u"ن":u"n",
    u"ه":u"h",
    # We have special handling for the following in the canonicalized Latin,
    # so that we have -a but -āh and -at-.
    u"ة":[u"h",[u"t"],[u"(t)"],u""],
    # control characters
    # The following are unnecessary because we handle them specially in
    # check_against_hyphen() and other_arabic_chars.
    #zwnj:[u"-"],#,u""], # ZWNJ (zero-width non-joiner)
    #zwj:[u"-"],#,u""], # ZWJ (zero-width joiner)
    # rare letters
    u"پ":u"p",
    u"چ":[u"č",u"ch"],
    u"ڤ":u"v",
    u"گ":u"g",
    u"ڨ":u"g",
    u"ڧ":u"q",
    # semivowels or long vowels, alif, hamza, special letters
    u"ا":u"ā", # ʾalif = \u0627
    # put empty string in list so not considered logically false, which can
    # mess with the logic
    silent_alif_subst:[u""],
    silent_alif_maqsuura_subst:[u""],
    # hamzated letters
    u"أ":hamza_match,
    u"إ":hamza_match,
    u"ؤ":hamza_match,
    u"ئ":hamza_match,
    u"ء":hamza_match,
    u"و":[[u"w"],[u"ū"],[u"ō"], u"v"],
    # Adding j here creates problems with e.g. an-nijir vs. النيجر
    u"ي":[[u"y"],[u"ī"],[u"ē"]], #u"j",
    u"ى":u"ā", # ʾalif maqṣūra = \u0649
    u"آ":[u"ʾaā",u"’aā",u"'aā",u"`aā"], # ʾalif madda = \u0622
    # put empty string in list so not considered logically false, which can
    # mess with the logic
    u"ٱ":[u""], # hamzatu l-waṣl = \u0671
    u"\u0670":u"aā", # ʾalif xanjariyya = dagger ʾalif (Koranic diacritic)
    # short vowels, šadda and sukūn
    u"\u064B":u"an", # fatḥatān
    u"\u064C":u"un", # ḍammatān
    u"\u064D":u"in", # kasratān
    u"\u064E":u"a", # fatḥa
    u"\u064F":[[u"u"],[u"o"]], # ḍamma
    u"\u0650":[[u"i"],[u"e"]], # kasra
    u"\u0651":u"\u0651", # šadda - handled specially when matching Latin šadda
    double_l_subst:u"\u0651", # handled specially when matching šadda in Latin
    u"\u0652":u"", #sukūn - no vowel
    # ligatures
    u"ﻻ":u"lā",
    u"ﷲ":u"llāh",
    # put empty string in list so not considered logically false, which can
    # mess with the logic
    u"ـ":[u""], # taṭwīl, no sound
    # numerals
    u"١":u"1", u"٢":u"2", u"٣":u"3", u"٤":u"4", u"٥":u"5",
    u"٦":u"6", u"٧":u"7", u"٨":u"8", u"٩":u"9", u"٠":u"0",
    # punctuation (leave on separate lines)
    u"؟":u"?", # question mark
    u"،":u",", # comma
    u"؛":u";", # semicolon
    u".":u".", # period
    u"!":u"!", # exclamation point
    u"'":[(u"'",)], # single quote, for bold/italic
    u" ":u" ",
    u"[":u"",
    u"]":u"",
    # The following are unnecessary because we handle them specially in
    # check_against_hyphen() and other_arabic_chars.
    #u"-":u"-",
    #u"–":u"-",
}

# exclude consonants like h ʿ ʕ ʕ that can occur second in a two-charcter
# sequence, because of cases like u"múdhhil" vs. u"مذهل"
latin_consonants_no_double_after_cons = u"bcdfgjklmnpqrstvwxyzʾʔḍḥḳḷṃṇṛṣṭṿẉỵẓḃċḋḟġḣṁṅṗṙṡṫẇẋẏżčǧȟǰňřšžḇḏẖḵḻṉṟṯẕḡs̄z̄çḑģḩķļņŗşţz̧ćǵḱĺḿńṕŕśẃźďľťƀđǥħłŧƶğḫʃɖʈt̤ð"
latin_consonants_no_double_after_cons_re = "[%s]" % (
        latin_consonants_no_double_after_cons)

# Characters that aren't in tt_to_arabic_matching but which are valid
# Arabic characters in some circumstances (in particular, opposite a hyphen,
# where they are matched in check_against_hyphen()). We need to tell
# get_matches() about this so it doesn't throw an "Encountered non-Arabic"
# error, but instead just returns an empty list of matches so match() will
# properly fail.
other_arabic_chars = [zwj, zwnj, "-", u"–"]

word_interrupting_chars = u"ـ[]"

build_canonicalize_latin = {}
for ch in u"abcdefghijklmnopqrstuvwyz3": # x not in this list! canoned to ḵ
    build_canonicalize_latin[ch] = "multiple"
build_canonicalize_latin[""] = "multiple"

# Make sure we don't canonicalize any canonical letter to any other one;
# e.g. could happen with ʾ, an alternative for ʿ.
for arabic in tt_to_arabic_matching:
    alts = tt_to_arabic_matching[arabic]
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

for arabic in tt_to_arabic_matching:
    alts = tt_to_arabic_matching[arabic]
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

# A list of Latin characters that are allowed to have particular unmatched
# Arabic characters following. This is used to allow short Latin vowels
# to correspond to long Arabic vowels. The value is the list of possible
# unmatching Arabic characters.
tt_skip_unmatching = {
    u"a":[u"ا"],
    u"u":[u"و"],
    u"o":[u"و"],
    u"i":[u"ي"],
    u"e":[u"ي"],
}

# A list of Latin characters that are allowed to be unmatched in the
# Arabic. The value is the corresponding Arabic character to insert.
tt_to_arabic_unmatching = {
    u"a":u"\u064E",
    u"u":u"\u064F",
    u"o":u"\u064F",
    u"i":u"\u0650",
    u"e":u"\u0650",
    # Rather than inserting DAGGER_ALIF directly, insert a special character
    # and convert it later, absorbing a previous fatḥa. We don't simply
    # absorb fatḥa before DAGGER_ALIF in post-canonicalization because
    # Wikitiki89 says the sequence fatḥa + DAGGER_ALIF is Koranic, and will
    # revert attempts to remove the fatḥa.
    u"ā":dagger_alif_subst,
    u"\u0651":u"\u0651",
    u"-":u"",
}

# Pre-canonicalize Latin, and Arabic if supplied. If Arabic is supplied,
# it should be the corresponding Arabic (after pre-pre-canonicalization),
# and is used to do extra canonicalizations.
def pre_canonicalize_latin(text, arabic=None, msgfun=msg):
    # Map to canonical composed form, eliminate presentation variants etc.
    text = nfkc_form(text)
    # remove L2R, R2L markers
    text = rsub(text, u"[\u200E\u200F]", "")
    # remove embedded comments
    text = rsub(text, u"<!--.*?-->", "")
    # remove embedded IPAchar templates
    text = rsub(text, r"\{\{IPAchar\|(.*?)\}\}", r"\1")
    # lowercase and remove leading/trailing spaces
    text = text.lower().strip()
    # canonicalize interior whitespace
    text = rsub(text, r"\s+", " ")
    # eliminate ' after space or - and before non-vowel, indicating elided /a/
    text = rsub(text, r"([ -])'([^'aeiouəāēīōū])", r"\1\2")
    # eliminate accents
    text = rsub(text, u".",
        {u"á":u"a", u"é":u"e", u"í":u"i", u"ó":u"o", u"ú":u"u",
         u"à":u"a", u"è":u"e", u"ì":u"i", u"ò":u"o", u"ù":u"u",
         u"ă":u"a", u"ĕ":u"e", u"ĭ":u"i", u"ŏ":u"o", u"ŭ":u"u",
         u"ā́":u"ā", u"ḗ":u"ē", u"ī́":u"ī", u"ṓ":u"ō", u"ū́":u"ū",
         u"ä":u"a", u"ë":u"e", u"ï":u"i", u"ö":u"o", u"ü":u"u"})
    # some accented macron letters have the accent as a separate Unicode char
    text = rsub(text, u".́",
        {u"ā́":u"ā", u"ḗ":u"ē", u"ī́":u"ī", u"ṓ":u"ō", u"ū́":u"ū"})
    # canonicalize weird vowels
    text = text.replace(u"ɪ", "i")
    text = text.replace(u"ɑ", "a")
    text = text.replace(u"æ", "a")
    text = text.replace(u"а", "a") # Cyrillic a
    # eliminate doubled vowels = long vowels
    text = rsub(text, u"([aeiou])\\1", {u"a":u"ā", u"e":u"ē", u"i":u"ī", u"o":u"ō", u"u":u"ū"})
    # eliminate vowels followed by colon = long vowels
    text = rsub(text, u"([aeiou])[:ː]", {u"a":u"ā", u"e":u"ē", u"i":u"ī", u"o":u"ō", u"u":u"ū"})
    # convert circumflexed vowels to long vowels
    text = rsub(text, u".",
        {u"â":u"ā", u"ê":u"ē", u"î":u"ī", u"ô":u"ō", u"û":u"ū"})
    # eliminate - or ' separating t-h, t'h, etc. in transliteration style
    # that uses th to indicate ث
    text = rsub(text, u"([dtgkcs])[-']h", u"\\1h")
    # substitute geminated digraphs, possibly with a hyphen in the middle
    text = rsub(text, u"dh(-?)dh", ur"ḏ\1ḏ")
    text = rsub(text, u"sh(-?)sh", ur"š\1š")
    text = rsub(text, u"th(-?)th", ur"ṯ\1ṯ")
    text = rsub(text, u"kh(-?)kh", ur"ḵ\1ḵ")
    text = rsub(text, u"gh(-?)gh", ur"ḡ\1ḡ")
    # misc substitutions
    text = rsub(text, u"ẗ$", "")
    # cases like fi 'l-ḡad(i) -> eventually fi l-ḡad
    text = rsub(text, r"\([aiu]\)($|[ |\[\]])", r"\1")
    text = rsub(text, r"\(tun\)$", "")
    text = rsub(text, r"\(un\)$", "")
    #### vowel/diphthong canonicalizations
    text = rsub(text, u"([aeiouəāēīōū])u", r"\1w")
    text = rsub(text, u"([aeiouəāēīōū])i", r"\1y")
    # Convert -iy- not followed by a vowel or y to long -ī-
    text = rsub(text, u"iy($|[^aeiouəyāēīōū])", ur"ī\1")
    # Same for -uw- -> -ū-
    text = rsub(text, u"uw($|[^aeiouəwāēīōū])", ur"ū\1")
    # Insert y between i and a
    text = rsub(text, u"([iī])([aā])", r"\1y\2")
    # Insert w between u and a
    text = rsub(text, u"([uū])([aā])", r"\1w\2")
    text = rsub(text, u"īy", u"iyy")
    text = rsub(text, u"ūw", u"uww")
    # Reduce cases of three characters in a row (e.g. from īyy -> iyyy -> iyy);
    # but not ''', which stands for boldface, or ..., which is legitimate
    text = rsub(text, r"([^'.])\1\1", r"\1\1")
    # Remove double consonant following another consonant, but only at
    # word boundaries, since that's the only time when these cases seem to
    # legitimately occur
    text = re.sub(ur"([^aeiouəāēīōū\W])(%s)\2\b" % (
        latin_consonants_no_double_after_cons_re), r"\1\2", text, 0, re.U)
    # Remove double consonant preceding another consonant but special-case
    # a known example that shouldn't be touched.
    if text != u"dunḡḡwān":
        text = re.sub(ur"([^aeiouəāēīōū\W])\1(%s)" % (
            latin_consonants_no_double_after_cons_re), r"\1\2", text, 0, re.U)
    if arabic:
        # Remove links from Arabic to simplify the following code
        arabic = remove_links(arabic)
        # If Arabic ends with -un, remove it from the Latin (it will be
        # removed from Arabic in pre-canonicalization). But not if the
        # Arabic has a space in it (may be legitimate, in Koranic quotes or
        # whatever).
        if arabic.endswith(u"\u064C") and " " not in arabic:
            newtext = rsub(text, "un$", "")
            if newtext != text:
                msgfun("Removing final -un from Latin %s" % text)
                text = newtext
            # Now remove -un from the Arabic.
            arabic = rsub(arabic, u"\u064C$", "")
        # If Arabic ends with tāʾ marbūṭa, canonicalize some Latin endings
        # right now. Only do this at the end of the text, not at the end
        # of each word, since an Arabic word in the middle might be in the
        # construct state.
        if arabic.endswith(u"اة"):
            text = rsub(text, ur"ā(\(t\)|t)$", u"āh")
        elif arabic.endswith(u"ة"):
            text = rsub(text, r"[ae](\(t\)|t)$", "a")
        # Do certain end-of-word changes on each word, comparing corresponding
        # Latin and Arabic words ...
        arabicwords = re.split(u" +", arabic)
        latinwords = re.split(u" +", text)
        # ... but only if the number of words in both is the same.
        if len(arabicwords) == len(latinwords):
            for i in xrange(len(latinwords)):
                aword = arabicwords[i]
                lword = latinwords[i]
                # If Arabic word ends with long alif or alif maqṣūra, not
                # preceded by fatḥatān, convert short -a to long -ā.
                if (re.search(u"[اى]$", aword) and not
                        re.search(u"\u064B[اى]$", aword)):
                    lword = rsub(lword, r"a$", u"ā")
                # If Arabic word ends in -yy, convert Latin -i/-ī to -iyy
                # If the Arabic actually ends in -ayy or similar, this should
                # have no effect because in any vowel+i combination, we
                # changed i->y
                if re.search(u"يّ$", aword):
                    lword = rsub(lword, u"[iī]$", "iyy")
                # If Arabic word ends in -y preceded by sukūn, assume
                # correct and convert final Latin -i/ī to -y.
                if re.search(u"\u0652ي$", aword):
                    lword = rsub(lword, u"[iī]$", "y")
                # Otherwise, if Arabic word ends in -y, convert Latin -i to -ī
                # WARNING: Many of these should legitimately be converted
                # to -iyy or perhaps (sukūn+)-y both in Arabic and Latin, but
                # it's impossible for us to know this.
                elif re.search(u"ي$", aword):
                    lword = rsub(lword, "i$", u"ī")
                # Except same logic, but for u/w vs. i/y
                if re.search(u"وّ$", aword):
                    lword = rsub(lword, u"[uū]$", "uww")
                if re.search(u"\u0652و$", aword):
                    lword = rsub(lword, u"[uū]$", "w")
                elif re.search(u"و$", aword):
                    lword = rsub(lword, "u$", u"ū")
                # Echo a final exclamation point in the Latin
                if re.search("!$", aword) and not re.search("!$", lword):
                    lword += "!"
                # Same for a final question mark
                if re.search(u"؟$", aword) and not re.search(u"\?$", lword):
                    lword += "?"
                latinwords[i] = lword
            text = " ".join(latinwords)
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
    text = text.lower().strip()
    return text

# Canonicalize a Latin transliteration and Arabic text to standard form.
# Can be done on only Latin or only Arabic (with the other one None), but
# is more reliable when both aare provided. This is less reliable than
# tr_matching() and is meant when that fails. Return value is a tuple of
# (CANONLATIN, CANONARABIC).
def canonicalize_latin_arabic(latin, arabic, msgfun=msg):
    if arabic is not None:
        arabic = pre_pre_canonicalize_arabic(arabic, msgfun=msgfun)
    if latin is not None:
        latin = pre_canonicalize_latin(latin, arabic, msgfun=msgfun)
    if arabic is not None:
        arabic = pre_canonicalize_arabic(arabic, safe=True, msgfun=msgfun)
        arabic = post_canonicalize_arabic(arabic, safe=True)
    if latin is not None:
        # Protect instances of two or more single quotes in a row so they don't
        # get converted to sequences of hamza half-rings.
        def quote_subst(m):
            return m.group(0).replace("'", multi_single_quote_subst)
        latin = re.sub(r"''+", quote_subst, latin)
        latin = rsub(latin, u".", tt_canonicalize_latin)
        latin_chars = u"[a-zA-Zāēīōūčḍḏḡḥḵṣšṭṯẓžʿʾ]"
        # Convert 3 to ʿ if next to a letter or letter symbol. This tries
        # to avoid converting 3 in numbers.
        latin = rsub(latin, u"(%s)3" % latin_chars, u"\\1ʿ")
        latin = rsub(latin, u"3(%s)" % latin_chars, u"ʿ\\1")
        latin = latin.replace(multi_single_quote_subst, "'")
        latin = post_canonicalize_latin(latin)
    return (latin, arabic)

# Special-casing for punctuation-space and diacritic-only text; don't
# pre-canonicalize.
def dont_pre_canonicalize_arabic(text):
    if u"\u2008" in text:
        return True
    rdtext = remove_diacritics(text)
    if len(rdtext) == 0:
        return True
    if rdtext == u"ـ":
        return True
    return False

# Early pre-canonicalization of Arabic, doing stuff that's safe. We split
# this from pre-canonicalization proper so we can do Latin pre-canonicalization
# between the two steps.
def pre_pre_canonicalize_arabic(text, msgfun=msg):
    if dont_pre_canonicalize_arabic(text):
        msgfun("Not pre-canonicalizing %s due to U+2008 or overly short" %
                text)
        return text
    # Map to canonical composed form, eliminate presentation variants.
    # But don't do it if word ligatures are present or length-1 words with
    # presentation variants, because we want to leave those alone.
    if (not re.search(u"[\uFDF0-\uFDFF]", text)
            and not re.search(u"(^|[\\W])[\uFB50-\uFDCF\uFE70-\uFEFF]($|[\\W])",
                text, re.U)):
        text = nfkc_form(text)
    # remove L2R, R2L markers
    text = rsub(text, u"[\u200E\u200F]", "")
    # remove leading/trailing spaces;
    text = text.strip()
    # canonicalize interior whitespace
    text = rsub(text, r"\s+", " ")
    # replace Farsi, etc. characters with corresponding Arabic characters
    text = text.replace(u"ی", u"ي") # FARSI YEH
    text = text.replace(u"ک", u"ك") # ARABIC LETTER KEHEH (06A9)
    # convert llh for allāh into ll+shadda+dagger-alif+h
    text = rsub(text, u"لله", u"للّٰه")
    # uniprint("text enter: %s" % text)
    # shadda+short-vowel (including tanwīn vowels, i.e. -an -in -un) gets
    # replaced with short-vowel+shadda during NFC normalisation, which
    # MediaWiki does for all Unicode strings; however, it makes the
    # transliteration process inconvenient, so undo it.
    text = rsub(text,
        u"([\u064B\u064C\u064D\u064E\u064F\u0650\u0670])\u0651", u"\u0651\\1")
    # tāʾ marbūṭa should always be preceded by fatḥa, alif, alif madda or
    # dagger alif; infer fatḥa if not. This fatḥa will force a match to an "a"
    # in the Latin, so we can safely have tāʾ marbūṭa itself match "h", "t"
    # or "", making it work correctly with alif + tāʾ marbūṭa where
    # e.g. اة = ā and still correctly allow e.g. رة = ra but disallow رة = r.
    text = rsub(text, u"([^\u064E\u0627\u0622\u0670])\u0629",
        u"\\1\u064E\u0629")
    # some Arabic text has a shadda after the initial consonant; remove it
    newtext = rsub(text, ur"(^|[ |\[\]])(.)" + SH, r"\1\2")
    if text != newtext:
        if " " in newtext:
            # Shadda after initial consonant can legitimately occur in
            # Koranic text, standing for assimilation of the final consonant
            # of the preceding word
            msgfun("Not removing shadda after initial consonant in %s because of space in text"
                    %  text)
        else:
            msgfun("Removing shadda after initial consonant in %s" % text)
            text = newtext
    # similarly for sukūn + consonant + shadda.
    newtext = rsub(text, SK + "(.)" + SH, SK + r"\1")
    if text != newtext:
        msgfun(u"Removing shadda after sukūn + consonant in %s" % text)
        text = newtext
    # fatḥa mistakenly placed after consonant + alif should go before.
    newtext = rsub(text, "([" + lconsonants + "])" + A + "?" + ALIF + A,
            r"\1" + AA)
    if text != newtext:
        msgfun(u"uFixing fatḥa after consonant + alif in %s" % text)
        text = newtext
    return text

# Pre-canonicalize the Arabic. If SAFE, only do "safe" operations appropriate
# to canonicalizing Arabic on its own, not before a tr_matching() operation.
def pre_canonicalize_arabic(text, safe=False, msgfun=msg):
    if dont_pre_canonicalize_arabic(text):
        return text
    # Remove final -un i3rab
    if text.endswith(u"\u064C"):
        if " " in text:
            # Don't remove final -un from text with spaces because it might
            # be a Koranic quote or similar where we want the -un
            msgfun("Not removing final -un from Arabic %s because it has a space in it" % text)
        else:
            msgfun("Removing final -un from Arabic %s" % text)
            text = rsub(text, u"\u064C$", "")
    if not safe:
        # Final alif or alif maqṣūra following fatḥatān is silent (e.g. in
        # accusative singular or words like عَصًا "stick" or هُذًى "guidance";
        # this is called tanwin nasb). So substitute special silent versions
        # of these vowels. Will convert back during post-canonicalization.
        text = rsub(text, u"\u064B\u0627", u"\u064B" + silent_alif_subst)
        text = rsub(text, u"\u064B\u0649", u"\u064B" +
                silent_alif_maqsuura_subst)
        # same but with the fatḥatan placed over the alif or alif maqṣūra
        # instead of over the previous letter (considered a misspelling but
        # common)
        text = rsub(text, u"\u0627\u064B", silent_alif_subst + u"\u064B")
        text = rsub(text, u"\u0649\u064B", silent_alif_maqsuura_subst +
                u"\u064B")
        # word-initial al + consonant + shadda: remove shadda
        text = rsub(text, u"(^|\\s|\[\[|\|)(\u0627\u064E?\u0644[" +
                lconsonants + u"])\u0651", u"\\1\\2")
        # same for hamzat al-waṣl + l + consonant + shadda, anywhere
        text = rsub(text,
                u"(\u0671\u064E?\u0644[" + lconsonants + u"])\u0651", u"\\1")
        # word-initial al + l + dagger-alif + h (allāh): convert second l
        # to double_l_subst; will match shadda in Latin allāh during
        # tr_matching(), will be converted back during post-canonicalization
        text = rsub(text, u"(^|\\s|\[\[|\|)(\u0627\u064E?\u0644)\u0644(\u0670?ه)",
            u"\\1\\2" + double_l_subst + u"\\3")
        # same for hamzat al-waṣl + l + l + dagger-alif + h occurring anywhere.
        text = rsub(text, u"(\u0671\u064E?\u0644)\u0644(\u0670?ه)",
            u"\\1" + double_l_subst + u"\\2")
        # word-initial al + sun letter: convert l to assimilating_l_subst; will
        # convert back during post-canonicalization; during tr_matching(),
        # assimilating_l_subst will match the appropriate character, or "l"
        text = rsub(text, u"(^|\\s|\[\[|\|)(\u0627\u064E?)\u0644([" +
                sun_letters + "])", u"\\1\\2" + assimilating_l_subst + u"\\3")
        # same for hamzat al-waṣl + l + sun letter occurring anywhere.
        text = rsub(text, u"(\u0671\u064E?)\u0644([" + sun_letters + "])",
            u"\\1" + assimilating_l_subst + u"\\2")
    return text

def post_canonicalize_arabic(text, safe=False):
    if dont_pre_canonicalize_arabic(text):
        return text
    if not safe:
        text = rsub(text, silent_alif_subst, u"ا")
        text = rsub(text, silent_alif_maqsuura_subst, u"ى")
        text = rsub(text, assimilating_l_subst, u"ل")
        text = rsub(text, double_l_subst, u"ل")
        text = rsub(text, A + "?" + dagger_alif_subst, DAGGER_ALIF)

        # add sukūn between adjacent consonants, but not in the first part of
        # a link of the sort [[foo|bar]], which we don't vocalize
        splitparts = []
        index = 0
        for part in re.split(r'(\[\[[^]]*\|)', text):
            if (index % 2) == 0:
                # do this twice because a sequence of three consonants won't be
                # matched by the initial one, since the replacement does
                # non-overlapping subs
                part = rsub(part,
                        u"([" + lconsonants + u"])([" + rconsonants + u"])",
                        u"\\1\u0652\\2")
                part = rsub(part,
                        u"([" + lconsonants + u"])([" + rconsonants + u"])",
                        u"\\1\u0652\\2")
            splitparts.append(part)
            index += 1
        text = ''.join(splitparts)

    # remove sukūn after ḍamma + wāw
    text = rsub(text, u"\u064F\u0648\u0652", u"\u064F\u0648")
    # remove sukūn after kasra + yā'
    text = rsub(text, u"\u0650\u064A\u0652", u"\u0650\u064A")
    # initial al + consonant + sukūn + sun letter: convert to shadda
    text = rsub(text, u"(^|\\s|\[\[|\|)(\u0627\u064E?\u0644)\u0652([" + sun_letters + "])",
         u"\\1\\2\\3\u0651")
    # same for hamzat al-waṣl + l + consonant + sukūn + sun letters anywhere
    text = rsub(text, u"(\u0671\u064E?\u0644)\u0652([" + sun_letters + "])",
         u"\\1\\2\u0651")
    # Undo shadda+short-vowel reversal in pre_pre_canonicalize_arabic.
    # Not strictly necessary as MediaWiki will automatically do this
    # reversal but ensures that e.g. we don't keep trying to revocalize and
    # save a page with a shadda in it. Don't undo shadda+dagger-alif because
    # that sequence may not get reversed to begin with.
    text = rsub(text,
        u"\u0651([\u064B\u064C\u064D\u064E\u064F\u0650])", u"\\1\u0651")
    return text

debug_tr_matching = False

# Vocalize Arabic based on transliterated Latin, and canonicalize the
# transliteration based on the Arabic.  This works by matching the Latin
# to the unvocalized Arabic and inserting the appropriate diacritics in
# the right places, so that ambiguities of Latin transliteration can be
# correctly handled. Returns a tuple of Arabic, Latin. If unable to match,
# throw an error if ERR, else return None.
def tr_matching(arabic, latin, err=False, msgfun=msg):
    origarabic = arabic
    origlatin = latin
    def debprint(x):
        if debug_tr_matching:
            uniprint(x)
    arabic = pre_pre_canonicalize_arabic(arabic, msgfun=msgfun)
    latin = pre_canonicalize_latin(latin, arabic, msgfun=msgfun)
    arabic = pre_canonicalize_arabic(arabic, msgfun=msgfun)
    # convert double consonant after non-cons to consonant + shadda,
    # but not multiple quotes or multiple periods
    latin = re.sub(ur"(^|[aeiouəāēīōū\W])([^'.])\2", u"\\1\\2\u0651",
            latin, 0, re.U)

    ar = [] # exploded Arabic characters
    la = [] # exploded Latin characters
    res = [] # result Arabic characters
    lres = [] # result Latin characters
    for cp in arabic:
        ar.append(cp)
    for cp in latin:
        la.append(cp)
    debprint("Arabic characters: %s" % ar)
    debprint("Latin characters: %s" % la)
    aind = [0] # index of next Arabic character
    alen = len(ar)
    lind = [0] # index of next Latin character
    llen = len(la)

    # Find occurrences of al- in Arabic text and note characte pos's after.
    # We treat these as beginning-of-word positions so we correctly handle
    # varieties of alif in this position, treating them the same as at the
    # beginning of a word. We don't need to match assimilating_l_subst
    # here because the only things that we care about after Arabic al-
    # are alif variations, which don't occur with assimilating_l_subst.
    after_al_pos = []
    for m in re.finditer(r"((^|\s|\[\[|\|)" + ALIF + "|" + ALIF_WASLA + ")" +
            A + "?" + L + SK + "?", arabic):
        after_al_pos.append(m.end(0))

    def is_bow(pos=None):
        if pos is None:
            pos = aind[0]
        return (pos == 0 or ar[pos - 1] in [u" ", u"[", u"|"] or
                pos in after_al_pos)

    # True if we are at the last character in a word.
    def is_eow(pos=None):
        if pos is None:
            pos = aind[0]
        return pos == alen - 1 or ar[pos + 1] in [u" ", u"]", u"|"]

    def get_matches():
        ac = ar[aind[0]]
        debprint("get_matches: ac is %s" % ac)
        bow = is_bow()
        eow = is_eow()

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
        debprint("get_matches: matches is %s" % matches)
        if matches == None:
            if ac in other_arabic_chars:
                return []
            if True:
                error("Encountered non-Arabic (?) character " + ac +
                    " at index " + str(aind[0]))
            else:
                matches = [ac]
        if type(matches) is not list:
            matches = [matches]
        return matches

    # attempt to match the current Arabic character against the current
    # Latin character(s). If no match, return False; else, increment the
    # Arabic and Latin pointers over the matched characters, add the Arabic
    # character to the result characters and return True.
    def match():
        matches = get_matches()

        ac = ar[aind[0]]

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

        debprint("match: lind=%s, la=%s" % (
            lind[0], lind[0] >= llen and "EOF" or la[lind[0]]))

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
                if l < llen and la[l] == cp:
                    debprint("cp: %s, l=%s, la=%s" % (cp, l, la[l]))
                    l = l + 1
                else:
                    debprint("cp: %s, unmatched")
                    matched = False
                    break
            if matched:
                res.append(ac)
                if preserve_latin:
                    for cp in m:
                        lres.append(cp)
                elif ac == u"ة":
                    if not is_eow():
                        lres.append(u"t")
                    elif aind[0] > 0 and (ar[aind[0] - 1] == u"ا" or
                            ar[aind[0] - 1] == u"آ"):
                        lres.append(u"h")
                    # else do nothing
                else:
                    subst = matches[0]
                    if type(subst) is list or type(subst) is tuple:
                        subst = subst[0]
                    for cp in subst:
                        lres.append(cp)
                lind[0] = l
                aind[0] = aind[0] + 1
                debprint("matched; lind is %s" % lind[0])
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

    # Check for an unmatched Latin short vowel or similar; if so, insert
    # corresponding Arabic diacritic.
    def check_unmatching():
        if not (lind[0] < llen):
            return False
        debprint("Unmatched Latin: %s at %s" % (la[lind[0]], lind[0]))
        unmatched = tt_to_arabic_unmatching.get(la[lind[0]])
        if unmatched != None:
            res.append(unmatched)
            lres.append(la[lind[0]])
            lind[0] = lind[0] + 1
            return True
        return False

    # Check for an Arabic long vowel that is unmatched but following a Latin
    # short vowel.
    def check_skip_unmatching():
        if not (lind[0] > 0 and aind[0] < alen):
            return False
        skip_char_pos = lind[0] - 1
        # Skip back over a hyphen, so we match wa-l-jabal against والجبل
        if la[skip_char_pos] == "-" and skip_char_pos > 0:
            skip_char_pos -= 1
        skip_chars = tt_skip_unmatching.get(la[skip_char_pos])
        if skip_chars != None and ar[aind[0]] in skip_chars:
            debprint("Skip-unmatching matched %s at %s following %s at %s" % (
                ar[aind[0]], aind[0], la[skip_char_pos], skip_char_pos))
            res.append(ar[aind[0]])
            aind[0] = aind[0] + 1
            return True
        return False

    # Check for Latin hyphen and match it against -, zwj, zwnj, Arabic space
    # or nothing. See the caller for some of the reasons we special-case
    # this.
    def check_against_hyphen():
        if lind[0] < llen and la[lind[0]] == "-":
            if aind[0] >= alen:
                lres.append("-")
            elif ar[aind[0]] in ["-", u"–", zwj, zwnj]:
                lres.append("-")
                res.append(ar[aind[0]])
                aind[0] += 1
            elif ar[aind[0]] == " ":
                # When matching against space, convert hyphen to space.
                lres.append(" ")
                res.append(" ")
                aind[0] += 1
            else:
                lres.append("-")
            lind[0] += 1
            return True
        return False

    # Check for plain alif matching hamza and canonicalize.
    def check_bow_alif():
        if not (is_bow() and aind[0] < alen and ar[aind[0]] == u"ا"):
            return False
        # Check for hamza + vowel.
        if not (lind[0] < llen - 1 and la[lind[0]] in hamza_match_chars and
                la[lind[0] + 1] in u"aeiouəāēīōū"):
            return False
        # long vowels should have been pre-canonicalized to have the
        # corresponding short vowel before them.
        assert la[lind[0] + 1] not in u"āēīōū"
        if la[lind[0] + 1] in u"ei":
            canonalif = u"إ"
        else:
            canonalif = u"أ"
        msgfun("Canonicalized alif to %s in %s (%s)" % (
            canonalif, origarabic, origlatin))
        res.append(canonalif)
        aind[0] += 1
        lres.append(u"ʾ")
        lind[0] += 1
        return True

    # Check for inferring tanwīn
    def check_eow_tanwin():
        tanwin_mapping = {"a":AN, "i":IN, "u":UN}
        # Infer tanwīn at EOW
        if (aind[0] > 0 and is_eow(aind[0] - 1) and lind[0] < llen - 1 and
                la[lind[0]] in "aiu" and la[lind[0] + 1] == "n"):
            res.append(tanwin_mapping[la[lind[0]]])
            lres.append(la[lind[0]])
            lres.append(la[lind[0] + 1])
            lind[0] += 2
            return True
        # Infer fatḥatān before EOW alif/alif maqṣūra
        if (aind[0] < alen and is_eow() and
                ar[aind[0]] in u"اى" and lind[0] < llen - 1 and
                la[lind[0]] == "a" and la[lind[0] + 1] == "n"):
            res.append(AN)
            res.append(ar[aind[0]])
            lres.append("a")
            lres.append("n")
            aind[0] += 1
            lind[0] += 2
            return True
        return False

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
        # The first clause ensures that shadda always gets processed first;
        # necessary in the case of the qiṭṭun example below, which otherwise
        # would be rendered as qiṭunn.
        if lind[0] < llen and la[lind[0]] == u"\u0651":
            debprint("Matched: Clause shadda")
            lind[0] += 1
            lres.append(u"\u0651")
            if aind[0] < alen and (
                    ar[aind[0]] == u"\u0651" or ar[aind[0]] == double_l_subst):
                res.append(ar[aind[0]])
                aind[0] += 1
            else:
                res.append(u"\u0651")
            matched = True
        # We need a special clause for hyphen for various reasons. One of them
        # is that otherwise we have problems with al-ʾimārāt against الإمارات,
        # where the إ is in BOW position against hyphen and is allowed to
        # match against nothing and does so, and then the hyphen matches
        # against nothing and the ʾ can't match. Another is so that we can
        # canonicalize it to space if matching against a space but keep it
        # a hyphen otherwise.
        elif check_against_hyphen():
            debprint("Matched: Clause check_against_hyphen()")
            matched = True
        # The effect of the next clause is to handle cases where the
        # Arabic has a right bracket or similar character and the Latin has
        # a short vowel or shadda that doesn't match and needs to go before
        # the right bracket. The is_bow() check is necessary because
        # left-bracket is part of word_interrupting_chars and when the
        # left bracket is word-initial opposite a short vowel, the bracket
        # needs to be handled first. Similarly for word-initial tatwil, etc.
        #
        # Note that we can't easily generalize the word_interrupting_chars
        # check. We used to do so, calling get_matches() and looking where
        # the match has only an empty string, but this messed up on words
        # like زنىً (zinan) where the silent_alif_maqsuura_subst has only
        # an empty string matching but we do want to consume it first
        # before checking for short vowels. Even earlier we had an even
        # more general check, calling get_matches() and checking that any
        # of the matches are an empty string. This had the side-effect of
        # fixing the qiṭṭun problem but made it impossible to vocalize the
        # ghurfatun al-kuuba example, among others.
        elif (not is_bow() and aind[0] < alen and
                ar[aind[0]] in word_interrupting_chars and
                check_unmatching()):
            debprint("Matched: Clause 1")
            matched = True
        elif check_bow_alif():
            debprint("Matched: Clause check_bow_alif()")
            matched = True
        elif aind[0] < alen and match():
            debprint("Matched: Clause match()")
            matched = True
        elif check_eow_tanwin():
            debprint("Matched: Clause check_eow_tanwin()")
            matched = True
        elif check_unmatching():
            debprint("Matched: Clause check_unmatching()")
            matched = True
        elif check_skip_unmatching():
            debprint("Matched: Clause check_skip_unmatching()")
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

def remove_diacritics(word):
    return arabiclib.remove_diacritics(word)

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
    # u"an":u"\u064B" = fatḥatān
    # u"un":u"\u064C" = ḍammatān
    # u"in":u"\u064D" = kasratān
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
def tr_latin_direct(text, pos, msgfun=msg):
    text = pre_canonicalize_latin(text, msgfun=msg)
    text = rsub(text, u"ah$", u"\u064Eة")
    text = rsub(text, u"āh$", u"\u064Eاة")
    text = rsub(text, u".", tt_to_arabic_direct)
    # convert double consonant to consonant + shadda
    text = rsub(text, u"([" + lconsonants + u"])\\1", u"\\1\u0651")
    text = post_canonicalize_arabic(text)

    return text

################################ Test code ##########################

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
        canonarabic, canonlatin = result
        trlatin = tr(canonarabic)
        uniout("tr_matching(%s, %s) = %s %s," %
                (arabic, latin, canonarabic, canonlatin))
        if trlatin == canonlatin:
            uniprint("tr() MATCHED")
            outcome = "matched"
        else:
            uniprint("tr() UNMATCHED (= %s)" % trlatin)
            outcome = "unmatched"
    canonlatin, _ = canonicalize_latin_arabic(latin, None)
    uniprint("canonicalize_latin(%s) = %s" %
            (latin, canonlatin))
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
    test("katabaq", u"كتب", "failed") # should fail
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
    test("wa-dakhala", u"و-دخل", "matched")
    test("wadakhala", u"و‍دخل", "failed") # should fail, ZWJ must match hyphen
    test("wadakhala", u"ودخل", "matched")
    # Six different ways of spelling a long ū.
    test("duuba", u"دوبة", "matched")
    test(u"dúuba", u"دوبة", "matched")
    test("duwba", u"دوبة", "matched")
    test("du:ba", u"دوبة", "matched")
    test(u"dūba", u"دوبة", "matched")
    test(u"dū́ba", u"دوبة", "matched")
    # w definitely as a consonant, should be preserved
    test("duwaba", u"دوبة", "matched")

    # Similar but for ī and y
    test("diiba", u"ديبة", "matched")
    test(u"díiba", u"ديبة", "matched")
    test("diyba", u"ديبة", "matched")
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
    test("bait al-duuba", u"بيت الدوبة", "matched")
    test("bait al-Duuba", u"بيت الدوبة", "matched")
    test("bait al-kuuba", u"بيت الكوبة", "matched")
    test("baitu l-kuuba", u"بيت ٱلكوبة", "matched")

    test(u"ʼáwʻada", u"أوعد", "matched")
    test(u"'áwʻada", u"أوعد", "matched")
    # The following should be self-canonicalized differently.
    test(u"`áwʻada", u"أوعد", "matched")

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

    # Test handling of tāʾ marbūṭa when final
    test("ghurfat", u"غرفةٌ", "matched")
    test("ghurfa(t)", u"غرفةٌ", "matched")
    test("ghurfa(tun)", u"غرفةٌ", "matched")
    test("ghurfat(un)", u"غرفةٌ", "matched")

    # Test handling of embedded links
    test(u"’ālati l-fam", u"[[آلة]] [[فم|الفم]]", "matched")
    test(u"arqām hindiyya", u"[[أرقام]] [[هندية]]", "matched")
    test(u"arqām hindiyya", u"[[رقم|أرقام]] [[هندية]]", "matched")
    test(u"arqām hindiyya", u"[[رقم|أرقام]] [[هندي|هندية]]", "matched")
    test(u"ʾufuq al-ħadaŧ", u"[[أفق]] [[حادثة|الحدث]]", "matched")

    # Test transliteration that omits initial hamza (should be inferrable)
    test(u"aṣdiqaa'", u"أَصدقاء", "matched")
    test(u"aṣdiqā́'", u"أَصدقاء", "matched")
    # Test random hamzas
    test(u"'aṣdiqā́'", u"أَصدقاء", "matched")
    # Test capital letters for emphatics
    test(u"aSdiqaa'", u"أَصدقاء", "matched")
    # Test final otiose alif maqṣūra after fatḥatān
    test("hudan", u"هُدًى", "matched")
    # Test opposite with fatḥatān after alif otiose alif maqṣūra
    test(u"zinan", u"زنىً", "matched")

    # Check that final short vowel is canonicalized to a long vowel in the
    # presence of a corresponding Latin long vowel.
    test("'animi", u"أنمي", "matched")
    # Also check for 'l indicating assimilation.
    test("fi 'l-marra", u"في المرة", "matched")

    # Test cases where short Latin vowel corresponds to Long Arabic vowel
    test("diba", u"ديبة", "unmatched")
    test("tamariid", u"تماريد", "unmatched")
    test("tamuriid", u"تماريد", "failed")

    # Single quotes in Arabic
    test("man '''huwa'''", u"من '''هو'''", "matched")

    # Alif madda
    test("'aabaa'", u"آباء", "matched")
    test("mir'aah", u"مرآة", "matched")

    # Test case where close bracket occurs at end of word and an unmatched
    # vowel or shadda needs to be before it.
    test(u"fuuliyy", u"[[فولي]]", "matched")
    test(u"fuula", u"[[فول]]", "matched")
    test(u"wa-'uxt", u"[[و]][[أخت]]", "unmatched")
    # Here we test when an open bracket occurs in the middle of a word and
    # an unmatched vowel or shadda needs to be before it.
    test(u"wa-'uxt", u"و[[أخت]]", "unmatched")

    # Test hamza against non-hamza
    test(u"'uxt", u"اخت", "matched")
    test(u"uxt", u"أخت", "matched")
    test(u"'ixt", u"اخت", "matched")
    test(u"ixt", u"أخت", "matched") # FIXME: Should be "failed" or should correct hamza

    # Test alif after al-
    test(u"al-intifaaḍa", u"[[الانتفاضة]]", "matched")
    test(u"al-'uxt", u"الاخت", "matched")

    # Test adding ! or ؟
    test(u"fan", u"فن!", "matched")
    test(u"fan!", u"فن!", "matched")
    test(u"fan", u"فن؟", "matched")
    test(u"fan?", u"فن؟", "matched")

    # Test inferring fatḥatān
    test("hudan", u"هُدى", "matched")
    test("qafan", u"قفا", "matched")
    test("qafan qafan", u"قفا قفا", "matched")

    # Case where shadda and -un are opposite each other; need to handle
    # shadda first.
    test(u"qiṭṭ", u"قِطٌ", "matched")

    # 3 consonants in a row
    test(u"Kūlūmbīyā", u"كولومبيا", "matched")
    test(u"fustra", u"فسترة", "matched")

    # Allāh
    test(u"allāh", u"الله", "matched")

    # Test dagger alif, alif maqṣūra
    test(u"raḥmān", u"رَحْمٰن", "matched")
    test(u"fusḥā", u"فسحى", "matched")
    test(u"fusḥā", u"فُسْحَى", "matched")
    test(u"'āxir", u"آخر", "matched")

    # Real-world tests
    test(u"’ijrā’iy", u"إجْرائِيّ", "matched")
    test(u"wuḍūʕ", u"وضوء", "matched")
    test(u"al-luḡa al-ʾingilīziyya", u"اَلْلُّغَة الْإنْجِلِيزِيّة", "unmatched")
    test(u"šamsíyya", u"شّمسيّة", "matched")
    test(u"Sirbiyā wa-l-Jabal al-Aswad", u"صربيا والجبل الأسود", "unmatched")
    test(u"al-’imaraat", u"الإمارات", "unmatched")
    # FIXME: Should we canonicalize to al-?
    test(u"al'aan(a)", u"الآن", "unmatched")
    test(u"yūnānīyya", u"يونانية", "matched")
    test(u"hindiy-'uruubiy", u"هندي-أوروبي", "unmatched")
    test(u"moldōva", u"مولدوفا", "unmatched")
    test(u"darà", u"درى", "matched")
    test(u"waraa2", u"وراء", "matched")
    test(u"takhaddaa", u"تحدى", "matched")
    test(u"qaránful", u"ﻗﺮﻧﻔﻞ", "matched")
    # Can't easily handle this one because ال matches against -r- in the
    # middle of a word.
    # test(u"al-sāʿa wa-'r-rubʿ", u"الساعة والربع", "matched")
    test(u"taḥṭīṭ", u"تخطيط", "matched")
    test(u"hāḏihi", u"هذه", "matched")
    test(u"ħaláːt", u"حَالاَتٌ", "unmatched")
    test(u"raqṣ šarkiyy", u"رقص شرقي", "matched")
    test(u"ibn ʾaḵ", u"[[اِبْنُ]] [[أَخٍ]]", "matched")
    test(u"al-wuṣṭā", u"الوسطى", "matched")
    test(u"fáħmu-l-xášab", u"فحم الخشب", "matched")
    test(u"gaṡor", u"قَصُر", "unmatched")
    # Getting this to work makes it hard to get e.g. nijir vs. نيجر to work.
    # test(u"sijāq", u"سِيَاق", "matched")
    test(u"winipiigh", u"وينيبيغ", "unmatched")
    test(u"ʿaḏrāʿ", u"عذراء", "matched")
    test(u"ʂaʈħ", u"سطْح", "matched")
    test(u"dʒa'", u"جاء", "unmatched")
    #will split when done through canon_arabic.py, but not here
    #test(u"ʿíndak/ʿíndak", u"عندك", "matched") # should split
    test(u"fi 'l-ḡad(i)", u"في الغد", "matched")
    test(u"ḩaythu", u"حَيثُ", "matched")
    test(u"’iʐhār", u"إظهار", "matched")
    test(u"taħli:l riya:dˤiy", u"تَحْلِيلْ رِيَاضِي", "matched")
    test(u"al-'ingilizíyya al-'amrikíyya", u"الإنجليزية الأمريكية", "unmatched")
    test(u"ḵаwḵa", u"خوخة", "matched") # this has a Cyrillic character in it
    test(u"’eħsās", u"احساس", "unmatched")
    # Up through page 848 "sense"
    test(u"wayd-jaylz", u"ويد–جيلز", "matched")
    test(u"finjáːn šæːy", u"فِنْجَان شَاي", "matched")
    test(u"múdhhil", u"مذهل", "matched")
    test(u"ixtiār", u"اختيار", "matched")
    test(u"miṯll", u"مثل", "matched")
    test(u"li-wajhi llāh", u"لِوَجْهِ اللهِ", "unmatched")

    # FIXME's: assimilating_l_subst only matches against canonical sun
    # letters, not against non-canonical ones like θ. We can fix that
    # by adding all the non-canonical ones to ttsun1[], or maybe just
    # matching anything that's not a vowel.
    #test(u"tišrīnu θ-θāni", u"تِشرينُ الثّانِي", "matched")

    # Final results
    uniprint("RESULTS: %s SUCCEEDED, %s FAILED." % (num_succeeded, num_failed))

if __name__ == "__main__":
    run_tests()

# For Vim, so we get 4-space indent
# vim: set sw=4:
