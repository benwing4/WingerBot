-- Authors: Benwing, ZxxZxxZ, Atitarev

local export = {}

local rsub = mw.ustring.gsub
local u = mw.ustring.char
local gcodepoint = mw.ustring.gcodepoint

local zwnj = u(0x200c) -- zero-width non-joiner
--local zwj = u(0x200d) -- zero-width joiner
--local lrm = u(0x200e) -- left-to-right mark
--local rlm = u(0x200f) -- right-to-left mark

local tt = {
	-- consonants
	["ب"]="b", ["ت"]="t", ["ث"]="ṯ", ["ج"]="j", ["ح"]="ḥ", ["خ"]="ḵ",
	["د"]="d", ["ذ"]="ḏ", ["ر"]="r", ["ز"]="z", ["س"]="s", ["ش"]="š",
	["ص"]="ṣ", ["ض"]="ḍ", ["ط"]="ṭ", ["ظ"]="ẓ", ["ع"]="ʿ", ["غ"]="ḡ",
	["ف"]="f", ["ق"]="q", ["ك"]="k", ["ل"]="l", ["م"]="m", ["ن"]="n",
	["ه"]="h",
	-- tāʾ marbūṭa (special) - always after a fátḥa (a), silent at the end of
	-- an utterance, "t" in ʾiḍāfa or with pronounced tanwīn
	-- \216\169 = tāʾ marbūṭa = ة
	-- control characters
	[zwnj]="-", -- ZWNJ (zero-width non-joiner)
	-- [zwj]="", -- ZWJ (zero-width joiner)
	-- rare letters
	["پ"]="p", ["چ"]="č", ["ڤ"]="v", ["گ"]="g", ["ڨ"]="g", ["ڧ"]="q",
	-- semivowels or long vowels, alif, hamza, special letters
	["ا"]="ā", -- ʾalif = \216\167
	-- hamzated letters
	["أ"]="ʾ", ["إ"]="ʾ", ["ؤ"]="ʾ", ["ئ"]="ʾ", ["ء"]="ʾ",
	["و"]="w", --"ū" after ḍamma (u) and not before diacritic = \217\136
	["ي"]="y", --"ī" after kasra (i) and not before diacritic = \217\138
	["ى"]="ā", -- ʾalif maqṣūra = \217\137
	["آ"]="ʾā", -- ʾalif madda = \217\162
	["ٱ"]= "", -- hamzatu l-waṣl = \217\177
	["\217\176"] = "ā", -- ʾalif xanjariyya = dagger ʾalif (Koranic diacritic)
	-- short vowels, šádda and sukūn
	-- \217\139 = "an" = fatḥatan
	-- \217\140 = "un" = ḍammatan
	-- \217\141 = "in" = kasratan
	["\217\142"]="a", -- fatḥa
	["\217\143"]="u", -- ḍamma
	["\217\144"]="i", -- kasra
	-- \217\145 = šadda - doubled consonant
	["\217\146"]="", --sukūn - no vowel
	-- ligatures
	["ﻻ"]="lā",
	["ﷲ"]="llāh",
	-- taṭwīl
	["ـ"]="", -- taṭwīl, no sound
	-- numerals
	["١"]="1", ["٢"]="2", ["٣"]="3", ["٤"]="4", ["٥"]="5",
	["٦"]="6", ["٧"]="7", ["٨"]="8", ["٩"]="9", ["٠"]="0",
	-- punctuation (leave on separate lines)
	["؟"]="?", -- question mark
	["،"]=",", -- comma
	["؛"]=";" -- semicolon
}

local consonants_needing_vowels = "بتثجحخدذرزسشصضطظعغفقكلمنهپچڤگڨڧأإؤئءةﷲ"
local consonants = consonants_needing_vowels .. "وي"
local punctuation = "؟،؛" .. "ـ" -- semicolon, comma, question mark, taṭwīl
local numbers = "١٢٣٤٥٦٧٨٩٠"

local before_diacritic_checking_subs = {
	------------ transformations prior to checking for diacritics --------------
	-- shadda+short-vowel (including tanwīn vowels, i.e. -an -in -un) gets
	-- replaced with short-vowel+shadda during NFC normalisation, which
	-- MediaWiki does for all Unicode strings; however, it makes the
	-- transliteration process inconvenient, so undo it.
	{"([\217\139\217\140\217\141\217\142\217\143\217\144\217\176])\217\145", "\217\145%1"},
	-- ignore alif jamīla (otiose alif in 3pl verb forms)
	--     #1: handle ḍamma + wāw + alif (final -ū)
	{"\217\143\217\136\216\167", "\217\143\217\136"},
	--     #2: handle wāw + sukūn + alif (final -w in -aw in defective verbs)
	--     this must go before the generation of w, which removes the waw here.
	{"\217\136\217\146\216\167", "\217\136\217\146"},
	-- ignore final alif or alif maqṣūra following fatḥatan (e.g. in accusative
	-- singular or words like عَصًا "stick" or هُذًى "guidance"; this is called
	-- tanwin nasb)
	{"\217\139[\216\167\217\137]", "\217\139"},
	-- same but with the fatḥatan placed over the alif or alif maqṣūra
	-- instead of over the previous letter (considered a misspelling but
	-- common)
	{"[\216\167\217\137]\217\139", "\217\139"},
	-- tāʾ marbūṭa should always be preceded by fatḥa, alif or dagger alif;
	-- infer fatḥa if not
	{"([^\217\142\216\167\217\176])\216\169", "%1\217\142\216\169"},
	-- similarly for alif between consonants, possibly marked with shadda
	-- (does not apply to initial alif, which is silent when not marked with
	-- hamza, or final alif, which might be pronounced as -an)
	{"([" .. consonants .. "]\217\145?)\216\167([" .. consonants .. "])",
		"%1\217\142\216\167%2"},
	-- infer fatḥa in case of non-fatḥa + alif/alif-maqṣūra + dagger alif
	{"([^\217\142])([\216\167\217\137]\217\176)", "%1\217\142%2"},
	-- infer kasra in case of hamza-under-alif not + kasra
	{"\216\165([^\217\144])", "\216\165\217\144%1"},
	-- ignore dagger alif placed over regular alif or alif maqṣūra
	{"([\216\167\217\137])\217\176", "%1"},

	-- initial al + consonant + shadda: remove shadda
	{"^([\216\167\217\177]\217\142?\217\132[" .. consonants .. "])\217\145", "%1"},
	{"%s([\216\167\217\177]\217\142?\217\132[" .. consonants .. "])\217\145", " %1"},
	-- handle utterance-initial or word-initial (a)l-, possibly marked with
	-- hamzatu l-waṣl
	{"^([\216\167\217\177])\217\142?\217\132",
		{["\216\167"] = "al-", ["\217\177"] = "l-"}},
	{"%s([\216\167\217\177])\217\142?\217\132",
		{["\216\167"] = " al-", ["\217\177"] = " l-"}}
}

-- Transliterate any words or phrases. OMIT_I3RAAB means leave out final
-- short vowels (ʾiʿrāb). FORCE_TRANSLATE causes even non-vocalized text to
-- be transliterated (normally the function checks for non-vocalized text and
-- returns nil, since such text is ambiguous in transliteration).
function export.tr(text, lang, sc, omit_i3raab, force_translate)
	-- make it possible to call this function from a template
	if type(text) == "table" then
		local function f(x) return (x ~= "") and x or nil end
		text, lang, sc, omit_i3raab, force_translate =
			f(text.args[1]), f(text.args[2]), f(text.args[3]), f(text.args[4]), f(text.args[5])
	end

	for _, sub in ipairs(before_diacritic_checking_subs) do
		text = rsub(text, sub[1], sub[2])
	end

	if not force_translate and not has_diacritics(text) then
		return nil
	end
	
	------------ transformations after checking for diacritics --------------
	-- Replace plain alif with hamzatu l-waṣl when followed by fatḥa/ḍamma/kasra.
	-- Must go after handling of initial al-, which distinguishes alif-fatḥa
	-- from alif w/hamzatu l-waṣl. Must go before generation of ū and ī, which
	-- eliminate the ḍamma/kasra.
	text = rsub(text, "\216\167([\217\142\217\143\217\144])", "\217\177%1")
 	-- ḍamma + waw not followed by a diacritic is ū, otherwise w
 	text = rsub(text, "\217\143\217\136([^\217\139\217\140\217\141\217\142\217\143\217\144\217\145\217\146\217\176])", "ū%1")
 	text = rsub(text, "\217\143\217\136$", "ū")
 	-- kasra + yaa not followed by a diacritic is ī, otherwise y
 	text = rsub(text, "\217\144\217\138([^\217\139\217\140\217\141\217\142\217\143\217\144\217\145\217\146\217\176])", "ī%1")
 	text = rsub(text, "\217\144\217\138$", "ī")
	-- convert shadda to double letter.
	text = rsub(text, "(.)\217\145", "%1%1")
	if not omit_i3raab then -- show ʾiʿrāb (desinential inflection) in transliteration
		-- tāʾ marbūṭa should not be rendered by -t if word-final even when
		-- ʾiʿrāb is shown; instead, use (t) before whitespace, nothing when final;
		-- but render final -اة as -āh, consistent with Wehr's dictionary 
		text = rsub(text, "\216\167\216\169$", "\216\167\h")
		text = rsub(text, "\216\169$", "")
 		text = rsub(text, "\216\169%s", "(t) ")
		text = rsub(text, ".", {
			["\216\169"] = "t", ["\217\139"] = "an", ["\217\141"] = "in", ["\217\140"] = "un",
			["\217\142"] = "a", ["\217\144"] = "i" , ["\217\143"] = "u"
		})
	else
		text = rsub(text, "\216\167\216\169$", "\216\167\h")
		text = rsub(text, "\216\169$", "")
		text = rsub(text, "\216\169", "(t)")
		text = rsub(text, "[\217\139\217\140\217\141]", "")
		text = rsub(text, "[\217\142\217\143\217\144]%s", " ")
		text = rsub(text, "[\217\142\217\143\217\144]$", "")
	end
	text = rsub(text, ".", tt)
	text = rsub(text, "aā", "ā")

	return text
end

local has_diacritics_subs = {
	-- FIXME! What about lam-alif ligature?
	-- remove punctuation and shadda
	-- must go before removing final consonants
	{"[" .. punctuation .. "\217\145]", ""},
	-- Remove consonants at end of word or utterance, so that we're OK with
	-- words lacking iʿrāb (must go before removing other consonants).
	-- If you want to catch places without iʿrāb, comment out the next two lines.
	{"[" .. consonants .. "]$", ""},
	{"[" .. consonants .. "]%s", " "},
	-- remove consonants (or alif) when followed by diacritics
	-- must go after removing shadda
	-- do not remove the diacritics yet because we need them to handle
	-- long-vowel sequences of diacritic + pseudo-consonant
	{"[" .. consonants .. "\216\167]([\217\139\217\140\217\141\217\142\217\143\217\144\217\146\217\176])", "%1"},
	-- the following two must go after removing consonants w/diacritics because
	-- we only want to treat vocalic wāw/yā' in them (we want to have removed
	-- wāw/yā' followed by a diacritic)
	-- remove ḍamma + wāw
	{"\217\143\217\136", ""},
	-- remove kasra + yā'
	{"\217\144\217\138", ""},
	-- remove fatḥa/fatḥatan + alif/alif-maqṣūra
	{"[\217\139\217\142][\216\167\217\137]", ""},
	-- remove diacritics
	{"[\217\139\217\140\217\141\217\142\217\143\217\144\217\146\217\176]", ""},
	-- remove numbers, hamzatu l-waṣl, alif madda
	{"[" .. numbers .. "ٱ" .. "آ" .. "]", ""},
	-- remove non-Arabic characters
	{"[^" .. u(0x0600) .. "-" .. u(0x06FF) .. u(0x0750) .. "-" .. u(0x077F) ..
		     u(0x08A0) .. "-" .. u(0x08FF) .. u(0xFB50) .. "-" .. u(0xFDFF) ..
		     u(0xFE70) .. "-" .. u(0xFEFF) .. "]", ""}
}

function has_diacritics(text)
	for _, sub in ipairs(has_diacritics_subs) do
		text = rsub(text, sub[1], sub[2])
	end
	return #text == 0
end


----------------------------------------------------------------------------
--                    Transliterate from Latin to Arabic                  --
----------------------------------------------------------------------------

---------       Transliterate with unvocalized Arabic to guide       ---------

local silent_alif_subst = u(0xfff1)
local silent_alif_maqsuura_subst = u(0xfff2)
local hamza_match={"ʾ","’","'","`"}
local hamza_match_or_empty={"ʾ","’","'","`",""}

-- Special-case matching at beginning of word. Plain alif normally corresponds
-- to nothing, and hamza seats might correspond to nothing (omitted hamza
-- at beginning of word). We can't allow e.g. أ to have "" as one of its
-- possibilities mid-word because that will screw up a word like سألة "saʾala",
-- which won't match at all because the أ will match nothing directly after
-- the Latin "s", and then the ʾ will never be matched.
local tt_to_arabic_matching_bow = { --beginning of word
	["ا"]={""},
	["أ"]=hamza_match_or_empty, ["إ"]=hamza_match_or_empty,
	["آ"]={"ʾaā","’aā","'aā","`aā","aā"}, -- ʾalif madda = \217\162
}

-- Special-case matching at end of word. Some ʾiʿrāb endings may appear in
-- the Arabic but not the transliteration; allow for that.
local tt_to_arabic_matching_eow = { --end of word
	["\217\140"]={"un",""}, -- ḍammatan
	["\217\142"]={"a",""}, -- fatḥa (in plurals)
	["\217\143"]={"u",""}, -- ḍamma (in diptotes)
	["\217\144"]={"i",""}, -- kasra (in duals)
}

-- This table maps Arabic characters to all the Latin characters that might
-- correspond to them. The entries can be a string (equivalent to a one-entry
-- array) or an array of strings. Each string might have multiple characters,
-- to handle things like خ=kh and ث=th.
local tt_to_arabic_matching = {
	-- consonants
	["ب"]="b", ["ت"]="t", ["ث"]={"ṯ","ŧ","θ","th"}, ["ج"]="j",
	-- allow what would normally be capital H, but we lowercase all text
	-- before processing
	["ح"]={"ḥ","ħ","h"}, ["خ"]={"ḵ","x","kh"},
	["د"]="d", ["ذ"]={"ḏ","đ","ð","dh"}, ["ر"]="r", ["ز"]="z",
	["س"]="s", ["ش"]={"š","sh"},
	-- allow non-emphatic to match so we can handle uppercase S, D, T, Z;
	-- we lowercase the text before processing to handle proper names and such
	["ص"]={"ṣ","sʿ","s"}, ["ض"]={"ḍ","dʿ","d"}, ["ط"]={"ṭ","tʿ","ṫ","t"}, ["ظ"]={"ẓ","ðʿ","đ̣","z"},
	["ع"]={"ʿ","ʕ","`","‘","ʻ","3"}, ["غ"]={"ḡ","ġ","ğ","gh"},
	["ف"]="f", ["ق"]="q", ["ك"]="k", ["ل"]="l", ["م"]="m", ["ن"]="n",
	["ه"]="h",
	["ة"]={"h","t","(t)",""},
	-- control characters
	[zwnj]={"-",""}, -- ZWNJ (zero-width non-joiner)
	-- [zwj]="", -- ZWJ (zero-width joiner)
	-- rare letters
	["پ"]="p", ["چ"]={"č","ch"}, ["ڤ"]="v", ["گ"]="g", ["ڨ"]="g", ["ڧ"]="q",
	-- semivowels or long vowels, alif, hamza, special letters
	["ا"]="ā", -- ʾalif = \216\167
	[silent_alif_subst]="",
	[silent_alif_maqsuura_subst]="",
	-- hamzated letters
	["أ"]=hamza_match, ["إ"]=hamza_match, ["ؤ"]=hamza_match,
	["ئ"]=hamza_match, ["ء"]=hamza_match,
	["و"]={"w","ū"},
	["ي"]={"y","ī"},
	["ى"]="ā", -- ʾalif maqṣūra = \217\137
	["آ"]={"ʾaā","’aā","'aā","`aā"}, -- ʾalif madda = \217\162
	["ٱ"]= "", -- hamzatu l-waṣl = \217\177
	["\217\176"] = "aā", -- ʾalif xanjariyya = dagger ʾalif (Koranic diacritic)
	-- short vowels, šadda and sukūn
	["\217\139"]="an", -- fatḥatan
	["\217\140"]="un", -- ḍammatan
	["\217\141"]="in", -- kasratan
	["\217\142"]="a", -- fatḥa
	["\217\143"]="u", -- ḍamma
	["\217\144"]="i", -- kasra
	["\217\145"]="\217\145", -- šadda - doubled consonant
	["\217\146"]="", --sukūn - no vowel
	-- ligatures
	["ﻻ"]="lā",
	["ﷲ"]="llāh",
	-- taṭwīl
	["ـ"]="", -- taṭwīl, no sound
	-- numerals
	["١"]="1", ["٢"]="2", ["٣"]="3", ["٤"]="4", ["٥"]="5",
	["٦"]="6", ["٧"]="7", ["٨"]="8", ["٩"]="9", ["٠"]="0",
	-- punctuation (leave on separate lines)
	["؟"]="?", -- question mark
	["،"]=",", -- comma
	["؛"]=";", -- semicolon
	[" "]=" "
}

local tt_to_arabic_unmatching = {
	["a"]="\217\142",
	["u"]="\217\143",
	["i"]="\217\144",
	["\217\145"]="\217\145",
}

function canonicalize_latin(text)
	text = mw.ustring.lower(text)
	-- eliminate accents
	text = rsub(text, ".",
		{["á"]="a", ["é"]="e", ["í"]="i", ["ó"]="o", ["ú"]="u",
		 ["ā́"]="ā", ["ḗ"]="ē", ["ī́"]="ī", ["ṓ"]="ō", ["ū́"]="ū"})
	-- some accented macron letters have the accent as a separate Unicode char
	text = rsub(text, ".́",
		{["ā́"]="ā", ["ḗ"]="ē", ["ī́"]="ī", ["ṓ"]="ō", ["ū́"]="ū"})
	-- eliminate doubled vowels = long vowels
	text = rsub(text, "([aeiou])%1", {a="ā", e="ē", i="ī", o="ō", u="ū"})
	-- eliminate vowels followed by colon = long vowels
	text = rsub(text, "([aeiou]):", {a="ā", e="ē", i="ī", o="ō", u="ū"})
	-- eliminate - or ' separating t-h, t'h, etc. in transliteration style
	-- that uses th to indicate ث
	text = rsub(text, "([dtgkcs])[-']h", "%1h")
	text = rsub(text, "ūw", "uww")
	text = rsub(text, "īy", "iyy")
	text = rsub(text, "ai", "ay")
	text = rsub(text, "au", "aw")
	text = rsub(text, "āi", "āy")
	text = rsub(text, "āu", "āw")
	text = rsub(text, "[-]", "") -- eliminate stray hyphens (e.g. in al-)
	-- add short vowel before long vowel since corresponding Arabic has it
	text = rsub(text, ".",
		{["ā"]="aā", ["ē"]="iī", ["ī"]="iī", ["ō"]="uū", ["ū"]="uū"})
	return text
end

function canonicalize_unvoc(unvoc)
	-- shadda+short-vowel (including tanwīn vowels, i.e. -an -in -un) gets
	-- replaced with short-vowel+shadda during NFC normalisation, which
	-- MediaWiki does for all Unicode strings; however, it makes the
	-- transliteration process inconvenient, so undo it.
	unvoc = rsub(unvoc,
		"([\217\139\217\140\217\141\217\142\217\143\217\144\217\176])\217\145", "\217\145%1")
	-- tāʾ marbūṭa should always be preceded by fatḥa, alif or dagger alif;
	-- infer fatḥa if not. This fatḥa will force a match to an "a" in the Latin,
	-- so we can safely have tāʾ marbūṭa itself match "h", "t" or "", making it
	-- work correctly with alif + tāʾ marbūṭa where e.g. اة = ā and stil
	-- correctly allow e.g. رة = ra but disallow رة = r.
	unvoc = rsub(unvoc, "([^\217\142\216\167\217\176])\216\169", "%1\217\142\216\169")
	-- Final alif or alif maqṣūra following fatḥatan is silent (e.g. in
	-- accusative singular or words like عَصًا "stick" or هُذًى "guidance"; this is
	-- called tanwin nasb). So substitute special silent versions of these
	-- vowels.
	unvoc = rsub(unvoc, "\217\139\216\167", "\217\139" .. silent_alif_subst)
	unvoc = rsub(unvoc, "\217\139\217\137", "\217\139" .. silent_alif_maqsuura_subst)
	-- same but with the fatḥatan placed over the alif or alif maqṣūra
	-- instead of over the previous letter (considered a misspelling but
	-- common)
	unvoc = rsub(unvoc, "\216\167\217\139", silent_alif_subst .. "\217\139")
	unvoc = rsub(unvoc, "\217\137\217\139", silent_alif_maqsuura_subst .. "\217\139")
	return unvoc
end

function canonicalize_arabic(text)
	text = rsub(text, silent_alif_subst, "ا")
	text = rsub(text, silent_alif_maqsuura_subst, "ى")
	-- add sukūn between adjacent consonants
	text = rsub(text, "([" .. consonants .. "])([" .. consonants .. "])", "%1\217\146%2")
	-- remove sukūn after ḍamma + wāw
	text = rsub(text, "\217\143\217\136\217\146", "\217\143\217\136")
	-- remove sukūn after kasra + yā'
	text = rsub(text, "\217\144\217\138\217\146", "\217\144\217\138")
	return text
end

-- Transliterate any words or phrases from Latin into Arabic script.
-- UNVOC is the unvocalized equivalent in Arabic. If unable to match, throw
-- an error if ERR, else return nil. This works by matching the
-- Latin to the unvocalized Arabic and inserting the appropriate diacritics
-- in the right places, so that ambiguities of Latin transliteration can be
-- correctly handled.
function export.tr_latin_matching(text, unvoc, err)
	-- make it possible to call this function from a template
	if type(text) == "table" then
		local function f(x) return (x ~= "") and x or nil end
		text, unvoc, err = f(text.args[1]), f(text.args[2]), f(text.args[3])
	end

	text = canonicalize_latin(text)
	-- convert double consonant to consonant + shadda
	text = rsub(text, "(.)%1", "%1\217\145")
	unvoc = canonicalize_unvoc(unvoc)

	local ar = {} -- exploded Arabic characters
	local la = {} -- exploded Latin characters
	local res = {} -- result Arabic characters
	for cp in gcodepoint(unvoc) do
		table.insert(ar, u(cp))
	end
	for cp in gcodepoint(text) do
		table.insert(la, u(cp))
	end
	local aind = 1 -- index of next Arabic character
	local alen = #ar
	local lind = 1 -- index of next Latin character
	local llen = #la
	
	-- attempt to match the current Arabic character against the current
	-- Latin character(s). If no match, return false; else, increment the
	-- Arabic and Latin pointers over the matched characters, add the Arabic
	-- character to the result characters and return true.
	function match()
		local ac = ar[aind]
		local bow = aind == 1 or ar[aind - 1] == " "
		local eow = aind == alen or ar[aind + 1] == " "
		local matches =
			bow and tt_to_arabic_matching_bow[ac] or
			eow and tt_to_arabic_matching_eow[ac] or
			tt_to_arabic_matching[ac]
		if matches == nil then
			if true then
				error("Encountered non-Arabic (?) character " .. ac ..
					" at index " .. aind)
			else
				matches = {ac}
			end
		end
		if type(matches) == "string" then
			matches = {matches}
		end
		for _, m in ipairs(matches) do
			local l = lind
			local matched = true
			for cp in gcodepoint(m) do
				if la[l] == u(cp) then
					l = l + 1
				else
					matched = false
					break
				end
			end
			if matched then
				lind = l
				aind = aind + 1
				table.insert(res, ac)
				return true
			end
		end
		return false
	end
	
	function cant_match()
		if aind < alen then
			error("Unable to match Arabic character " .. ar[aind] ..
				" at index " .. aind)
		else
			error("Unable to match trailing Latin character " .. la[lind] ..
				" at index " .. lind)
		end
	end

	-- Here we go through the unvocalized Arabic letter for letter, matching
	-- up the consonants we encounter with the corresponding Latin consonants
	-- using the table in tt_to_arabic_matching and copying the Arabic
	-- consonants into a destination array. When we don't match, we check for
	-- allowed unmatching Latin characters in tt_to_arabic_unmatching, which
	-- handles short vowels and shadda. If this doesn't match either, and we
	-- have left-over Arabic or Latin characters, we reject the whole match,
	-- either returning false or signaling an error.
	
	while aind <= alen or lind <= llen do
		local matched = false
		if aind <= alen and match() then
			matched = true
		else
			local unmatched = tt_to_arabic_unmatching[la[lind]]
			if unmatched then
				table.insert(res, unmatched)
				lind = lind + 1
				matched = true
			end
		end
		if not matched then
			if err then
				cant_match()
			else
				return false
			end
		end
	end
	
	local arabic = table.concat(res, "")
	arabic = canonicalize_arabic(arabic)
	return arabic
end

--------- Transliterate directly, without unvocalized Arabic to guide ---------
---------                         (NEEDS WORK)                        ---------

local tt_to_arabic_direct = {
	-- consonants
	["b"]="ب", ["t"]="ت", ["ṯ"]="ث", ["θ"]="ث", -- ["th"]="ث",
	["j"]="ج",
	["ḥ"]="ح", ["ħ"]="ح", ["ḵ"]="خ", ["x"]="خ", -- ["kh"]="خ",
	["d"]="د", ["ḏ"]="ذ", ["ð"]="ذ", ["đ"]="ذ", -- ["dh"]="ذ",
	["r"]="ر", ["z"]="ز", ["s"]="س", ["š"]="ش", -- ["sh"]="ش",
	["ṣ"]="ص", ["ḍ"]="ض", ["ṭ"]="ط", ["ẓ"]="ظ",
	["ʿ"]="ع", ["ʕ"]="ع",
	["`"]="ع",
	["3"]="ع",
	["ḡ"]="غ", ["ġ"]="غ", ["ğ"]="غ",  -- ["gh"]="غ",
	["f"]="ف", ["q"]="ق", ["k"]="ك", ["l"]="ل", ["m"]="م", ["n"]="ن",
	["h"]="ه",
	-- ["a"]="ة", ["ah"]="ة"
	-- tāʾ marbūṭa (special) - always after a fátḥa (a), silent at the end of
	-- an utterance, "t" in ʾiḍāfa or with pronounced tanwīn
	-- \216\169 = tāʾ marbūṭa = ة
	-- control characters
	-- [zwj]="", -- ZWJ (zero-width joiner)
	-- rare letters
	["p"]="پ", ["č"]="چ", ["v"]="ڤ", ["g"]="گ",
	-- semivowels or long vowels, alif, hamza, special letters
	["ā"] = "\217\142ا", -- ʾalif = \216\167
	-- ["aa"]="\217\142ا", ["a:"]="\217\142ا"
	-- hamzated letters
	["ʾ"]="ء",
	["’"]="ء",
	["'"]="ء",
	["w"]="و",
	["y"]="ي",
	["ū"]="\217\143و", -- ["uu"]="\217\143و", ["u:"]="\217\143و"
	["ī"]="\217\144ي", -- ["ii"]="\217\144ي", ["i:"]="\217\144ي"
	-- ["ā"]="ى", -- ʾalif maqṣūra = \217\137
	-- ["an"] = "\217\139" = fatḥatan
	-- ["un"] = "\217\140" = ḍammatan
	-- ["in"] = "\217\141" = kasratan
	["a"] = "\217\142", -- fatḥa
	["u"] = "\217\143", -- ḍamma
	["i"] = "\217\144", -- kasra
	-- \217\145 = šadda - doubled consonant
	-- ["\217\146"]="", --sukūn - no vowel
	-- ligatures
	-- ["ﻻ"]="lā",
	-- ["ﷲ"]="llāh",
	-- taṭwīl
	-- numerals
	["1"]="١", ["2"]="٢",-- ["3"]="٣",
	["4"]="٤", ["5"]="٥",
	["6"]="٦", ["7"]="٧", ["8"]="٨", ["9"]="٩", ["0"]="٠",
	-- punctuation (leave on separate lines)
	["?"]="؟", -- question mark
	[","]="،", -- comma
	[";"]="؛" -- semicolon
}

-- Transliterate any words or phrases from Latin into Arabic script.
-- POS, if not nil, is e.g. "noun" or "verb", controlling how to handle
-- final -a.
--
-- FIXME: NEEDS WORK. Works but ignores POS. Doesn't yet generate the correct
-- seat for hamza (need to reuse code in Module:ar-verb to do this). Always
-- transliterates final -a as fatḥa, never as tāʾ marbūṭa (should make use of
-- POS for this). Doesn't (and can't) know about cases where sh, th, etc.
-- stand for single letters rather than combinations.
function export.tr_latin_direct(text, pos)
	-- make it possible to call this function from a template
	if type(text) == "table" then
		local function f(x) return (x ~= "") and x or nil end
		text, pos =	f(text.args[1]), f(text.args[2])
	end

	text = canonicalize_latin(text)
	text = rsub(text, "ah$", "\217\142ة")
	text = rsub(text, "āh$", "\217\142اة")
	text = rsub(text, ".", tt_to_arabic_direct)
	-- convert double consonant to consonant + shadda
	text = rsub(text, "([" .. consonants .. "])%1", "%1\217\145")
	text = canonicalize_arabic(text)

	return text
end

return export
