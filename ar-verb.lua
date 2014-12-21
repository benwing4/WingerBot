--[[
 
Author: User:Benwing; early version by User:Atitarev, User:ZxxZxxZ
 
Todo:
 
1. Finish unimplemented conjugation types.
2. Fix hamza handling. The assumption is that radicals are specified as bare
   hamza i.e. hamza-on-theline. Hamza handling needs to happen in a few places:
   (a) there need to be special checks for final hamza in I-hollow verbs,
   because the active participle ends in '-in';
   (b) there needs to be a special check in form I sound, geminate and defective
   verbs for initial hamza because the imperative of such verbs has no hamza and
   instead previous vowel lengthened (as if there were a word-initial hamza);
   (c) there needs to be a similar check for initial hamza in form VIII verbs --
   here, conversion of hamza to long vowel is optional, and both forms occur in
   the past and imperative, with the form preserving hamza more common and
   should be listed first;
   (d) in postprocess_term() there needs to be a check for the initial
   sequence hamza-short vowel-hamza-sukuun, which is converted to
   hamza-long vowel; this should also handle initial hamza-over-alif and
   hamza-under-alif, or we should change the code that generates these;
   (e) in postprocess_term() there needs to be code to apply the proper "seats"
   to hamzas. This includes mapping bare hamza to hamza-over-alif,
   hamza-under-alif, alif-madda, hamza-over-waw, hamza-over-yaa, or
   hamza-on-the-line depending on surrounding vowels, according to the rules in
   Wikipedia article "Hamza".
3. Implement irregular verbs as special cases and recognize them, e.g.
   -- sa'ala yas'alu "ask" with alternative jussive/imperative yasal/sal;
   -- ra'ā yarā "see";
   -- 'arā yurī "show";
   -- ḥayya/ḥayiya yaḥyā "live";
   -- istaḥā/yastaḥī "be ashamed of";
   -- 'akala ya'kulu "eat" with imperative kul;
   -- 'axadha ya'xudhu "take" with imperative xudh;
   -- ittaxadha yattaxidhu "take";
   -- 'amara ya'muru "order" with imperative mur.
--]]

local m_utilities = require("Module:utilities")
local m_links = require("Module:links")
local ar_translit = require("Module:ar-translit")

local lang = require("Module:languages").getByCode("ar")

local rfind = mw.ustring.find
local rsub = mw.ustring.gsub
local rmatch = mw.ustring.match
local rsplit = mw.text.split
local usub = mw.ustring.sub

local export = {}

-- Within this module, conjugations are the functions that do the actual
-- conjugating by creating the forms of a basic verb.
-- They are defined further down.
local conjugations = {}
local dia = {
	s = "\217\146",
	a = "\217\142",
	i = "\217\144",
	u = "\217\143",
	an = "\217\139",
	in_ = "\217\141",
	un = "\217\140",
	sh = "\217\145",
	sh_a = "\217\142\217\145",
	sh_i = "\217\144\217\145",
	sh_u = "\217\143\217\145"
	}
local alif = "ا"
local amaq = "ى" -- alif maqṣūra
local yaa = "ي"
local waw = "و"
local hamza = "ء"
local hamza_on_alif = "أ"
local hamza_under_alif = "إ"
local amad = "آ" -- alif madda
local ma = "م" .. dia.a
local mu = "م" .. dia.u
local aa = dia.a .. alif
local aamaq = dia.a .. amaq
local ah = dia.a .. "ة"
local aah = aa .. "ة"
local ii = dia.i .. yaa
local uu = dia.u .. waw
local ay = dia.a .. yaa
local aw = dia.a .. waw

-- Utility functions

local function ine(x) -- If Not Empty
	if x == nil then
		return nil
	elseif rfind(x, '^".*"$') then
		local ret = rmatch(x, '^"(.*)"$')
		return ret
	elseif rfind(x, "^'.*'$") then
		local ret = rmatch(x, "^'(.*)'$")
		return ret
	elseif x == "" then
		return nil
	else
		return x
	end
end

local function contains(tab, item)
	for _, value in pairs(tab) do
		if value == item then
			return true
		end
	end
	return false
end

local function insert_if_not(tab, item)
	if not contains(tab, item) then
		table.insert(tab, item)
	end
end

local function links(word, alt, translit, showI3raab, tag, gloss)
	return m_links.full_link(word, alt, lang, nil, nil, nil, {["tr"] = (translit == true) and ar_translit.tr(alt or word, nil, nil, showI3raab) or translit, ["gloss"] = gloss})
end

local function tag_text(text, tag, class)
	return m_links.full_link(nil, text, lang, nil, nil, nil, nil, nil)
end

-- The main entry point.
-- This is the only function that can be invoked from a template.
function export.show(frame)
	local origargs = frame:getParent().args
	local args = {}
	-- Convert empty arguments to nil, and "" or '' arguments to empty
	for k, v in pairs(origargs) do
		args[k] = ine(v)
	end

	PAGENAME = mw.title.getCurrentTitle().text
	NAMESPACE = mw.title.getCurrentTitle().nsText
		
	--if this named parameter passed, make the verb intransitive, passive forms don't exist
	local intrans = args["intrans"]

	local conj_type = args[1] or frame.args[1] or
		error("Conjugation type has not been specified. Please pass parameter 1 to the template or module invocation.")

	-- derive form and weakness from conj type
	local form, weakness
	if rfind(conj_type, "%-") then
		local form_weakness = rsplit(conj_type, "%-")
		assert(#form_weakness == 2)
		form = form_weakness[1]
		weakness = form_weakness[2]
	else
		form = conj_type
		weakness = nil
	end
	
	-- get radicals, defaulting to ف-ع-ل (or ف-ل-ل for geminate, or with the
	-- appropriate radical replaced by waw for assimilated/hollow/defective)
	local rad1 = args[2] or weakness == "assimilated" and waw or "ف"
	local rad2 = args[3] or weakness == "hollow" and waw or
		weakness == "geminate" and "ل" or "ع"
	local rad3 = args[4] or weakness == "defective" and waw or
		weakness == "geminate" and rad2 or "ل"
	-- if weakness unspecified, derive from radicals
	if weakness == nil then
		if is_waw_yaa(rad3) and rad1 == waw and form == "I" then
			weakness = "assimilated+defective"
		elseif is_waw_yaa(rad3) then
			weakness = "defective"
		elseif rad2 == rad3 and (form == "I" or form == "III" or form == "IV" or
				form == "VI" or form == "VII" or form == "VIII" or form == "X") then
			weakness = "geminate"
		elseif is_waw_yaa(rad2) and (form == "I" or form == "IV" or
				form == "VII" or form == "VIII" or form == "X") then
			weakness = "hollow"
		elseif rad1 == waw and form == "I" then
			weakness = "assimilated"
		else
			weakness = "sound"
		end
		conj_type = form .. "-" .. weakness
	end

	-- use form and weakness to initialize categories, title
	local categories = {"Arabic form-" .. form .. " verbs",
		"Arabic " .. weakness .. " verbs"}
	local title = "form-" .. form .. " " .. weakness
		
	if not conjugations[conj_type] then
		error("Unknown conjugation type '" .. conj_type .. "'")
	end

	local forms = {}
	conjugations[conj_type](forms, args, rad1, rad2, rad3)

	-- transitive/intransitive
	if intrans then
		table.insert(categories, "Arabic intransitive verbs")
	else
		table.insert(categories, "Arabic transitive verbs")
	end
	
	return make_table(forms, title, intrans) .. m_utilities.format_categories(categories, lang)
	-- for testing forms only, comment out the line above and uncomment to see all forms with their names
	--return test_forms(forms, title, intrans)
end

-- Version of main entry point meant for calling from the debug console.
function export.show2(args, parargs)
	local frame = {args = args, getParent = function() return {args = parargs} end}
	return export.show(frame)
end

-- Conjugation functions

function check_aiu(vtype, vowel)
	if vowel ~= "a" and vowel ~= "i" and vowel ~= "u" then
		error(vtype .. " vowel '" .. vowel .. "' should be a, i, or u")
	end
end

function is_waw_yaa(rad)
	return rad == waw or rad == yaa
end

function check_waw_yaa(rad)
	if not is_waw_yaa(rad) then
		error("Expecting weak radical: '" .. rad .. "' should be " .. waw .. " or " .. yaa)
	end
end

function is_guttural(rad)
	return rad == hamza or rad == "ه" or rad == "ع" or rad == "ح"
end

function nonpast_from_past_vowel(vowel, rad2, rad3)
	return past_vowel == "i" and "a" or past_vowel == "u" and "u" or
		(is_guttural(rad2) or is_guttural(rad3)) and "a" or "u"
end

-- determine the imperative vowel based on non-past vowel
function imper_vowel_from_nonpast(nonpast_vowel)
	if nonpast_vowel == "a" or nonpast_vowel == "i" then
		return "i"
	elseif nonpast_vowel == "u" then
		return "u"
	else
		error("Non-past vowel '" .. nonpast_vowel .. "' isn't a, i, or u, should have been caught earlier")
	end
end

local function make_form_i_sound_assimilated_verb(forms, args, rad1, rad2, rad3,
		assimilated)
	-- need to provide two vowels - past and non-past
	local past_vowel = args[5] or "a"
	local nonpast_vowel = args[6] or nonpast_from_past_vowel(past_vowel)
	check_aiu("past", past_vowel)
	check_aiu("non-past", nonpast_vowel)

	-- Verbal nouns (maṣādir) for form I are unpredictable and have to be supplied
	insert_verbal_noun(forms, args, {})

	-- past and non-past stems, active and passive 
	local past_stem = rad1 .. dia.a .. rad2 .. dia[past_vowel] .. rad3
	local nonpast_stem = assimilated and rad2 .. dia[nonpast_vowel] .. rad3 or
		rad1 .. dia.s .. rad2 .. dia[nonpast_vowel] .. rad3
	local ps_past_stem = rad1 .. dia.u .. rad2 .. dia.i .. rad3
	local ps_nonpast_stem = rad1 .. dia.s .. rad2 .. dia.a .. rad3

	-- determine the imperative vowel based on non-past vowel
	local imper_vowel = imper_vowel_from_nonpast(nonpast_vowel)
	
	-- imperative stem
	local imper_stem = assimilated and rad2 .. dia[nonpast_vowel] .. rad3 or
		alif .. dia[imper_vowel] .. rad1 .. dia.s .. rad2 .. dia[nonpast_vowel] .. rad3

	-- make forms
	make_sound_verb(forms, past_stem, ps_past_stem, nonpast_stem,
		ps_nonpast_stem, imper_stem, "a")

	-- active participle
	insert_form(forms, "ap", rad1 .. aa .. rad2 .. dia.i .. rad3 .. dia.un)
	-- passive participle
	insert_form(forms, "pp", ma .. rad1 .. dia.s .. rad2 .. dia.u .. "و" .. rad3 .. dia.un)
end
	
conjugations["I-sound"] = function(forms, args, rad1, rad2, rad3)
	make_form_i_sound_assimilated_verb(forms, args, rad1, rad2, rad3, false)
end

conjugations["I-assimilated"] = function(forms, args, rad1, rad2, rad3)
	make_form_i_sound_assimilated_verb(forms, args, rad1, rad2, rad3, "assimilated")
end

local function make_form_i_defective_verb(forms, args, rad1, rad2, rad3,
		assimilated)
	-- need to provide two vowels - past and non-past
	local past_vowel = args[5] or "a"
	local nonpast_vowel = args[6] or past_vowel == "i" and "a" or
		past_vowel == "u" and "u" or rad3 == yaa and "i" or "u"
	check_aiu("past", past_vowel)
	check_aiu("non-past", nonpast_vowel)

	-- Verbal nouns (maṣādir) for form I are unpredictable and have to be supplied
	insert_verbal_noun(forms, args, {})

	-- past and non-past stems, active and passive 
	local past_stem = rad1 .. dia.a .. rad2
	local nonpast_stem = assimilated and rad2 or
		rad1 .. dia.s .. rad2
	local ps_past_stem = rad1 .. dia.u .. rad2
	local ps_nonpast_stem = rad1 .. dia.s .. rad2

	-- determine the imperative vowel based on non-past vowel
	local imper_vowel = imper_vowel_from_nonpast(nonpast_vowel)
	
	-- imperative stem
	local imper_stem = assimilated and rad2 or
		alif .. dia[imper_vowel] .. rad1 .. dia.s .. rad2

	-- make forms
	make_form_i_defective_verb_from_stems(forms, past_stem, ps_past_stem,
		nonpast_stem, ps_nonpast_stem, imper_stem, rad3, past_vowel,
		nonpast_vowel)

	-- active participle
	insert_form(forms, "ap", rad1 .. aa .. rad2 .. dia.in_)
	-- passive participle
	insert_form(forms, "pp", ma .. rad1 .. dia.s .. rad2 ..
		(rad3 == yaa and ii or uu) .. dia.sh .. dia.un)
end
	
conjugations["I-defective"] = function(forms, args, rad1, rad2, rad3)
	make_form_i_defective_verb(forms, args, rad1, rad2, rad3, false)
end

conjugations["I-assimilated+defective"] = function(forms, args, rad1, rad2, rad3)
	make_form_i_defective_verb(forms, args, rad1, rad2, rad3, "assimilated")
end

conjugations["I-hollow"] = function(forms, args, rad1, rad2, rad3)
	-- need to specify up to two vowels, past and non-past
	local past_vowel = args[5] or rad2 == yaa and "i" or "u"
	local nonpast_vowel = args[6] or past_vowel
	check_aiu("past", past_vowel)
	check_aiu("non-past", nonpast_vowel)
	check_waw_yaa(rad2)
	local lengthened_nonpast = nonpast_vowel == "u" and uu or
		nonpast_vowel == "i" and ii or aa

	-- Verbal nouns (maṣādir) for form I are unpredictable and have to be supplied
	insert_verbal_noun(forms, args, {})

	-- active past stems - vowel (v) and consonant (c)
	local past_v_stem = rad1 .. aa .. rad3
	local past_c_stem = rad1 .. dia[past_vowel] .. rad3

	-- active non-past stems - vowel (v) and consonant (c)
	local nonpast_v_stem = rad1 .. lengthened_nonpast .. rad3
	local nonpast_c_stem = rad1 .. dia[nonpast_vowel] .. rad3

	-- passive past stems - vowel (v) and consonant (c)
	-- 'ufīla, 'ufiltu
	local ps_past_v_stem = rad1 .. ii .. rad3
	local ps_past_c_stem = rad1 .. dia.i .. rad3

	-- passive non-past stems - vowel (v) and consonant (c)
	-- yufāla/yufalna
	-- stem is built differently but conjugation is identical to sound verbs
	local ps_nonpast_v_stem = rad1 .. aa .. rad3
	local ps_nonpast_c_stem = rad1 .. dia.a .. rad3

	-- imperative stem
	local imper_v_stem = nonpast_v_stem
	local imper_c_stem = nonpast_c_stem

	-- make forms
	make_hollow_geminate_verb(forms, past_v_stem, past_c_stem, ps_past_v_stem,
		ps_past_c_stem, nonpast_v_stem, nonpast_c_stem, ps_nonpast_v_stem,
		ps_nonpast_c_stem, imper_v_stem, imper_c_stem, "a", false)
	
	-- active participle
	insert_form(forms, "ap", rad1 .. aa .. hamza .. dia.i .. rad3 .. dia.un)
	-- passive participle
	insert_form(forms, "pp", ma .. rad1 .. (rad2 == yaa and ii or uu) .. rad3 .. dia.un)
end

conjugations["I-geminate"] = function(forms, args, rad1, rad2, rad3)
	-- need to specify two vowels, past and non-past
	local past_vowel = args[5] or "a"
	local nonpast_vowel = args[6] or nonpast_from_past_vowel(past_vowel)

	-- Verbal nouns (maṣādir) for form I are unpredictable and have to be supplied
	insert_verbal_noun(forms, args, {})

	-- active past stems - vowel (v) and consonant (c)
	local past_v_stem = rad1 .. dia.a .. rad2 .. dia.sh
	local past_c_stem = rad1 .. dia.a .. rad2 .. dia[past_vowel] .. rad2

	-- active non-past stems - vowel (v) and consonant (c)
	local nonpast_v_stem = rad1 .. dia[nonpast_vowel] .. rad2 .. dia.sh
	local nonpast_c_stem = rad1 .. dia.s .. rad2 .. dia[nonpast_vowel] .. rad2

	-- passive past stems - vowel (v) and consonant (c)
	-- dulla/dulilta
	local ps_past_v_stem = rad1 .. dia.u .. rad2 .. dia.sh
	local ps_past_c_stem = rad1 .. dia.u .. rad2 .. dia.i .. rad2

	-- passive non-past stems - vowel (v) and consonant (c)
	--yudallu/yudlalna
	-- stem is built differently but conjugation is identical to sound verbs
	local ps_nonpast_v_stem = rad1 .. dia.a .. rad2 .. dia.sh
	local ps_nonpast_c_stem = rad1 .. dia.s .. rad2 .. dia.a .. rad2

	-- determine the imperative vowel based on non-past vowel
	local imper_vowel = imper_vowel_from_nonpast(nonpast_vowel)

	-- imperative stem
	local imper_v_stem = rad1 .. dia[nonpast_vowel] .. rad2 .. dia.sh
	local imper_c_stem = alif .. dia[imper_vowel] .. rad1 .. dia.s .. rad2 .. dia[nonpast_vowel] .. rad2

	-- make forms
	make_hollow_geminate_verb(forms, past_v_stem, past_c_stem, ps_past_v_stem,
		ps_past_c_stem, nonpast_v_stem, nonpast_c_stem, ps_nonpast_v_stem,
		ps_nonpast_c_stem, imper_v_stem, imper_c_stem, "a", "geminate")
	
	-- active participle
	insert_form(forms, "ap", rad1 .. aa .. rad2 .. dia.sh .. dia.un)
	-- passive participle
	insert_form(forms, "pp", ma .. rad1 .. dia.s .. rad2 .. dia.u .. "و" .. rad2 .. dia.un)
end

function make_form_ii_sound_defective_verb(forms, args, rad1, rad2, rad3)
	local defective = rad3 == nil
	local vn = defective and
		"تَ" .. rad1 .. dia.s .. rad2 .. dia.i .. "ي" .. ah .. dia.un or
		"تَ" .. rad1 .. dia.s .. rad2 .. dia.i .. "ي" .. rad3 .. dia.un

	-- various stem bases
	local past_stem_base = rad1 .. dia.a .. rad2 .. dia.sh
	local nonpast_stem_base = rad1 .. dia.a .. rad2 .. dia.sh
	local ps_past_stem_base = rad1 .. dia.u .. rad2 .. dia.sh
	local imper_stem_base = nonpast_stem_base

	-- make forms
	make_augmented_sound_defective_verb(forms, args, rad3,
		past_stem_base, nonpast_stem_base, ps_past_stem_base, imper_stem_base,
		"u", vn, false)
end

conjugations["II-sound"] = function(forms, args, rad1, rad2, rad3)
	make_form_ii_sound_defective_verb(forms, args, rad1, rad2, rad3)
end

conjugations["II-defective"] = function(forms, args, rad1, rad2, rad3)
	make_form_ii_sound_defective_verb(forms, args, rad1, rad2)
end

function make_form_iii_sound_defective_verb(forms, args, rad1, rad2, rad3)
	local defective = rad3 == nil
	local vn = defective and
		{mu .. rad1 .. aa .. rad2 .. aah .. dia.un,
			rad1 .. dia.i .. rad2 .. aa .. hamza .. dia.un} or
		{mu .. rad1 .. aa .. rad2 .. dia.a .. rad3 .. ah .. dia.un,
			rad1 .. dia.i .. rad2 .. aa .. rad3 .. dia.un}

	-- various stem bases
	local past_stem_base = rad1 .. aa .. rad2
	local nonpast_stem_base = rad1 .. aa .. rad2
	local ps_past_stem_base = rad1 .. uu .. rad2
	local imper_stem_base = nonpast_stem_base

	-- make forms
	make_augmented_sound_defective_verb(forms, args, rad3,
		past_stem_base, nonpast_stem_base, ps_past_stem_base, imper_stem_base,
		"u", vn, false)
end

conjugations["III-sound"] = function(forms, args, rad1, rad2, rad3)
	make_form_iii_sound_defective_verb(forms, args, rad1, rad2, rad3)
end

conjugations["III-defective"] = function(forms, args, rad1, rad2, rad3)
	make_form_iii_sound_defective_verb(forms, args, rad1, rad2)
end

conjugations["III-geminate"] = function(forms, args, rad1, rad2, rad3)
	-- other form will be inserted when we add sound forms
	local vn = {mu .. rad1 .. aa .. rad2 .. dia.sh .. ah .. dia.un}

	-- various stem bases
	local past_stem_base = rad1 .. aa
	local nonpast_stem_base = rad1 .. aa
	local ps_past_stem_base = rad1 .. uu
	local imper_stem_base = nonpast_stem_base

	-- make forms
	make_augmented_geminate_verb(forms, args, rad2,
		past_stem_base, nonpast_stem_base, ps_past_stem_base, imper_stem_base,
		vn, "III")
	
	-- also have alternative sound (non-compressed) forms
	make_form_iii_sound_defective_verb(forms, args, rad1, rad2, rad2)
end

function make_form_iv_sound_defective_verb(forms, args, rad1, rad2, rad3)
	local defective = rad3 == nil
	local vn = defective and
		hamza_under_alif .. dia.i .. rad1 .. dia.s .. rad2 .. aa .. hamza .. dia.un or
		hamza_under_alif .. dia.i .. rad1 .. dia.s .. rad2 .. aa .. rad3 .. dia.un

	-- various stem bases
	local past_stem_base = hamza_on_alif .. dia.a .. rad1 .. dia.s .. rad2
	local nonpast_stem_base = rad1 .. dia.s .. rad2
	local ps_past_stem_base = hamza_on_alif .. dia.u .. rad1 .. dia.s .. rad2
	local imper_stem_base = past_stem_base

	-- make forms
	make_augmented_sound_defective_verb(forms, args, rad3,
		past_stem_base, nonpast_stem_base, ps_past_stem_base, imper_stem_base,
		"u", vn, false)
end

conjugations["IV-sound"] = function(forms, args, rad1, rad2, rad3)
	make_form_iv_sound_defective_verb(forms, args, rad1, rad2, rad3)
end

conjugations["IV-defective"] = function(forms, args, rad1, rad2, rad3)
	make_form_iv_sound_defective_verb(forms, args, rad1, rad2, yaa)
end

conjugations["IV-hollow"] = function(forms, args, rad1, rad2, rad3)
	local vn = hamza_under_alif .. dia.i .. rad1 .. aa .. rad3 .. ah .. dia.un

	-- various stem bases
	local past_stem_base = hamza_on_alif .. dia.a .. rad1
	local nonpast_stem_base = rad1
	local ps_past_stem_base = hamza_on_alif .. dia.u .. rad1
	local imper_stem_base = past_stem_base

	-- make forms
	make_augmented_hollow_verb(forms, args, rad3,
		past_stem_base, nonpast_stem_base, ps_past_stem_base, imper_stem_base,
		vn, "IV")
end

conjugations["IV-geminate"] = function(forms, args, rad1, rad2, rad3)
	local vn = hamza_under_alif .. dia.i .. rad1 .. dia.s .. rad2 .. aa .. rad2 .. dia.un

	-- various stem bases
	local past_stem_base = hamza_on_alif .. dia.a .. rad1
	local nonpast_stem_base = rad1
	local ps_past_stem_base = hamza_on_alif .. dia.u .. rad1
	local imper_stem_base = past_stem_base

	-- make forms
	make_augmented_geminate_verb(forms, args, rad2,
		past_stem_base, nonpast_stem_base, ps_past_stem_base, imper_stem_base,
		vn, "IV")
end

-- Inflection functions

-- Implementation of inflect_tense(). See that function. Also used directly
-- to add the imperative, which has only five forms.
function inflect_tense_1(forms, tense, prefixes, stems, endings, pnums)
	if prefixes == nil then
		error("For tense '" .. tense .. "', prefixes = nil")
	end
	if stems == nil then
		error("For tense '" .. tense .. "', stems = nil")
	end
	if endings == nil then
		error("For tense '" .. tense .. "', endings = nil")
	end
	if type(prefixes) == "table" and #pnums ~= #prefixes then
		error("For tense '" .. tense .. "', found " .. #prefixes .. " prefixes but expected " .. #pnums)
	end
	if type(stems) == "table" and #pnums ~= #stems then
		error("For tense '" .. tense .. "', found " .. #stems .. " stems but expected " .. #pnums)
	end
	if #pnums ~= #endings then
		error("For tense '" .. tense .. "', found " .. #endings .. " endings but expected " .. #pnums)
	end

	-- First, initialize any nil entries to sequences.
	for i, pnum in ipairs(pnums) do
		if forms[pnum .. "-" .. tense] == nil then
			forms[pnum .. "-" .. tense] = {}
		end
	end

	-- Now add entries
	for i = 1, #pnums do
		-- Extract endings for this person-number combo
		local ends = endings[i]
		if type(ends) == "string" then ends = {ends} end
		-- Extract prefix for this person-number combo
		local prefix = prefixes
		if type(prefix) == "table" then prefix = prefix[i] end
		-- Extract stem for this person-number combo
		local stem = stems
		if type(stem) == "table" then stem = stem[i] end
		-- Add entries for stem + endings
		for j, ending in ipairs(ends) do
			local form = prefix .. stem .. ending
			if ine(form) and form ~= "-"
					-- and (not data.impers or pnums[i] == "3sg")
					then
				table.insert(forms[pnums[i] .. "-" .. tense], form)
			end
		end
	end
end

-- Add to FORMS the inflections for the tense indicated by TENSE (the suffix
-- in the forms names, e.g. 'perf'), formed by combining the PREFIXES
-- (either a single string or a sequence of 13 strings), STEMS
-- (either a single string or a sequence of 13 strings) with the
-- ENDINGS (a sequence of 13 values, each of which is either a string
-- or a sequence of one or more possible endings). If existing
-- inflections already exist, they will be added to, not overridden.
function inflect_tense(forms, tense, prefixes, stems, endings)
	local pnums = {"1s", "2sm", "2sf", "3sm", "3sf",
				   "2d", "3dm", "3df",
				   "1p", "2pm", "2pf", "3pm", "3pf"}
	inflect_tense_1(forms, tense, prefixes, stems, endings, pnums)
end

-- Like inflect_tense() but for the imperative, which has only five forms
-- instead of 13.
function inflect_tense_impr(forms, stems, endings)
	local pnums = {"2sm", "2sf", "2d", "2pm", "2pf"}
	inflect_tense_1(forms, "impr", "", stems, endings, pnums)
end

-- Add VALUE (a string or array) to the end of any entries in FORMS[NAME],
-- initializing it to an empty array if needed.
function insert_form(forms, name, value)
	if forms[name] == nil then
		forms[name] = {}
	end
	if type(value) == "table" then
		for _, entry in ipairs(value) do
			table.insert(forms[name], entry)
		end
	else
		table.insert(forms[name], value)
	end
end

-- Insert verbal noun VN into FORMS["vn"], but allow it to be overridden by
-- ARGS["vn"]
function insert_verbal_noun(forms, args, vn)
	insert_form(forms, "vn", args["vn"] and rsplit(args["vn"], ",") or vn)
end

-----------------------
-- sets of past endings
-----------------------

local past_endings = {
	-- singular
	dia.s .. "تُ", dia.s .. "تَ", dia.s .. "تِ", dia.a, dia.a .. "تْ",
	--dual
	dia.s .. "تُمَا", aa, dia.a .. "تَا",
	-- plural
	dia.s .. "نَا", dia.s .. "تُمْ",
	-- two Arabic diacritics don't work together in Wikimedia
	--dia.s .. "تُنَّ",
	dia.s .. "تُن" .. dia.sh_a, uu .. alif, dia.s .. "نَ"
}

-- make endings for defective past in -aytu or -awtu
local function make_past_endings_ay_aw(ayaw, third_sg_masc)
	return {
	-- singular
	ayaw .. dia.s .. "تُ", ayaw ..  dia.s .. "تَ", ayaw .. dia.s .. "تِ",
	third_sg_masc, dia.a .. "تْ",
	--dual
	ayaw .. dia.s .. "تُمَا", ayaw .. aa, dia.a .. "تَا",
	-- plural
	ayaw .. dia.s .. "نَا", ayaw .. dia.s .. "تُمْ",
	-- two Arabic diacritics don't work together in Wikimedia
	--ayaw .. dia.s .. "تُنَّ",
	ayaw .. dia.s .. "تُن" .. dia.sh_a, aw .. dia.s .. alif, ayaw .. dia.s .. "نَ"
	}
end

-- past defective -aytu endings
local past_endings_ay = make_past_endings_ay_aw(ay, aamaq)
-- past defective -awtu endings
local past_endings_aw = make_past_endings_ay_aw(aw, aa)

-- make endings for defective past in -ītu or -ūtu
local function make_past_endings_ii_uu(iiuu)
	return {
	-- singular
	iiuu .. "تُ", iiuu .. "تَ", iiuu .. "تِ", iiuu .. dia.a, iiuu .. dia.a .. "تْ",
	--dual
	iiuu .. "تُمَا", iiuu .. aa, iiuu .. dia.a .. "تَا",
	-- plural
	iiuu .. "نَا", iiuu .. "تُمْ",
	-- two Arabic diacritics don't work together in Wikimedia
	--iiuu .. "تُنَّ",
	iiuu .. "تُن" .. dia.sh_a, uu .. alif, iiuu .. "نَ"
	}
end

-- past defective -ītu endings
local past_endings_ii = make_past_endings_ii_uu(ii)
-- past defective -ūtu endings
local past_endings_uu = make_past_endings_ii_uu(uu)

--------------------------------------
-- functions to inflect the past tense
--------------------------------------

--generate past verbs using specified vowel and consonant stems; works for
--sound, assimilated, hollow, and geminate verbs, active and passive
function past_2stem_conj(forms, tense, v_stem, c_stem)
	inflect_tense(forms, tense, "", {
		-- singular
		c_stem, c_stem, c_stem, v_stem, v_stem,
		--dual
		c_stem, v_stem, v_stem,
		-- plural
		c_stem, c_stem, c_stem, v_stem, c_stem
	}, past_endings)
end

--generate past verbs using single specified stem; works for sound and
--assimilated verbs, active and passive
function past_1stem_conj(forms, tense, stem)
	past_2stem_conj(forms, tense, stem, stem)
end

----------------------------------------
-- sets of non-past prefixes and endings
----------------------------------------

-- prefixes for non-past forms in -a-
local nonpast_prefixes_a = {
	-- singular
	"أَ", "تَ", "تَ", "يَ", "تَ",
	--dual
	"تَ", "يَ", "تَ",
	-- plural
	"نَ", "تَ", "تَ", "يَ", "يَ"
}

-- prefixes for non-past forms in -u- (passive, and active forms II - IV)
local nonpast_prefixes_u = {
	-- singular
	"أُ", "تُ", "تُ", "يُ", "تُ",
	--dual
	"تُ", "يُ", "تُ",
	-- plural
	"نُ", "تُ", "تُ", "يُ", "يُ"
}

-- make any set of non-past endings given the five distinct endings
local function make_nonpast_endings(null, fem, dual, pl, fempl)
	return {
	-- singular
	null, null, fem, null, null,
	-- dual
	dual, dual, dual,
	-- plural
	null, pl, fempl, pl, fempl
	}
end

-- endings for non-past indicative
local indic_endings = make_nonpast_endings(
	dia.u,
	dia.i .. "ينَ",
	dia.a .. "انِ",
	dia.u .. "ونَ",
	dia.s .. "نَ"
)

-- make the endings for non-past subjunctive/jussive
local function make_subj_juss_endings(dia_null) 
	return make_nonpast_endings(
	dia_null,
	dia.i .. "ي",
	dia.a .. "ا",
	dia.u .. "و",
	dia.s .. "نَ"
	)
end

-- endings for non-past subjunctive
local subj_endings = make_subj_juss_endings(dia.a)

-- endings for non-past jussive
local juss_endings = make_subj_juss_endings(dia.s)

-- endings for alternative geminate non-past jussive in -a; same as subjunctive
local juss_endings_alt_a = subj_endings

-- endings for alternative geminate non-past jussive in -i
local juss_endings_alt_i = make_subj_juss_endings(dia.i)

-- endings for defective non-past indicative in -ā
local indic_endings_aa = make_nonpast_endings(
	aamaq,
	ay .. dia.s .. "نَ",
	ay .. dia.a .. "انِ",
	aw .. dia.s .. "نَ",
	ay .. dia.s .. "نَ"
)

-- make endings for defective non-past indicative in -ī or -ū
local function make_indic_endings_ii_uu(iiuu)
	return make_nonpast_endings(
	iiuu,
	ii .. "نَ",
	iiuu .. dia.a .. "انِ",
	uu .. "نَ",
	iiuu .. "نَ"
	)
end

-- endings for defective non-past indicative in -ī
local indic_endings_ii = make_indic_endings_ii_uu(ii)

-- endings for defective non-past indicative in -ū
local indic_endings_uu = make_indic_endings_ii_uu(uu)

-- endings for defective non-past subjunctive in -ā
local subj_endings_aa = make_nonpast_endings(
	aamaq,
	ay .. dia.s,
	ay .. aa,
	aw .. dia.s .. alif,
	ay .. dia.s .. "نَ"
)

-- make endings for defective non-past subjunctive in -ī or -ū
local function make_subj_endings_ii_uu(iiuu)
	return make_nonpast_endings(
	iiuu .. dia.a,
	ii,
	iiuu .. aa,
	uu .. alif,
	iiuu .. "نَ"
	)
end

-- endings for defective non-past subjunctive in -ī
local subj_endings_ii = make_subj_endings_ii_uu(ii)

-- endings for defective non-past subjunctive in -ū
local subj_endings_uu = make_subj_endings_ii_uu(uu)

-- endings for defective non-past jussive in -ā
local juss_endings_aa = make_nonpast_endings(
	dia.a,
	ay .. dia.s,
	ay .. aa,
	aw .. dia.s .. alif,
	ay .. dia.s .. "نَ"
)

-- make endings for defective non-past jussive in -ī or -ū
local function make_juss_endings_ii_uu(iu, iiuu)
	return make_nonpast_endings(
	iu,
	ii,
	iiuu .. aa,
	uu .. alif,
	iiuu .. "نَ"
	)
end

-- endings for defective non-past jussive in -ī
local juss_endings_ii = make_juss_endings_ii_uu(dia.i, ii)

-- endings for defective non-past jussive in -ū
local juss_endings_uu = make_juss_endings_ii_uu(dia.u, uu)

---------------------------------------
-- functions to inflect non-past tenses
---------------------------------------

-- Generate non-past conjugation, with two stems, for vowel-initial and
-- consonant-initial endings, respectively. Useful for active and passive;
-- for all forms; for all weaknesses (sound, assimilated, hollow, defective
-- and geminate) and for all types of non-past (indicative, subjunctive,
-- jussive) except not for the imperative, and not for the jussive non-past
-- where 2 stems are needed (i.e. hollow, geminate), because the pattern of
-- vowel-initial and consonant-initial is different for jussive verbs
-- (for geminate jussives, there are three alternants, and two of them, with
-- terminations -a and -i, can use this function, whereas the one in a null
-- termination needs the special jussive version. Both stems may be the same,
-- e.g. for sound verbs.
--
-- PREFIXES will generally be either "a" (= 'nonpast_prefixes_a', for active
-- forms I and V - X) or "u" (= 'nonpast_prefixes_u', for active forms II - IV
-- and all passive forms). Otherwise, it should be either a single string
-- (often "") or an array (table) of 13 items. ENDINGS should similarly be an
-- array of 13 items. If ENDINGS is nil or omitted, infer the endings from
-- the tense. If JUSSIVE is true, or ENDINGS is nil and TENSE indicatives
-- jussive, use the jussive set of vowel/consonant stems (different from the
-- normal ones).
function nonpast_2stem_conj(forms, tense, prefixes, v_stem, c_stem, endings, jussive)
	if prefixes == "a" then prefixes = nonpast_prefixes_a
	elseif prefixes == "u" then prefixes = nonpast_prefixes_u
	end
	if endings == nil then
		if tense == "impf" or tense == "ps-impf" then
			endings = indic_endings
		elseif tense == "subj" or tense == "ps-subj" then
			endings = subj_endings
		elseif tense == "juss" or tense == "ps-juss" then
			jussive = true
			endings = juss_endings
		else
			error("Unrecognized tense '" .. tense .."'")
		end
	end
	if not jussive then
		inflect_tense(forms, tense, prefixes, {
			-- singular
			v_stem, v_stem, v_stem, v_stem, v_stem,
			--dual
			v_stem, v_stem, v_stem,
			-- plural
			v_stem, v_stem, c_stem, v_stem, c_stem
		}, endings)
	else
		inflect_tense(forms, tense, prefixes, {
			-- singular
			-- 'adlul, tadlul, tadullī, yadlul, tadlul
			c_stem, c_stem, v_stem, c_stem, c_stem,
			--dual
			-- tadullā, yadullā, tadullā
			v_stem, v_stem, v_stem,
			-- plural
			-- nadlul, tadullū, tadlulna, yadullū, yadlulna
			c_stem, v_stem, c_stem, v_stem, c_stem
		}, endings)
	end
end

function nonpast_1stem_conj(forms, tense, prefixes, stem, endings, jussive)
	nonpast_2stem_conj(forms, tense, prefixes, stem, stem, endings, jussive)
end

function nonpast_1stem_all_conj(forms, prefixes, stem)
	nonpast_1stem_conj(forms, "impf", prefixes, stem)
	nonpast_1stem_conj(forms, "subj", prefixes, stem)
	nonpast_1stem_conj(forms, "juss", prefixes, stem)
end

function pass_nonpast_1stem_all_conj(forms, stem)
	nonpast_1stem_conj(forms, "ps-impf", "u", stem)
	nonpast_1stem_conj(forms, "ps-subj", "u", stem)
	nonpast_1stem_conj(forms, "ps-juss", "u", stem)
end

function nonpast_2stem_all_conj(forms, prefixes, v_stem, c_stem)
	nonpast_2stem_conj(forms, "impf", prefixes, v_stem, c_stem)
	nonpast_2stem_conj(forms, "subj", prefixes, v_stem, c_stem)
	nonpast_2stem_conj(forms, "juss", prefixes, v_stem, c_stem)
end

function pass_nonpast_2stem_all_conj(forms, v_stem, c_stem)
	nonpast_2stem_conj(forms, "ps-impf", "u", v_stem, c_stem)
	nonpast_2stem_conj(forms, "ps-subj", "u", v_stem, c_stem)
	nonpast_2stem_conj(forms, "ps-juss", "u", v_stem, c_stem)
end

-- generate active/passive jussive geminative form I (also IV, VII, VIII, X)
function jussive_gem_conj(forms, tense, prefixes, v_stem, c_stem)
	-- alternative in -a
	nonpast_2stem_conj(forms, tense, prefixes, v_stem, c_stem, juss_endings_alt_a)
	-- alternative in -i
	nonpast_2stem_conj(forms, tense, prefixes, v_stem, c_stem, juss_endings_alt_i)
	-- alternative in -null; requires different combination of v_stem and
	-- c_stem since the null endings require the c_stem (e.g. "tadlul" here)
	-- whereas the corresponding endings above in -a or -i require the v_stem
	-- (e.g. "tadulla, tadulli" above)
	nonpast_2stem_conj(forms, tense, prefixes, v_stem, c_stem, juss_endings, "jussive")
end

-----------------------------
-- sets of imperative endings
-----------------------------

-- extract the second person jussive endings to get corresponding imperative
-- endings
local function imperative_endings_from_jussive(endings)
	return {endings[2], endings[3], endings[6], endings[10], endings[11]}
end

-- normal imperative endings
local impr_endings = imperative_endings_from_jussive(juss_endings)
-- alternative geminate imperative endings in -a
local impr_endings_alt_a = imperative_endings_from_jussive(juss_endings_alt_a)
-- alternative geminate imperative endings in -i
local impr_endings_alt_i = imperative_endings_from_jussive(juss_endings_alt_i)
-- defective imperative endings in -ā
local impr_endings_aa = imperative_endings_from_jussive(juss_endings_aa)
-- defective imperative endings in -ī
local impr_endings_ii = imperative_endings_from_jussive(juss_endings_ii)
-- defective imperative endings in -ū
local impr_endings_uu = imperative_endings_from_jussive(juss_endings_uu)

--------------------------------------
-- functions to inflect the imperative
--------------------------------------

-- generate imperative forms for sound or assimilated verbs
function make_1stem_imperative(forms, stem)
	inflect_tense_impr(forms, stem, impr_endings)
end

-- generate imperative forms for two-stem verbs (hollow or geminate)
function make_2stem_imperative(forms, v_stem, c_stem)
	inflect_tense_impr(forms,
		{c_stem, v_stem, v_stem, v_stem, c_stem}, impr_endings)
end

-- generate imperative forms for geminate verbs form I (also IV, VII, VIII, X)
function make_gem_imperative(forms, v_stem, c_stem)
	inflect_tense_impr(forms,
		{v_stem, v_stem, v_stem, v_stem, c_stem}, impr_endings_alt_a)
	inflect_tense_impr(forms,
		{v_stem, v_stem, v_stem, v_stem, c_stem}, impr_endings_alt_i)
	make_2stem_imperative(forms, v_stem, c_stem)
end

------------------------------------
-- functions to inflect entire verbs
------------------------------------

-- generate finite parts of a sound verb (also works for assimilated verbs)
-- from five stems plus the prefix letter in the active non-past ("a" or "u")
function make_sound_verb(forms, past_stem, ps_past_stem, nonpast_stem,
		ps_nonpast_stem, imper_stem, prefix_letter)
	past_1stem_conj(forms, "perf", past_stem)
	past_1stem_conj(forms, "ps-perf", ps_past_stem)
	nonpast_1stem_all_conj(forms, prefix_letter, nonpast_stem)
	pass_nonpast_1stem_all_conj(forms, ps_nonpast_stem)
	make_1stem_imperative(forms, imper_stem)
end

-- generate finite parts of an augmented (form II+) defective verb from five
-- stems plus the prefix letter in the active non-past ("a" or "u") and
-- a flag indicating if we are form V/VI
function make_defective_verb(forms, past_stem, ps_past_stem, nonpast_stem,
		ps_nonpast_stem, imper_stem, past_suffs, indic_suffs,
		subj_suffs, juss_suffs, impr_suffs, prefix_letter)
	inflect_tense(forms, "perf", "", past_stem, past_suffs)
	inflect_tense(forms, "ps-perf", "", ps_past_stem, past_endings_ii)
	nonpast_1stem_conj(forms, "impf", prefix_letter, nonpast_stem, indic_suffs)
	nonpast_1stem_conj(forms, "subj", prefix_letter, nonpast_stem, subj_suffs)
	nonpast_1stem_conj(forms, "juss", prefix_letter, nonpast_stem, juss_suffs)
	nonpast_1stem_conj(forms, "ps-impf", "u", ps_nonpast_stem, indic_endings_aa)
	nonpast_1stem_conj(forms, "ps-subj", "u", ps_nonpast_stem, subj_endings_aa)
	nonpast_1stem_conj(forms, "ps-juss", "u", ps_nonpast_stem, juss_endings_aa)
	inflect_tense_impr(forms, imper_stem, impr_suffs)
end

function make_form_i_defective_verb_from_stems(forms, past_stem, ps_past_stem,
		nonpast_stem, ps_nonpast_stem, imper_stem, rad3, past_vowel,
		nonpast_vowel)
	local past_suffs =
		rad3 == yaa and past_vowel == "a" and past_endings_ay or
		rad3 == waw and past_vowel == "a" and past_endings_aw or
		past_vowel == "i" and past_endings_ii or
		past_endings_uu
	local indic_suffs, subj_suffs, juss_suffs, impr_suffs
	if nonpast_vowel == "a" then
		indic_suffs = indic_endings_aa
		subj_suffs = subj_endings_aa
		juss_suffs = juss_endings_aa
		impr_suffs = impr_endings_aa
	elseif nonpast_vowel == "i" then
		indic_suffs = indic_endings_ii
		subj_suffs = subj_endings_ii
		juss_suffs = juss_endings_ii
		impr_suffs = impr_endings_ii
	else
		assert(nonpast_vowel == "u")
		indic_suffs = indic_endings_uu
		subj_suffs = subj_endings_uu
		juss_suffs = juss_endings_uu
		impr_suffs = impr_endings_uu
	end
	make_defective_verb(forms, past_stem, ps_past_stem, nonpast_stem,
		ps_nonpast_stem, imper_stem, past_suffs, indic_suffs,
		subj_suffs, juss_suffs, impr_suffs, "a")
end

-- generate finite parts of an augmented (form II+) defective verb from five
-- stems plus the prefix letter in the active non-past ("a" or "u") and
-- a flag indicating if we are form V/VI
function make_augmented_defective_verb(forms, past_stem, ps_past_stem,
		nonpast_stem, ps_nonpast_stem, imper_stem, prefix_letter, form56)
	make_defective_verb(forms, past_stem, ps_past_stem, nonpast_stem,
		ps_nonpast_stem, imper_stem, past_endings_ay,
		form56 and indic_endings_aa or indic_endings_ii,
		form56 and subj_endings_aa or subj_endings_ii,
		form56 and juss_endings_aa or juss_endings_ii,
		form56 and impr_endings_aa or impr_endings_ii,
		prefix_letter)
end

-- generate finite parts of an augmented (form II+) sound or defective verb,
-- given the following:
--
-- FORMS, ARGS = arguments from conjugation function
-- RAD3 = last radical; should be nil for defective verb
-- PAST_STEM_BASE = active past stem minus last syllable (= -al or -ā)
-- NONPAST_STEM_BASE = non-past stem minus last syllable (= -al/-il or -ā/-ī)
-- PS_PAST_STEM_BASE = passive past stem minus last syllable (= -il or -ī)
-- IMPER_STEM_BASE = imperative stem minus last syllable (= -al/-il or -ā/-ī)
-- PREFIX_VOWEL = "u" for forms II, III, IV, else "a"
-- VN = verbal noun
-- FORM56 = true if this is form V or VI
function make_augmented_sound_defective_verb(forms, args, rad3,
		past_stem_base, nonpast_stem_base, ps_past_stem_base, imper_stem_base,
		prefix_vowel, vn, form56)

	insert_verbal_noun(forms, args, vn)

	local defective = rad3 == nil
	local a_base_suffix = defective and "" or dia.a .. rad3
	local i_base_suffix = defective and "" or dia.i .. rad3
	
	-- past and non-past stems, active and passive 
	local past_stem = past_stem_base .. a_base_suffix
	local nonpast_stem = nonpast_stem_base ..
		(form56 and a_base_suffix or i_base_suffix)
	local ps_past_stem = ps_past_stem_base .. i_base_suffix
	local ps_nonpast_stem = nonpast_stem_base .. a_base_suffix
	-- imperative stem
	local imper_stem = imper_stem_base ..
		(form56 and a_base_suffix or i_base_suffix)

	-- make forms
	if defective then
		make_augmented_defective_verb(forms, past_stem, ps_past_stem, nonpast_stem,
			ps_nonpast_stem, imper_stem, prefix_vowel, form56)
	else	
		make_sound_verb(forms, past_stem, ps_past_stem, nonpast_stem,
			ps_nonpast_stem, imper_stem, prefix_vowel)
	end

	-- active and passive participle
	if defective then
		insert_form(forms, "ap", mu .. nonpast_stem .. dia.in_)
		insert_form(forms, "pp", mu .. ps_nonpast_stem .. dia.an)
	else
		insert_form(forms, "ap", mu .. nonpast_stem .. dia.un)
		insert_form(forms, "pp", mu .. ps_nonpast_stem .. dia.un)
	end
end

-- generate finite parts of a sound verb from ten stems (vowel and consonant
-- stems for each of past and non-past, active and passive, plus imperative)
-- plus the prefix letter in the active non-past ("a" or "u"), plus a flag
-- indicating if we are a geminate verb
function make_hollow_geminate_verb(forms, past_v_stem, past_c_stem, ps_past_v_stem,
	ps_past_c_stem, nonpast_v_stem, nonpast_c_stem, ps_nonpast_v_stem,
	ps_nonpast_c_stem, imper_v_stem, imper_c_stem, prefix_letter, geminate)
	past_2stem_conj(forms, "perf", past_v_stem, past_c_stem)
	past_2stem_conj(forms, "ps-perf", ps_past_v_stem, ps_past_c_stem)
	nonpast_2stem_conj(forms, "impf", prefix_letter, nonpast_v_stem, nonpast_c_stem)
	nonpast_2stem_conj(forms, "subj", prefix_letter, nonpast_v_stem, nonpast_c_stem)
	nonpast_2stem_conj(forms, "ps-impf", "u", ps_nonpast_v_stem, ps_nonpast_c_stem)
	nonpast_2stem_conj(forms, "ps-subj", "u", ps_nonpast_v_stem, ps_nonpast_c_stem)
	if geminate then
		jussive_gem_conj(forms, "juss", prefix_letter, nonpast_v_stem, nonpast_c_stem)
		jussive_gem_conj(forms, "ps-juss", "u", ps_nonpast_v_stem, ps_nonpast_c_stem)
		make_gem_imperative(forms, imper_v_stem, imper_c_stem)
	else
		nonpast_2stem_conj(forms, "juss", prefix_letter, nonpast_v_stem, nonpast_c_stem)
		nonpast_2stem_conj(forms, "ps-juss", "u", ps_nonpast_v_stem, ps_nonpast_c_stem)
		make_2stem_imperative(forms, imper_v_stem, imper_c_stem)
	end
end

-- generate finite parts of an augmented (form II+) hollow verb,
-- given the following:
--
-- FORMS, ARGS = arguments from conjugation function
-- RAD3 = last radical (after the hollowness)
-- PAST_STEM_BASE = invariable part of active past stem
-- NONPAST_STEM_BASE = invariable part of non-past stem
-- PS_PAST_STEM_BASE = invariable part of passive past stem
-- IMPER_STEM_BASE = invariable part of imperative stem
-- VN = verbal noun
-- FORM = the verb form ("IV", "VII", "VIII", "X")
function make_augmented_hollow_verb(forms, args, rad3,
	past_stem_base, nonpast_stem_base, ps_past_stem_base, imper_stem_base,
	vn, form)
	insert_verbal_noun(forms, args, vn)

	local form410 = form == "IV" or form == "X"
	local prefix_letter = form == "IV" and "u" or "a"

	local a_base_suffix_v, a_base_suffix_c
	local i_base_suffix_v, i_base_suffix_c
	
	a_base_suffix_v = aa .. rad3         -- 'af-āl-a, inf-āl-a
	a_base_suffix_c = dia.a .. rad3      -- 'af-al-tu, inf-al-tu
	i_base_suffix_v = ii .. rad3         -- 'uf-īl-a, unf-īl-a
	i_base_suffix_c = dia.i .. rad3      -- 'uf-il-tu, unf-il-tu
	
	-- past and non-past stems, active and passive, for vowel-initial and
	-- consonant-initial endings
	local past_v_stem = past_stem_base .. a_base_suffix_v
	local past_c_stem = past_stem_base .. a_base_suffix_c
	-- yu-f-īl-u, ya-staf-īl-u but yanf-āl-u, yaft-āl-u
	local nonpast_v_stem = nonpast_stem_base ..
		(form410 and i_base_suffix_v or a_base_suffix_v)
	local nonpast_c_stem = nonpast_stem_base ..
		(form410 and i_base_suffix_c or a_base_suffix_c)
	local ps_past_v_stem = ps_past_stem_base .. i_base_suffix_v
	local ps_past_c_stem = ps_past_stem_base .. i_base_suffix_c
	local ps_nonpast_v_stem = nonpast_stem_base .. a_base_suffix_v
	local ps_nonpast_c_stem = nonpast_stem_base .. a_base_suffix_c

	-- imperative stem
	local imper_v_stem = imper_stem_base ..
		(form410 and i_base_suffix_v or a_base_suffix_v)
	local imper_c_stem = imper_stem_base ..
		(form410 and i_base_suffix_c or a_base_suffix_c)

	-- make forms
	make_hollow_geminate_verb(forms, past_v_stem, past_c_stem, ps_past_v_stem,
		ps_past_c_stem, nonpast_v_stem, nonpast_c_stem, ps_nonpast_v_stem,
		ps_nonpast_c_stem, imper_v_stem, imper_c_stem, prefix_letter, false)

	-- active participle
	insert_form(forms, "ap", mu .. nonpast_v_stem .. dia.un)
	-- passive participle
	insert_form(forms, "pp", mu .. ps_nonpast_v_stem .. dia.un)
end

-- generate finite parts of an augmented (form II+) geminate verb,
-- given the following:
--
-- FORMS, ARGS = arguments from conjugation function
-- RAD3 = last radical (the one that gets geminated)
-- PAST_STEM_BASE = invariable part of active past stem
-- NONPAST_STEM_BASE = invariable part of non-past stem
-- PS_PAST_STEM_BASE = invariable part of passive past stem
-- IMPER_STEM_BASE = invariable part of imperative stem
-- VN = verbal noun
-- FORM = the verb form ("III", "IV", "VI", "VII", "VIII", "IX", "X")
function make_augmented_geminate_verb(forms, args, rad3,
	past_stem_base, nonpast_stem_base, ps_past_stem_base, imper_stem_base,
	vn, form)
	insert_verbal_noun(forms, args, vn)

	local prefix_letter = (form == "III" or form == "IV") and "u" or "a"

	local a_base_suffix_v, a_base_suffix_c
	local i_base_suffix_v, i_base_suffix_c
	
	if form == "IV" or form == "X" then
		a_base_suffix_v = dia.a .. rad3 .. dia.sh         -- 'af-all
		a_base_suffix_c = dia.s .. rad3 .. dia.a .. rad3  -- 'af-lal
		i_base_suffix_v = dia.i .. rad3 .. dia.sh         -- yuf-ill
		i_base_suffix_c = dia.s .. rad3 .. dia.i .. rad3  -- yuf-lil
	else
		a_base_suffix_v = rad3 .. dia.sh         -- fā-ll, infa-ll
		a_base_suffix_c = rad3 .. dia.a .. rad3  -- fā-lal, infa-lal
		i_base_suffix_v = rad3 .. dia.sh         -- yufā-ll, yanfa-ll
		i_base_suffix_c = rad3 .. dia.i .. rad3  -- yufā-lil, yanfa-lil
	end
	
	-- past and non-past stems, active and passive, for vowel-initial and
	-- consonant-initial endings
	local past_v_stem = past_stem_base .. a_base_suffix_v
	local past_c_stem = past_stem_base .. a_base_suffix_c
	local nonpast_v_stem = nonpast_stem_base ..
		(form == "VI" and a_base_suffix_v or i_base_suffix_v)
	local nonpast_c_stem = nonpast_stem_base ..
		(form == "VI" and a_base_suffix_c or i_base_suffix_c)
	local ps_past_v_stem = ps_past_stem_base .. i_base_suffix_v
	local ps_past_c_stem = ps_past_stem_base .. i_base_suffix_c
	local ps_nonpast_v_stem = nonpast_stem_base .. a_base_suffix_v
	local ps_nonpast_c_stem = nonpast_stem_base .. a_base_suffix_c

	-- imperative stem
	local imper_v_stem = imper_stem_base ..
		(form == "VI" and a_base_suffix_v or i_base_suffix_v)
	local imper_c_stem = imper_stem_base ..
		(form == "VI" and a_base_suffix_c or i_base_suffix_c)

	-- make forms
	make_hollow_geminate_verb(forms, past_v_stem, past_c_stem, ps_past_v_stem,
		ps_past_c_stem, nonpast_v_stem, nonpast_c_stem, ps_nonpast_v_stem,
		ps_nonpast_c_stem, imper_v_stem, imper_c_stem, prefix_letter,
		"geminate")

	-- FIXME!!!!!!! Implement non-compressed forms as alternatives for
	-- form III and VI; or maybe this should be implemented in the callers

	-- active participle
	insert_form(forms, "ap", mu .. nonpast_v_stem .. dia.un)
	-- passive participle
	insert_form(forms, "pp", mu .. ps_nonpast_v_stem .. dia.un)
end

----------------------------------------
-- functions to create inflection tables
----------------------------------------

-- Test function - shows all forms, see "show" function's comments
function test_forms(forms, title, intr)

	local text = "<br/>"
	for key, form in pairs(forms) do
		-- check for empty strings and nil's
		if form ~= "" and form then
			--text =  key .. [=[: {{Arab|]=] .. forms[key] .. [=[}}{{LR}}, ]=] 
			text = text .. key .. ": " .. forms[key] .. ", <br/>" 
		end
	end

   return text
end

-- post-process forms to eliminate phonological anomalies
function postprocess_term(term)
	-- iw, iy -> ī (assimilated verbs)
	term = rsub(term, dia.i .. waw .. dia.s, ii)
	term = rsub(term, dia.i .. yaa .. dia.s, ii)
	-- uw, uy -> ū (assimilated verbs)
	term = rsub(term, dia.u .. waw .. dia.s, uu)
	term = rsub(term, dia.u .. yaa .. dia.s, uu)
	return term
end

-- Make the table
function make_table(forms, title, intr)

	local passive = true
	
	local intrans_txt = " (transitive) "
	if intr then
		intrans_txt = " (intransitive) "
		passive = false
	end
	
	local title = "Conjugation of ''" .. forms["3sm-perf"][1] .. intrans_txt .. "''" .. (title and " (" .. title .. ")" or "")

	-- compute # of verbal nouns before we collapse them
	local num_vns = type(forms["vn"]) == "table" and #forms["vn"] or 1
	
	-- Format and and add transliterations to all forms
	for key, form in pairs(forms) do
		-- check for empty strings and nil's
		if form ~= "" and form then
			-- automatic transliteration
			if type(form) == "string" then
				form = {form}
			end
			-- omit duplicates
			local form_nondup = {}
			for _, entry in ipairs(form) do
				entry = postprocess_term(entry)
				insert_if_not(form_nondup, entry)
			end
			-- convert each individual entry into Arabic and Latin span
			local arabic_spans = {}
			local latin_spans = {}
			for _, entry in ipairs(form_nondup) do
				table.insert(arabic_spans, "<span lang=\"ar\" class=\"Arab\">[[" .. entry .. "|" .. entry .. "]]</span>")
				table.insert(latin_spans, "<span style=\"color: #888\">" .. ar_translit.tr(entry, nil, nil, "showI3raab") .. "</span>")
			end
			-- concatenate spans
			forms[key] = table.concat(arabic_spans, ", ") .. "<br/>" ..
				table.concat(latin_spans, ", ")
		else
			forms[key] = "&mdash;"
		end
	end

	local text = [=[<div class="NavFrame" style="width:100%">
<div class="NavHead" style="height:2.5em">]=] .. title  .. [=[</div>
<div class="NavContent">

{| border="1" color="#cdcdcd" style="border-collapse:collapse; line-height:2.5em; border:1px solid #555555; background:#fdfdfd; width:100%; text-align:center" class="inflection-table"
|-
! colspan="6" style="background:#dedede" | verbal noun]=] .. (num_vns > 1 and "s" or "") .. "<br />" .. tag_text(num_vns > 1 and "المصادر" or "المصدر") .. [=[

| colspan="7" | ]=] .. links(forms["vn"]) .. [=[

|-
! colspan="6" style="background:#dedede" | active participle<br />]=] .. tag_text("اسم الفاعل") .. [=[

| colspan="7" | ]=] .. links(forms["ap"])

	if passive then
		text = text .. [=[

|-
! colspan="6" style="background:#dedede" | passive participle<br />]=] .. tag_text("اسم المفعول") .. [=[

| colspan="7" | ]=] .. links(forms["pp"])
	end

	text = text .. [=[

|-
! colspan="12" style="background:#bcbcbc" | active voice<br />]=] .. tag_text("الفعل المعلوم") .. [=[

|-
! colspan="2" style="background:#cdcdcd" | 
! colspan="3" style="background:#cdcdcd" | singular<br />]=] .. tag_text("المفرد") .. [=[

! rowspan="12" style="background:#cdcdcd;width:.5em" | 
! colspan="2" style="background:#cdcdcd" | dual<br />]=] .. tag_text("المثنى") .. [=[

! rowspan="12" style="background:#cdcdcd;width:.5em" | 
! colspan="3" style="background:#cdcdcd" | plural<br />]=] .. tag_text("الجمع") .. [=[

|-
! colspan="2" style="background:#cdcdcd" | 
! style="background:#cdcdcd" | 1<sup>st</sup> person<br />]=] .. tag_text("المتكلم") .. [=[

! style="background:#cdcdcd" | 2<sup>nd</sup> person<br />]=] .. tag_text("المخاطب") .. [=[

! style="background:#cdcdcd" | 3<sup>rd</sup> person<br />]=] .. tag_text("الغائب") .. [=[

! style="background:#cdcdcd" | 2<sup>nd</sup> person<br />]=] .. tag_text("المخاطب") .. [=[

! style="background:#cdcdcd" | 3<sup>rd</sup> person<br />]=] .. tag_text("الغائب") .. [=[

! style="background:#cdcdcd" | 1<sup>st</sup> person<br />]=] .. tag_text("المتكلم") .. [=[

! style="background:#cdcdcd" | 2<sup>nd</sup> person<br />]=] .. tag_text("المخاطب") .. [=[

! style="background:#cdcdcd" | 3<sup>rd</sup> person<br />]=] .. tag_text("الغائب") .. [=[

|-
! rowspan="2" style="background:#cdcdcd" | perfect indicative<br />]=] .. tag_text("الماضي") .. [=[

! style="background:#dedede" | ''m''
| rowspan="2" | ]=] .. links(forms["1s-perf"]) .. [=[

| ]=] .. links(forms["2sm-perf"]) .. [=[

| ]=] .. links(forms["3sm-perf"]) .. [=[

| rowspan="2" | ]=] .. links(forms["2d-perf"]) .. [=[

| ]=] .. links(forms["3dm-perf"]) .. [=[

| rowspan="2" | ]=] .. links(forms["1p-perf"]) .. [=[

| ]=] .. links(forms["2pm-perf"]) .. [=[

| ]=] .. links(forms["3pm-perf"]) .. [=[

|-
! style="background:#dedede" | ''f''
| ]=] .. links(forms["2sf-perf"]) .. [=[

| ]=] .. links(forms["3sf-perf"]) .. [=[

| ]=] .. links(forms["3df-perf"]) .. [=[

| ]=] .. links(forms["2pf-perf"]) .. [=[

| ]=] .. links(forms["3pf-perf"]) .. [=[

|-
! rowspan="2" style="background:#cdcdcd" | imperfect indicative<br />]=] .. tag_text("المضارع") .. [=[

! style="background:#dedede" | ''m''
| rowspan="2" | ]=] .. links(forms["1s-impf"]) .. [=[

| ]=] .. links(forms["2sm-impf"]) .. [=[

| ]=] .. links(forms["3sm-impf"]) .. [=[

| rowspan="2" | ]=] .. links(forms["2d-impf"]) .. [=[

| ]=] .. links(forms["3dm-impf"]) .. [=[

| rowspan="2" | ]=] .. links(forms["1p-impf"]) .. [=[

| ]=] .. links(forms["2pm-impf"]) .. [=[

| ]=] .. links(forms["3pm-impf"]) .. [=[

|-
! style="background:#dedede" | ''f''
| ]=] .. links(forms["2sf-impf"]) .. [=[

| ]=] .. links(forms["3sf-impf"]) .. [=[

| ]=] .. links(forms["3df-impf"]) .. [=[

| ]=] .. links(forms["2pf-impf"]) .. [=[

| ]=] .. links(forms["3pf-impf"]) .. [=[

|-
! rowspan="2" style="background:#cdcdcd" | subjunctive<br />]=] .. tag_text("المضارع المنصوب") .. [=[

! style="background:#dedede" | ''m''
| rowspan="2" | ]=] .. links(forms["1s-subj"]) .. [=[

| ]=] .. links(forms["2sm-subj"]) .. [=[

| ]=] .. links(forms["3sm-subj"]) .. [=[

| rowspan="2" | ]=] .. links(forms["2d-subj"]) .. [=[

| ]=] .. links(forms["3dm-subj"]) .. [=[

| rowspan="2" | ]=] .. links(forms["1p-subj"]) .. [=[

| ]=] .. links(forms["2pm-subj"]) .. [=[

| ]=] .. links(forms["3pm-subj"]) .. [=[

|-
! style="background:#dedede" | ''f''
| ]=] .. links(forms["2sf-subj"]) .. [=[

| ]=] .. links(forms["3sf-subj"]) .. [=[

| ]=] .. links(forms["3df-subj"]) .. [=[

| ]=] .. links(forms["2pf-subj"]) .. [=[

| ]=] .. links(forms["3pf-subj"]) .. [=[

|-
! rowspan="2" style="background:#cdcdcd" | jussive<br />]=] .. tag_text("المضارع المجزوم") .. [=[

! style="background:#dedede" | ''m''
| rowspan="2" | ]=] .. links(forms["1s-juss"]) .. [=[

| ]=] .. links(forms["2sm-juss"]) .. [=[

| ]=] .. links(forms["3sm-juss"]) .. [=[

| rowspan="2" | ]=] .. links(forms["2d-juss"]) .. [=[

| ]=] .. links(forms["3dm-juss"]) .. [=[

| rowspan="2" | ]=] .. links(forms["1p-juss"]) .. [=[

| ]=] .. links(forms["2pm-juss"]) .. [=[

| ]=] .. links(forms["3pm-juss"]) .. [=[

|-
! style="background:#dedede" | ''f''

| ]=] .. links(forms["2sf-juss"]) .. [=[

| ]=] .. links(forms["3sf-juss"]) .. [=[

| ]=] .. links(forms["3df-juss"]) .. [=[

| ]=] .. links(forms["2pf-juss"]) .. [=[

| ]=] .. links(forms["3pf-juss"]) .. [=[

|-
! rowspan="2" style="background:#cdcdcd" | imperative<br />]=] .. tag_text("الأمر") .. [=[

! style="background:#dedede" | ''m''
| rowspan="2" | 
| ]=] .. links(forms["2sm-impr"]) .. [=[

| rowspan="2" | 

| rowspan="2" | ]=] .. links(forms["2d-impr"]) .. [=[

| rowspan="2" | 

| rowspan="2" | 
| ]=] .. links(forms["2pm-impr"]) .. [=[

| rowspan="2" | 

|-
! style="background:#dedede" | ''f''
| ]=] .. links(forms["2sf-impr"]) .. [=[

| ]=] .. links(forms["2pf-impr"])

	if passive then
		text = text .. [=[

|-
! colspan="12" style="background:#bcbcbc" | passive voice<br />]=] .. tag_text("الفعل المجهول") .. [=[

|-
| colspan="2" style="background:#cdcdcd" | 
! colspan="3" style="background:#cdcdcd" | singular<br />]=] .. tag_text("المفرد") .. [=[

| rowspan="10" style="background:#cdcdcd;width:.5em" | 
! colspan="2" style="background:#cdcdcd" | dual<br />]=] .. tag_text("المثنى") .. [=[

| rowspan="10" style="background:#cdcdcd;width:.5em" | 
! colspan="3" style="background:#cdcdcd" | plural<br />]=] .. tag_text("الجمع") .. [=[

|-
| colspan="2" style="background:#cdcdcd" | 
! style="background:#cdcdcd" | 1<sup>st</sup> person<br />]=] .. tag_text("المتكلم") .. [=[

! style="background:#cdcdcd" | 2<sup>nd</sup> person<br />]=] .. tag_text("المخاطب") .. [=[

! style="background:#cdcdcd" | 3<sup>rd</sup> person<br />]=] .. tag_text("الغائب") .. [=[

! style="background:#cdcdcd" | 2<sup>nd</sup> person<br />]=] .. tag_text("المخاطب") .. [=[

! style="background:#cdcdcd" | 3<sup>rd</sup> person<br />]=] .. tag_text("الغائب") .. [=[

! style="background:#cdcdcd" | 1<sup>st</sup> person<br />]=] .. tag_text("المتكلم") .. [=[

! style="background:#cdcdcd" | 2<sup>nd</sup> person<br />]=] .. tag_text("المخاطب") .. [=[

! style="background:#cdcdcd" | 3<sup>rd</sup> person<br />]=] .. tag_text("الغائب") .. [=[

|-
! rowspan="2" style="background:#cdcdcd" | perfect indicative<br />]=] .. tag_text("الماضي") .. [=[

! style="background:#dedede" | ''m''
| rowspan="2" | ]=] .. links(forms["1s-ps-perf"]) .. [=[

| ]=] .. links(forms["2sm-ps-perf"]) .. [=[

| ]=] .. links(forms["3sm-ps-perf"]) .. [=[

| rowspan="2" | ]=] .. links(forms["2d-ps-perf"]) .. [=[

| ]=] .. links(forms["3dm-ps-perf"]) .. [=[

| rowspan="2" | ]=] .. links(forms["1p-ps-perf"]) .. [=[

| ]=] .. links(forms["2pm-ps-perf"]) .. [=[

| ]=] .. links(forms["3pm-ps-perf"]) .. [=[

|-
! style="background:#dedede" | ''f''
| ]=] .. links(forms["2sf-ps-perf"]) .. [=[

| ]=] .. links(forms["3sf-ps-perf"]) .. [=[

| ]=] .. links(forms["3df-ps-perf"]) .. [=[

| ]=] .. links(forms["2pf-ps-perf"]) .. [=[

| ]=] .. links(forms["3pf-ps-perf"]) .. [=[

|-
! rowspan="2" style="background:#cdcdcd" | imperfect indicative<br />]=] .. tag_text("المضارع") .. [=[

! style="background:#dedede" | ''m''
| rowspan="2" | ]=] .. links(forms["1s-ps-impf"]) .. [=[

| ]=] .. links(forms["2sm-ps-impf"]) .. [=[

| ]=] .. links(forms["3sm-ps-impf"]) .. [=[

| rowspan="2" | ]=] .. links(forms["2d-ps-impf"]) .. [=[

| ]=] .. links(forms["3dm-ps-impf"]) .. [=[

| rowspan="2" | ]=] .. links(forms["1p-ps-impf"]) .. [=[

| ]=] .. links(forms["2pm-ps-impf"]) .. [=[

| ]=] .. links(forms["3pm-ps-impf"]) .. [=[

|-
! style="background:#dedede" | ''f''
| ]=] .. links(forms["2sf-ps-impf"]) .. [=[

| ]=] .. links(forms["3sf-ps-impf"]) .. [=[

| ]=] .. links(forms["3df-ps-impf"]) .. [=[

| ]=] .. links(forms["2pf-ps-impf"]) .. [=[

| ]=] .. links(forms["3pf-ps-impf"]) .. [=[

|-
! rowspan="2" style="background:#cdcdcd" | subjunctive<br />]=] .. tag_text("المضارع المنصوب") .. [=[

! style="background:#dedede" | ''m''
| rowspan="2" | ]=] .. links(forms["1s-ps-subj"]) .. [=[

| ]=] .. links(forms["2sm-ps-subj"]) .. [=[

| ]=] .. links(forms["3sm-ps-subj"]) .. [=[

| rowspan="2" | ]=] .. links(forms["2d-ps-subj"]) .. [=[

| ]=] .. links(forms["3dm-ps-subj"]) .. [=[

| rowspan="2" | ]=] .. links(forms["1p-ps-subj"]) .. [=[

| ]=] .. links(forms["2pm-ps-subj"]) .. [=[

| ]=] .. links(forms["3pm-ps-subj"]) .. [=[

|-
! style="background:#dedede" | ''f''
| ]=] .. links(forms["2sf-ps-subj"]) .. [=[

| ]=] .. links(forms["3sf-ps-subj"]) .. [=[

| ]=] .. links(forms["3df-ps-subj"]) .. [=[

| ]=] .. links(forms["2pf-ps-subj"]) .. [=[

| ]=] .. links(forms["3pf-ps-subj"]) .. [=[

|-
! rowspan="2" style="background:#cdcdcd" | jussive<br />]=] .. tag_text("المضارع المجزوم") .. [=[

! style="background:#dedede" | ''m''
| rowspan="2" | ]=]
	text = text .. links(forms["1s-ps-juss"]) .. [=[

| ]=] .. links(forms["2sm-ps-juss"]) .. [=[

| ]=] .. links(forms["3sm-ps-juss"]) .. [=[

| rowspan="2" | ]=] .. links(forms["2d-ps-juss"]) .. [=[

| ]=] .. links(forms["3dm-ps-juss"]) .. [=[

| rowspan="2" | ]=] .. links(forms["1p-ps-juss"]) .. [=[

| ]=] .. links(forms["2pm-ps-juss"]) .. [=[

| ]=] .. links(forms["3pm-ps-juss"]) .. [=[

|-
! style="background:#dedede" | ''f''
| ]=] .. links(forms["2sf-ps-juss"]) .. [=[

| ]=] .. links(forms["3sf-ps-juss"]) .. [=[

| ]=] .. links(forms["3df-ps-juss"]) .. [=[

| ]=] .. links(forms["2pf-ps-juss"]) .. [=[

| ]=] .. links(forms["3pf-ps-juss"])
	end

	text = text .. [=[

|}
</div>
</div>]=]

   return text
end
 
return export

-- For Vim, so we get 4-space tabs
-- vim: set ts=4 sw=4 noet:
