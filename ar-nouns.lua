-- Author: Benwing, based on early version by CodeCat.

local m_utilities = require("Module:utilities")
local m_links = require("Module:links")
local ar_utilities = require("Module:ar-utilities")

-- example of -an word with tall alif, besides ʿaṣan and riḍan (which can
-- also be spelled with alif maqṣūra):
-- qafan قَفَا "nape" m. and f.; pl. aqfiya/aqfin/aqfāʾ/qufiyy/qifiyy

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
local TA_M   = u(0x0629) -- tāʾ marbūṭa = ة
local TA     = u(0x062A) -- tāʾ = ت
local HYPHEN = u(0x0640)
local NUN    = u(0x0646) -- nūn = ن
local WAW    = u(0x0648) -- wāw = و
local YA     = u(0x064A) -- yā = ي

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
local AH    = A .. TA_M
local AT    = A .. TA
local AA    = A .. ALIF
local AAMAQ = A .. AMAQ
local AAH   = AA .. TA_M
local AAT   = AA .. TA
local II    = I .. YA
local IY	= II
local UU    = U .. WAW
local AY    = A .. YA
local AW    = A .. WAW
local AYSK  = AY .. SK
local AWSK  = AW .. SK
local NA    = NUN .. A
local NI    = NUN .. I
local AAN   = AA .. NUN
local AANI  = AA .. NI
local AYN   = AYSK .. NUN
local AYNI  = AYSK .. NI
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
	-- e.g. "nom_sg_ind" for nouns or "nom_m_sg_ind" for adjectives. The value of
	-- an entry is an array of alternatives (e.g. different plurals), where each
	-- alternative is either a string of the form "ARABIC" or "ARABIC/TRANSLIT",
	-- or an array of such strings (this is used for alternative spellings involving
	-- different hamza seats, e.g. مُبْتَدَؤُون or مُبْتَدَأُون). Alternative hamza spellings
	-- are separated in display by an "inner separator" (/), while alternatives on
	-- the level of different plurals are separated by an "outer seprator" (;).
	return {forms = {}, title = nil, categories = {},
		allgenders = {"m", "f"},
		allstates = {"ind", "def", "con"},
		allnumbers = {"sg", "du", "pl"},
		allcases = {"nom", "acc", "gen"}}
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

-- Find the stems associated with a particular gender/number combination.
-- ARGS is the set of all arguments; ARG is the name of the argument
-- (e.g. "f" for "f", "f2", ... for feminine singular); SGS is the list
-- of singular stems to base derived forms off of (masculine or feminine
-- as appropriate), an array of length-two arrays of {COMBINED_STEM, TYPE}
-- as returned by stem_and_type(); DEFAULT is the default stem to use
-- (typically either 'f', 'd' or 'p', or nil for no default); ISFEM is
-- true if this is feminine gender; NUM is 'sg', 'du' or 'pl'.
function do_gender_number(args, arg, sgs, default, isfem, num)
	results = {}
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

-- The main entry point for noun tables.
-- This and show_adj are the only functions that can be invoked from a template.
function export.show_noun(frame)
	local origargs = frame:getParent().args
	local args = {}
	-- Convert empty arguments to nil, and "" or '' arguments to empty
	for k, v in pairs(origargs) do
		args[k] = ine(v)
	end
	
	local data = init_data()
	data.numgens = function() return data.numbers end

	local sgs, pls
	if not args[1] and not args[2] and mw.title.getCurrentTitle().nsText == "Template" then
		sgs = {{"{{{1}}}", "tri"}}
		pls = {{"{{{2}}}", "tri"}}
	else
		if not args[1] then error("Parameter 1 (singular inflection) may not be empty.") end
		if args[1] == "-" then
			sgs = {{"", "-"}}
		else
			sgs = {}
			insert_stems(args[1], sgs, {{args[1], ""}}, false, 'sg')
		end
		local i = 2
		while args['head' .. i] do
			local arg = args['head' .. i]
			insert_stems(arg, sgs, {{arg, ""}}, false, 'sg')
			i = i + 1
		end
		pls = do_gender_number(args, "pl", sgs, nil, false, "pl")
	end

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

	local function call_inflections(stemtypes, data, num)
		if contains(data.numbers, num) then
			for _, stemtype in ipairs(stemtypes) do
				call_inflection(stemtype[1], stemtype[2], data, num)
			end
		end
	end

	-- Generate the singular, dual and plural forms
	local dus = (contains(data.numbers, "du") and
		do_gender_number(args, "d", sgs, "d", false, "du") or {})
	call_inflections(sgs, data, "sg")
	call_inflections(dus, data, "du")
	call_inflections(pls, data, "pl")
	
	-- Make the table
	return make_noun_table(data) .. m_utilities.format_categories(data.categories, lang)
end

-- The main entry point for adjective tables.
-- This is the only function that can be invoked from a template.
function export.show_adj(frame)
	local origargs = frame:getParent().args
	local args = {}
	-- Convert empty arguments to nil, and "" or '' arguments to empty
	for k, v in pairs(origargs) do
		args[k] = ine(v)
	end
	
	local data = init_data()
	data.numgens = function()
		local numgens = {}
		for _, gender in data.allgenders do
			for _, number in data.numbers do
				return gender .. "_" .. number
			end
		end
	end

	local msgs = {} -- masculine singular stems
	if not args[1] and mw.title.getCurrentTitle().nsText == "Template" then
		msgs = {{"{{{1}}}", "tri"}}
	else
		if not args[1] then error("Parameter 1 (singular inflection) may not be empty.") end
		if args[1] == "-" then
			msgs = {{"", "-"}}
		else
			insert_stems(args[1], msgs, {{args[1], ""}}, false, 'sg')
		end
		local i = 2
		while args['head' .. i] do
			local arg = args['head' .. i]
			insert_stems(arg, msgs, {{arg, ""}}, false, 'sg')
			i = i + 1
		end
	end

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

	local function call_inflections(stemtypes, data, gen, num)
		if contains(data.numbers, num) then
			for _, stemtype in ipairs(stemtypes) do
				call_inflection(stemtype[1], stemtype[2], data,
					gen .. "_" .. num)
			end
		end
	end

	-- Generate the singular, dual and plural forms
	call_inflections(msgs, data, "m", "sg")
	call_inflections(fsgs, data, "f", "sg")
	call_inflections(mdus, data, "m", "du")
	call_inflections(fdus, data, "f", "du")
	call_inflections(mpls, data, "m", "pl")
	call_inflections(fpls, data, "f", "pl")
	
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

