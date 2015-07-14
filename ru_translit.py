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
# 1. Should we canonicalize ɛ when it matches э? e.g. лавэ (lavɛ́)?
# 2. Cases like бере́г (berjóg) -- should we canonicalize to ё? Probably not?
# 3. Ask Anatoli: Is it safe to convert H to X opposite Cyrillic Х?
#    Occurs in Христова vs. Hristóva
# 4. Ask Anatoli: Is it safe to convert b to v opposite Cyrillic в?
#    Occurs many times, e.g. in раздваивать vs. razdvaibat'
# 5. Ask Anatoli about splitting templates: {{t+|ru|Катар|m|tr=Kátar, Katár}}
#    becomes {{t+|ru|Катар|m|tr=Kátar}}, {{t+|ru|Катар|m|tr=Katár}} and
#    then {{t+|ru|Ка́тар|m}}, {{t+|ru|Ката́р|m}} after accenting the Russian
#    and removing the now-redundant transliteration
# 6. Consider removing a stray paren from the Latin when it's unmatched and
#    no parens in the Russian, e.g. in recycling: {{t|ru|вторичная переработка|f|tr=vtoríčnaja pererabótka)|sc=Cyrl}}

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
    return unicodedata.normalize("NFKC", unicode(txt))

def nfd_form(txt):
    return unicodedata.normalize("NFKD", unicode(txt))

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

    # е after a vowel, at the beginning of a word or after non-word char
    # becomes je
    def replace_e(m):
        ttab = {u"Е":u"Je", u"е":u"je", u"Ѣ":u"Jě", u"ѣ":u"jě"}
        return m.group(1) + ttab[m.group(2)]
    # repeat to handle sequences of ЕЕЕЕЕ...
    for i in xrange(2):
        text = re.sub("(^|[" + russian_vowels + r"\W]" + ACGROPT +
                # re.U so \W is Unicode-dependent
                u")([ЕеѢѣ])", replace_e, text, 0, re.U)

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

# list of items to pre-canonicalize to ʺ, which needs to be first in the list
double_quote_like = [u"ʺ",u"”",u"″"]
# list of items to match-canonicalize to ʺ, which needs to be first in the list
double_quote_like_matching = double_quote_like + [u'"']
# list of items to pre-canonicalize to ʹ, which needs to be first in the list
single_quote_like = [u"ʹ",u"’",u"ʼ",u"´",u"′",u"ʲ",u"ь",u"ˈ",u"`",u"‘"]
# list of items to match-canonicalize to ʹ, which needs to be first in the list
# Don't put 'j here because we might legitimately have ья or similar
single_quote_like_matching = single_quote_like + [u"'ʹ",u"'"]
# regexps to use for early canonicalization in pre_canonicalize_latin()
double_quote_like_re = "[" + "".join(double_quote_like) + "]"
single_quote_like_re = "[" + "".join(single_quote_like) + "]"

russian_to_latin_lookalikes = {
        u"а":"a", u"е":"e", u"о":"o", u"х":"x", u"ӓ":u"ä", u"ё":u"ë", u"с":"c",
        u"і":"i",
        u"а́":u"á", u"е́":u"é", u"о́":"ó", u"і́":u"í",
        u"р":"p", u"у":"y",
        u"А":"A", u"Е":"E", u"О":"O", u"Х":"X", u"Ӓ":u"ä", u"Ё":u"Ë", u"С":"C",
        u"І":"I", u"К":"K",
        u"А́":"Á", u"Е́":"É", u"О́":"Ó", u"І́":"Í",
    }
latin_to_russian_lookalikes = dict(
        [(y, x) for x, y in russian_to_latin_lookalikes.items()])
# Filter out multi-char sequences, which will work only on the right side of
# the correspondence (the accented Russian chars; the other way will be
# handled by the non-accented equivalents, i.e. accented Russian with accent
# as separate character will be converted to accented Latin with Latin as
# separate character, which is exactly what we want.
russian_lookalikes_re = "[" + "".join(
        [x for x in russian_to_latin_lookalikes.keys() if len(x) == 1]) + "]"
latin_lookalikes_re = "[" + "".join(
        [x for x in russian_to_latin_lookalikes.values() if len(x) == 1]) + "]"

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

tt_to_russian_matching_uppercase = {
    u"А":u"A",
    u"Б":u"B",
    u"В":[u"V",u"B",u"W"],
    # most of these entries are here for the lowercase equivalent
    u'Г':[u'G',[u'V'],[u'X'],[(u"Χ",)],[u'Kh'],[u'H']],
    u"Д":u"D",
    # Canonicalize to capital_e_subst, which we later map to either Je or E
    # depending on what precedes. We don't use regular capital E as the
    # canonical character because Э also maps to E.
    # FIXME: Yo 'O ʹO 'Jo ʹJo should be converted to Jo.
    u"Е":[capital_e_subst,"E","Je","Ye",u"'E",u"ʹE",
        # O matches for after hushing sounds
        [u"Ɛ"],[u"Jo"],[u"Yo"],[u"'O"],[u"ʹO"],[u"'Jo"],[u"ʹJo"],[u"O"]],
    # FIXME: Yo 'O ʹO 'Jo ʹJo should be converted to Jo
    u"Ё":[u"Jo"+AC,u"Yo"+AC,u"'O"+AC,u"ʹO"+AC,u"'Jo"+AC,u"ʹJo"+AC,u"O"+AC,
        u"Ë",[u"Jo"],[u"Yo"],[u"'O"],[u"ʹO"],[u"'Jo"],[u"ʹJo"],[u"O"]],
    u"Ж":[u"Ž",u"zh",u"ʐ"], # no cap equiv: u"ʐ"?
    u"З":u"Z",
    u"И":[u"I",u"Yi",u"Y",u"'I",u"ʹI",u"Ji",u"И"],
    u"Й":[u"J",u"Y",u"Ĭ",u"I",u"Ÿ"],
    u"К":[u"K","Ck",u"C"],
    u"Л":u"L",
    u"М":u"M",
    u"Н":[u"N",u"H"],
    u"О":u"O",
    u"П":u"P",
    u"Р":u"R",
    u"С":[u"S",u"C"],
    u"Т":u"T",
    u"У":[u"U",u"Y",u"Ou"],
    u"Ф":[u"F",u"Ph"],
    # final X is Greek
    u"Х":[u"X",u"Kh",u"Ch",u"Č",u"Χ",u"H"], # Ch might have been canoned to Č
    u"Ц":[u"C",u"T͡s",u"Ts",u"Tz"],
    u'Ч':[u'Č',u"Ch",u"Tsch",u"Tsč",u"Tch",u"Tč",u"T͡ɕ",u"Ć",[u"Š"],[u"Sh"]],
    u"Ш":[u"Š",u"Sh"],
    u"Щ":[u"Šč",u"Shch",u"Sch",u"Sč",u"Š(č)",u"Ŝč",u"Ŝ",u"Š'",u"ʂ",u"Sh'",
        u"Š",u"Sh"],# No cap equiv? u"ʂ",
    u"Ъ":double_quote_like_matching + [u""],
    u"Ы":[u"Y",u"I",u"Ɨ",u"Ы",u"ı"],
    u"Ь":single_quote_like_matching + [u""],
    u"Э":[u"E",u"Ė",[u"Ɛ"]], # FIXME should we canonicalize ɛ here?
    u"Ю":[u"Ju",u"Yu",u"'U",u"ʹU",u"U",u"'Ju",u"ʹJu"],
    u"Я":[u"Ja",u"Ya",u"'A",u"ʹA",u"A",u"'Ja",u"ʹJa"],
    # archaic, pre-1918 letters
    u'І':u'I',
    # We will later map to Jě/jě as necessary.
    u'Ѣ':[u'Ě',u"E"],
    u'Ѳ':u'F',
    u'Ѵ':u'I',
}

tt_to_russian_matching_non_case = {
    # Russian style quotes
    u'«':[u'“',u'"'],
    u'»':[u'”',u'"'],
    # numerals
    u"1":u"1", u"2":u"2", u"3":u"3", u"4":u"4", u"5":u"5",
    u"6":u"6", u"7":u"7", u"8":u"8", u"9":u"9", u"0":u"0",
    # punctuation (leave on separate lines)
    u",":u",", # comma
    u";":u";", # semicolon
    u":":u":", # colon
    # these are now handled by check_unmatch_either()
    #u"?":[u"?",u""], # question mark
    #u".":[u".",u""], # period
    #u"!":[u"!",u""], # exclamation point
    u"-":u"-", # hyphen/dash
    u"—":[u"—",u"-"], # long dash
    u"/":u"/", # slash
    u'"':[(u'"',)], # quotation mark
    u"'":[(u"'",),(u"ʹ"),u""], # single quote, for bold/italic
    u"(":u"(", # parens
    u")":u")",
    u" ":u" ",
    u"[":u"",
    u"]":u"",
    # these are now handled by check_unmatch_either()
    #AC:[AC,""],
    #GR:[GR,""],
    # UNCLEAR WE NEED THE FOLLOWING DUE TO consume_against_eow_hard_sign()
    capital_silent_hard_sign:[u""],
    small_silent_hard_sign:[u""],
}

# Convert string, list of stuff of tuple of stuff into lowercase
def lower_entry(x):
    if isinstance(x, list):
        return [lower_entry(y) for y in x]
    if isinstance(x, tuple):
        return tuple(lower_entry(y) for y in x)
    if x == capital_e_subst:
        return small_e_subst
    return x.lower()

tt_to_russian_matching = {}
for k,v in tt_to_russian_matching_uppercase.items():
    if isinstance(v, basestring):
        v = [v]
    tt_to_russian_matching[k] = v + [lower_entry(x) for x in v]
    tt_to_russian_matching[k.lower()] = [lower_entry(x) for x in v]
tt_to_russian_matching[u"ё"][0:0] = [small_jo_subst]
tt_to_russian_matching[u"ю"][0:0] = [small_ju_subst]
for k,v in tt_to_russian_matching_non_case.items():
    tt_to_russian_matching[k] = v

tt_to_russian_matching_2char = {
    u"ый":["yj","yi","y"],
    u"ий":["ij","yi",u"i"],
    # ja for ся is strange but occurs in ться vs. tʹja
    u"ся":["sja","sa",u"ja"], # especially in the reflexive ending
    u"нн":["nn","n"],
    u"ть":[u"tʹ",u"ť",u"ț"],
    # FIXME: Canonicalize these to convert weird char into tj
    u"тё":[u"tjo"+AC,u"ťo"+AC,u"ț"+AC,[u"ťo"],[u"țo"]],
    u"те":[u"te",u"ťe",u"țe"],
    u"ие":["ije",u"ʹje",u"'je","je"],
    u"сч":[u"sč",u"šč",u"š"],
    u"зч":[u"zč",u"šč",u"š"],
    u"ия":["ija","ia"],
    u"ьо":[u"ʹo",u"ʹjo",u"'jo",u"jo"],
    u"ль":[u"lʹ",u"ľ"],
    u"дж":[u"dž",u"j"],
    u"кс":[u"ks",u"x"],
}

tt_to_russian_matching_3char = {
    u" — ":[u" — ",u"—",u" - ",u"-"],
}

tt_to_russian_matching_4char = {
    u"вств":[u"vstv","stv"],
}

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

# Pre-canonicalize Latin, and Russian if supplied. If Russian is supplied,
# it should be the corresponding Russian (after pre-pre-canonicalization),
# and is used to do extra canonicalizations.
def pre_canonicalize_latin(text, russian=None):
    debprint("pre_canonicalize_latin: Enter, text=%s" % text)
    # remove L2R, R2L markers
    text = rsub(text, u"[\u200E\u200F]", "")
    # remove embedded comments
    text = rsub(text, u"<!--.*?-->", "")
    # remove embedded IPAchar templates
    text = rsub(text, r"\{\{IPAchar\|(.*?)\}\}", r"\1")
    # canonicalize whitespace, including things like no-break space
    text = re.sub(r"\s+", " ", text, 0, re.U)
    # remove leading/trailing spaces
    text = text.strip()
    # decompose accented letters
    text = rsub(text, u"[áéíóúýńÁÉÍÓÚÝŃàèìòùỳÀÈÌÒÙỲ]",
            {u"á":"a"+AC, u"é":"e"+AC, u"í":"i"+AC,
             u"ó":"o"+AC, u"ú":"u"+AC, u"ý":"y"+AC, u"ń":"n"+AC,
             u"Á":"A"+AC, u"É":"E"+AC, u"Í":"I"+AC,
             u"Ó":"O"+AC, u"Ú":"U"+AC, u"Ý":"Y"+AC, u"Ń":"N"+AC,
             u"à":"a"+GR, u"è":"e"+GR, u"ì":"i"+GR,
             u"ò":"o"+GR, u"ù":"u"+GR, u"ỳ":"y"+GR,
             u"À":"A"+GR, u"È":"E"+GR, u"Ì":"I"+GR,
             u"Ò":"O"+GR, u"Ù":"U"+GR, u"Ỳ":"Y"+GR,})

    # "compose" digraphs
    text = rsub(text, u"[czskCZSK]h",
        {"ch":u"č", "zh":u"ž", "sh":u"š", "kh":"x",
         "Ch":u"Č", "Zh":u"Ž", "Sh":u"Š", "Kh":"X"})

    # canonicalize quote-like signs to make matching easier.
    text = rsub(text, double_quote_like_re, double_quote_like[0])
    text = rsub(text, single_quote_like_re, single_quote_like[0])

    # sub non-Latin similar chars to Latin
    text = rsub(text, russian_lookalikes_re, russian_to_latin_lookalikes)
    text = rsub(text, u"[эε]",u'ɛ') # Cyrillic э, Greek ε to Latin ɛ

    # remove some accents
    text = rsub(text, u"[äïöüÿÄÏÖÜŸǎǐǒǔǍǏǑǓ]",
            {u"ä":"a",u"ï":"i",u"ö":"o",u"ü":"u",
             u"ǎ":"a",u"ǐ":"i",u"ǒ":"o",u"ǔ":"u",
             u"Ä":"A",u"Ï":"I",u"ö":"O",u"Ü":"U",
             u"Ǎ":"A",u"Ǐ":"I",u"Ǒ":"O",u"Ǔ":"U",})

    # remove [[...]] from Latin
    if text.startswith("[[") and text.endswith("]]"):
        text = text[2:-2]

    # remove '''...''', ''...'' from Latin if not in Russian
    if russian:
        if (text.startswith("'''") and text.endswith("'''") and
                not russian.startswith("'''") and not russian.endswith("'''")):
            text = text[3:-3]
        elif (text.startswith("''") and text.endswith("''") and
                not russian.startswith("''") and not russian.endswith("''")):
            text = text[2:-2]

    # remove leading/trailing spaces again, cases like ''podnimát' ''
    text = text.strip()

    debprint("pre_canonicalize_latin: Exit, text=%s" % text)
    return text

def tr_canonicalize_latin(text):
    # recompose accented letters
    text = rsub(text, "[aeiouyAEIOUY][" + AC + GR + "]",
        {"a"+AC:u"á", "e"+AC:u"é", "i"+AC:u"í",
         "o"+AC:u"ó", "u"+AC:u"ú", "y"+AC:u"ý", "n"+AC:u"ń",
         "A"+AC:u"Á", "E"+AC:u"É", "I"+AC:u"Í",
         "O"+AC:u"Ó", "U"+AC:u"Ú", "Y"+AC:u"Ý", "N"+AC:u"Ń",
         "a"+GR:u"à", "e"+GR:u"è", "i"+GR:u"ì",
         "o"+GR:u"ò", "u"+GR:u"ù", "y"+GR:u"ỳ",
         "A"+GR:u"À", "E"+GR:u"È", "I"+GR:u"Ì",
         "O"+GR:u"Ò", "U"+GR:u"Ù", "Y"+GR:u"Ỳ",})

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
    bow_or_vowel = u"(^|[- \[aeiouyěAEIOUYĚʺʹ%s%s]%s)" % (
            capital_e_subst, small_e_subst, ACGROPT)
    # repeat to handle sequences of ЕЕЕЕЕ...
    for i in xrange(2):
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

def canonicalize_latin_foreign(latin, russian):
    return canonicalize_latin_russian(latin, russian)

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
    # canonicalize whitespace, including things like no-break space
    text = re.sub(r"\s+", " ", text, 0, re.U)
    # remove leading/trailing spaces
    text = text.strip()

    text = tr_canonicalize_russian(text)

    # Convert word-final hard sign to special silent character; will be
    # undone later
    text = rsub(text, u"Ъ($|[- \]])", capital_silent_hard_sign + r"\1")
    text = rsub(text, u"ъ($|[- \]])", small_silent_hard_sign + r"\1")

    # sub non-Cyrillic similar chars to Cyrillic
    text = rsub(text, latin_lookalikes_re, latin_to_russian_lookalikes)

    return text

def pre_canonicalize_russian(text):
    return text

def post_canonicalize_russian(text):
    text = text.replace(capital_silent_hard_sign, u"Ъ")
    text = text.replace(small_silent_hard_sign, u"ъ")
    return text

debug_tr_matching = False
def debprint(x):
    if debug_tr_matching:
        uniprint(x)

# Vocalize Russian based on transliterated Latin, and canonicalize the
# transliteration based on the Russian.  This works by matching the Latin
# to the Russian and transferring Latin stress marks to the Russian as
# appropriate, so that ambiguities of Latin transliteration can be
# correctly handled. Returns a tuple of Russian, Latin. If unable to match,
# throw an error if ERR, else return None.
def tr_matching(russian, latin, err=False, msgfun=None):
    origrussian = russian
    origlatin = latin
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

    def get_matches_nchar(numchar):
        assert numchar >= 2 and numchar <= 4
        assert rind[0] + numchar <= rlen
        ac = "".join(ru[rind[0]:rind[0]+numchar])
        debprint("get_matches_%schar: ac (%schar) is %s" % (
            numchar, numchar, ac))
        if numchar == 4:
            matches = tt_to_russian_matching_4char.get(ac)
        elif numchar == 3:
            matches = tt_to_russian_matching_3char.get(ac)
        elif numchar == 2:
            matches = tt_to_russian_matching_2char.get(ac)
        debprint("get_matches_%schar: matches is %s" % (numchar, matches))
        if matches == None:
            matches = []
        elif type(matches) is not list:
            matches = [matches]
        return ac, matches

    def get_matches():
        assert rind[0] < rlen
        ac = ru[rind[0]]
        debprint("get_matches: ac is %s" % ac)
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
        return ac, matches

    def skip_vertical_bar_link():
        # Check for link of the form [[foo|bar]] and skip over the part
        # up through the vertical bar, copying it
        if rind[0] < rlen and ru[rind[0]] == '[':
            newpos = rind[0]
            while newpos < rlen and ru[newpos] != ']':
                if ru[newpos] == '|':
                    newpos += 1
                    debprint("skip_vertical_bar_link: skip over [[...|, rind=%s -> %s" % (
                        rind[0], newpos))
                    while rind[0] < newpos:
                        res.append(ru[rind[0]])
                        rind[0] += 1
                    return True
                newpos += 1
        return False

    # attempt to match the current Russian character (or multi-char sequence,
    # if NUMCHAR > 1) against the current Latin character(s). If no match,
    # return False; else, increment the Russian and Latin pointers over
    # the matched characters, add the Russian character to the result
    # characters and return True.
    def match(numchar):
        if rind[0] + numchar > rlen:
            return False

        if numchar > 1:
            ac, matches = get_matches_nchar(numchar)
        else:
            ac, matches = get_matches()

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
                debprint("cp: %s" % cp)
                if l < llen and la[l] == cp:
                    l = l + 1
                else:
                    matched = False
                    break
            if matched:
                for c in ac:
                    res.append(c)
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
                rind[0] = rind[0] + len(ac)
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

    # Handle acute or grave accent or punctuation, which can be unmatching
    # on either side.
    def check_unmatch_either():
        unmatch_either = [AC, GR, "!", "?", "."]
        # Matching accents
        if (lind[0] < llen and rind[0] < rlen and
                la[lind[0]] in unmatch_either and
                la[lind[0]] == ru[rind[0]]):
            res.append(ru[rind[0]])
            lres.append(la[lind[0]])
            rind[0] += 1
            lind[0] += 1
            return True
        # Unmatched accent on Latin side
        if lind[0] < llen and la[lind[0]] in unmatch_either:
            res.append(la[lind[0]])
            lres.append(la[lind[0]])
            lind[0] += 1
            return True
        # Unmatched accent on Russian side
        if rind[0] < rlen and ru[rind[0]] in unmatch_either:
            res.append(ru[rind[0]])
            lres.append(ru[rind[0]])
            rind[0] += 1
            return True
        return False

    def consume_against_eow_hard_sign():
        if rind[0] < rlen and ru[rind[0]] in [capital_silent_hard_sign,
                small_silent_hard_sign]:
            # Consume any hard/soft-like signs
            if lind[0] < llen and la[lind[0]] in ([u"Ъ",u"ъ"] +
                    double_quote_like_matching + single_quote_like_matching):
                lind[0] += 1
            res.append(ru[rind[0]])
            rind[0] += 1
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
        # Check for matching or unmatching acute/grave accent or punctuation.
        # We do this first to deal with cases where the Russian has a
        # right bracket, single quote or similar character that can be
        # unmatching, and the Latin has an unmatched accent, which needs
        # to be matched first.
        if check_unmatch_either():
            matched = True
        elif consume_against_eow_hard_sign():
            debprint("Matched: consume_against_eow_hard_sign()")
            matched = True
        elif skip_vertical_bar_link():
            debprint("Matched: skip_vertical_bar_link()")
            matched = True
        elif match(4):
            debprint("Matched: Clause match(4)")
            matched = True
        elif match(3):
            debprint("Matched: Clause match(3)")
            matched = True
        elif match(2):
            debprint("Matched: Clause match(2)")
            matched = True
        elif match(1):
            debprint("Matched: Clause match(1)")
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

def remove_diacritics(text):
    text = text.replace(AC, "")
    text = text.replace(GR, "")
    return text

################################ Test code ##########################

num_failed = 0
num_succeeded = 0

def test(latin, russian, should_outcome, expectedrussian=None):
    def msg(text):
      print text.encode('utf-8')
    global num_succeeded, num_failed
    if not expectedrussian:
        expectedrussian = russian
    try:
        result = tr_matching(russian, latin, True, msg)
    except RuntimeError as e:
        uniprint(u"%s" % e)
        result = False
    if result == False:
        uniprint("tr_matching(%s, %s) = %s" % (russian, latin, result))
        outcome = "failed"
        canonrussian = expectedrussian
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
    if canonrussian != expectedrussian:
        uniprint("Canon Russian FAILED, expected %s got %s"% (
            expectedrussian, canonrussian))
    canonlatin, _ = canonicalize_latin_russian(latin, None)
    uniprint("canonicalize_latin(%s) = %s" %
            (latin, canonlatin))
    if outcome == should_outcome and canonrussian == expectedrussian:
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
    test(u"zóntik", u"зо́нтик", "matched", u"зо́нтик")
    test(u"zóntik", u"зонтик", "matched", u"зо́нтик")
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
    test(u"ébe ébe", u"ебе ебе", "matched", u"е́бе е́бе")
    test(u"Ébe Ébe", u"Ебе Ебе", "matched", u"Е́бе Е́бе")
    test(u"yéye yéye", u"ее ее", "matched", u"е́е е́е")
    test(u"yéye yéye", u"е́е е́е", "matched")
    test("yeye yeye", u"е́е е́е", "matched")

    # Test with ju after hushing sounds
    test(u"broshúra", u"брошюра", "matched", u"брошю́ра")
    test(u"broshyúra", u"брошюра", "matched", u"брошю́ра")
    test(u"zhurí", u"жюри", "matched", u"жюри́")

    # Test with ' representing ь, which should be canonicalized to ʹ
    test(u"pal'da", u"пальда", "matched")

    # Test with jo
    test(u"ketjó", u"кетё", "matched")
    test(u"kétjo", u"кетё", "unmatched", u"ке́тё")
    test(u"kešó", u"кешё", "matched")
    test(u"kešjó", u"кешё", "matched")

    # Test handling of embedded links, including unmatched acute accent
    # directly before right bracket on Russian side
    test(u"pala volu", u"пала [[вола|волу]]", "matched")
    test(u"pala volú", u"пала [[вола|волу]]", "matched", u"пала [[вола|волу́]]")
    test(u"volu pala", u"[[вола|волу]] пала", "matched")
    test(u"volú pala", u"[[вола|волу]] пала", "matched", u"[[вола|волу́]] пала")
    test(u"volupala", u"[[вола|волу]]пала", "matched")
    test(u"pala volu", u"пала [[волу]]", "matched")
    test(u"pala volú", u"пала [[волу]]", "matched", u"пала [[волу́]]")
    test(u"volu pala", u"[[волу]] пала", "matched")
    test(u"volú pala", u"[[волу]] пала", "matched", u"[[волу́]] пала")
    test(u"volúpala", u"[[волу]]пала", "matched", u"[[волу́]]пала")

    # Silent hard signs
    test("mir", u"миръ", "matched")
    test("mir", u"міръ", "matched")
    test("MIR", u"МІРЪ", "matched")

    # Single quotes in Russian
    test("volu '''pala'''", u"волу '''пала'''", "matched")
    test("volu pala", u"волу '''пала'''", "matched")
    test(u"volu '''palá'''", u"волу '''пала'''", "matched", u"волу '''пала́'''")
    test(u"volu palá", u"волу '''пала'''", "matched", u"волу '''пала́'''")
    # Here the single quote after l should become ʹ but not the others
    test(u"volu '''pal'dá'''", u"волу '''пальда'''", "matched", u"волу '''пальда́'''")
    test(u"bólʹše vsevó", u"[[бо́льше]] [[всё|всего́]]", "unmatched")

    # Some real-world tests
    # FIXME!!
    # test(u"Gorbačóv", u"Горбачев", "matched", u"Горбачёв")
    test(u"Igor", u"Игорь", "matched")
    test(u"rajón″", u"районъ", "matched", u"райо́нъ")
    test(u"karantin’", u"карантинъ", "matched")
    test(u"blyad", u"блядь", "matched")
    test(u"ródъ", u"родъ", "matched", u"ро́дъ")
    test(u"soból´", u"соболь", "matched", u"собо́ль")
    test(u"časóvn'a", u"часовня", "matched", u"часо́вня")
    test(u"ėkzistencializm", u"экзистенциализм", "matched")
    test(u"ješčó", u"ещё", "matched")
    test(u"pardoń", u"пардон́", "matched")
    # The following Latin has Russian ё
    test(u"lёgkoe", u"лёгкое", "matched")
    test(u"prýšik", u"прыщик", "matched", u"пры́щик")
    test(u"''d'ejstvít'el'nost'''", u"действительность", "matched",
            u"действи́тельность")
    test(u"óstrov Rejun'jón", u"остров Реюньон", "matched", u"о́стров Реюньо́н")
    test(u"staromodny", u"старомодный", "matched")
    # also should match when listed Russian 2-char sequence fails to match
    # as such but can match char-by-char
    test(u"niy", u"ный", "matched")
    test(u"trudít’sa", u"трудиться", "matched", u"труди́ться")
    test(u"vsestorónij", u"всесторонний", "matched", u"всесторо́нний")
    test(u"Válle-d’Aósta", u"Валле-д'Аоста", "matched", u"Ва́лле-д'Ао́ста")
    test(u"interesovátʹja", u"интересоваться", "matched", u"интересова́ться")
    test(u"rešímosť", u"решимость", "matched", u"реши́мость")
    test(u"smirénje", u"смирение", "matched", u"смире́ние")
    test(u"prékhodjaschij", u"преходящий", "matched", u"пре́ходящий")
    test(u"čústvo jazyká", u"чувство языка", "matched", u"чу́вство языка́")
    test(u"zanoš'ivost'", u"заносчивость", "matched")
    test(u"brezgátь", u"брезгать", "matched", u"брезга́ть")
    test(u"adaptacia", u"адаптация", "matched")
    test(u"apryiórniy", u"априо́рный", "matched")
    # The following has Latin é in the Cyrillic
    test(u"prostrе́l", u"прострéл", "matched", u"простре́л")
    test(u"razdvaibat'", u"раздваивать", "matched")
    # The following has Latin a in the Cyrillic
    test(u"Malán'ja", u"Мaла́нья", "matched", u"Мала́нья")
    test(u"''podnimát' ''", u"поднимать", "matched", u"поднима́ть")
    test(u"priv'áš'ivyj", u"привязчивый", "matched", u"привя́зчивый")
    test(u"zaméthyj", u"заметный", "matched", u"заме́тный")
    # FIXME, should canonicalize the yo; Cyrillic has Latin ë
    test(u"beznadyozhnyi", u"безнадëжный", "unmatched", u"безнадёжный")
    test(u"žénščinы", u"женщины", "matched", u"же́нщины")
    test(u"diakhronicheskyi", u"диахронический", "matched")
    test(u"m'áχkij", u"мягкий", "unmatched", u"мя́гкий")
    test(u"vnimӓtelʹnyj",u"внима́тельный", "matched")
    test(u"brítanskij ángliskij", u"британский английский", "matched",
            u"бри́танский а́нглийский")
    test(u"gospódʹ", u"Госпо́дь", "matched")
    test(u"ťomnij", u"тёмный", "unmatched")
    test(u"bidonviľ", u"бидонвиль", "matched")
    test(u"zádneje sidénʹje", u"заднее сидение", "matched", u"за́днее сиде́ние")
    test(u"s volkámi žitʹ - po-vólčʹi vytʹ", u"с волками жить — по-волчьи выть",
            "matched", u"с волка́ми жить — по-во́лчьи выть")
    test(u"Tajikskaja SSR", u"Таджикская ССР", "matched")
    test(u"loxodroma", u"локсодрома", "matched")
    test(u"prostophilya", u"простофиля", "matched")
    test(u"polevój gospitál‘", u"полевой госпиталь", "matched",
            u"полево́й госпита́ль")
    test(u"vrémja—dén’gi", u"время — деньги", "matched", u"вре́мя — де́ньги")
    test(u"piniǎ", u"пиния", "matched")
    test(u"losjón", u"лосьон", "matched", u"лосьо́н")

    # Test adding !, ? or .
    test(u"fan", u"фан!", "matched")
    test(u"fan!", u"фан!", "matched")
    test(u"fan!", u"фан", "matched", u"фан!")
    test(u"fan", u"фан?", "matched")
    test(u"fan?", u"фан?", "matched")
    test(u"fan?", u"фан", "matched", u"фан?")
    test(u"fan", u"фан.", "matched")
    test(u"fan.", u"фан.", "matched")
    test(u"fan.", u"фан", "matched", u"фан.")

    # Final results
    uniprint("RESULTS: %s SUCCEEDED, %s FAILED." % (num_succeeded, num_failed))

if __name__ == "__main__":
    run_tests()

# For Vim, so we get 4-space indent
# vim: set sw=4:
