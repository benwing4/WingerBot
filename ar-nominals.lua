-- Author: Benwing, based on early version by CodeCat.

--[[
FIXME: Nouns/adjectives to create to exemplify complex declensions:
-- riḍan (رِضًا or رِضًى)
--]]

local m_utilities = require("Module:utilities")
local m_links = require("Module:links")
local ar_utilities = require("Module:ar-utilities")

local lang = require("Module:languages").getByCode("ar")
local u = mw.ustring.char
local rfind = mw.ustring.find
local rsubn = mw.ustring.gsub
local rmatch = mw.ustring.match
local rsplit = mw.text.split

local BOGUS_CHAR = u(0xFFFD)

-- hamza variants
local HAMZA            = u(0x0621) -- hamza on the line (stand-alone hamza) = ء
local HAMZA_ON_ALIF  = u(0x0623)
local HAMZA_ON_WAW   = u(0x0624)
local HAMZA_UNDER_ALIF = u(0x0625)
local HAMZA_ON_YA    = u(0x0626)
local HAMZA_ANY = "[" .. HAMZA .. HAMZA_ON_ALIF .. HAMZA_UNDER_ALIF .. HAMZA_ON_WAW .. HAMZA_ON_YA .. "]"
local HAMZA_PH = u(0xFFF0) -- hamza placeholder

-- various letters
local ALIF   = u(0x0627) -- ʾalif = ا
local AMAQ   = u(0x0649) -- ʾalif maqṣūra = ى
local AMAD   = u(0x0622) -- ʾalif madda = آ
local TAM    = u(0x0629) -- tāʾ marbūṭa = ة
local T      = u(0x062A) -- tāʾ = ت
local HYPHEN = u(0x0640)
local N      = u(0x0646) -- nūn = ن
local W      = u(0x0648) -- wāw = و
local Y      = u(0x064A) -- yā = ي

-- diacritics
local A  = u(0x064E) -- fatḥa
local AN = u(0x064B) -- fatḥatān (fatḥa tanwīn)
local U  = u(0x064F) -- ḍamma
local UN = u(0x064C) -- ḍammatān (ḍamma tanwīn)
local I  = u(0x0650) -- kasra
local IN = u(0x064D) -- kasratān (kasra tanwīn)
local SK = u(0x0652) -- sukūn = no vowel
local SH = u(0x0651) -- šadda = gemination of consonants
local DAGGER_ALIF = u(0x0670)
local DIACRITIC_ANY_BUT_SH = "[" .. A .. I .. U .. AN .. IN .. UN .. SK .. DAGGER_ALIF .. "]"

-- common combinations
local NA    = N .. A
local NI    = N .. I
local AH    = A .. TAM
local AT    = A .. T
local AA    = A .. ALIF
local AAMAQ = A .. AMAQ
local AAH   = AA .. TAM
local AAT   = AA .. T
local II    = I .. Y
local IIN   = II .. N
local IINA  = II .. NA
local IY	= II
local UU    = U .. W
local UUN   = UU .. N
local UUNA  = UU .. NA
local AY    = A .. Y
local AW    = A .. W
local AYSK  = AY .. SK
local AWSK  = AW .. SK
local AAN   = AA .. N
local AANI  = AA .. NI
local AYN   = AYSK .. N
local AYNI  = AYSK .. NI
local AWN   = AWSK .. N
local AWNA  = AWSK .. NA
local AYNA  = AYSK .. NA
local AYAAT = AY .. AAT
local UNU = "[" .. UN .. U .. "]"

-- optional diacritics/letters
local AOPT = A .. "?"
local AOPTA = A .. "?" .. ALIF
local IOPT = I .. "?"
local UOPT = U .. "?"
local UNOPT = UN .. "?"
local UNUOPT = UNU .. "?"
local SKOPT = SK .. "?"

local consonants_needing_vowels = "بتثجحخدذرزسشصضطظعغفقكلمنهپچڤگڨڧأإؤئءةﷲ"
-- consonants on the right side; includes alif madda
local rconsonants = consonants_needing_vowels .. "ويآ"
-- consonants on the left side; does not include alif madda
local lconsonants = consonants_needing_vowels .. "وي"
local CONS = "[" .. lconsonants .. "]"
local CONSPAR = "([" .. lconsonants .. "])"

local LRM = u(0x200E) --left-to-right mark

-- First syllable or so of elative/color-defect adjective
local ELCD_START = "^" .. HAMZA_ON_ALIF .. AOPT .. CONSPAR
local export = {}

-- Functions that do the actual inflecting by creating the forms of a basic term.
local inflections = {}

function ine(x) -- If Not Empty
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

-- Compare two items, recursively comparing arrays.
-- FIXME, doesn't work for tables that aren't arrays.
function equals(x, y)
	if type(x) == "table" and type(y) == "table" then
		if #x ~= #y then
			return false
		end
		for key, value in ipairs(x) do
			if not equals(value, y[key]) then
				return false
			end
		end
		return true
	end
	return x == y
end

-- true if array contains item
function contains(tab, item)
	for _, value in pairs(tab) do
		if equals(value, item) then
			return true
		end
	end
	return false
end

-- append to array if element not already present
function insert_if_not(tab, item)
	if not contains(tab, item) then
		table.insert(tab, item)
	end
end

-- version of rsubn() that discards all but the first return value
function rsub(term, foo, bar)
	local retval = rsubn(term, foo, bar)
	return retval
end

function make_link(arabic)
	--return m_links.full_link(nil, arabic, lang, nil, "term", nil, {tr = "-"}, false)
	return m_links.full_link(nil, arabic, lang, nil, "term", nil, {}, false)
end

function init_data()
	-- forms contains a table of forms for each inflectional category,
	-- e.g. "nom_sg_ind" for nouns or "nom_m_sg_ind" for adjectives. The value
	-- of an entry is an array of alternatives (e.g. different plurals), where
	-- each alternative is either a string of the form "ARABIC" or
	-- "ARABIC/TRANSLIT", or an array of such strings (this is used for
	-- alternative spellings involving different hamza seats,
	-- e.g. مُبْتَدَؤُون or مُبْتَدَأُون). Alternative hamza spellings are separated
	-- in display by an "inner separator" (/), while alternatives on
	-- the level of different plurals are separated by an "outer seprator" (;).
	return {forms = {}, title = nil, categories = {},
		allgenders = {"m", "f"},
		allstates = {"ind", "def", "con"},
		allnumbers = {"sg", "du", "pl"},
		engnumbers = {sg="singular", du="dual", pl="plural",
					  coll="collective", sing="singulative", pauc="paucal"},
		allcases = {"nom", "acc", "gen", "inf"}}
end

function init(origargs)
	local args = {}
	-- Convert empty arguments to nil, and "" or '' arguments to empty
	for k, v in pairs(origargs) do
		args[k] = ine(v)
	end

	local data = init_data()
	return args, origargs, data
end

-- Can manually specify which states are to appear, and whether to omit the
-- definite article in the definite state.
function parse_state_spec(data, args)
	if args["omitarticle"] then
		data.omitarticle = true
	end
	if args["state"] then
		data.states = rsplit(args["state"], ",")
		for _, state in ipairs(data.states) do
			if not contains(data.allstates, state) then
				error("For state=, value '" .. state .. "' should be one of " ..
					table.concat(data.allstates, ", "))
			end
		end
		return true
	else
		data.states = data.allstates
		return false
	end
end

-- Can manually specify which numbers are to appear.
function parse_number_spec(data, args)
	if args["number"] then
		data.numbers = rsplit(args["number"], ",")
		for _, num in ipairs(data.numbers) do
			if not contains(data.allnumbers, num) then
				error("For number=, value '" .. num .. "' should be one of " ..
					table.concat(data.allnumbers, ", "))
			end
		end
		return true
	else
		data.numbers = data.allnumbers
		return false
	end
end

-- For stem STEM, convert to stem-and-type format and insert stem and type
-- into RESULTS, checking to make sure it's not already there. SGS is the
-- list of singular items to base derived forms off of (masculine or feminine
-- as appropriate), an array of length-two arrays of {COMBINED_STEM, TYPE} as
-- returned by stem_and_type(); ISFEM is true if this is feminine gender;
-- NUM is 'sg', 'du' or 'pl'.
function insert_stems(stem, results, sgs, isfem, num)
	if stem == "-" then
		return
	end
	for _, sg in ipairs(sgs) do
		local combined_stem, ty = export.stem_and_type(stem,
			sg[1], sg[2], isfem, num)
		insert_if_not(results, {combined_stem, ty})
	end
end

-- Handle manually specified overrides of individual forms. Separate
-- outer-level alternants with ; or , or the Arabic equivalents; separate
-- inner-level alternants with | (we can't use / because it's already in
-- use separating Arabic from translit).
--
-- Also determine lemma and allow it to be overridden.
-- Also allow POS (part of speech) to be overridden.
function handle_lemma_and_overrides(data, args)
	local function handle_override(arg)
		if args[arg] then
			local ovval = {}
			local alts1 = rsplit(args[arg], "[;,؛،]")
			for _, alt1 in ipairs(alts1) do
				local alts2 = rsplit(alt1, "|")
				table.insert(ovval, alts2)
			end
			data.forms[arg] = ovval
		end
	end

	for _, numgen in ipairs(data.allnumgens) do
		for _, state in ipairs(data.allstates) do
			for _, case in ipairs(data.allcases) do
				local arg = case .. "_" .. numgen .. "_" .. state
				handle_override(arg)
				if args[arg] then
					insert_cat(data, numgen,
						"Arabic NOUNs with irregular SINGULAR",
						"SINGULAR of irregular NOUN")
				end
			end
		end
	end

	function get_lemma()
		for _, numgen in ipairs(data.numgens()) do
			for _, state in ipairs(data.states) do
				local arg = "lemma_" .. numgen .. "_" .. state
				if data.forms[arg] and #data.forms[arg] > 0 then
					return data.forms[arg]
				end
			end
		end
		return nil
	end

	data.forms["lemma"] = get_lemma()
	handle_override("lemma")

	if args["pos"] then
		data.pos = args["pos"]
	end
end

-- Find the stems associated with a particular gender/number combination.
-- ARGS is the set of all arguments; ARG is the name of the argument
-- (e.g. "f" for "f", "f2", ... for feminine singular); SGS is the list
-- of singular stems to base derived forms off of (masculine or feminine
-- as appropriate), an array of length-two arrays of {COMBINED_STEM, TYPE}
-- as returned by stem_and_type(); DEFAULT is the default stem to use
-- (typically either 'f', 'd' or 'p', or nil for no default); ISFEM is
-- true if this is feminine gender; NUM is 'sg', 'du' or 'pl'.
function do_gender_number(args, arg, sgs, default, isfem, num)
	local results = {}
	local function handle_stem(stem)
		insert_stems(stem, results, sgs, isfem, num)
	end

	if not args[arg] then
		if not default then
			return results
		end
		handle_stem(default)
		return results
	end
	-- For explicitly specified arguments, make sure there's at least one
	-- base to generate off of; otherwise specifying e.g. 'sing=- pauc=فُلَان'
	-- won't override paucal.
	if #sgs == 0 then
		sgs = {{"", ""}}
	end
	handle_stem(args[arg])
	local i = 2
	while args[arg .. i] do
		handle_stem(args[arg .. i])
		i = i + 1
	end
	return results
end

-- Generate inflections for the given combined stem and type, for NUMGEN
-- (number or number-gender combination, of the sort that forms part of
-- keys in DATA).
function call_inflection(combined_stem, ty, data, numgen)
	if ty == "-" then
		return
	end

	if not inflections[ty] then
		error("Unknown inflection type '" .. ty .. "'")
	end
	
	local ar, tr = split_arabic_tr(combined_stem)
	inflections[ty](ar, tr, data, numgen)
end

local function call_inflections(stemtypes, data, numgen)
	if contains(data.numbers, rsub(numgen, "^.*_", "")) then
		for _, stemtype in ipairs(stemtypes) do
			call_inflection(stemtype[1], stemtype[2], data, numgen)
		end
	end
end

function get_heads(args, headtype)
	if not args[1] and mw.title.getCurrentTitle().nsText == "Template" then
		return {{"{{{1}}}", "tri"}}, true
	end

	local heads
	if not args[1] then error("Parameter 1 (" .. headtype .. " stem) may not be empty.") end
	if args[1] == "-" then
		heads = {{"", "-"}}
	else
		heads = {}
		insert_stems(args[1], heads, {{args[1], ""}}, false, 'sg')
	end
	local i = 2
	while args['head' .. i] do
		local arg = args['head' .. i]
		insert_stems(arg, heads, {{arg, ""}}, false, 'sg')
		i = i + 1
	end
	return heads, false
end

-- The main entry point for noun tables.
function export.show_noun(frame)
	local args, origargs, data = init(frame:getParent().args)
	data.pos = "noun"
	data.numgens = function() return data.numbers end
	data.allnumgens = data.allnumbers

	local sgs, is_template = get_heads(args, 'singular')
	local pls = is_template and {{"{{{pl}}}", "tri"}} or
		do_gender_number(args, "pl", sgs, nil, false, "pl")

	parse_state_spec(data, args)

	-- Can manually specify which numbers are to appear, and exactly those
	-- numbers will appear. Otherwise, if any plurals given, duals and plurals
	-- appear; else, only singular (on the assumption that the word is a proper
	-- noun or abstract noun that exists only in the singular); however,
	-- singular won't appear if "-" given for singular, and similarly for dual.
	if not parse_number_spec(data, args) then
		data.numbers = {}
		local sgarg1 = args[1]
		local duarg1 = args["du"]
		if sgarg1 ~= "-" then
			table.insert(data.numbers, "sg")
		end
		if #pls > 0 then
			-- Dual appears if either: explicit dual stem (not -) is given, or
			-- default dual is used and explicit singular stem (not -) is given.
			if (duarg1 and duarg1 ~= "-") or (not duarg1 and sgarg1 ~= "-") then
				table.insert(data.numbers, "du")
			end
			table.insert(data.numbers, "pl")
		end
	end

	-- Generate the singular, dual and plural forms
	local dus = (contains(data.numbers, "du") and
		do_gender_number(args, "d", sgs, "d", false, "du") or {})
	call_inflections(sgs, data, "sg")
	call_inflections(dus, data, "du")
	call_inflections(pls, data, "pl")
	
	handle_lemma_and_overrides(data, args)

	-- Make the table
	return make_noun_table(data) .. m_utilities.format_categories(data.categories, lang)
end

-- The main entry point for collective noun tables.
function export.show_coll_noun(frame)
	local args, origargs, data = init(frame:getParent().args)
	data.pos = "collective noun"
	data.allnumbers = {"coll", "sing", "du", "pauc", "pl"}
	data.numgens = function() return data.numbers end
	data.allnumgens = data.allnumbers

	local colls, is_template = get_heads(args, 'collective')
	local pls = is_template and {{"{{{pl}}}", "tri"}} or
		do_gender_number(args, "pl", colls, nil, false, "pl")

	parse_state_spec(data, args)

	-- If collective noun is already feminine in form, don't try to
	-- form a feminine singulative
	local already_feminine = false
	for _, stemtype in ipairs(colls) do
		if rfind(stemtype[1], TAM .. UNUOPT .. "$") then
			already_feminine = true
		end
	end

	local sings = do_gender_number(args, "sing", colls,
		not already_feminine and "f" or nil, true, "sg")
	local dus = do_gender_number(args, "d", sings, "d", true, "du")
	local paucs = do_gender_number(args, "pauc", sings, "sfp", true, "pl")

	-- Can manually specify which numbers are to appear, and exactly those
	-- numbers will appear. Otherwise, if any plurals given, plurals appear,
	-- and if singulative given, dual and paucal appear.
	if not parse_number_spec(data, args) then
		data.numbers = {}
		if args[1] ~= "-" then
			table.insert(data.numbers, "coll")
		end
		if #sings > 0 then
			table.insert(data.numbers, "sing")
		end
		if #dus > 0 then
			table.insert(data.numbers, "du")
		end
		if #paucs > 0 then
			table.insert(data.numbers, "pauc")
		end
		if #pls > 0 then
			table.insert(data.numbers, "pl")
		end
	end

	-- Generate the collective, singulative, dual, paucal and plural forms
	call_inflections(colls, data, "coll")
	call_inflections(sings, data, "sing")
	call_inflections(dus, data, "du")
	call_inflections(paucs, data, "pauc")
	call_inflections(pls, data, "pl")
	
	handle_lemma_and_overrides(data, args)

	-- Make the table
	return make_coll_noun_table(data) .. m_utilities.format_categories(data.categories, lang)
end

-- The main entry point for adjective tables.
function export.show_adj(frame)
	local args, origargs, data = init(frame:getParent().args)
	data.pos = "adjective"
	data.numgens = function()
		local numgens = {}
		for _, gender in ipairs(data.allgenders) do
			for _, number in ipairs(data.numbers) do
				table.insert(numgens, gender .. "_" .. number)
			end
		end
		return numgens
	end
	data.allnumgens = {}
	for _, gender in ipairs(data.allgenders) do
		for _, number in ipairs(data.allnumbers) do
			table.insert(data.allnumgens, gender .. "_" .. number)
		end
	end

	local msgs = get_heads(args, 'masculine singular')
	local fsgs = do_gender_number(args, "f", msgs, "f", true, "sg")

	parse_state_spec(data, args)
	parse_number_spec(data, args)

	local mdus = (contains(data.numbers, "du") and
		do_gender_number(args, "d", msgs, "d", false, "du") or {})
	local fdus = (contains(data.numbers, "du") and
		do_gender_number(args, "fd", fsgs, "d", true, "du") or {})
	local mpls = (contains(data.numbers, "pl") and
		do_gender_number(args, "pl", msgs, "p", false, "pl") or {})
	local fpls = (contains(data.numbers, "pl") and
		do_gender_number(args, "fpl", fsgs, "p", true, "pl") or {})

	-- Generate the singular, dual and plural forms
	call_inflections(msgs, data, "m_sg")
	call_inflections(fsgs, data, "f_sg")
	call_inflections(mdus, data, "m_du")
	call_inflections(fdus, data, "f_du")
	call_inflections(mpls, data, "m_pl")
	call_inflections(fpls, data, "f_pl")
	
	handle_lemma_and_overrides(data, args)

	-- Make the table
	return make_adj_table(data) .. m_utilities.format_categories(data.categories, lang)
end


-- Inflection functions

function do_translit(term)
	return lang:transliterate(term) or BOGUS_CHAR
end

function split_arabic_tr(term)
	if not rfind(term, "/") then
		return term, do_translit(term)
	else
		splitvals = rsplit(term, "/")
		if #splitvals ~= 2 then
			error("Must have at most one slash in a combined Arabic/translit expr: '" .. term .. "'")
		end
		return splitvals[1], splitvals[2]
	end
end

function reorder_shadda(word)
	-- shadda+short-vowel (including tanwīn vowels, i.e. -an -in -un) gets
	-- replaced with short-vowel+shadda during NFC normalisation, which
	-- MediaWiki does for all Unicode strings; however, it makes the
	-- detection process inconvenient, so undo it.
	word = rsub(word, "(" .. DIACRITIC_ANY_BUT_SH .. ")" .. SH, SH .. "%1")
	return word
end

function combine_with_ending(ar, tr, ending)
	local endingar, endingtr = split_arabic_tr(ending)
	allar = hamza_seat(ar .. endingar)
	tr = tr .. endingtr
	allartr = {}
	for _, arval in ipairs(allar) do
		table.insert(allartr, arval .. "/" .. tr)
	end
	return allartr
end

function add_inflection(data, key, stem, tr, ending)
	if data.forms[key] == nil then
		data.forms[key] = {}
	end
	if type(ending) ~= "table" then
		ending = {ending}
	end
	for _, endingval in ipairs(ending) do
		insert_if_not(data.forms[key], combine_with_ending(stem, tr, endingval))
	end
end

-- Form inflections from combination of STEM, with transliteration TR,
-- and ENDINGS (and definite article where necessary) and store in DATA,
-- for the number or gender/number determined by NUMGEN ("sg", "du", "pl", or
-- "m_sg", "f_pl", etc. for adjectives). ENDINGS is an array of 12 values,
-- each of which is a string or array of alternatives. The order of ENDINGS
-- is indefinite nom, acc, gen; definite nom, acc, gen; construct-state
-- nom, acc, gen; informal indefinite, definite, construct; lemma indefinite,
-- definite, construct. (Normally the lemma is based off of the indefinite,
-- but if the inflection has been restricted to particular states, it comes
-- from one of those states, in the order indefinite, definite, construct.)
function add_inflections(stem, tr, data, numgen, endings)
	assert(#endings == 15)
	-- Return a list of combined of ar/tr forms, with the ending tacked on.
	-- There may be more than one form because of alternative hamza seats that
	-- may be supplied, e.g. مُبْتَدَؤُون or مُبْتَدَأُون (mubtadaʾūn "(grammatical) subjects").
	local defstem, deftr
	if data.omitarticle then
		defstem = stem
		deftr = tr
	else
		defstem = "ال" .. stem
		-- apply sun-letter assimilation
		deftr = rsub("al-" .. tr, "^al%-([sšṣtṯṭdḏḍzžẓnrḷ])", "a%1-%1")
	end

	add_inflection(data, "nom_" .. numgen .. "_ind", stem, tr, endings[1])
	add_inflection(data, "acc_" .. numgen .. "_ind", stem, tr, endings[2])
	add_inflection(data, "gen_" .. numgen .. "_ind", stem, tr, endings[3])
	add_inflection(data, "nom_" .. numgen .. "_def", defstem, deftr, endings[4])
	add_inflection(data, "acc_" .. numgen .. "_def", defstem, deftr, endings[5])
	add_inflection(data, "gen_" .. numgen .. "_def", defstem, deftr, endings[6])
	add_inflection(data, "nom_" .. numgen .. "_con", stem, tr, endings[7])
	add_inflection(data, "acc_" .. numgen .. "_con", stem, tr, endings[8])
	add_inflection(data, "gen_" .. numgen .. "_con", stem, tr, endings[9])
	add_inflection(data, "inf_" .. numgen .. "_ind", stem, tr, endings[10])
	add_inflection(data, "inf_" .. numgen .. "_def", defstem, deftr, endings[11])
	add_inflection(data, "inf_" .. numgen .. "_con", stem, tr, endings[12])
	add_inflection(data, "lemma_" .. numgen .. "_ind", stem, tr, endings[13])
	add_inflection(data, "lemma_" .. numgen .. "_def", defstem, deftr, endings[14])
	add_inflection(data, "lemma_" .. numgen .. "_con", stem, tr, endings[15])
end	

-- Insert into a category and a type variable (e.g. m_sg_type) for the
-- declension type of a particular declension (e.g. masculine singular for
-- adjectives). CATVALUE is the category and ENGVALUE is the English
-- description of the declension type. In these values, NOUN is replaced
-- with either "noun" or "adjective", SINGULAR is replaced with the English
-- equivalent of the number in NUMGEN (e.g. "singular", "dual" or "plural")
-- while BROKSING is the same but uses "broken plural" in place of "plural".
function insert_cat(data, numgen, catvalue, engvalue)
	local singpl = data.engnumbers[rsub(numgen, "^.*_", "")]
	assert(singpl ~= nil)
	local broksingpl = rsub(singpl, "plural", "broken plural")
	local adjnoun = data.pos
	if rfind(broksingpl, "broken plural") and (rfind(catvalue, "BROKSING") or
			rfind(engvalue, "BROKSING")) then
		table.insert(data.categories, "Arabic " .. adjnoun .. "s with broken plural")
	end
	catvalue = rsub(catvalue, "NOUN", adjnoun)
	catvalue = rsub(catvalue, "SINGULAR", singpl)
	catvalue = rsub(catvalue, "BROKSING", broksingpl)
	engvalue = rsub(engvalue, "NOUN", adjnoun)
	engvalue = rsub(engvalue, "SINGULAR", singpl)
	engvalue = rsub(engvalue, "BROKSING", broksingpl)
	if catvalue ~= "" then
		insert_if_not(data.categories, catvalue)
	end
	if engvalue ~= "" then
		local key = numgen .. "_type"
		if data.forms[key] == nil then
			data.forms[key] = {}
		end
		insert_if_not(data.forms[key], engvalue)
	end
end

-- Handle triptote and diptote inflections
function triptote_diptote(stem, tr, data, numgen, is_dip, lc)
	-- Remove any case ending
	if rfind(stem, "[" .. UN .. U .. "]$") then
		stem = rsub(stem, "[" .. UN .. U .. "]$", "")
		tr = rsub(tr, "un?$", "")
	end

	if rfind(stem, TAM .. "$") then
		if rfind(tr, "h$") then
			tr = rsub(tr, "h$", "t")
		elseif not rfind(tr, "t$") then
			tr = tr .. "t"
		end
	end

	add_inflections(canon_hamza(stem), tr, data, numgen,
		{is_dip and U or UN,
		 is_dip and A or AN .. ((rfind(stem, "[" .. HAMZA_ON_ALIF .. TAM .. "]$")
			or rfind(stem, "[" .. AMAD .. ALIF .. "]" .. HAMZA .. "$")
			) and "" or ALIF),
		 is_dip and A or IN,
		 U, A, I,
		 lc and UU or U,
		 lc and AA or A,
		 lc and II or I,
		 {}, {}, {}, -- omit informal inflections
		 {}, {}, {}, -- omit lemma inflections
		})

	-- add category and informal and lemma inflections
	local tote = lc and "long construct" or is_dip and "diptote" or "triptote"
	local singpl_tote = "BROKSING " .. tote
	local cat_prefix = "Arabic NOUNs with " .. tote .. " BROKSING"
	if rfind(stem, "[" .. AMAD .. ALIF .. "]" .. TAM .. "$") then
		add_inflections(stem, rsub(tr, "t$", ""), data, numgen,
			{{}, {}, {},
			 {}, {}, {},
			 {}, {}, {},
			 "/t", "/t", "/t", -- informal pron. is -āt
			 "/h", "/h", "/t", -- lemma uses -āh
			})
		insert_cat(data, numgen, cat_prefix .. " in -āh",
			singpl_tote .. " in " .. make_link(HYPHEN .. AAH))
	elseif rfind(stem, TAM .. "$") then
		add_inflections(stem, rsub(tr, "t$", ""), data, numgen,
			{{}, {}, {},
			 {}, {}, {},
			 {}, {}, {},
			 "", "", "/t",
			 "", "", "/t",
			})
		insert_cat(data, numgen, cat_prefix .. " in -a",
			singpl_tote .. " in " .. make_link(HYPHEN .. AH))
	elseif lc then
		add_inflections(stem, tr, data, numgen,
			{{}, {}, {},
			 {}, {}, {},
			 {}, {}, {},
			 "", "", UU,
			 "", "", UU,
			})
		insert_cat(data, numgen, cat_prefix,
			singpl_tote)
	else
		-- also special-case the nisba ending, which has an informal
		-- pronunciation.
		if rfind(stem, IY .. SH .. "$") then
			local infstem = rsub(stem, SH .. "$", "")
			local inftr = rsub(tr, "iyy$", "ī")
			-- add informal and lemma inflections separately
			add_inflections(infstem, inftr, data, numgen,
				{{}, {}, {},
				 {}, {}, {},
				 {}, {}, {},
				 "", "", "",
				 {}, {}, {},
				})
			add_inflections(stem, tr, data, numgen,
				{{}, {}, {},
				 {}, {}, {},
				 {}, {}, {},
				 {}, {}, {},
				 "", "", "",
				})
		else
			add_inflections(stem, tr, data, numgen,
				{{}, {}, {},
				 {}, {}, {},
				 {}, {}, {},
				 "", "", "",
				 "", "", "",
				})
		end
		insert_cat(data, numgen, "Arabic NOUNs with basic " .. tote .. " BROKSING",
			"basic " .. singpl_tote)
	end
end

-- Regular triptote
inflections["tri"] = function(stem, tr, data, numgen)
	triptote_diptote(stem, tr, data, numgen, false)
end

-- Regular diptote
inflections["di"] = function(stem, tr, data, numgen)
	triptote_diptote(stem, tr, data, numgen, true)
end

-- Elative and color/defect adjective: usually same as diptote,
-- might be invariable
function elative_color_defect(stem, tr, data, numgen)
	if rfind(stem, "[" .. ALIF .. AMAQ .. "]$") then
		invariable(stem, tr, data, numgen)
	else
		triptote_diptote(stem, tr, data, numgen, true)
	end
end

-- Elative: usually same as diptote, might be invariable
inflections["el"] = function(stem, tr, data, numgen)
	elative_color_defect(stem, tr, data, numgen)
end

-- Color/defect adjective: Same as elative
inflections["cd"] = function(stem, tr, data, numgen)
	elative_color_defect(stem, tr, data, numgen)
end

-- Triptote with lengthened ending in the construct state
inflections["lc"] = function(stem, tr, data, numgen)
	triptote_diptote(stem, tr, data, numgen, false, true)
end

function in_defective(stem, tr, data, numgen, tri)
	if not rfind(stem, IN .. "$") then
		error("'in' declension stem should end in -in: '" .. stem .. "'")
	end

	stem = rsub(stem, IN .. "$", "")
	tr = rsub(tr, "in$", "")

	add_inflections(canon_hamza(stem), tr, data, numgen,
		{IN, tri and IY .. AN or IY .. A, IN,
		 II, IY .. A, II,
		 II, IY .. A, II,
		 II, II, II,
		 IN, II, II,
		})
	local tote = tri and "triptote" or "diptote"

	insert_cat(data, numgen, "Arabic NOUNs with " .. tote .. " BROKSING in -in",
		"BROKSING " .. tote .. " in " .. make_link(HYPHEN .. IN))
end

function detect_in_type(stem, ispl)
	if ispl and rfind(stem, "^" .. CONS .. AOPT .. CONS .. AOPTA .. CONS .. IN .. "$") then -- layālin
		return 'diin'
	else -- other -in words
		return 'triin'
	end
end

-- Defective in -in
inflections["in"] = function(stem, tr, data, numgen)
	in_defective(stem, tr, data, numgen,
		detect_in_type(stem, rfind(numgen, "pl")) == 'triin')
end

-- Defective in -in, force "triptote" variant
inflections["triin"] = function(stem, tr, data, numgen)
	in_defective(stem, tr, data, numgen, true)
end

-- Defective in -in, force "diptote" variant
inflections["diin"] = function(stem, tr, data, numgen)
	in_defective(stem, tr, data, numgen, false)
end

-- Defective in -an (comes in two variants, depending on spelling with tall alif or alif maqṣūra)
inflections["an"] = function(stem, tr, data, numgen)
	local tall_alif
	if rfind(stem, AN .. ALIF .. "$") then
		tall_alif = true
		stem = rsub(stem, AN .. ALIF .. "$", "")
	elseif rfind(stem, AN .. AMAQ .. "$") then
		tall_alif = false
		stem = rsub(stem, AN .. AMAQ .. "$", "")
	else
		error("Invalid stem for 'an' declension type: " .. stem)
	end
	tr = rsub(tr, "an$", "")

	if tall_alif then
		add_inflections(canon_hamza(stem), tr, data, numgen,
			{AN .. ALIF, AN .. ALIF, AN .. ALIF,
			 AA, AA, AA,
			 AA, AA, AA,
			 AA, AA, AA,
			 AN .. ALIF, AA, AA,
			})
	else
		add_inflections(canon_hamza(stem), tr, data, numgen,
			{AN .. AMAQ, AN .. AMAQ, AN .. AMAQ,
			 AAMAQ, AAMAQ, AAMAQ,
			 AAMAQ, AAMAQ, AAMAQ,
			 AAMAQ, AAMAQ, AAMAQ,
			 AA .. AMAQ, AAMAQ, AAMAQ,
			})
	end

	-- FIXME: Should we distinguish between tall alif and alif maqṣūra?
	insert_cat(data, numgen, "Arabic NOUNs with BROKSING in -an",
		"BROKSING in " .. make_link(HYPHEN .. AN .. (tall_alif and ALIF or AMAQ)))
end

function invariable(stem, tr, data, numgen)
	add_inflections(stem, tr, data, numgen,
		{"", "", "",
		 "", "", "",
		 "", "", "",
		 "", "", "",
		 "", "", "",
		})
	
	insert_cat(data, numgen, "Arabic NOUNs with invariable BROKSING",
		"BROKSING invariable")
end

-- Invariable in -ā (non-loanword type)
inflections["inv"] = function(stem, tr, data, numgen)
	invariable(stem, tr, data, numgen)
end

-- Invariable in -ā (loanword type, behaving in the dual as if ending in -a, I think!)
inflections["lwinv"] = function(stem, tr, data, numgen)
	invariable(stem, tr, data, numgen)
end

-- Duals
inflections["d"] = function(stem, tr, data, numgen)
	if rfind(stem, ALIF .. NI .. "?$") then
		stem = rsub(stem, AOPTA .. NI .. "?$", "")
	elseif rfind(stem, AMAD .. NI .. "?$") then
		stem = rsub(stem, AMAD .. NI .. "?$", HAMZA_PH)
	else
		error("Dual stem should end in -ān(i): '" .. stem .. "'")
	end
	tr = rsub(tr, "āni?$", "")
	add_inflections(canon_hamza(stem), tr, data, numgen,
		{AANI, AYNI, AYNI,
		 AANI, AYNI, AYNI,
		 AA, AYSK, AYSK,
		 AYN, AYN, AYSK,
		 AAN, AAN, AA,
		})
	insert_cat(data, numgen, "", "dual in " .. make_link(HYPHEN .. AANI))
end

-- Sound masculine plural
inflections["smp"] = function(stem, tr, data, numgen)
	if not rfind(stem, UUNA .. "?$") then
		error("Sound masculine plural stem should end in -ūn(a): '" .. stem .. "'")
	end
	stem = rsub(stem, UUNA .. "?$", "")
	tr = rsub(tr, "ūna?$", "")
	add_inflections(canon_hamza(stem), tr, data, numgen,
		{UUNA, IINA, IINA,
		 UUNA, IINA, IINA,
		 UU,   II,   II,
		 IIN,  IIN,  II,
		 UUN,  UUN,  UU,
		})
	insert_cat(data, numgen, "Arabic NOUNs with sound masculine plural",
		"sound masculine plural")
end

-- Sound feminine plural
inflections["sfp"] = function(stem, tr, data, numgen)
	if not rfind(stem, "[" .. ALIF .. AMAD .. "]" .. T .. UN .. "?$") then
		error("Sound feminine plural stem should end in -āt(un): '" .. stem .. "'")
	end
	stem = rsub(stem, UN .. "$", "")
	tr = rsub(tr, "un$", "")
	add_inflections(stem, tr, data, numgen,
		{UN, IN, IN,
		 U,  I,  I,
		 U,  I,  I,
		 "", "", "",
		 "", "", "",
		})
	insert_cat(data, numgen, "Arabic NOUNs with sound feminine plural",
		"sound feminine plural")
end

-- Plural of defective in -an
inflections["awnp"] = function(stem, tr, data, numgen)
	if not rfind(stem, AWNA .. "?$") then
		error("'awnp' plural stem should end in -awn(a): '" .. stem .. "'")
	end
	stem = rsub(stem, AWNA .. "?$", "")
	tr = rsub(tr, "awna?$", "")
	add_inflections(canon_hamza(stem), tr, data, numgen,
		{AWNA, AYNA, AYNA,
		 AWNA, AYNA, AYNA,
		 AWSK, AYSK, AYSK,
		 AYN, AYN, AYSK,
		 AWN, AWN, AWSK,
		})
	insert_cat(data, numgen, "Arabic NOUNs with sound plural in -awna",
		"sound plural in " .. make_link(HYPHEN .. AWNA))
end

-- Detect declension of noun or adjective stem or lemma. We allow triptotes,
-- diptotes and sound plurals to either come with ʾiʿrāb or not. We detect
-- some cases where vowels are missing, when it seems fairly unambiguous to
-- do so. ISFEM is true if we are dealing with a feminine stem. NUM is
-- 'sg', 'du', or 'pl', depending on the number of the stem.
function export.detect_type(stem, isfem, num)
	-- Not strictly necessary because the caller (stem_and_type) already
	-- reorders, but won't hurt, and may be necessary if this function is
	-- called from an external caller.
	stem = reorder_shadda(stem)
	local origstem = stem
	-- So that we don't get tripped up by alif madda, we replace alif madda
	-- with the sequence hamza + fatḥa + alif before the regexps below.
	stem = rsub(stem, AMAD, HAMZA .. AA)
	if num == 'du' then
		if rfind(stem, ALIF .. NI .. "?$") then
			return 'd'
		else
			error("Malformed stem for dual, should end in the nominative dual ending -ān(i): '" .. origstem .. "'")
		end
	end
	if rfind(stem, IN .. "$") then -- -in words
		return detect_in_type(stem, num == 'pl')
	elseif rfind(stem, AN .. "[" .. ALIF .. AMAQ .. "]$") then
		return 'an'
	elseif rfind(stem, AN .. "$") then
		error("Malformed stem, fatḥatan should be over second-to-last letter: " .. origstem)
	elseif num == 'pl' and rfind(stem, AW .. SKOPT .. N .. AOPT .. "$") then
		return 'awnp'
	elseif num == 'pl' and rfind(stem, ALIF .. T .. UNOPT .. "$") then
		return 'sfp'
	elseif num == 'pl' and rfind(stem, W .. N .. AOPT .. "$") then
		return 'smp'
	elseif rfind(stem, UN .. "$") then -- explicitly specified triptotes (we catch sound feminine plurals above)
		return 'tri'
	elseif rfind(stem, U .. "$") then -- explicitly specified diptotes
		return 'di'
	elseif num == 'pl' and ( -- various diptote plural patterns
		rfind(stem, "^" .. CONS .. AOPT .. CONS .. AOPTA .. CONS .. IOPT .. Y .. "?" .. CONS .. "$") or -- fawākih, daqāʾiq, makātib, mafātīḥ
		rfind(stem, "^" .. CONS .. AOPT .. CONS .. AOPTA .. CONS .. SH .. "$") or -- maqāmm
		rfind(stem, "^" .. CONS .. U .. CONS .. AOPT .. CONS .. AOPTA .. HAMZA .. "$") or -- wuzarāʾ
		rfind(stem, ELCD_START .. SKOPT .. CONS .. IOPT .. CONS .. AOPTA .. HAMZA .. "$") or -- ʾaṣdiqāʾ
		rfind(stem, ELCD_START .. IOPT .. CONS .. SH .. AOPTA .. HAMZA .. "$") -- ʾaqillāʾ
	    ) then
		return 'di'
	elseif num == 'sg' and ( -- diptote singular patterns (mostly adjectives)
		rfind(stem, "^" .. CONS .. A .. CONS .. SK .. CONS .. AOPTA .. "[" .. N .. HAMZA .. "]$") or -- kaslān "lazy", qamrāʾ "moon-white, moonlight"
		rfind(stem, "^" .. CONS .. A .. CONS .. SH .. AOPTA .. "[" .. N .. HAMZA .. "]$") or -- laffāʾ "plump (fem.)"
		rfind(stem, ELCD_START .. SK .. CONS .. A .. CONS .. "$") or -- ʾabyad
		rfind(stem, ELCD_START .. A .. CONS .. SH .. "$") or -- ʾalaff
		-- do the following on the origstem so we can check specifically for alif madda
		rfind(origstem, "^" .. AMAD .. CONS .. A .. CONS .. "$") -- ʾālam "more painful", ʾāḵar "other"
		) then
		return 'di'
	elseif rfind(stem, AMAQ .. "$") then -- kaslā, ḏikrā (spelled with alif maqṣūra)
		return 'inv'
	elseif rfind(stem, "[" .. ALIF .. SK .. "]" .. Y .. AOPTA .. "$") then -- dunyā, hadāyā (spelled with tall alif after yāʾ)
		return 'inv'
	elseif rfind(stem, ALIF .. "$") then -- kāmērā, lībiyā (spelled with tall alif; we catch dunyā and hadāyā above)
		return 'lwinv'
	else
		return 'tri'
	end
end

-- Replace hamza (of any sort) at the end of a word, possibly followed by
-- a nominative case ending or -in or -an, with HAMZA_PH, and replace alif
-- madda at the end of a word with HAMZA_PH plus fatḥa + alif. To undo these
-- changes, use hamza_seat().
function canon_hamza(word)
	word = rsub(word, AMAD .. "$", HAMZA_PH .. AA)
	word = rsub(word, HAMZA_ANY .. "([" .. UN .. U .. IN .. "]?)$", HAMZA_PH .. "%1")
	word = rsub(word, HAMZA_ANY .. "(" .. AN .. "[" .. ALIF .. AMAQ .. "])$", HAMZA_PH .. "%1")
	return word
end

-- Supply the appropriate hamza seat(s) for a placeholder hamza.
function hamza_seat(word)
	if rfind(word, HAMZA_PH) then -- optimization to avoid many regexp substs
		return ar_utilities.process_hamza(word)
	end
	return {word}
end

--[[
-- Supply the appropriate hamza seat for a placeholder hamza in a combined
-- Arabic/translation expression.
function split_and_hamza_seat(word)
	if rfind(word, HAMZA_PH) then -- optimization to avoid many regexp substs
		local ar, tr = split_arabic_tr(word)
		-- FIXME: Do something with all values returned
		ar = ar_utilities.process_hamza(ar)[1]
		return ar .. "/" .. tr
	end
	return word
end
--]]

-- Return stem and type of an argument given the singular stem and whether
-- this is a plural argument. WORD may be of the form ARABIC, ARABIC/TR,
-- ARABIC:TYPE, ARABIC/TR:TYPE, or TYPE, for Arabic stem ARABIC with
-- transliteration TR and of type (i.e. declension) TYPE. If the type
-- is omitted, it is auto-detected using detect_type(). If the transliteration
-- is omitted, it is auto-transliterated from the Arabic. If only the type
-- is present, it is a sound plural type ('sf', 'sm' or 'awn'),
-- in which case the stem and translit are generated from the singular by
-- regular rules. SG may be of the form ARABIC/TR or ARABIC. ISFEM is true
-- if WORD is a feminine stem. NUM is either 'sg', 'du' or 'pl' according to
-- the number of the stem. The return value will be in the ARABIC/TR format.
function export.stem_and_type(word, sg, sgtype, isfem, num)
	local rettype = nil
	if rfind(word, ":") then
		local split = rsplit(word, ":")
		if #split > 2 then
			error("More than one colon found in argument: '" .. word .. "'")
		end
		word, rettype = split[1], split[2]
	end

	local ar, tr = split_arabic_tr(word)
	-- Need to reorder shaddas here so that shadda at the end of a stem
	-- followed by ʾiʿrāb or a plural ending or whatever can get processed
	-- correctly. This processing happens in various places so make sure
	-- we return the reordered Arabic in all circumstances.
	ar = reorder_shadda(ar)
	local artr = ar .. "/" .. tr

	-- Now return split-out ARABIC/TR and TYPE, with shaddas reordered in
	-- the Arabic.
	if rettype then
		return artr, rettype
	end

	-- Likewise, do shadda reordering for the singular.
	local sgar, sgtr = split_arabic_tr(sg)
	sgar = reorder_shadda(sgar)

	-- Apply a substitution to the singular Arabic and translit. If a
	-- substitution could be made, return the combined ARABIC/TR with
	-- substitutions made; else, return nil. The Arabic has ARFROM
	-- replaced with ARTO, while the translit has TRFROM replaced with
	-- TRTO, and if that doesn't match, replace TRFROM2 with TRTO2.
	local function sub(arfrom, arto, trfrom, trto, trfrom2, trto2, trfrom3, trto3)
		if rfind(sgar, arfrom) then
			local arret = rsub(sgar, arfrom, arto)
			local trret = sgtr
			if rfind(sgtr, trfrom) then
				trret = rsub(sgtr, trfrom, trto)
			elseif trfrom2 and rfind(sgtr, trfrom2) then
				trret = rsub(sgtr, trfrom2, trto2)
			elseif trfrom3 and rfind(sgtr, trfrom3) then
				trret = rsub(sgtr, trfrom3, trto3)
			elseif not rfind(sgtr, BOGUS_CHAR) then
				error("Transliteration '" .. sgtr .."' does not have same ending as Arabic '" .. sgar .. "'")
			end
			return arret .. "/" .. trret
		else
			return nil
		end
	end

	if (num ~= 'sg' or not isfem) and (word == "elf" or word == "cdf" or word == "intf" or word == "rf" or word == "f") then
		error("Inference of form for inflection type '" .. word .. "' only allowed in singular feminine")
	end
	
	if num ~= 'du' and word == "d" then
		error("Inference of form for inflection type '" .. word .. "' only allowed in dual")
	end
	
	if num ~= 'pl' and (word == "sfp" or word == "smp" or word == "awnp" or word == "cdp" or word == "p") then
		error("Inference of form for inflection type '" .. word .. "' only allowed in plural")
	end

	local function is_intensive_adj(ar)
		return rfind(ar, "^" .. CONS .. A .. CONS .. SK .. CONS .. AOPTA .. N .. UOPT .. "$") or
			rfind(ar, "^" .. CONS .. A .. CONS .. SK .. AMAD .. N .. UOPT .. "$") or
			rfind(ar, "^" .. CONS .. A .. CONS .. SH .. AOPTA .. N .. UOPT .. "$")
	end
		
	if word == "intf" then
		if not is_intensive_adj(sgar) then
			error("Singular base not in CACCān form: " .. sgar)
		end
		local ret = (
			sub(AMAD .. N .. UOPT .. "$", AMAD, "nu?$", "") or -- ends in -ʾān
			sub(AOPTA .. N .. UOPT .. "$", AMAQ, "nu?$", "") -- ends in -ān
		)
		return ret, "inv"
	end

	if word == "elf" then
		local ret = (
			sub(ELCD_START .. SK .. "[" .. Y .. W .. "]" .. A .. CONSPAR .. UOPT .. "$",
				"%1" .. UU .. "%2" .. AMAQ, "ʾa(.)[yw]a(.)u?", "%1ū%2ā") or -- ʾajyad
			sub(ELCD_START .. SK .. CONSPAR .. A .. CONSPAR .. UOPT .. "$",
				"%1" .. U .. "%2" .. SK .. "%3" .. AMAQ, "ʾa(.)(.)a(.)u?", "%1u%2%3ā") or -- ʾakbar
			sub(ELCD_START .. A .. CONSPAR .. SH .. UOPT .. "$",
				"%1" .. U .. "%2" .. SH .. AMAQ, "ʾa(.)a(.)%2u?", "%1u%2%2ā") or -- ʾaqall
			sub(ELCD_START .. SK .. CONSPAR .. AMAQ .. "$",
				"%1" .. U .. "%2" .. SK .. Y .. ALIF, "ʾa(.)(.)ā", "%1u%2yā") or -- ʾadnā
			sub("^" .. AMAD .. CONSPAR .. A .. CONSPAR .. UOPT .. "$",
				HAMZA_ON_ALIF .. U .. "%1" .. SK .. "%2" .. AMAQ, "ʾā(.)a(.)u?", "ʾu%1%2ā") -- ʾālam "more painful", ʾāḵar "other"
		)
		if not ret then
			error("Singular base not an elative adjective: " .. sgar)
		end
		return ret, "inv"
	end

	if word == "cdf" then
		local ret = (
			sub(ELCD_START .. SK .. CONSPAR .. A .. CONSPAR .. UOPT .. "$",
				"%1" .. A .. "%2" .. SK .. "%3" .. AA .. HAMZA, "ʾa(.)(.)a(.)u?", "%1a%2%3āʾ") or -- ʾaḥmar
			sub(ELCD_START .. A .. CONSPAR .. SH .. UOPT .. "$",
				"%1" .. A .. "%2" .. SH .. AA .. HAMZA, "ʾa(.)a(.)%2u?", "%1a%2%2āʾ") or -- ʾalaff
			sub(ELCD_START .. SK .. CONSPAR .. AMAQ .. "$",
				"%1" .. A .. "%2" .. SK .. Y .. AA .. HAMZA, "ʾa(.)(.)ā", "%1a%2yāʾ") -- ʾaʿmā
		)
		if not ret then
			error("Singular base not a color/defect adjective: " .. sgar)
		end
		return ret, "cd" -- so plural will be correct
	end

	if word == "rf" then
		if rfind(sgar, TAM .. UNUOPT .. "$") then
			error("Singular base is already feminine: " .. sgar)
		end

		sgar = canon_hamza(sgar)
	
		local ret = (
			sub(AN .. "[" .. ALIF .. AMAQ .. "]$", AAH, "an$", "āh") or -- ends in -an
			sub(IN .. "$", IY .. AH, "in$", "iya") or -- ends in -in
			sub(AOPT .. "[" .. ALIF .. AMAQ .. "]$", AAH, "ā$", "āh") or -- ends in alif or alif maqṣūra
			-- We separate the ʾiʿrāb and no-ʾiʿrāb cases even though we can
			-- do a single Arabic regexp to cover both because we want to
			-- remove u(n) from the translit only when ʾiʿrāb is present to
			-- lessen the risk of removing -un in the actual stem. We also
			-- allow for cases where the ʾiʿrāb is present in Arabic but not
			-- in translit.
			sub(UNU .. "$", AH, "un?$", "a", "$", "a") or -- anything else + -u(n)
			sub("$", AH, "$", "a") -- anything else
		)
		return ret, "tri"
	end

	if word == "f" then
		if sgtype == "cd" then
			return export.stem_and_type("cdf", sg, sgtype, true, 'sg')
		elseif sgtype == "el" then
			return export.stem_and_type("elf", sg, sgtype, true, 'sg')
		elseif is_intensive_adj(sgar) then
			return export.stem_and_type("intf", sg, sgtype, true, 'sg')
		else
			return export.stem_and_type("rf", sg, sgtype, true, 'sg')
		end
	end

	if word == "p" then
		if sgtype == "cd" then
			return export.stem_and_type("cdp", sg, sgtype, isfem, 'pl')
		elseif isfem then
			return export.stem_and_type("sfp", sg, sgtype, true, 'pl')
		elseif sgtype == "an" then
			return export.stem_and_type("awnp", sg, sgtype, false, 'pl')
		else
			return export.stem_and_type("smp", sg, sgtype, false, 'pl')
		end
	end

	if word == "d" then
		sgar = canon_hamza(sgar)
		local ret = (
			sub(AN .. "[" .. ALIF .. AMAQ .. "]$", AY .. AAN, "an$", "ayān") or -- ends in -an
			sub(IN .. "$", IY .. AAN, "in$", "iyān") or -- ends in -in
		    sgtype == "lwinv" and sub(AOPTA .. "$", AT .. AAN, "ā$", "atān") or -- lwinv, ends in alif
			sub(AOPT .. "[" .. ALIF .. AMAQ .. "]$", AY .. AAN, "ā$", "ayān") or -- ends in alif or alif maqṣūra
			-- We separate the ʾiʿrāb and no-ʾiʿrāb cases even though we can
			-- do a single Arabic regexp to cover both because we want to
			-- remove u(n) from the translit only when ʾiʿrāb is present to
			-- lessen the risk of removing -un in the actual stem. We also
			-- allow for cases where the ʾiʿrāb is present in Arabic but not
			-- in translit.
			--
			-- NOTE: Collapsing the "h$" and "$" cases into "h?$" doesn't work
			-- in the case of words ending in -āh, which end up having the
			-- translit end in -tāntān.
			sub(TAM .. UNU .. "$", T .. AAN, "[ht]un?$", "tān", "h$", "tān", "$", "tān") or -- ends in tāʾ marbuṭa + -u(n)
			sub(TAM .. "$", T .. AAN, "h$", "tān", "$", "tān") or -- ends in tāʾ marbuṭa
			-- Same here as above
			sub(UNU .. "$", AAN, "un?$", "ān", "$", "ān") or -- anything else + -u(n)
			sub("$", AAN, "$", "ān") -- anything else
		)
		return ret, "d"
	end

	if word == "sfp" then
		sgar = canon_hamza(sgar)
		sgar = rsub(sgar, AMAD .. "(" .. TAM .. UNUOPT .. ")$", HAMZA_PH .. AA .. "%1")
		sgar = rsub(sgar, HAMZA_ANY .. "(" .. AOPT .. TAM .. UNUOPT .. ")$", HAMZA_PH .. "%1")
		local ret = (
			sub(AOPTA .. TAM .. UNUOPT .. "$", AYAAT, "ā[ht]$", "ayāt", "ātun?$", "ayāt") or -- ends in -āh
			sub(AOPT .. TAM .. UNUOPT .. "$", AAT, "a$", "āt", "atun?$", "āt") or -- ends in -a
			sub(AN .. "[" .. ALIF .. AMAQ .. "]$", AYAAT, "an$", "ayāt") or -- ends in -an
			sub(IN .. "$", IY .. AAT, "in$", "iyāt") or -- ends in -in
			sgtype == "inv" and (
				sub(AOPT .. "[" .. ALIF .. AMAQ .. "]$", AYAAT, "ā$", "ayāt") -- ends in alif or alif maqṣūra
	        ) or
			sgtype == "lwinv" and (
				sub(AOPTA .. "$", AAT, "ā$", "āt") -- loanword ending in tall alif
			) or
			-- We separate the ʾiʿrāb and no-ʾiʿrāb cases even though we can
			-- do a single Arabic regexp to cover both because we want to
			-- remove u(n) from the translit only when ʾiʿrāb is present to
			-- lessen the risk of removing -un in the actual stem. We also
			-- allow for cases where the ʾiʿrāb is present in Arabic but not
			-- in translit.
			sub(UNU .. "$", AAT, "un?$", "āt", "$", "āt") or -- anything else + -u(n)
			sub("$", AAT, "$", "āt") -- anything else
		)
		return ret, "sfp"
	end

	if word == "smp" then
		sgar = canon_hamza(sgar)
		local ret = (
			sub(IN .. "$", UUN, "in$", "ūn") or -- ends in -in
			-- See comments above for why we have two cases, one for UNU and
			-- one for non-UNU
			sub(UNU .. "$", UUN, "un?$", "ūn", "$", "ūn") or -- anything else + -u(n)
			sub("$", UUN, "$", "ūn") -- anything else
		)
		return ret, "smp"
	end

	if word == "cdp" then
		local ret = (
			sub(ELCD_START .. SK .. W .. A .. CONSPAR .. UOPT .. "$",
				"%1" .. UU .. "%2", "ʾa(.)wa(.)u?", "%1ū%2") or -- ʾaswad
			sub(ELCD_START .. SK .. Y .. A .. CONSPAR .. UOPT .. "$",
				"%1" .. II .. "%2", "ʾa(.)ya(.)u?", "%1ī%2") or -- ʾabyaḍ
			sub(ELCD_START .. SK .. CONSPAR .. A .. CONSPAR .. UOPT .. "$",
				"%1" .. U .. "%2" .. SK .. "%3", "ʾa(.)(.)a(.)u?", "%1u%2%3") or -- ʾaḥmar
			sub(ELCD_START .. A .. CONSPAR .. SH .. UOPT .. "$",
				"%1" .. U .. "%2" .. SH, "ʾa(.)a(.)%2u?", "%1u%2%2") or -- ʾalaff
			sub(ELCD_START .. SK .. CONSPAR .. AMAQ .. "$",
				"%1" .. U .. "%2" .. Y, "ʾa(.)(.)ā", "%1u%2y") or -- ʾaʿmā
			sub("^" .. CONSPAR .. A .. W .. SKOPT .. CONSPAR .. AA .. HAMZA .. UOPT .. "$", "%1" .. UU .. "%2", "(.)aw(.)āʾu?", "%1ū%2") or -- sawdāʾ
			sub("^" .. CONSPAR .. A .. Y .. SKOPT .. CONSPAR .. AA .. HAMZA .. UOPT .. "$", "%1" .. II .. "%2", "(.)ay(.)āʾu?", "%1ī%2") or -- bayḍāʾ
			sub("^" .. CONSPAR .. A .. CONSPAR .. SK .. CONSPAR .. AA .. HAMZA .. UOPT .. "$", "%1" .. U .. "%2" .. SK .. "%3", "(.)a(.)(.)āʾu?", "%1u%2%3") or -- ʾḥamrāʾ/ʿamyāʾ
			sub("^" .. CONSPAR .. A .. CONSPAR .. SH .. AA .. HAMZA .. UOPT .. "$", "%1" .. U .. "%2" .. SH, "(.)a(.)%2āʾu?", "%1u%2%2") -- laffāʾ
		)
		if not ret then
			error("For 'cdp', singular must be masculine or feminine color/defect adjective: " .. sgar)
		end
		return ret, "tri"
	end

	if word == "awnp" then
		local ret = (
			sub(AN .. "[" .. ALIF .. AMAQ .. "]$", AWSK .. N, "an$", "awn") -- ends in -an
		)
		if not ret then
			error("For 'awnp', singular must end in -an: " .. sgar)
		end
		return ret, "awnp"
	end

	--FIXME: Special nouns don't exist any more, delete this
	--if rfind(word, "^[a-z]") then --special nouns like imru, imraa
	--	return "", word
	--end
	return artr, export.detect_type(ar, isfem, num)
end

-- local outersep = " <small style=\"color: #888\">or</small> "
-- need LRM here so multiple Arabic plurals end up agreeing in order with
-- the transliteration
local outersep = LRM .. "; "
local innersep = LRM .. "/"

function show_form(form, use_parens)
	if not form then
		return "&mdash;"
	elseif type(form) ~= "table" then
		error("a non-table value was given in the list of inflected forms.")
	end
	if #form == 0 then
		return "&mdash;"
	end
	
	local arabicvals = {}
	local latinvals = {}
	local parenvals = {}
	
	-- Accumulate separately the Arabic and transliteration into
	-- ARABICVALS and LATINVALS, then concatenate each down below.
	-- However, if USE_PARENS, we put each transliteration directly
	-- after the corresponding Arabic, in parens, and put the results
	-- in PARENVALS, which get concatenated below. (This is used in the
	-- title of the declension table.)
	for _, subform in ipairs(form) do
		local ar_span, tr_span
		local ar_subspan, tr_subspan
		local ar_subspans = {}
		local tr_subspans = {}
		if type(subform) ~= "table" then
			subform = {subform}
		end
		for _, subsubform in ipairs(subform) do
			local arabic, translit = split_arabic_tr(subsubform)
			if arabic == "-" then
				ar_subspan = "&mdash;"
				tr_subspan = "&mdash;"
			else
				if rfind(translit, BOGUS_CHAR) then
					translit = nil
				end
				tr_subspan = translit and "<span style=\"color: #888\">" .. translit .. "</span>" or "?"

				if arabic:find("{{{") then
					ar_subspan = m_links.full_link(nil, arabic, lang, nil, nil, nil, {tr = "-"}, false)
				else
					ar_subspan = m_links.full_link(arabic, nil, lang, nil, nil, nil, {tr = "-"}, false)
				end
			end

			insert_if_not(ar_subspans, ar_subspan)
			insert_if_not(tr_subspans, tr_subspan)
		end

		ar_span = table.concat(ar_subspans, innersep)
		tr_span = table.concat(tr_subspans, innersep)

		if use_parens then
			table.insert(parenvals, ar_span .. " (" .. tr_span .. ")")
		else
			table.insert(arabicvals, ar_span)
			table.insert(latinvals, tr_span)
		end
	end

	if use_parens then
		return table.concat(parenvals, outersep)
	else
		local arabic_span = table.concat(arabicvals, outersep)
		local latin_span = table.concat(latinvals, outersep)
		return arabic_span .. "<br />" .. latin_span
	end
end

function make_table(data, wikicode)
	-- Function used as replace arg of call to rsub(). Replace the
	-- specified param with its (HTML) value. The param references appear
	-- as {{{PARAM}}} in the wikicode.
	local function repl(param)
		if param == "lemma" then
			return show_form(data.forms["lemma"], "use parens")
		elseif param == "pos" then
			return data.pos
		elseif param == "info" then
			return data.title and " (" .. data.title .. ")" or ""
		elseif rfind(param, "type$") then
			return table.concat(data.forms[param], outersep)
		else
			return show_form(data.forms[param])
		end
	end
	
	-- For states not in the list of those to be displayed, clear out the
	-- corresponding inflections so they appear as a dash.
	for _, state in ipairs(data.allstates) do
		if not contains(data.states, state) then
			for _, numgen in ipairs(data.numgens()) do
				for _, case in ipairs(data.allcases) do
					data.forms[case .. "_" .. numgen .. "_" .. state] = {}
				end
			end
		end
	end

	return rsub(wikicode, "{{{([a-z_]+)}}}", repl)
end

function generate_noun_num(num)
	return [=[! style="background: #CDCDCD;" | Indefinite
! style="background: #CDCDCD;" | Definite
! style="background: #CDCDCD;" | Construct
|-
! style="background: #EFEFEF;" | Informal
| {{{inf_]=] .. num .. [=[_ind}}}
| {{{inf_]=] .. num .. [=[_def}}}
| {{{inf_]=] .. num .. [=[_con}}}
|-
! style="background: #EFEFEF;" | Nominative
| {{{nom_]=] .. num .. [=[_ind}}}
| {{{nom_]=] .. num .. [=[_def}}}
| {{{nom_]=] .. num .. [=[_con}}}
|-
! style="background: #EFEFEF;" | Accusative
| {{{acc_]=] .. num .. [=[_ind}}}
| {{{acc_]=] .. num .. [=[_def}}}
| {{{acc_]=] .. num .. [=[_con}}}
|-
! style="background: #EFEFEF;" | Genitive
| {{{gen_]=] .. num .. [=[_ind}}}
| {{{gen_]=] .. num .. [=[_def}}}
| {{{gen_]=] .. num .. [=[_con}}}
]=]
end

-- Make the noun table
function make_noun_table(data)
	local wikicode = [=[<div class="NavFrame">
<div class="NavHead">Declension of {{{pos}}} {{{lemma}}}</div>
<div class="NavContent">
{| class="inflection-table" style="border-width: 1px; border-collapse: collapse; background:#F9F9F9; text-align:center; width:100%;"
]=]

	if contains(data.numbers, "sg") then
		wikicode = wikicode .. [=[|-
! style="background: #CDCDCD;" rowspan=2 | Singular
! style="background: #CDCDCD;" colspan=3 | {{{sg_type}}}
|-
]=] .. generate_noun_num('sg')
	end
	if contains(data.numbers, "du") then
		wikicode = wikicode .. [=[|-
! style="background: #CDCDCD;" | Dual
]=] .. generate_noun_num('du')
	end
	if contains(data.numbers, "pl") then
		wikicode = wikicode .. [=[|-
! style="background: #CDCDCD;" rowspan=2 | Plural
! style="background: #CDCDCD;" colspan=3 | {{{pl_type}}}
|-
]=] .. generate_noun_num('pl')
	end
	wikicode = wikicode .. [=[|}
</div>
</div>]=]

	return make_table(data, wikicode)
end

-- Make the collective noun table
function make_coll_noun_table(data)
	local wikicode = [=[<div class="NavFrame">
<div class="NavHead">Declension of {{{pos}}} {{{lemma}}}</div>
<div class="NavContent">
{| class="inflection-table" style="border-width: 1px; border-collapse: collapse; background:#F9F9F9; text-align:center; width:100%;"
]=]

	if contains(data.numbers, "coll") then
		wikicode = wikicode .. [=[|-
! style="background: #CDCDCD;" rowspan=2 | Collective
! style="background: #CDCDCD;" colspan=3 | {{{coll_type}}}
|-
]=] .. generate_noun_num('coll')
	end
	if contains(data.numbers, "sing") then
		wikicode = wikicode .. [=[|-
! style="background: #CDCDCD;" rowspan=2 | Singulative
! style="background: #CDCDCD;" colspan=3 | {{{sing_type}}}
|-
]=] .. generate_noun_num('sing')
	end
	if contains(data.numbers, "du") then
		wikicode = wikicode .. [=[|-
! style="background: #CDCDCD;" | Dual
]=] .. generate_noun_num('du')
	end
	if contains(data.numbers, "pauc") then
		wikicode = wikicode .. [=[|-
! style="background: #CDCDCD;" rowspan=2 | Paucal (3-10)
! style="background: #CDCDCD;" colspan=3 | {{{pauc_type}}}
|-
]=] .. generate_noun_num('pauc')
	end
	if contains(data.numbers, "pl") then
		wikicode = wikicode .. [=[|-
! style="background: #CDCDCD;" rowspan=2 | Plural of variety
! style="background: #CDCDCD;" colspan=3 | {{{pl_type}}}
|-
]=] .. generate_noun_num('pl')
	end
	wikicode = wikicode .. [=[|}
</div>
</div>]=]

	return make_table(data, wikicode)
end

function generate_adj_num(num)
	return [=[|-
! style="background: #CDCDCD;" | Indefinite
! style="background: #CDCDCD;" | Definite
! style="background: #CDCDCD;" | Indefinite
! style="background: #CDCDCD;" | Definite
|-
! style="background: #EFEFEF;" | Informal
| {{{inf_m_]=] .. num .. [=[_ind}}}
| {{{inf_m_]=] .. num .. [=[_def}}}
| {{{inf_f_]=] .. num .. [=[_ind}}}
| {{{inf_f_]=] .. num .. [=[_def}}}
|-
! style="background: #EFEFEF;" | Nominative
| {{{nom_m_]=] .. num .. [=[_ind}}}
| {{{nom_m_]=] .. num .. [=[_def}}}
| {{{nom_f_]=] .. num .. [=[_ind}}}
| {{{nom_f_]=] .. num .. [=[_def}}}
|-
! style="background: #EFEFEF;" | Accusative
| {{{acc_m_]=] .. num .. [=[_ind}}}
| {{{acc_m_]=] .. num .. [=[_def}}}
| {{{acc_f_]=] .. num .. [=[_ind}}}
| {{{acc_f_]=] .. num .. [=[_def}}}
|-
! style="background: #EFEFEF;" | Genitive
| {{{gen_m_]=] .. num .. [=[_ind}}}
| {{{gen_m_]=] .. num .. [=[_def}}}
| {{{gen_f_]=] .. num .. [=[_ind}}}
| {{{gen_f_]=] .. num .. [=[_def}}}
]=]
end

-- Make the adjective table
function make_adj_table(data)
	local wikicode = [=[<div class="NavFrame">
<div class="NavHead">Declension of {{{pos}}} {{{lemma}}}</div>
<div class="NavContent">
{| class="inflection-table" style="border-width: 1px; border-collapse: collapse; background:#F9F9F9; text-align:center; width:100%;"
]=]

	if contains(data.numbers, "sg") then
		wikicode = wikicode .. [=[|-
! style="background: #CDCDCD;" rowspan=3 | Singular
! style="background: #CDCDCD;" colspan=2 | Masculine
! style="background: #CDCDCD;" colspan=2 | Feminine
|-
! style="background: #CDCDCD;" colspan=2 | {{{m_sg_type}}}
! style="background: #CDCDCD;" colspan=2 | {{{f_sg_type}}}
]=] .. generate_adj_num('sg')
	end
	if contains(data.numbers, "du") then
		wikicode = wikicode .. [=[|-
! style="background: #CDCDCD;" rowspan=2 | Dual
! style="background: #CDCDCD;" colspan=2 | Masculine
! style="background: #CDCDCD;" colspan=2 | Feminine
]=] .. generate_adj_num('du')
	end
	if contains(data.numbers, "pl") then
		wikicode = wikicode .. [=[|-
! style="background: #CDCDCD;" rowspan=3 | Plural
! style="background: #CDCDCD;" colspan=2 | Masculine
! style="background: #CDCDCD;" colspan=2 | Feminine
|-
! style="background: #CDCDCD;" colspan=2 | {{{m_pl_type}}}
! style="background: #CDCDCD;" colspan=2 | {{{f_pl_type}}}
]=] .. generate_adj_num('pl')
	end
	wikicode = wikicode .. [=[|}
</div>
</div>]=]

	return make_table(data, wikicode)
end

return export

-- For Vim, so we get 4-space tabs
-- vim: set ts=4 sw=4 noet:
