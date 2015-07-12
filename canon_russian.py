#!/usr/bin/env python
#coding: utf-8

#    canon_russian.py is free software: you can redistribute it and/or modify
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

import blib
import ru_translit
from canon_foreign import canon_links

langs_with_terms_derived_from_russian = [
  u"Abkhaz",
  u"Adyghe",
  u"Afrikaans",
  u"Ahtna",
  u"Albanian",
  u"Aleut",
  u"Alutiiq",
  u"Arabic",
  u"Armenian",
  u"Azeri",
  u"Bashkir",
  u"Belarusian",
  u"Bengali",
  u"Bulgarian",
  u"Catalan",
  u"Central Kurdish",
  u"Chechen",
  u"Chinese",
  u"Chuvash",
  u"Crimean Tatar",
  u"Czech",
  u"Danish",
  u"Dutch",
  u"English",
  u"Esperanto",
  u"Estonian",
  u"Faroese",
  u"Finnish",
  u"French",
  u"Gagauz",
  u"Georgian",
  u"German",
  u"Greek",
  u"Hebrew",
  u"Hindi",
  u"Hungarian",
  u"Icelandic",
  u"Ido",
  u"Ingrian",
  u"Irish",
  u"Italian",
  u"Japanese",
  u"Karakalpak",
  u"Karelian",
  u"Kazakh",
  u"Ket",
  u"Khakas",
  u"Kildin Sami",
  u"Korean",
  u"Kyrgyz",
  u"Latin",
  u"Latvian",
  u"Lezgi",
  u"Lithuanian",
  u"Lojban",
  u"Macedonian",
  u"Malay",
  u"Mandarin",
  u"Mongolian",
  u"Nivkh",
  u"Norman",
  u"Norwegian Bokmål",
  u"Norwegian Nynorsk",
  u"Norwegian",
  u"Ossetian",
  u"Persian",
  u"Polish",
  u"Portuguese",
  u"Romanian",
  u"Serbo-Croatian",
  u"Skolt Sami",
  u"Slovak",
  u"Slovene",
  u"Spanish",
  u"Swedish",
  u"Taimyr Pidgin Russian",
  u"Tajik",
  u"Tatar",
  u"Tlingit",
  u"Translingual",
  u"Turkish",
  u"Turkmen",
  u"Tuvan",
  u"Ukrainian",
  u"Urdu",
  u"Uyghur",
  u"Uzbek",
  u"Veps",
  u"Vietnamese",
  u"Volapük",
  u"Votic",
  u"Yakut",
  u"Yiddish",
  u"Yup'ik",
  u"Zazaki",
]

pa = blib.init_argparser("Canonicalize Russian and translit")
pa.add_argument("--cattype", default="borrowed",
    help="Categories to examine ('vocab', 'borrowed', 'translit')")

parms = pa.parse_args()
startFrom, upTo = blib.parse_start_end(parms.start, parms.end)

canon_links(parms.save, parms.verbose, parms.cattype, "ru", "Russian", "Cyrl",
    ru_translit, langs_with_terms_derived_from_russian, startFrom, upTo)