-- Form inflections from combination of STEM, with transliteration TR,
-- and ENDINGS (and definite article where necessary) and store in DATA,
-- for the number or gender/number determined by NUMGEN ("sg", "du", "pl", or
-- "m_sg", "f_pl", etc. for adjectives). ENDINGS is an array of 12 values,
-- each of which is a string or array of alternatives. The order of ENDINGS
-- is indefinite nom, acc, gen; definite nom, acc, gen; construct-state
-- nom, acc, gen; informal indefinite, definite, construct.
function add_inflections(stem, tr, data, numgen, endings)
	assert(#endings == 12)
	-- Return a list of combined of ar/tr forms, with the ending tacked on.
	-- There may be more than one form because of alternative hamza seats that
	-- may be supplied, e.g. مُبْتَدَؤُون or مُبْتَدَأُون (mubtadaʾūn "(grammatical) subjects").
	local function combine(ar, tr, ending)
		local endingar, endingtr = split_arabic_tr(ending)
		allar = hamza_seat(ar .. endingar)
		tr = tr .. endingtr
		allartr = {}
		for _, arval in ipairs(allar) do
			table.insert(allartr, arval .. "/" .. tr)
		end
		return allartr
	end
	local function add_inflection(key, stem, tr, ending)
		if data.forms[key] == nil then
			data.forms[key] = {}
		end
		if type(ending) ~= "table" then
			ending = {ending}
		end
		for _, endingval in ipairs(ending) do
			insert_if_not(data.forms[key], combine(stem, tr, endingval))
		end
	end
	local defstem, deftr
	if data.omitarticle then
		defstem = stem
		deftr = tr
	else
		defstem = "ال" .. stem
		-- apply sun-letter assimilation
		deftr = rsub("al-" .. tr, "^al%-([sšṣtṯṭdḏḍzžẓnrḷ])", "a%1-%1")
	end

	add_inflection("nom_" .. numgen .. "_ind", stem, tr, endings[1])
	add_inflection("acc_" .. numgen .. "_ind", stem, tr, endings[2])
	add_inflection("gen_" .. numgen .. "_ind", stem, tr, endings[3])
	add_inflection("nom_" .. numgen .. "_def", defstem, deftr, endings[4])
	add_inflection("acc_" .. numgen .. "_def", defstem, deftr, endings[5])
	add_inflection("gen_" .. numgen .. "_def", defstem, deftr, endings[6])
	add_inflection("nom_" .. numgen .. "_con", stem, tr, endings[7])
	add_inflection("acc_" .. numgen .. "_con", stem, tr, endings[8])
	add_inflection("gen_" .. numgen .. "_con", stem, tr, endings[9])
	add_inflection("inf_" .. numgen .. "_ind", stem, tr, endings[10])
	add_inflection("inf_" .. numgen .. "_def", defstem, deftr, endings[11])
	add_inflection("inf_" .. numgen .. "_con", stem, tr, endings[12])
end	

function insert_cat(data, numgen, catvalue, engvalue)
	local singpl = rfind(numgen, "sg") and "singular" or "broken plural"
	local adjnoun = rfind(numgen, "_") and "adjective" or "noun"
	if singpl == "broken plural" and (rfind(catvalue, "SINGULAR") or rfind(engvalue, "SINGULAR")) then
		table.insert(data.categories, "Arabic " .. adjnoun .. "s with broken plural")
	end
	catvalue = rsub(catvalue, "NOUN", adjnoun)
	catvalue = rsub(catvalue, "SINGULAR", singpl)
	engvalue = rsub(engvalue, "SINGULAR", singpl)
	if catvalue ~= "" then
		table.insert(data.categories, catvalue)
	end
	local key = numgen .. "_type"
	if data.forms[key] == nil then
		data.forms[key] = {}
	end
	table.insert(data.forms[key], engvalue)
end

function triptote_diptote(stem, tr, data, numgen, is_dip, lc)
	-- Remove any case ending
	if rfind(stem, "[" .. UN .. U .. "]$") then
		stem = rsub(stem, "[" .. UN .. U .. "]$", "")
		tr = rsub(tr, "un?$", "")
	end

	if rfind(stem, TA_M .. "$") then
		if rfind(tr, "h$") then
			tr = rsub(tr, "h$", "t")
		elseif not rfind(tr, "t$") then
			tr = tr .. "t"
		end
	end

	stem = canon_hamza(stem)
	add_inflections(stem, tr, data, numgen,
		{is_dip and U or UN,
		 is_dip and A or AN .. ((rfind(stem, "[" .. HAMZA_ON_ALIF .. TA_M .. "]$")
			or rfind(stem, "[" .. AMAD .. ALIF .. "]" .. HAMZA .. "$")
			) and "" or ALIF),
		 is_dip and A or IN,
		 U, A, I,
		 lc and UU or U,
		 lc and AA or A,
		 lc and II or I,
		 {}, {}, {}, -- omit informal inflections
		})

	-- add informal inflections, special-casing ending with -a but not -āh
	if rfind(stem, "[^" .. AMAD .. ALIF .. "]" .. TA_M .. "$") then
		local inftr = rsub(tr, "t$", "")
		add_inflections(stem, inftr, data, numgen,
			{{}, {}, {},
			 {}, {}, {},
			 {}, {}, {},
			 "", "", "/t",
			})
	else
		add_inflections(stem, tr, data, numgen,
			{{}, {}, {},
			 {}, {}, {},
			 {}, {}, {},
			 "", "", lc and UU or "",
			})
	end

	local tote = lc and "long construct" or is_dip and "diptote" or "triptote"
	local singpl_tote = "SINGULAR " .. tote
	local cat_prefix = "Arabic NOUNs with " .. tote .. " SINGULAR"
	if rfind(stem, "[" .. AMAD .. ALIF .. "]" .. TA_M .. "$") then
		insert_cat(data, numgen, cat_prefix .. " in -āh",
			singpl_tote .. " in " .. make_link(HYPHEN .. AAH))
	elseif rfind(stem, TA_M .. "$") then
		insert_cat(data, numgen, cat_prefix .. " in -a",
			singpl_tote .. " in " .. make_link(HYPHEN .. AH))
	elseif lc then
		insert_cat(data, numgen, cat_prefix,
			singpl_tote)
	else
		insert_cat(data, numgen, "Arabic NOUNs with basic " .. tote .. " SINGULAR",
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

-- The word فَم ("mouth"), with alternative irregular construct
inflections["fam"] = function(stem, tr, data, numgen)
	local FAM = "فَم"
	local F = "ف"
	add_inflections("", "", data, numgen,
		{FAM .. UN, FAM .. AN .. ALIF, FAM .. IN,
		 FAM .. U, FAM .. A, FAM .. I,
		 {FAM .. U, F .. UU}, {FAM .. A, F .. AA}, {FAM .. I, F .. II},
		 FAM, FAM, {FAM, F .. UU},
		})
	insert_cat(data, numgen, "Arabic NOUNs with irregular singular",
		"singular of irregular noun")
end

-- The word اِمْرُؤ ("man")
inflections["imru"] = function(stem, tr, data, numgen)
	add_inflections("", "", data, numgen,
	{"اِمْرُؤٌ", "اِمْرَأً", "اِمْرِئٍ",
		 "مَرْءُ", "مَرْءَ", "مَرْءِ",
		 "اِمْرُؤُ", "اِمْرَأَ", "اِمْرِئِ",
		 "?", "?", "?",
		})
	insert_cat(data, numgen, "Arabic NOUNs with irregular singular",
		"singular of irregular noun")
end

-- The word اِمْرُؤ ("man") in dual
inflections["imrud"] = function(stem, tr, data, numgen)
	add_inflections("", "", data, numgen,
		{"اِمْرَآنِ", "اِمْرَأَيْنِ", "اِمْرَأَيْنِ",
		 "مَرْآنِ", "مَرْأَيْنِ", "مَرْأَيْنِ",
		 "اِمْرَآ", "اِمْرَأَيْ", "اِمْرَأَيْ",
	"اِمْرَأَيْن", "مَرْأَيْن", "اِمْرَأَيْ",
		})
	insert_cat(data, numgen, "Arabic NOUNs with irregular dual",
		"dual of irregular noun")
end

-- The word اِمْرَأَة ("woman")
inflections["imraa"] = function(stem, tr, data, numgen)
	local IMRAA = "اِمْرَأَة"
	local MARA = "مَرْأَة"
	add_inflections("", "", data, numgen,
		{IMRAA .. UN, IMRAA .. AN, IMRAA .. IN,
		 MARA .. U, MARA .. A, MARA .. I,
		 IMRAA .. U, IMRAA .. A, IMRAA .. I,
		 IMRAA, MARA, IMRAA .. "/imraʾat",
		})
	insert_cat(data, numgen, "Arabic NOUNs with irregular singular",
		"singular of irregular noun")
end

-- The word اِمْرَأَة ("woman") in dual
inflections["imraad"] = function(stem, tr, data, numgen)
	local IMRAAT = "اِمْرَأَت"
	local MARAT = "مَرْأَت"
	add_inflections("", "", data, numgen,
		{IMRAAT .. AANI, IMRAAT .. AYNI, IMRAAT .. AYNI,
		 MARAT .. AANI, MARAT .. AYNI, MARAT .. AYNI,
		 IMRAAT .. AA, IMRAAT .. AYSK, IMRAAT .. AYSK,
		 IMRAAT .. AYN, MARAT .. AYN, IMRAAT .. AYSK,
		})
	insert_cat(data, numgen, "Arabic NOUNs with irregular dual",
		"dual of irregular noun")
end

function in_defective(stem, tr, data, numgen, sgin)
	if not rfind(stem, IN .. "$") then
		error("'in' declension stem should end in -in: '" .. stem .. "'")
	end
	stem = rsub(stem, IN .. "$", "")
	tr = rsub(tr, "in$", "")

	add_inflections(canon_hamza(stem), tr, data, numgen,
		{IN, sgin and IY .. AN or IY .. A, IN,
		 II, IY .. A, II,
		 II, IY .. A, II,
		 II, II, II,
		})
	local tote = sgin and "triptote" or "diptote"

	insert_cat(data, numgen, "Arabic NOUNs with " .. tote .. " SINGULAR in -in",
		"SINGULAR " .. tote .. " in " .. make_link(HYPHEN .. IN))
end

-- Defective in -in
inflections["in"] = function(stem, tr, data, numgen)
	in_defective(stem, tr, data, numgen, rfind(numgen, "sg"))
end

-- Defective in -in, force singular variant
inflections["sgin"] = function(stem, tr, data, numgen)
	in_defective(stem, tr, data, numgen, true)
end

-- Defective in -in, force plural variant
inflections["plin"] = function(stem, tr, data, numgen)
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
			})
	else
		add_inflections(canon_hamza(stem), tr, data, numgen,
			{AN .. AMAQ, AN .. AMAQ, AN .. AMAQ,
			 AAMAQ, AAMAQ, AAMAQ,
			 AAMAQ, AAMAQ, AAMAQ,
			 AAMAQ, AAMAQ, AAMAQ,
			})
	end

	-- FIXME: Should we distinguish between tall alif and alif maqṣūra?
	insert_cat(data, numgen, "Arabic NOUNs with SINGULAR in -an",
		"SINGULAR in " .. make_link(HYPHEN .. AN .. (tall_alif and ALIF or AMAQ)))
end

function invariable(stem, tr, data, numgen)
	add_inflections(stem, tr, data, numgen,
		{"", "", "",
		 "", "", "",
		 "", "", "",
		 "", "", "",
		})
	
	insert_cat(data, numgen, "Arabic NOUNs with invariable SINGULAR",
		"SINGULAR invariable")
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
		})
	insert_cat(data, numgen, "", "dual in " .. make_link(HYPHEN .. AANI))
end

-- Sound masculine plural
inflections["smp"] = function(stem, tr, data, numgen)
	if not rfind(stem, UU .. NA .. "?$") then
		error("Sound masculine plural stem should end in -ūn(a): '" .. stem .. "'")
	end
	stem = rsub(stem, UU .. NA .. "?$", "")
	tr = rsub(tr, "ūna?$", "")
	add_inflections(canon_hamza(stem), tr, data, numgen,
		{UU .. NA, II .. NA, II .. NA,
		 UU .. NA, II .. NA, II .. NA,
		 UU,       II,       II,
		 II .. NUN, II .. NUN, II,
		})
	insert_cat(data, numgen, "Arabic NOUNs with sound masculine plural",
		"sound masculine plural")
end

-- Sound feminine plural
inflections["sfp"] = function(stem, tr, data, numgen)
	if not rfind(stem, "[" .. ALIF .. AMAD .. "]" .. TA .. UN .. "?$") then
		error("Sound feminine plural stem should end in -āt(un): '" .. stem .. "'")
	end
	stem = rsub(stem, UN .. "$", "")
	tr = rsub(tr, "un$", "")
	add_inflections(stem, tr, data, numgen,
		{UN, IN, IN,
		 U,  I,  I,
		 U,  I,  I,
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
	if num == 'pl' and rfind(stem, "^" .. CONS .. AOPT .. CONS .. AOPTA .. CONS .. IN .. "$") then -- layālin
		return 'plin'
	elseif rfind(stem, IN .. "$") then -- other -in words
		return 'sgin'
	elseif rfind(stem, AN .. "[" .. ALIF .. AMAQ .. "]$") then
		return 'an'
	elseif rfind(stem, AN .. "$") then
		error("Malformed stem, fatḥatan should be over second-to-last letter: " .. origstem)
	elseif num == 'pl' and rfind(stem, AW .. SKOPT .. NUN .. AOPT .. "$") then
		return 'awnp'
	elseif num == 'pl' and rfind(stem, ALIF .. TA .. UNOPT .. "$") then
		return 'sfp'
	elseif num == 'pl' and rfind(stem, WAW .. NUN .. AOPT .. "$") then
		return 'smp'
	elseif rfind(stem, UN .. "$") then -- explicitly specified triptotes (we catch sound feminine plurals above)
		return 'tri'
	elseif rfind(stem, U .. "$") then -- explicitly specified diptotes
		return 'di'
	elseif num == 'pl' and ( -- various diptote plural patterns
		rfind(stem, "^" .. CONS .. AOPT .. CONS .. AOPTA .. CONS .. IOPT .. YA .. "?" .. CONS .. "$") or -- fawākih, daqāʾiq, makātib, mafātīḥ
		rfind(stem, "^" .. CONS .. AOPT .. CONS .. AOPTA .. CONS .. SH .. "$") or -- maqāmm
		rfind(stem, "^" .. CONS .. U .. CONS .. AOPT .. CONS .. AOPTA .. HAMZA .. "$") or -- wuzarāʾ
		rfind(stem, ELCD_START .. SKOPT .. CONS .. IOPT .. CONS .. AOPTA .. HAMZA .. "$") or -- ʾaṣdiqāʾ
		rfind(stem, ELCD_START .. IOPT .. CONS .. SH .. AOPTA .. HAMZA .. "$") -- ʾaqillāʾ
	    ) then
		return 'di'
	elseif num == 'sg' and ( -- diptote singular patterns (mostly adjectives)
		rfind(stem, "^" .. CONS .. A .. CONS .. SK .. CONS .. AOPTA .. "[" .. NUN .. HAMZA .. "]$") or -- kaslān "lazy", qamrāʾ "moon-white, moonlight"
		rfind(stem, "^" .. CONS .. A .. CONS .. SH .. AOPTA .. "[" .. NUN .. HAMZA .. "]$") or -- laffāʾ "plump (fem.)"
		rfind(stem, ELCD_START .. SK .. CONS .. A .. CONS .. "$") or -- ʾabyad
		rfind(stem, ELCD_START .. A .. CONS .. SH .. "$") or -- ʾalaff
		-- do the following on the origstem so we can check specifically for alif madda
		rfind(origstem, "^" .. AMAD .. CONS .. A .. CONS .. "$") -- ʾālam "more painful", ʾāḵar "other"
		) then
		return 'di'
	elseif rfind(stem, AMAQ .. "$") then -- kaslā, ḏikrā (spelled with alif maqṣūra)
		return 'inv'
	elseif rfind(stem, "[" .. ALIF .. SK .. "]" .. YA .. AOPTA .. "$") then -- dunyā, hadāyā (spelled with tall alif after yāʾ)
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
-- is present, it is either a type describing a single irregular word, e.g.
-- 'fam', 'imru' or 'imraa' (in which case the stem is immaterial because
-- it is already known) or it is a sound plural type ('sf', 'sm' or 'awn'),
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
	
	if num ~= 'du' and (word == "d" or word == "imraad" or word == "imrud") then
		error("Inference of form for inflection type '" .. word .. "' only allowed in dual")
	end
	
	if num ~= 'pl' and (word == "sfp" or word == "smp" or word == "awnp" or word == "cdp" or word == "p") then
		error("Inference of form for inflection type '" .. word .. "' only allowed in plural")
	end

	local function is_intensive_adj(ar)
		return rfind(ar, "^" .. CONS .. A .. CONS .. SK .. CONS .. AOPTA .. NUN .. UOPT .. "$") or
			rfind(ar, "^" .. CONS .. A .. CONS .. SK .. AMAD .. NUN .. UOPT .. "$") or
			rfind(ar, "^" .. CONS .. A .. CONS .. SH .. AOPTA .. NUN .. UOPT .. "$")
	end
		
	if word == "intf" then
		if not is_intensive_adj(sgar) then
			error("Singular base not in CACCān form: " .. sgar)
		end
		local ret = (
			sub(AMAD .. NUN .. UOPT .. "$", AMAD, "nu?$", "") or -- ends in -ʾān
			sub(AOPTA .. NUN .. UOPT .. "$", AMAQ, "nu?$", "") -- ends in -ān
		)
		return ret, "inv"
	end

	if word == "elf" then
		local ret = (
			sub(ELCD_START .. SK .. "[" .. YA .. WAW .. "]" .. A .. CONSPAR .. UOPT .. "$",
				"%1" .. UU .. "%2" .. AMAQ, "ʾa(.)[yw]a(.)u?", "%1ū%2ā") or -- ʾajyad
			sub(ELCD_START .. SK .. CONSPAR .. A .. CONSPAR .. UOPT .. "$",
				"%1" .. U .. "%2" .. SK .. "%3" .. AMAQ, "ʾa(.)(.)a(.)u?", "%1u%2%3ā") or -- ʾakbar
			sub(ELCD_START .. A .. CONSPAR .. SH .. UOPT .. "$",
				"%1" .. U .. "%2" .. SH .. AMAQ, "ʾa(.)a(.)%2u?", "%1u%2%2ā") or -- ʾaqall
			sub(ELCD_START .. SK .. CONSPAR .. AMAQ .. "$",
				"%1" .. U .. "%2" .. SK .. YA .. ALIF, "ʾa(.)(.)ā", "%1u%2yā") or -- ʾadnā
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
				"%1" .. A .. "%2" .. SK .. YA .. AA .. HAMZA, "ʾa(.)(.)ā", "%1a%2yāʾ") -- ʾaʿmā
		)
		if not ret then
			error("Singular base not a color/defect adjective: " .. sgar)
		end
		return ret, "cd" -- so plural will be correct
	end

	if word == "rf" then
		if rfind(sgar, TA_M .. UNUOPT .. "$") then
			error("Singular base is already feminine: " .. sgar)
		end

		sgar = canon_hamza(sgar)
	
		local ret = (
			sub(AN .. "[" .. ALIF .. AMAQ .. "]$", AY .. AH, "an$", "aya") or -- ends in -an
			sub(IN .. "$", IY .. AH, "in$", "iya") or -- ends in -in
			sub(AOPT .. "[" .. ALIF .. AMAQ .. "]$", AY .. AH, "ā$", "aya") or -- ends in alif or alif maqṣūra
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
		if sgtype == "imru" then
			return "", "imrud"
		elseif sgtype == "imraa" then
			return "", "imraad"
		elseif sgtype == "fam" then
			return "فَمَان/famān", "d"
		end
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
			sub(TA_M .. UNU .. "$", TA .. AAN, "[ht]un?$", "tān", "h$", "tān", "$", "tān") or -- ends in tāʾ marbuṭa + -u(n)
			sub(TA_M .. "$", TA .. AAN, "h$", "tān", "$", "tān") or -- ends in tāʾ marbuṭa
			-- Same here as above
			sub(UNU .. "$", AAN, "un?$", "ān", "$", "ān") or -- anything else + -u(n)
			sub("$", AAN, "$", "ān") -- anything else
		)
		return ret, "d"
	end

	if word == "sfp" then
		sgar = canon_hamza(sgar)
		sgar = rsub(sgar, AMAD .. "(" .. TA_M .. UNUOPT .. ")$", HAMZA_PH .. AA .. "%1")
		sgar = rsub(sgar, HAMZA_ANY .. "(" .. AOPT .. TA_M .. UNUOPT .. ")$", HAMZA_PH .. "%1")
		local ret = (
			sub(AOPTA .. TA_M .. UNUOPT .. "$", AYAAT, "ā[ht]$", "ayāt", "ātun?$", "ayāt") or -- ends in -āh
			sub(AOPT .. TA_M .. UNUOPT .. "$", AAT, "a$", "āt", "atun?$", "āt") or -- ends in -a
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
			sub(IN .. "$", UU .. NUN, "in$", "ūn") or -- ends in -in
			-- See comments above for why we have two cases, one for UNU and
			-- one for non-UNU
			sub(UNU .. "$", UU .. NUN, "un?$", "ūn", "$", "ūn") or -- anything else + -u(n)
			sub("$", UU .. NUN, "$", "ūn") -- anything else
		)
		return ret, "smp"
	end

	if word == "cdp" then
		local ret = (
			sub(ELCD_START .. SK .. WAW .. A .. CONSPAR .. UOPT .. "$",
				"%1" .. UU .. "%2", "ʾa(.)wa(.)u?", "%1ū%2") or -- ʾaswad
			sub(ELCD_START .. SK .. YA .. A .. CONSPAR .. UOPT .. "$",
				"%1" .. II .. "%2", "ʾa(.)ya(.)u?", "%1ī%2") or -- ʾabyaḍ
			sub(ELCD_START .. SK .. CONSPAR .. A .. CONSPAR .. UOPT .. "$",
				"%1" .. U .. "%2" .. SK .. "%3", "ʾa(.)(.)a(.)u?", "%1u%2%3") or -- ʾaḥmar
			sub(ELCD_START .. A .. CONSPAR .. SH .. UOPT .. "$",
				"%1" .. U .. "%2" .. SH, "ʾa(.)a(.)%2u?", "%1u%2%2") or -- ʾalaff
			sub(ELCD_START .. SK .. CONSPAR .. AMAQ .. "$",
				"%1" .. U .. "%2" .. YA, "ʾa(.)(.)ā", "%1u%2y") or -- ʾaʿmā
			sub("^" .. CONSPAR .. A .. WAW .. SKOPT .. CONSPAR .. AA .. HAMZA .. UOPT .. "$", "%1" .. UU .. "%2", "(.)aw(.)āʾu?", "%1ū%2") or -- sawdāʾ
			sub("^" .. CONSPAR .. A .. YA .. SKOPT .. CONSPAR .. AA .. HAMZA .. UOPT .. "$", "%1" .. II .. "%2", "(.)ay(.)āʾu?", "%1ī%2") or -- bayḍāʾ
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
			sub(AN .. "[" .. ALIF .. AMAQ .. "]$", AWSK .. NUN, "an$", "awn") -- ends in -an
		)
		if not ret then
			error("For 'awnp', singular must end in -an: " .. sgar)
		end
		return ret, "awnp"
	end

	if rfind(word, "^[a-z]") then --special nouns like fam, imru, imraa
		return "", word
	end
	return artr, export.detect_type(ar, isfem, num)
end

-- local outersep = " <small style=\"color: #888\">or</small> "
local outersep = "; "
local innersep = "/"

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
	local function get_form(numgen, state)
		local form = "nom_" .. numgen .. "_" .. state
		if not data.forms[form] or #data.forms[form] == 0 then
			return nil
		end
		return data.forms[form]
	end
	
	local function get_lemma()
		for _, numgen in ipairs(data.numgens()) do
			for _, state in ipairs(data.allstates) do
				local form = get_form(number, state)
				if form then
					-- Delete ʾiʿrāb but not -in or -an
					return rsub(form, "[" .. A .. I .. U .. UN .. "]$", "")
				end
			end
		end
		return nil
	end
	
	-- Function used as replace arg of call to rsub(). Replace the
	-- specified param with its (HTML) value. The param references appear
	-- as {{{PARAM}}} in the wikicode below.
	local function repl(param)
		if param == "lemma" then
			return show_form(data.forms["lemma"] or get_lemma(), "use parens")
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

-- Make the noun table
function make_noun_table(data)
	local wikicode = [=[<div class="NavFrame">
<div class="NavHead">Declension of noun {{{lemma}}}</div>
<div class="NavContent">
{| class="inflection-table" style="border-width: 1px; border-collapse: collapse; background:#F9F9F9; text-align:center; width:100%;"
]=]

	if contains(data.numbers, "sg") then
		wikicode = wikicode .. [=[|-
! style="background: #CDCDCD;" rowspan=2 | Singular
! style="background: #CDCDCD;" colspan=3 | {{{sg_type}}}
|-
! style="background: #CDCDCD;" | Indefinite
! style="background: #CDCDCD;" | Definite
! style="background: #CDCDCD;" | Construct
|-
! style="background: #EFEFEF;" | Informal
| {{{inf_sg_ind}}}
| {{{inf_sg_def}}}
| {{{inf_sg_con}}}
|-
! style="background: #EFEFEF;" | Nominative
| {{{nom_sg_ind}}}
| {{{nom_sg_def}}}
| {{{nom_sg_con}}}
|-
! style="background: #EFEFEF;" | Accusative
| {{{acc_sg_ind}}}
| {{{acc_sg_def}}}
| {{{acc_sg_con}}}
|-
! style="background: #EFEFEF;" | Genitive
| {{{gen_sg_ind}}}
| {{{gen_sg_def}}}
| {{{gen_sg_con}}}
]=]
	end
	if contains(data.numbers, "du") then
		wikicode = wikicode .. [=[|-
! style="background: #CDCDCD;" | Dual
! style="background: #CDCDCD;" | Indefinite
! style="background: #CDCDCD;" | Definite
! style="background: #CDCDCD;" | Construct
|-
! style="background: #EFEFEF;" | Informal
| {{{inf_du_ind}}}
| {{{inf_du_def}}}
| {{{inf_du_con}}}
|-
! style="background: #EFEFEF;" | Nominative
| {{{nom_du_ind}}}
| {{{nom_du_def}}}
| {{{nom_du_con}}}
|-
! style="background: #EFEFEF;" | Accusative
| {{{acc_du_ind}}}
| {{{acc_du_def}}}
| {{{acc_du_con}}}
|-
! style="background: #EFEFEF;" | Genitive
| {{{gen_du_ind}}}
| {{{gen_du_def}}}
| {{{gen_du_con}}}
]=]
	end
	if contains(data.numbers, "pl") then
		wikicode = wikicode .. [=[|-
! style="background: #CDCDCD;" rowspan=2 | Plural
! style="background: #CDCDCD;" colspan=3 | {{{pl_type}}}
|-
! style="background: #CDCDCD;" | Indefinite
! style="background: #CDCDCD;" | Definite
! style="background: #CDCDCD;" | Construct
|-
! style="background: #EFEFEF;" | Informal
| {{{inf_pl_ind}}}
| {{{inf_pl_def}}}
| {{{inf_pl_con}}}
|-
! style="background: #EFEFEF;" | Nominative
| {{{nom_pl_ind}}}
| {{{nom_pl_def}}}
| {{{nom_pl_con}}}
|-
! style="background: #EFEFEF;" | Accusative
| {{{acc_pl_ind}}}
| {{{acc_pl_def}}}
| {{{acc_pl_con}}}
|-
! style="background: #EFEFEF;" | Genitive
| {{{gen_pl_ind}}}
| {{{gen_pl_def}}}
| {{{gen_pl_con}}}
]=]
	end
	wikicode = wikicode .. [=[|}
</div>
</div>]=]

	make_table(data, wikicode)
end

-- Make the adjective table
function make_adj_table(data)
	local wikicode = [=[<div class="NavFrame">
<div class="NavHead">Declension of adjective {{{lemma}}}</div>
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
|-
! style="background: #CDCDCD;" | Indefinite
! style="background: #CDCDCD;" | Definite
! style="background: #CDCDCD;" | Indefinite
! style="background: #CDCDCD;" | Definite
|-
! style="background: #EFEFEF;" | Informal
| {{{inf_m_sg_ind}}}
| {{{inf_m_sg_def}}}
| {{{inf_f_sg_ind}}}
| {{{inf_f_sg_def}}}
|-
! style="background: #EFEFEF;" | Nominative
| {{{nom_m_sg_ind}}}
| {{{nom_m_sg_def}}}
| {{{nom_f_sg_ind}}}
| {{{nom_f_sg_def}}}
|-
! style="background: #EFEFEF;" | Accusative
| {{{acc_m_sg_ind}}}
| {{{acc_m_sg_def}}}
| {{{acc_f_sg_ind}}}
| {{{acc_f_sg_def}}}
|-
! style="background: #EFEFEF;" | Genitive
| {{{gen_m_sg_ind}}}
| {{{gen_m_sg_def}}}
| {{{gen_f_sg_ind}}}
| {{{gen_f_sg_def}}}
]=]
	end
	if contains(data.numbers, "du") then
		wikicode = wikicode .. [=[|-
! style="background: #CDCDCD;" rowspan=2 | Dual
! style="background: #CDCDCD;" colspan=2 | Masculine
! style="background: #CDCDCD;" colspan=2 | Feminine
|-
! style="background: #CDCDCD;" | Indefinite
! style="background: #CDCDCD;" | Definite
! style="background: #CDCDCD;" | Indefinite
! style="background: #CDCDCD;" | Definite
|-
! style="background: #EFEFEF;" | Informal
| {{{inf_m_du_ind}}}
| {{{inf_m_du_def}}}
| {{{inf_f_du_ind}}}
| {{{inf_f_du_def}}}
|-
! style="background: #EFEFEF;" | Nominative
| {{{nom_m_du_ind}}}
| {{{nom_m_du_def}}}
| {{{nom_f_du_ind}}}
| {{{nom_f_du_def}}}
|-
! style="background: #EFEFEF;" | Accusative
| {{{acc_m_du_ind}}}
| {{{acc_m_du_def}}}
| {{{acc_f_du_ind}}}
| {{{acc_f_du_def}}}
|-
! style="background: #EFEFEF;" | Genitive
| {{{gen_m_du_ind}}}
| {{{gen_m_du_def}}}
| {{{gen_f_du_ind}}}
| {{{gen_f_du_def}}}
]=]
	end
	if contains(data.numbers, "pl") then
		wikicode = wikicode .. [=[|-
! style="background: #CDCDCD;" rowspan=3 | Plural
! style="background: #CDCDCD;" colspan=2 | Masculine
! style="background: #CDCDCD;" colspan=2 | Feminine
|-
! style="background: #CDCDCD;" colspan=2 | {{{m_pl_type}}}
! style="background: #CDCDCD;" colspan=2 | {{{f_pl_type}}}
|-
! style="background: #CDCDCD;" | Indefinite
! style="background: #CDCDCD;" | Definite
! style="background: #CDCDCD;" | Indefinite
! style="background: #CDCDCD;" | Definite
|-
! style="background: #EFEFEF;" | Informal
| {{{inf_m_pl_ind}}}
| {{{inf_m_pl_def}}}
| {{{inf_f_pl_ind}}}
| {{{inf_f_pl_def}}}
|-
! style="background: #EFEFEF;" | Nominative
| {{{nom_m_pl_ind}}}
| {{{nom_m_pl_def}}}
| {{{nom_f_pl_ind}}}
| {{{nom_f_pl_def}}}
|-
! style="background: #EFEFEF;" | Accusative
| {{{acc_m_pl_ind}}}
| {{{acc_m_pl_def}}}
| {{{acc_f_pl_ind}}}
| {{{acc_f_pl_def}}}
|-
! style="background: #EFEFEF;" | Genitive
| {{{gen_m_pl_ind}}}
| {{{gen_m_pl_def}}}
| {{{gen_f_pl_ind}}}
| {{{gen_f_pl_def}}}
]=]
	end
	wikicode = wikicode .. [=[|}
</div>
</div>]=]

	return make_table(data, wikicode)
end

return export

-- For Vim, so we get 4-space tabs
-- vim: set ts=4 sw=4 noet:
