-- Authors: Benwing, ZxxZxxZ, Atitarev

local export = {}

local u = mw.ustring.char
local rfind = mw.ustring.find
local rsubn = mw.ustring.gsub
local rmatch = mw.ustring.match
local rsplit = mw.text.split
local gcodepoint = mw.ustring.gcodepoint

-- version of rsubn() that discards all but the first return value
function rsub(term, foo, bar)
	local retval = rsubn(term, foo, bar)
	return retval
end

local zwnj = u(0x200c) -- zero-width non-joiner
--local zwj = u(0x200d) -- zero-width joiner
--local lrm = u(0x200e) -- left-to-right mark
--local rlm = u(0x200f) -- right-to-left mark

-- A comment about notation like \216\169: We use this in place of directly
-- encoding diacritics to avoid difficulties with display in the editing window.
-- These are decimal (NOT octal) encodings of the UTF-8 equivalent of the
-- characters, e.g. \216\169 = D8 A9 in UTF-8 = U+0629 = ة = tāʾ marbūṭa.
local tt = {
	-- consonants
	["ب"]="b", ["ت"]="t", ["ث"]="ṯ", ["ج"]="j", ["ح"]="ḥ", ["خ"]="ḵ",
	["د"]="d", ["ذ"]="ḏ", ["ر"]="r", ["ز"]="z", ["س"]="s", ["ش"]="š",
	["ص"]="ṣ", ["ض"]="ḍ", ["ط"]="ṭ", ["ظ"]="ẓ", ["ع"]="ʿ", ["غ"]="ḡ",
	["ف"]="f", ["ق"]="q", ["ك"]="k", ["ل"]="l", ["م"]="m", ["ن"]="n",
	["ه"]="h",
	-- tāʾ marbūṭa (special) - always after a fátḥa (a), silent at the end of
	-- an utterance, "t" in ʾiḍāfa or with pronounced tanwīn. We catch
	-- most instances of tāʾ marbūṭa before we get to this stage.
	["\216\169"]="t", -- tāʾ marbūṭa = ة
	-- control characters
	[zwnj]="-", -- ZWNJ (zero-width non-joiner)
	-- [zwj]="", -- ZWJ (zero-width joiner)
	-- rare letters
	["پ"]="p", ["چ"]="č", ["ڤ"]="v", ["ڥ"]="v", ["گ"]="g", ["ڨ"]="g", ["ڧ"]="q",
	-- semivowels or long vowels, alif, hamza, special letters
	["ا"]="ā", -- ʾalif = \216\167
	-- hamzated letters
	["أ"]="ʾ", -- hamza over alif = \216\163
	["إ"]="ʾ", -- hamza under alif = \216\165
	["ؤ"]="ʾ", -- hamza over wāw = \216\164
	["ئ"]="ʾ", -- hamza over yā = \216\166
	["ء"]="ʾ", -- hamza on the line = \216\161
	-- long vowels
	["و"]="w", --"ū" after ḍamma (u) and not before diacritic = \217\136
	["ي"]="y", --"ī" after kasra (i) and not before diacritic = \217\138
	["ى"]="ā", -- ʾalif maqṣūra = \217\137
	["آ"]="ʾā", -- ʾalif madda = \216\162
	["ٱ"]= "", -- hamzatu l-waṣl = \217\177
	["\217\176"] = "ā", -- ʾalif xanjariyya = dagger ʾalif (Koranic diacritic)
	-- short vowels, šádda and sukūn
	["\217\139"]="an", -- fatḥatan
	["\217\140"]="un", -- ḍammatan
	["\217\141"]="in", -- kasratan
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
	["«"]='"', -- quotation mark
	["»"]='"', -- quotation mark
	["٫"]=".", -- decimal point
	["٬"]=",", -- thousands separator
	["٪"]="%", -- percent sign
	["،"]=",", -- comma
	["؛"]=";" -- semicolon
}

local sun_letters = "تثدذرزسشصضطظلن"
-- For use in implementing sun-letter assimilation of ال (al-)
local ttsun1 = {}
local ttsun2 = {}
local ttsun3 = {}
for cp in gcodepoint(sun_letters) do
	local ch = u(cp)
	ttsun1[ch] = tt[ch]
	ttsun2["l-" .. ch] = tt[ch] .. "-" .. ch
	table.insert(ttsun3, tt[ch])
end
-- For use in implementing elision of al-
local sun_letters_tr = table.concat(ttsun3, "")

local consonants_needing_vowels = "بتثجحخدذرزسشصضطظعغفقكلمنهپچڤگڨڧأإؤئءةﷲ"
-- consonants on the right side; includes alif madda
local rconsonants = consonants_needing_vowels .. "ويآ"
-- consonants on the left side; does not include alif madda
local lconsonants = consonants_needing_vowels .. "وي"
-- Arabic semicolon, comma, question mark; taṭwīl; period, exclamation point,
-- single quote for bold/italic
local punctuation = "؟،؛" .. "ـ" .. ".!'"
local numbers = "١٢٣٤٥٦٧٨٩٠"

local before_diacritic_checking_subs = {
	------------ transformations prior to checking for diacritics --------------
	-- convert llh for allāh into ll+shadda+dagger-alif+h
	{"لله", "للّٰه"},
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
	-- tāʾ marbūṭa should always be preceded by fatḥa, alif, alif madda or
	-- dagger alif; infer fatḥa if not
	{"([^\217\142\216\167\216\162\217\176])\216\169", "%1\217\142\216\169"},
	-- similarly for alif between consonants, possibly marked with shadda
	-- (does not apply to initial alif, which is silent when not marked with
	-- hamza, or final alif, which might be pronounced as -an)
	{"([" .. lconsonants .. "]\217\145?)\216\167([" .. rconsonants .. "])",
		"%1\217\142\216\167%2"},
	-- infer fatḥa in case of non-fatḥa + alif/alif-maqṣūra + dagger alif
	{"([^\217\142])([\216\167\217\137]\217\176)", "%1\217\142%2"},
	-- infer kasra in case of hamza-under-alif not + kasra
	{"\216\165([^\217\144])", "\216\165\217\144%1"},
	-- ignore dagger alif placed over regular alif or alif maqṣūra
	{"([\216\167\217\137])\217\176", "%1"},

	----------- rest of these concern definite article alif-lām ----------
	-- NOTE: \217\132 = lām = ل
	-- in kasra/ḍamma + alif + lam, make alif into hamzatu l-waṣl, so we
	-- handle cases like بِالتَّوْفِيق (bi-t-tawfīq) correctly
	{"([\217\143\217\144])\216\167\217\132", "%1\217\177\217\132"},
	-- al + consonant + shadda (only recognize word-initially if regular alif): remove shadda
	{"^(\216\167\217\142?\217\132[" .. lconsonants .. "])\217\145", "%1"},
	{"%s(\216\167\217\142?\217\132[" .. lconsonants .. "])\217\145", " %1"},
	{"(\217\177\217\142?\217\132[" .. lconsonants .. "])\217\145", "%1"},
	-- handle l- hamzatu l-waṣl or word-initial al-
	{"^\216\167\217\142?\217\132", "al-"},
	{"%s\216\167\217\142?\217\132", " al-"},
	-- next one for bi-t-tawfīq
	{"([\217\143\217\144])\217\177\217\142?\217\132", "%1-l-"},
	-- next one for remaining hamzatu l-waṣl (at beginning of word)
	{"\217\177\217\142?\217\132", "l-"},
	-- special casing if the l in al- has a shadda on it (as in الَّذِي "that"),
	-- so we don't mistakenly double the dash
	{"l%-\217\145", "ll"},
	-- implement assimilation of sun letters
	{"l%-[" .. sun_letters .. "]", ttsun2},
}

-- Transliterate the word(s) in TEXT. LANG (the language) and SC (the script)
-- are ignored. OMIT_I3RAAB means leave out final short vowels (ʾiʿrāb).
-- GRAY_I3RAAB means render transliterate short vowels (ʾiʿrāb) in gray.
-- FORCE_TRANSLATE causes even non-vocalized text to be transliterated
-- (normally the function checks for non-vocalized text and returns nil,
-- since such text is ambiguous in transliteration).
function export.tr(text, lang, sc, omit_i3raab, gray_i3raab, force_translate)
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
	-- kasra + yaa not followed by a diacritic (or ū from prev step) is ī, otherwise y
	text = rsub(text, "\217\144\217\138([^\217\139\217\140\217\141\217\142\217\143\217\144\217\145\217\146\217\176ū])", "ī%1")
	text = rsub(text, "\217\144\217\138$", "ī")
	-- convert shadda to double letter.
	text = rsub(text, "(.)\217\145", "%1%1")
	if not omit_i3raab and gray_i3raab then -- show ʾiʿrāb grayed in transliteration
		-- decide whether to gray out the t in ﺓ. If word begins with al- or l-, yes.
		-- Otherwise, no if word ends in a/i/u, yes if ends in an/in/un.
		text = rsub(text, "^(a?l%-[^%s]+)\216\169([\217\139\217\140\217\141\217\142\217\143\217\144])",
			'%1<span style="color: #888888">t</span>%2')
		text = rsub(text, "(%sa?l%-[^%s]+)\216\169([\217\139\217\140\217\141\217\142\217\143\217\144])",
			'%1<span style="color: #888888">t</span>%2')
		text = rsub(text, "\216\169([\217\142\217\143\217\144])", "t%1")
		text = rsub(text, "\216\169([\217\139\217\140\217\141])",
			'<span style="color: #888888">t</span>%1')
		text = rsub(text, ".", {
			["\217\139"] = '<span style="color: #888888">an</span>',
			["\217\141"] = '<span style="color: #888888">in</span>',
			["\217\140"] = '<span style="color: #888888">un</span>'
		})
		text = rsub(text, "([\217\142\217\143\217\144])%s", {
			["\217\142"] = '<span style="color: #888888">a</span> ',
			["\217\144"] = '<span style="color: #888888">i</span> ',
			["\217\143"] = '<span style="color: #888888">u</span> '
		})
		text = rsub(text, "[\217\142\217\143\217\144]$", {
			["\217\142"] = '<span style="color: #888888">a</span>',
			["\217\144"] = '<span style="color: #888888">i</span>',
			["\217\143"] = '<span style="color: #888888">u</span>'
		})
		text = rsub(text, '</span><span style="color: #888888">', "")
	elseif omit_i3raab then -- omit ʾiʿrāb in transliteration
		text = rsub(text, "[\217\139\217\140\217\141]", "")
		text = rsub(text, "[\217\142\217\143\217\144]%s", " ")
		text = rsub(text, "[\217\142\217\143\217\144]$", "")
	end
	-- tāʾ marbūṭa should not be rendered by -t if word-final even when
	-- ʾiʿrāb (desinential inflection) is shown; instead, use (t) before
	-- whitespace, nothing when final; but render final -ﺍﺓ and -ﺁﺓ as -āh,
	-- consistent with Wehr's dictionary
	text = rsub(text, "([\216\167\216\162])\216\169$", "%1h")
	-- Ignore final tāʾ marbūṭa (it appears as "a" due to the preceding
	-- short vowel). Need to do this after graying or omitting word-final
	-- ʾiʿrāb.
	text = rsub(text, "\216\169$", "")
	if not omit_i3raab then -- show ʾiʿrāb in transliteration
		text = rsub(text, "\216\169%s", "(t) ")
	else
		-- When omitting ʾiʿrāb, show all non-absolutely-final instances of
		-- tāʾ marbūṭa as (t), with trailing ʾiʿrāb omitted.
		text = rsub(text, "\216\169", "(t)")
	end
	-- tatwīl should be rendered as - at beginning or end of word. It will
	-- be rendered as nothing in the middle of a word (FIXME, do we want
	-- this?)
	text = rsub(text, "^ـ", "-")
	text = rsub(text, "%sـ", " -")
	text = rsub(text, "ـ$", "-")
	text = rsub(text, "ـ%s", "- ")
	-- Now convert remaining Arabic chars according to table.
	text = rsub(text, ".", tt)
	text = rsub(text, "aā", "ā")
	-- Implement elision of al- after a final vowel. We do this
	-- conservatively, only handling elision of the definite article rather
	-- than elision in other cases of hamzat al-waṣl (e.g. form-I imperatives
	-- or form-VII and above verbal nouns) partly because elision in
	-- these cases isn't so common in MSA and partly to avoid excessive
	-- elision in case of words written with initial bare alif instead of
	-- properly with hamzated alif. Possibly we should reconsider.
	-- At the very least we currently don't handle elision of الَّذِي (allaḏi)
	-- correctly because we special-case it to appear without the hyphen;
	-- perhaps we should reconsider that.
	text = rsub(text, "([aiuāīū]) a([" .. sun_letters_tr .. "]%-)",
		"%1 %2")
	if gray_i3raab then
		text = rsub(text, "([aiuāīū]</span>) a([" .. sun_letters_tr .. "]%-)",
			"%1 %2")
	end
	-- Special-case the transliteration of allāh, without the hyphen
	text = rsub(text, "^(a?)l%-lāh", "%1llāh")
	text = rsub(text, "(%sa?)l%-lāh", "%1llāh")

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
	{"[" .. lconsonants .. "]$", ""},
	{"[" .. lconsonants .. "]%s", " "},
	-- remove consonants (or alif) when followed by diacritics
	-- must go after removing shadda
	-- do not remove the diacritics yet because we need them to handle
	-- long-vowel sequences of diacritic + pseudo-consonant
	{"[" .. lconsonants .. "\216\167]([\217\139\217\140\217\141\217\142\217\143\217\144\217\146\217\176])", "%1"},
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

