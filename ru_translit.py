#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Authors: Benwing; Atitarev for tr() and tr_adj() functions, in Lua

#    ru_translit.py is free software: you can redistribute it and/or modify
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

from blib import remove_links

# FIXME:
#
# 1. Check with Anatoli -- always safe to canonicalize sh to š etc. in
#    preprocessing? 'h' can stand for г in ahá; can this ever occur after š or
#    whatever?
# 2. Fix code that converts Russian е to do it after all but Russian
#    consonants.

AC = u"\u0301"
GR = u"\u0300"
ACGR = "[" + AC + GR + "]"
ACGROPT = "[" + AC + GR + "]?"

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

def nfc_form(txt):
    return unicodedata.normalize("NFKC", txt)

def nfd_form(txt):
    return unicodedata.normalize("NFKD", txt)

tt = {
    u"А":u"A", u"Б":u"B", u"В":u"V", u"Г":u"G", u"Д":u"D", u"Е":u"E",
    u"Ё":u"Jó", u"Ж":u"Ž", u"З":u"Z", u"И":u"I", u"Й":u"J",
    u"К":u"K", u"Л":u"L", u"М":u"M", u"Н":u"N", u"О":u"O", u"П":u"P",
    u"Р":u"R", u"С":u"S", u"Т":u"T", u"У":u"U", u"Ф":u"F",
    u"Х":u"X", u"Ц":u"C", u"Ч":u"Č", u"Ш":u"Š", u"Щ":u"Šč", u"Ъ":u"ʺ",
    u"Ы":u"Y", u"Ь":u"ʹ", u"Э":u"E", u"Ю":u"Ju", u"Я":u"Ja",
    u'а':u'a', u'б':u'b', u'в':u'v', u'г':u'g', u'д':u'd', u'е':u'e',
    u'ё':u'jó', u'ж':u'ž', u'з':u'z', u'и':u'i', u'й':u'j',
    u'к':u'k', u'л':u'l', u'м':u'm', u'н':u'n', u'о':u'o', u'п':u'p',
    u'р':u'r', u'с':u's', u'т':u't', u'у':u'u', u'ф':u'f',
    u'х':u'x', u'ц':u'c', u'ч':u'č', u'ш':u'š', u'щ':u'šč', u'ъ':u'ʺ',
    u'ы':u'y', u'ь':u'ʹ', u'э':u'e', u'ю':u'ju', u'я':u'ja',
    # Russian style quotes
    u'«':u'“', u'»':u'”',
    # archaic, pre-1918 letters
    u'І':u'I', u'і':u'i', u'Ѳ':u'F', u'ѳ':u'f',
    u'Ѣ':u'Ě', u'ѣ':u'ě', u'Ѵ':u'I', u'ѵ':u'i',
}

russian_vowels = u"АОУҮЫЭЯЁЮИЕЪЬІѢѴаоуүыэяёюиеъьіѣѵAEIOUYĚaeiouyě"

# Transliterates text, which should be a single word or phrase. It should
# include stress marks, which are then preserved in the transliteration.
def tr(text, lang=None, sc=None):
    text = remove_links(text)
    text = tr_canonicalize_russian(text)

    # Remove word-final hard sign
    text = rsub(text, u"[Ъъ]($|[- \]])", ur"\1")

    # ё after a "hushing" consonant becomes ó (ё is mostly stressed)
    text = rsub(text, u"([жшчщЖШЧЩ])ё", ur"\1ó")
    # ю after ж and ш becomes u (e.g. брошюра, жюри)
    text = rsub(text, u"([жшЖШ])ю", ur"\1u")

    # е after a vowel or at the beginning of a word becomes je
    bow_or_vowel = u"(^|[- \[%s]%s)" % (russian_vowels, ACGROPT)
    def replace_e(m):
        ttab = {u"Е":u"Je", u"е":u"je", u"Ѣ":u"Jě", u"ѣ":u"jě"}
        return m.group(1) + ttab[m.group(2)]
    # repeat to handle sequences of ЕЕЕЕЕ...
    text = rsub(text, u"%s([ЕеѢѣ])" % bow_or_vowel, replace_e)
    text = rsub(text, u"%s([ЕеѢѣ])" % bow_or_vowel, replace_e)

    text = rsub(text, '.', tt)

    # compose accented characters
    text = tr_canonicalize_latin(text)

    return text

# for adjectives and pronouns; in Lua, may be called directly from a template
# FIXME: Isn't properly translated to Python yet
def tr_adj(text):
    trtext = tr(text)

    # handle genitive/accusative endings, which are spelled -ого/-его (-ogo/-ego) but transliterated -ovo/-evo
    #only for adjectives and pronouns, excluding words like много, ого
    pattern = u"([oeóéOEÓÉ][\u0301\u0300]?)([gG])([oO][\u0301\u0300]?)"
    reflexive = u"([sS][jJ][aáAÁ][\u0301\u0300]?)"
    v = {u"g":u"v", u"G":u"V"}
    repl = lambda e, g, o, sja:  e + v[g] + o + (sja or "")
    trtext = rsub(trtext, pattern + u"%f[^%a\u0301\u0300]", repl)
    trtext = rsub(trtext, pattern + reflexive + u"%f[^%a\u0301\u0300]", repl)

    return tr

############################################################################
#                     Transliterate from Latin to Russian                  #
############################################################################

#########       Transliterate with Russian to guide       #########

multi_single_quote_subst = u"\ufff1"
capital_e_subst = u"\ufff2"
small_e_subst = u"\ufff3"
small_jo_subst = u"\ufff4"
small_ju_subst = u"\ufff5"
capital_silent_hard_sign = u"\ufff6"
small_silent_hard_sign = u"\ufff7"

# This dict maps Russian characters to all the Latin characters that
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
# like ж=zh.

tt_to_russian_matching = {
    u"А":u"A",
    u"Б":u"B",
    u"В":u"V",
    u"Г":u"G",
    u"Д":u"D",
    # Canonicalize to capital_e_subst, which we later map to either Je or E
    # depending on what precedes. We don't use regular capital E as the
    # canonical character because Э also maps to E.
    u"Е":[capital_e_subst,"E","Je","Ye",[u"Ɛ"]],
    # FIXME: Yo should be converted to Jo
    u"Ё":[u"Jo"+AC,u"Yo"+AC,[u"Jo"],[u"Yo"]],
    u"Ж":[u"Ž",u"zh"],
    u"З":u"Z",
    u"И":u"I",
    u"Й":[u"J",u"Y"],
    u"К":u"K",
    u"Л":u"L",
    u"М":u"M",
    u"Н":u"N",
    u"О":u"O",
    u"П":u"P",
    u"Р":u"R",
    u"С":u"S",
    u"Т":u"T",
    u"У":u"U",
    u"Ф":u"F",
    u"Х":u"X",
    u"Ц":u"C",
    u"Ч":[u"Č",u"Ch",[u"Š"],[u"Sh"]],
    u"Ш":[u"Š",u"Sh"],
    u"Щ":[u"Šč",u"Shch"],
    u"Ъ":[u"ʺ",u'"'],
    u"Ы":u"Y",
    u"Ь":[u"ʹ",u"'"],
    u"Э":u"E",
    u"Ю":[u"Ju",u"Yu",u"U"],
    u"Я":[u"Ja",u"Ya",u"A"],
    u'а':u'a',
    u'б':u'b',
    u'в':u'v',
    u'г':[u'g',[u'v'],[u'x'],[u'kh'],[u'h']],
    u'д':u'd',
    # Canonicalize to small_e_subst, which we later map to either je or e
    # depending on what precedes. We don't use regular small e as the
    # canonical character because э also maps to e.
    u"е":[small_e_subst,"e","je","ye",[u"ɛ"]],
    # FIXME: yo should be converted to jo
    u'ё':[small_jo_subst,u'jo'+AC,u"yo"+AC,u"o"+AC,[u"jo"],[u"yo"],[u"o"]],
    u'ж':[u'ž',u"zh"],
    u'з':u'z',
    u'и':u'i',
    u'й':u'j',
    u'к':u'k',
    u'л':u'l',
    u'м':u'm',
    u'н':u'n',
    u'о':u'o',
    u'п':u'p',
    u'р':u'r',
    u'с':u's',
    u'т':u't',
    u'у':u'u',
    u'ф':u'f',
    u'х':u'x',
    u'ц':u'c',
    u'ч':[u'č',u"ch",[u"š"],[u"sh"]],
    u'ш':[u'š',u"sh"],
    u'щ':[u'šč',u"shch"],
    u'ъ':[u'ʺ',u'"'],
    u'ы':u'y',
    u'ь':[u'ʹ',u"'"],
    u'э':u'e',
    u'ю':[small_ju_subst,u'ju',u"yu",u"u"],
    u'я':[u'ja',u"ya"],
    # Russian style quotes
    u'«':[u'“',u'"'],
    u'»':[u'”',u'"'],
    # archaic, pre-1918 letters
    u'І':u'I',
    u'і':u'i',
    u'Ѳ':u'F',
    u'ѳ':u'f',
    # We will later map to Jě/jě as necessary.
    u'Ѣ':[u'Ě',u"E"],
    u'ѣ':[u'ě',u"e"],
    u'Ѵ':u'I',
    u'ѵ':u'i',
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
    u"'":[(u"'",)], # single quote, for bold/italic
    u" ":u" ",
    u"[":u"",
    u"]":u"",
    # accents
    AC:[AC,""],
    capital_silent_hard_sign:u"",
    small_silent_hard_sign:u"",
}

word_interrupting_chars = u"-[]"

build_canonicalize_latin = {}
for ch in u"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ":
    build_canonicalize_latin[ch] = "multiple"
build_canonicalize_latin[""] = "multiple"

# Make sure we don't canonicalize any canonical letter to any other one;
# e.g. could happen with ʾ, an alternative for ʿ.
for russian in tt_to_russian_matching:
    alts = tt_to_russian_matching[russian]
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

for russian in tt_to_russian_matching:
    alts = tt_to_russian_matching[russian]
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
# Russian. The value is the corresponding Russian character to insert.
tt_to_russian_unmatching = {
    AC:AC,
}

# Pre-canonicalize Latin, and Russian if supplied. If Russian is supplied,
# it should be the corresponding Russian (after pre-pre-canonicalization),
# and is used to do extra canonicalizations.
def pre_canonicalize_latin(text, russian=None):
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
    # decompose accented letters
    text = rsub(text, u"[áéíóúÁÉÍÓÚ]",
        {u"á":"a"+AC, u"é":"e"+AC, u"í":"i"+AC, u"ó":"o"+AC, u"ú":"u"+AC,
         u"Á":"A"+AC, u"É":"E"+AC, u"Í":"I"+AC, u"Ó":"O"+AC, u"Ú":"U"+AC,})
    # "compose" digraphs
    text = rsub(text, u"[czskCZSK]h",
        {"ch":u"č", "zh":u"ž", "sh":u"š", "kh":"x",
         "Ch":u"Č", "Zh":u"Ž", "Sh":u"Š", "Kh":"X"})

    return text

def tr_canonicalize_latin(text):
    # recompose accented letters
    text = rsub(text, "[aeiouAEIOU]" + AC,
        {"a"+AC:u"á", "e"+AC:u"é", "i"+AC:u"í", "o"+AC:u"ó", "u"+AC:u"ú",
         "A"+AC:u"Á", "E"+AC:u"É", "I"+AC:u"Í", "O"+AC:u"Ó", "U"+AC:u"Ú",})

    return text

def post_canonicalize_latin(text):
    # Handle Russian jo/ju, with or without preceding hushing consonant that
    # suppresses the j. We initially considered not using small_jo_subst
    # and small_ju_subst and just remove j after hushing consonants before
    # o/u, but that catches too many things; there may be genuine instances
    # of hushing consonant + j (Cyrillic й) + o/u.
    text = rsub(text, u"([žčšŽČŠ])%s" % small_jo_subst, r"\1o" + AC)
    text = text.replace(small_jo_subst, "jo" + AC)
    text = rsub(text, u"([žšŽŠ])%s" % small_ju_subst, r"\1u")
    text = text.replace(small_ju_subst, "ju")

    # convert capital_e_subst to either E or Je, and small_e_subst to
    # either e or je; similarly, maybe map Ě to Jě, ě to jě.
    # Do before recomposing accented letters.
    bow_or_vowel = u"(^|[- \[aeiouěAEIOUĚʺʹ%s%s]%s)" % (
            capital_e_subst, small_e_subst, ACGROPT)
    # repeat to handle sequences of ЕЕЕЕЕ...
    for i in [0,1]:
        text = rsub(text, u"(%s)%s" % (bow_or_vowel, capital_e_subst), r"\1Je")
        text = rsub(text, u"(%s)%s" % (bow_or_vowel, small_e_subst), r"\1je")
        text = rsub(text, u"(%s)Ě" % bow_or_vowel, r"\1Jě")
        text = rsub(text, u"(%s)ě" % bow_or_vowel, r"\1jě")
    text = text.replace(capital_e_subst, "E")
    text = text.replace(small_e_subst, "e")

    # recompose accented letters
    text = tr_canonicalize_latin(text)

    text = text.strip()
    return text

# Canonicalize a Latin transliteration and Russian text to standard form.
# Can be done on only Latin or only Russian (with the other one None), but
# is more reliable when both aare provided. This is less reliable than
# tr_matching() and is meant when that fails. Return value is a tuple of
# (CANONLATIN, CANONARABIC).
def canonicalize_latin_russian(latin, russian):
    if russian is not None:
        russian = pre_pre_canonicalize_russian(russian)
    if latin is not None:
        latin = pre_canonicalize_latin(latin, russian)
    if russian is not None:
        russian = pre_canonicalize_russian(russian)
        russian = post_canonicalize_russian(russian)
    if latin is not None:
        # Protect instances of two or more single quotes in a row so they don't
        # get converted to sequences of ʹ characters.
        def quote_subst(m):
            return m.group(0).replace("'", multi_single_quote_subst)
        latin = re.sub(r"''+", quote_subst, latin)
        latin = rsub(latin, u".", tt_canonicalize_latin)
        latin = latin.replace(multi_single_quote_subst, "'")
        latin = post_canonicalize_latin(latin)
    return (latin, russian)

def tr_canonicalize_russian(text):
    # Ё needs converting if is decomposed
    text = rsub(text, u"ё", u"ё")
    text = rsub(text, u"Ё", u"Ё")

    return text

# Early pre-canonicalization of Russian, doing stuff that's safe. We split
# this from pre-canonicalization proper so we can do Latin pre-canonicalization
# between the two steps.
def pre_pre_canonicalize_russian(text):
    # remove L2R, R2L markers
    text = rsub(text, u"[\u200E\u200F]", "")
    # remove leading/trailing spaces
    text = text.strip()
    # canonicalize interior whitespace
    text = rsub(text, r"\s+", " ")

    text = tr_canonicalize_russian(text)

    # Convert word-final hard sign to special silent character; will be
    # undone later
    text = rsub(text, u"Ъ($|[- \]])", capital_silent_hard_sign + r"\1")
    text = rsub(text, u"ъ($|[- \]])", small_silent_hard_sign + r"\1")

    return text

def pre_canonicalize_russian(text):
    return text

def post_canonicalize_russian(text):
    text = text.replace(capital_silent_hard_sign, u"Ъ")
    text = text.replace(small_silent_hard_sign, u"ъ")
    return text

debug_tr_matching = False

# Vocalize Russian based on transliterated Latin, and canonicalize the
# transliteration based on the Russian.  This works by matching the Latin
# to the Russian and transferring Latin stress marks to the Russian as
# appropriate, so that ambiguities of Latin transliteration can be
# correctly handled. Returns a tuple of Russian, Latin. If unable to match,
# throw an error if ERR, else return None.
def tr_matching(russian, latin, err=False, msgfun=None):
    origrussian = russian
    origlatin = latin
    def debprint(x):
        if debug_tr_matching:
            uniprint(x)
    russian = pre_pre_canonicalize_russian(russian)
    latin = pre_canonicalize_latin(latin, russian)
    russian = pre_canonicalize_russian(russian)

    ru = [] # exploded Russian characters
    la = [] # exploded Latin characters
    res = [] # result Russian characters
    lres = [] # result Latin characters
    for cp in russian:
        ru.append(cp)
    for cp in latin:
        la.append(cp)
    rind = [0] # index of next Russian character
    rlen = len(ru)
    lind = [0] # index of next Latin character
    llen = len(la)

    def is_bow(pos=None):
        if pos is None:
            pos = rind[0]
        return pos == 0 or ru[pos - 1] in [u" ", u"[", u"|", u"-"]

    # True if we are at the last character in a word.
    def is_eow(pos=None):
        if pos is None:
            pos = rind[0]
        return pos == rlen - 1 or ru[pos + 1] in [u" ", u"]", u"|", u"-"]

    def get_matches():
        ac = ru[rind[0]]
        debprint("get_matches: ac is %s" % ac)
        bow = is_bow()
        eow = is_eow()

        matches = tt_to_russian_matching.get(ac)
        debprint("get_matches: matches is %s" % matches)
        if matches == None:
            if True:
                error("Encountered non-Russian (?) character " + ac +
                    " at index " + str(rind[0]))
            else:
                matches = [ac]
        if type(matches) is not list:
            matches = [matches]
        return matches

    # attempt to match the current Russian character against the current
    # Latin character(s). If no match, return False; else, increment the
    # Russian and Latin pointers over the matched characters, add the Russian
    # character to the result characters and return True.
    def match():
        matches = get_matches()

        ac = ru[rind[0]]

        # Check for link of the form [[foo|bar]] and skip over the part
        # up through the vertical bar, copying it
        if ac == '[':
            newpos = rind[0]
            while newpos < rlen and ru[newpos] != ']':
                if ru[newpos] == '|':
                    newpos += 1
                    while rind[0] < newpos:
                        res.append(ru[rind[0]])
                        rind[0] += 1
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
                rind[0] = rind[0] + 1
                debprint("matched; lind is %s" % lind[0])
                return True
        return False

    def cant_match():
        if rind[0] < rlen and lind[0] < llen:
            error("Unable to match Russian character %s at index %s, Latin character %s at index %s" %
                (ru[rind[0]], rind[0], la[lind[0]], lind[0]))
        elif rind[0] < rlen:
            error("Unable to match trailing Russian character %s at index %s" %
                (ru[rind[0]], rind[0]))
        else:
            error("Unable to match trailing Latin character %s at index %s" %
                (la[lind[0]], lind[0]))

    # Check for an unmatched Latin short vowel or similar; if so, insert
    # corresponding Russian diacritic.
    def check_unmatching():
        if not (lind[0] < llen):
            return False
        debprint("Unmatched Latin: %s at %s" % (la[lind[0]], lind[0]))
        unmatched = tt_to_russian_unmatching.get(la[lind[0]])
        if unmatched != None:
            res.append(unmatched)
            lres.append(la[lind[0]])
            lind[0] = lind[0] + 1
            return True
        return False

    # Here we go through the Russian letter for letter, matching
    # up the consonants we encounter with the corresponding Latin consonants
    # using the dict in tt_to_russian_matching and copying the Russian
    # consonants into a destination array. When we don't match, we check for
    # allowed unmatching Latin characters in tt_to_russian_unmatching, which
    # handles acute accents. If this doesn't match either, and we have
    # left-over Russian or Latin characters, we reject the whole match,
    # either returning False or signaling an error.

    while rind[0] < rlen or lind[0] < llen:
        matched = False
        # The effect of the next clause is to handle cases where the
        # Russian has a right bracket or similar character and the Latin has
        # an acute accent that doesn't match and needs to go before
        # the right bracket. The is_bow() check is necessary for reasons
        # described in ar_translit.py, where this check comes from.
        #
        # FIXME: Is this still necessary here? Is there a better way?
        # E.g. splitting the Russian string on occurrences of left/right
        # brackets and handling the remaining occurrences piece-by-piece?
        if (not is_bow() and rind[0] < rlen and
                ru[rind[0]] in word_interrupting_chars and
                check_unmatching()):
            debprint("Matched: Clause 1")
            matched = True
        elif rind[0] < rlen and match():
            debprint("Matched: Clause match()")
            matched = True
        elif check_unmatching():
            debprint("Matched: Clause check_unmatching()")
            matched = True
        if not matched:
            if err:
                cant_match()
            else:
                return False

    russian = "".join(res)
    latin = "".join(lres)
    russian = post_canonicalize_russian(russian)
    latin = post_canonicalize_latin(latin)
    return russian, latin

num_failed = 0
num_succeeded = 0

def test(latin, russian, should_outcome):
    def msg(text):
      print text.encode('utf-8')
    global num_succeeded, num_failed
    try:
        result = tr_matching(russian, latin, True, msg)
    except RuntimeError as e:
        uniprint(u"%s" % e)
        result = False
    if result == False:
        uniprint("tr_matching(%s, %s) = %s" % (russian, latin, result))
        outcome = "failed"
    else:
        canonrussian, canonlatin = result
        trlatin = tr(canonrussian)
        uniout("tr_matching(%s, %s) = %s %s," %
                (russian, latin, canonrussian, canonlatin))
        if trlatin == canonlatin:
            uniprint("tr() MATCHED")
            outcome = "matched"
        else:
            uniprint("tr() UNMATCHED (= %s)" % trlatin)
            outcome = "unmatched"
    canonlatin, _ = canonicalize_latin_russian(latin, None)
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

    # Test inferring accents in both Cyrillic and Latin
    test("zontik", u"зонтик", "matched")
    test(u"zóntik", u"зо́нтик", "matched")
    test(u"zóntik", u"зонтик", "matched")
    test("zontik", u"зо́нтик", "matched")
    test("zontik", u"зо́нтик", "matched")

    # Things that should fail
    test("zontak", u"зонтик", "failed")
    test("zontika", u"зонтик", "failed")

    # Test with Cyrillic e
    test(u"jebepʹje jebe", u"ебепье ебе", "matched")
    test(u"jebepʹe jebe", u"ебепье ебе", "matched")
    test("Jebe Jebe", u"Ебе Ебе", "matched")
    test("ebe ebe", u"ебе ебе", "matched")
    test("Ebe Ebe", u"Ебе Ебе", "matched")
    test("yebe yebe", u"ебе ебе", "matched")
    test("yebe yebe", u"[[ебе]] [[ебе]]", "matched")
    test("Yebe Yebe", u"Ебе Ебе", "matched")
    test(u"ébe ébe", u"ебе ебе", "matched")
    test(u"Ébe Ébe", u"Ебе Ебе", "matched")
    test(u"yéye yéye", u"ее ее", "matched")
    test(u"yéye yéye", u"е́е е́е", "matched")
    test("yeye yeye", u"е́е е́е", "matched")

    # Test with ju after hushing sounds
    test(u"broshúra", u"брошюра", "matched")
    test(u"broshyúra", u"брошюра", "matched")
    test(u"zhurí", u"жюри", "matched")

    # Test with ' representing ь, which should be canonicalized to ʹ
    test(u"pal'da", u"пальда", "matched")

    # Test with jo
    test(u"ketjó", u"кетё", "matched")
    test(u"kétjo", u"кетё", "unmatched")
    test(u"kešó", u"кешё", "matched")
    test(u"kešjó", u"кешё", "matched")

    # Test handling of embedded links, including unmatched acute accent
    # directly before right bracket on Russian side
    test(u"pala volu", u"пала [[вола|волу]]", "matched")
    test(u"pala volú", u"пала [[вола|волу]]", "matched")
    test(u"volu pala", u"[[вола|волу]] пала", "matched")
    test(u"volú pala", u"[[вола|волу]] пала", "matched")
    test(u"volupala", u"[[вола|волу]]пала", "matched")
    test(u"pala volu", u"пала [[волу]]", "matched")
    test(u"pala volú", u"пала [[волу]]", "matched")
    test(u"volu pala", u"[[волу]] пала", "matched")
    test(u"volú pala", u"[[волу]] пала", "matched")
    test(u"volúpala", u"[[волу]]пала", "matched")

    # Silent hard signs
    test("mir", u"миръ", "matched")
    test("mir", u"міръ", "matched")
    test("MIR", u"МІРЪ", "matched")

    # Single quotes in Russian
    test("volu '''pala'''", u"волу '''пала'''", "matched")
    test(u"volu '''palá'''", u"волу '''пала'''", "matched")
    # Here the single quote after l should become ʹ but not the others
    test(u"volu '''pal'dá'''", u"волу '''пальда'''", "matched")
    test(u"bólʹše vsevó", u"[[бо́льше]] [[всё|всего́]]", "unmatched")

    # # Test adding ! or ؟
    # test(u"fan", u"فن!", "matched")
    # test(u"fan!", u"فن!", "matched")
    # test(u"fan", u"فن؟", "matched")
    # test(u"fan?", u"فن؟", "matched")

    # Final results
    uniprint("RESULTS: %s SUCCEEDED, %s FAILED." % (num_succeeded, num_failed))

if __name__ == "__main__":
    run_tests()

# For Vim, so we get 4-space indent
# vim: set sw=4:
