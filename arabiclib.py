#!/usr/bin/env python
#coding: utf-8

import re

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
W = u"و"
L = u"ل"
N = u"ن"
T = u"ت"

# combinations
AW = A + W
AY = A + Y
IY = I + Y
UW = U + W
AA = A + ALIF
II = IY
IIN = IY + N
IINA = IIN + A
UU = UW
UUN = UU + N
UUNA = UUN + A
AWN = AW + SK + N
AWNA = AWN + A
UNU = "[" + UN + U + "]"
UNUOPT = UNU + "?"
AH = A + TAM
AAH = AA + TAM
AAT = AA + T
AATUN = AAT + UN
IYAH = I + Y + AH
AYAAT = AY + AAT
IYAAT = IY + AAT
IYYAH = IY + SH + AH

def remove_diacritics(word):
  return re.sub(DIACRITIC_ANY, "", word)

def reorder_shadda(text):
  # shadda+short-vowel (including tanwīn vowels, i.e. -an -in -un) gets
  # replaced with short-vowel+shadda during NFC normalisation, which
  # MediaWiki does for all Unicode strings; however, it makes
  # detection and replacement processes inconvenient, so undo it.
  return re.sub("(" + DIACRITIC_ANY_BUT_SH + ")" + SH, SH + r"\1", text)

arabic_adj_headword_templates = [
  "ar-adj", "ar-adj-sound", "ar-adj-in", "ar-adj-an", "ar-nisba",
  "ar-adj-fem", "ar-adj-pl", "ar-adj-dual"]

arabic_noun_headword_templates = [
  # Nouns/numerals/pronouns
  "ar-noun", "ar-coll-noun", "ar-sing-noun", "ar-noun-nisba",
  "ar-proper noun", "ar-numeral", "ar-pron",
  "ar-noun-pl", "ar-noun-dual"]

arabic_participle_headword_templates = [
  "ar-act-participle", "ar-pass-participle"]

arabic_verb_headword_templates = [
  "ar-verb", "ar-verb-form"]

arabic_other_headword_templates = [
  "ar-adv", "ar-con", "ar-interj", "ar-particle", "ar-prep"]

arabic_nominal_headword_templates = (
    arabic_adj_headword_templates +
    arabic_noun_headword_templates +
    arabic_participle_headword_templates)

arabic_non_verbal_headword_templates = (
    arabic_nominal_headword_templates +
    arabic_other_headword_templates)

arabic_all_headword_templates = (
    arabic_adj_headword_templates +
    arabic_noun_headword_templates +
    arabic_participle_headword_templates +
    arabic_verb_headword_templates +
    arabic_other_headword_templates)

arabic_decl_templates = [
  "ar-decl-noun", "ar-decl-gendered-noun", "ar-decl-coll-noun",
    "ar-decl-sing-noun", "ar-decl-adj", "ar-decl-numeral"]