-- Return true if transliteration TR is an irregular transliteration of
-- ARABIC. Return false if ARABIC can't be transliterated. For purposes of
-- establishing regularity, hyphens are ignored and word-final tāʾ marbūṭa
-- can be transliterated as "(t)", "" or "t".
function export.irregular_translit(arabic, tr)
	if not arabic or arabic == "" or not tr or tr == "" then
		return false
	end
	local regtr = export.tr(arabic)
	if not regtr or regtr == tr then
		return false
	end
	local arwords = rsplit(arabic, " ")
	local regwords = rsplit(regtr, " ")
	local words = rsplit(tr, " ")
	if #regwords ~= #words or #regwords ~= #arwords then
		return true
	end
	for i=1,#regwords do
		local regword = regwords[i]
		local word = words[i]
		local arword = arwords[i]
		-- Resolve final (t) in auto-translit to t, h or nothing
		if rfind(regword, "%(t%)$") then
			regword = rfind(word, "āh$") and rsub(regword, "%(t%)$", "h") or
				rfind(word, "t$") and rsub(regword, "%(t%)$", "t") or
				rsub(regword, "%(t%)$", "")
		end
		-- Resolve clitics + short a + alif-lām, which may get auto-translated
		-- to contain long ā, to short a if the manual translit has it; note
		-- that currently in cases with assimilated l, the auto-translit will
		-- fail, so we won't ever get here and don't have to worry about
		-- auto-translit l against manual-translit assimilated char.
		local clitic_chars = "^[وفكل]" -- separate line to avoid L2R display weirdness
		if rfind(arword, clitic_chars .. "\217\142?[\216\167\217\177]\217\132") and rfind(word, "^[wfkl]a%-") then
			regword = rsub(regword, "^([wfkl])ā", "%1a")
		end
		-- Ignore hyphens when comparing
		if rsub(regword, "%-", "") ~= rsub(word, "%-", "") then
			return true
		end
	end
	return false
end

return export

-- For Vim, so we get 4-space tabs
-- vim: set ts=4 sw=4 noet:
