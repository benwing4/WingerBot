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
L = u"ل"
Y = u"ي"

# combinations
UUN = U + u"ون"
UUNA = UUN + A
UNU = "[" + UN + U + "]"
UNUOPT = UNU + "?"

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
  # MediaWiki does for all Unicode strings; however, it makes
  # detection and replacement processes inconvenient, so undo it.
  return re.sub("(" + DIACRITIC_ANY_BUT_SH + ")" + SH, SH + r"\1", text)
