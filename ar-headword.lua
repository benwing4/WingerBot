-- Authors: Benwing, CodeCat

local ar_translit = require("Module:ar-translit")

local lang = require("Module:languages").getByCode("ar")

local export = {}
local pos_functions = {}

-- diacritics
local u = mw.ustring.char
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

-- various letters and signs
local TAM    = u(0x0629) -- tāʾ marbūṭa = ة

-- common combinations
local UNU   = "[" .. UN .. U .. "]"

-----------------------
-- Utility functions --
-----------------------

-- If Not Empty
local function ine(arg)
	if arg == "" then
		return nil
	else
		return arg
	end
end

local function list_to_set(list)
	local set = {}
	for _, item in ipairs(list) do
		set[item] = true
	end
	return set
end

-- version of mw.ustring.gsub() that discards all but the first return value
function rsub(term, foo, bar)
	local retval = mw.ustring.gsub(term, foo, bar)
	return retval
end

local rfind = mw.ustring.find

function remove_links(text)
	text = rsub(text, "%[%[[^|%]]*|", "")
	text = rsub(text, "%[%[", "")
	text = rsub(text, "%]%]", "")
	return text
end

function reorder_shadda(text)
	-- shadda+short-vowel (including tanwīn vowels, i.e. -an -in -un) gets
	-- replaced with short-vowel+shadda during NFC normalisation, which
	-- MediaWiki does for all Unicode strings; however, it makes the
	-- detection process inconvenient, so undo it. (For example, the tracking
	-- code below would fail to detect the -un in سِتٌّ because the shadda
	-- would come after the -un.)
	text = rsub(text, "(" .. DIACRITIC_ANY_BUT_SH .. ")" .. SH, SH .. "%1")
	return text
end

-- Tracking functions

local trackfn = require("Module:debug").track
function track(page)
	trackfn("ar-headword/" .. page)
	return true
end

function track_form(argname, form, translit, pos)
	form = reorder_shadda(remove_links(form))

	-- Examples of what you can find by looking at what links to the given
	-- pages:
	--
	-- Template:tracking/ar-headword/unvocalized (all unvocalized pages)
	-- Template:tracking/ar-headword/unvocalized/pl (all unvocalized pages
	--   where the plural is unvocalized, whether specified using pl=,
	--   pl2=, etc.)
	-- Template:tracking/ar-headword/unvocalized/head (all unvocalized pages
	--   where the head is unvocalized)
	-- Template:tracking/ar-headword/unvocalized/head/nouns (all nouns --
	--   excluding proper nouns, collective nouns, singulative nouns --
	--   where the head is unvocalized)
	-- Template:tracking/ar-headword/unvocalized/head/proper nouns (all
	--   proper nouns where the head is unvocalized)
	-- Template:tracking/ar-headword/unvocalized/head/not proper nouns (all
	--   words that are not proper nouns where the head is unvocalized)
	-- Template:tracking/ar-headword/unvocalized/adjectives (all
	--   adjectives where any parameter is unvocalized; currently only works
	--   for heads, so equivalent to .../unvocalized/head/adjectives)
	-- Template:tracking/ar-headword/unvocalized-empty-head (all pages
	--   with an empty head)
	-- Template:tracking/ar-headword/unvocalized-manual-translit (all
	--   unvocalized pages with manual translit)
	-- Template:tracking/ar-headword/unvocalized-manual-translit/head/nouns
	--   (all nouns where the head is unvocalized but has manual translit)
	-- Template:tracking/ar-headword/unvocalized-no-translit (all unvocalized
	--   pages without manual translit)
	-- Template:tracking/ar-headword/i3rab (all pages with any parameter
	--   containing i3rab of either -un, -u, -a or -i)
	-- Template:tracking/ar-headword/i3rab-un (all pages with any parameter
	--   containing an -un i3rab ending)
	-- Template:tracking/ar-headword/i3rab-un/pl (all pages where a form
	--   specified using pl=, pl2=, etc. contains an -un i3rab ending)
	-- Template:tracking/ar-headword/i3rab-u/head (all pages with a head
	--   containing an -u i3rab ending)
	-- Template:tracking/ar-headword/i3rab/head/proper nouns (all proper nouns
	--   with a head containing i3rab of either -un, -u, -a or -i)
	--
	-- In general, the format is one of the following:
	--
	-- Template:tracking/ar-headword/FIRSTLEVEL
	-- Template:tracking/ar-headword/FIRSTLEVEL/ARGNAME
	-- Template:tracking/ar-headword/FIRSTLEVEL/POS
	-- Template:tracking/ar-headword/FIRSTLEVEL/ARGNAME/POS
	--
	-- FIRSTLEVEL can be one of "unvocalized", "unvocalized-empty-head" or its
	-- opposite "unvocalized-specified", "unvocalized-manual-translit" or its
	-- opposite "unvocalized-no-translit", "i3rab", "i3rab-un", "i3rab-u",
	-- "i3rab-a", or "i3rab-i".
	--
	-- ARGNAME is either "head" or an argument such as "pl", "f", "cons", etc.
	-- This automatically includes arguments specified as head2=, pl3=, etc.
	--
	-- POS is a part of speech, lowercase and pluralized, e.g. "nouns",
	-- "adjectives", "proper nouns", "collective nouns", etc. or
	-- "not proper nouns", which includes all parts of speech but proper nouns.
	function dotrack(page)
		track(page)
		track(page .. "/" .. argname)
		if pos then
			track(page .. "/" .. pos)
			track(page .. "/" .. argname .. "/" .. pos)
			if pos ~= "proper nouns" then
				track(page .. "/not proper nouns")
				track(page .. "/" .. argname .. "/not proper nouns")
			end
		end
	end
	function track_i3rab(arabic, tr)
		if rfind(form, arabic .. "$") then
			dotrack("i3rab")
			dotrack("i3rab-" .. tr)
		end
	end
	track_i3rab(UN, "un")
	track_i3rab(U, "u")
	track_i3rab(A, "a")
	track_i3rab(I, "i")
	if form == "" or not lang:transliterate(form) then
		dotrack("unvocalized")
		if form == "" then
			dotrack("unvocalized-empty-head")
		else
			dotrack("unvocalized-specified")
		end
		if translit then
			dotrack("unvocalized-manual-translit")
		else
			dotrack("unvocalized-no-translit")
		end
	end
end

local function prepend_cat(data, pos)
	table.insert(data.categories, 1, lang:getCanonicalName() .. " " .. pos)
end

local function append_cat(data, pos)
	table.insert(data.categories, lang:getCanonicalName() .. " " .. pos)
end

-- The main entry point.
function export.show(frame)
	local poscat = frame.args[1] or error("Part of speech has not been specified. Please pass parameter 1 to the module invocation.")
	
	local params = {
		[1] = {list = "head", allow_holes = true, default = ""},
		["head"] = {default = ""},
		["tr"] = {list = true, allow_holes = true},
	}
	
	local args = frame:getParent().args  -- TODO: Use [[Module:parameters]] here
	
	-- Gather parameters
	local data = {heads = {}, translits = {}, genders = {}, inflections = {}, categories = {lang:getCanonicalName() .. " " .. poscat}}
	
	local head = args["head"] or args[1] or ""
	local translit = ine(args["tr"])
	local i = 1
	
	local irreg_translit = false

	while head do
		table.insert(data.heads, head)
		data.translits[#data.heads] = translit
		if ar_translit.irregular_translit(head, translit) then
			irreg_translit = true
		end
		track_form("head", head, translit, poscat)
		
		i = i + 1
		head = ine(args["head" .. i])
		translit = ine(args["tr" .. i])
	end

	if irreg_translit then
		append_cat(data, "terms with irregular pronunciations")
	end
	
	if pos_functions[poscat] then
		pos_functions[poscat].func(args, data)
	end
	
	if args[3] or args[4] or args[5] or args[6] or args[7] or args[8] or args[9] then
		track("num")
	end
	
	if args["head"] then
		track("head")
	end
	
	if args["g"] then
		track("g")
	end

	return require("Module:headword").full_headword(lang, nil, data.heads, data.translits, data.genders, data.inflections, data.categories, nil)
end

-- Get a list of inflections. See handle_infl() for meaning of ARGS, ARGPREF
-- and DEFGENDER.
local function getargs(args, argpref, defgender)
	-- Gather parameters
	local forms = {}
	
	local form = ine(args[argpref])
	local translit = ine(args[argpref .. "tr"])
	local gender = ine(args[argpref .. "g"])
	local gender2 = ine(args[argpref .. "g2"])
	local i = 1
	
	while form do
		local genderlist = (gender or gender2) and {gender, gender2} or defgender and {defgender} or nil
		track_form(argpref, form, translit)
		table.insert(forms, {term = form, translit = translit, gender = genderlist})

		i = i + 1
		form = ine(args[argpref .. i])
		translit = ine(args[argpref .. i .. "tr"])
		gender = ine(args[argpref .. i .. "g"])
		gender2 = ine(args[argpref .. i .. "g2"])
	end

	return forms
end

-- Get a list of inflections from the arguments in ARGS based on argument
-- prefix ARGPREF (e.g. "pl" to snarf arguments called "pl", "pl2", etc.,
-- along with "pltr", "pl2tr", etc. and optional gender(s) "plg", "plg2",
-- "pl2g", "pl2g2", "pl3g", "pl3g2", etc.). Label with LABEL (e.g. "plural"),
-- which will appear in the headword. Insert into inflections list
-- INFLS. Optional DEFGENDER is default gender to insert if gender
-- isn't given; otherwise, no gender is inserted. (This is used for
-- singulative forms of collective nouns, and collective forms of singulative
-- nouns, which have different gender from the base form(s).)
local function handle_infl(args, data, argpref, label, defgender)
	local newinfls = getargs(args, argpref, defgender)
	newinfls.label = label

	if #newinfls > 0 then
		table.insert(data.inflections, newinfls)
	end
end

-- Handle a basic inflection (e.g. plural, feminine) along with the construct,
-- definite and oblique variants of this inflection. Can also handle the base
-- construct/definite/oblique variants if both ARGPREF and LABEL are given
-- as blank strings. If NOBASE or ARGPREF is blank, skip the base inflection.
local function handle_all_infl(args, data, argpref, label, nobase)
	if not nobase and argpref ~= "" then
		handle_infl(args, data, argpref, label)
	end
	
	local labelsp = label == "" and "" or label .. " "
	handle_infl(args, data, argpref .. "cons", labelsp .. "construct state")
	handle_infl(args, data, argpref .. "def", labelsp .. "definite state")
	handle_infl(args, data, argpref .. "obl", labelsp .. "oblique")
	handle_infl(args, data, argpref .. "inf", labelsp .. "informal")
end

-- Handle the case where pl=-, indicating an uncountable noun.
local function handle_noun_plural(args, data)
	if args["pl"] == "-" then
		table.insert(data.inflections, {label = "usually [[Appendix:Glossary#uncountable|uncountable]]"})
		append_cat(data, "uncountable nouns")
	else
		handle_infl(args, data, "pl", "plural")
	end
end

local valid_genders = list_to_set(
	{"m", "m-s", "m-pr", "m-s-pr", "m-np", "m-s-np",
	 "f", "f-s", "f-pr", "f-s-pr", "f-np", "f-s-np",
	 "m-d", "m-d-pr", "m-d-np",
	 "f-d", "f-d-pr", "f-d-np",
	 "m-p", "m-p-pr", "m-p-np",
	 "f-p", "f-p-pr", "f-p-np",
	 "p", "p-pr", "p-np",
	 "pr", "np"
	})

local function is_masc_sg(g)
	return g == "m" or g == "m-pr" or g == "m-np"
end
local function is_fem_sg(g)
	return g == "f" or g == "f-pr" or g == "f-np"
end

-- Handle gender in unnamed param 2 and a second gender in param g2,
-- inserting into the list of genders in GENDER. Also insert categories
-- into CATS if the gender is unexpected for the form of the noun
-- or if multiple genders occur. If gender unspecified, default to
-- DEFAULT, which may be omitted.
local function handle_gender(args, data, default)
	local g = ine(args[2]) or default
	local g2 = ine(args["g2"])

	local function process_gender(g)
		if not g then
			table.insert(data.genders, "?")
		elseif valid_genders[g] then
			table.insert(data.genders, g)
		else
			error("Unrecognized gender: " .. g)
		end
	end

	process_gender(g)
	if g2 then
		process_gender(g2)
	end

	if g and g2 then
		append_cat(data, "terms with multiple genders")
	elseif is_masc_sg(g) or is_fem_sg(g) then
		local head = ine(args["head"]) or ine(args[1])
		if head then
			head = rsub(reorder_shadda(remove_links(head)), UNU .. "?$", "")
			local ends_with_tam = rfind(head, "^[^ ]*" .. TAM .. "$") or
				rfind(head, "^[^ ]*" .. TAM .. " ")
			if is_masc_sg(g) and ends_with_tam then
				append_cat(data, "masculine terms with feminine ending")
			elseif is_fem_sg(g) and not ends_with_tam then
				append_cat(data, "feminine terms lacking feminine ending")
			end
		end
	end
end

-- Part-of-speech functions

pos_functions["adjectives"] = {
	func = function(args, data)
		handle_all_infl(args, data, "", "") -- handle cons, def, obl, inf
		handle_all_infl(args, data, "f", "feminine")
		handle_all_infl(args, data, "d", "dual")
		handle_all_infl(args, data, "cpl", "common plural")
		handle_all_infl(args, data, "pl", "masculine plural")
		handle_all_infl(args, data, "fpl", "feminine plural")
		handle_infl(args, data, "el", "elative")
	end
}

function handle_sing_coll_noun_infls(args, data)
	handle_all_infl(args, data, "", "") -- handle cons, def, obl, inf
	handle_all_infl(args, data, "d", "dual")
	handle_all_infl(args, data, "pauc", "paucal")
	handle_noun_plural(args, data)
	handle_all_infl(args, data, "pl", "plural", "nobase")
end

-- Collective and singulative tracking code. FIXME: This is old and may not
-- be needed anymore. ARGS are the template arguments. COLLSING is either
-- "coll" or "sing" according to whether we're dealing with collective or
-- singulative nouns. OTHER is the other of the two possible values of
-- COLLSING. DEFGENDER is the default gender for nouns of this type --
-- "m" for collectives, "f" for singulatives.
function track_coll_sing(args, collsing, other, defgender)
	local g = ine(args[2]) or defgender
	if g ~= defgender then
		track(collsing .. " n" .. defgender)
	end
	
	local otherg = ine(args[other .. "g"])
	if otherg then
		track(other .. "g")

		if is_masc_sg(otherg) or is_fem_sg(otherg) then
			track(other .. "g/" .. otherg)
		else
			track(other .. "g/-")
		end
	end
end

pos_functions["collective nouns"] = {
	func = function(args, data)
		prepend_cat(data, "nouns")
		table.insert(data.inflections, {label = "collective"})
		
		track_coll_sing(args, "coll", "sing", "m")
		handle_gender(args, data, "m")
		-- Handle sing= (the corresponding singulative noun) and singg= (its gender)
		handle_infl(args, data, "sing", "singulative", "f")
		handle_sing_coll_noun_infls(args, data)
	end
}

pos_functions["singulative nouns"] = {
	func = function(args, data)
		prepend_cat(data, "nouns")
		table.insert(data.inflections, {label = "singulative"})
		
		track_coll_sing(args, "sing", "coll", "f")
		handle_gender(args, data, "f")
		-- Handle coll= (the corresponding collective noun) and collg= (its gender)
		handle_infl(args, data, "coll", "collective", "m")
		handle_sing_coll_noun_infls(args, data)
	end
}

function handle_noun_infls(args, data, singonly)
	handle_all_infl(args, data, "", "") -- handle cons, def, obl, inf
	
	if not singonly then
		handle_all_infl(args, data, "d", "dual")
		handle_noun_plural(args, data)
		handle_all_infl(args, data, "pl", "plural", "nobase")
	end
	
	handle_all_infl(args, data, "f", "feminine")
	handle_all_infl(args, data, "m", "masculine")
end

pos_functions["nouns"] = {
	func = function(args, data)
		handle_gender(args, data)
		handle_noun_infls(args, data)
	end
}

pos_functions["numerals"] = {
	func = function(args, data)
		append_cat(data, "cardinal numbers")
		handle_gender(args, data)
		handle_noun_infls(args, data)
	end
}

pos_functions["proper nouns"] = {
	func = function(args, data)
		handle_gender(args, data)
		handle_noun_infls(args, data, "singular only")
	end
}

pos_functions["pronouns"] = {
	params = {
		["g"] = {},
		["g2"] = {},
		
		["f"]  = {}, ["ftr"]  = {}, ["fg"]  = {}, ["fg2"]  = {},
		
		["fcons"]  = {}, ["fconstr"]  = {}, ["fconsg"]  = {}, ["fconsg2"]  = {},
		["fcons2"] = {}, ["fcons2tr"] = {}, ["fcons2g"] = {}, ["fcons2g2"] = {},
		["fcons3"] = {}, ["fcons3tr"] = {}, ["fcons3g"] = {}, ["fcons3g2"] = {},
		["fcons4"] = {}, ["fcons4tr"] = {}, ["fcons4g"] = {}, ["fcons4g2"] = {},
		
		["fdef"]  = {}, ["fdeftr"]  = {}, ["fdefg"]  = {}, ["fdefg2"]  = {},
		["fdef2"] = {}, ["fdef2tr"] = {}, ["fdef2g"] = {}, ["fdef2g2"] = {},
		["fdef3"] = {}, ["fdef3tr"] = {}, ["fdef3g"] = {}, ["fdef3g2"] = {},
		["fdef4"] = {}, ["fdef4tr"] = {}, ["fdef4g"] = {}, ["fdef4g2"] = {},
		
		["fobl"]  = {}, ["fobltr"]  = {}, ["foblg"]  = {}, ["foblg2"]  = {},
		["fobl2"] = {}, ["fobl2tr"] = {}, ["fobl2g"] = {}, ["fobl2g2"] = {},
		["fobl3"] = {}, ["fobl3tr"] = {}, ["fobl3g"] = {}, ["fobl3g2"] = {},
		["fobl4"] = {}, ["fobl4tr"] = {}, ["fobl4g"] = {}, ["fobl4g2"] = {},
		
		["finf"]  = {}, ["finftr"]  = {}, ["finfg"]  = {}, ["finfg2"]  = {},
		["finf2"] = {}, ["finf2tr"] = {}, ["finf2g"] = {}, ["finf2g2"] = {},
		["finf3"] = {}, ["finf3tr"] = {}, ["finf3g"] = {}, ["finf3g2"] = {},
		["finf4"] = {}, ["finf4tr"] = {}, ["finf4g"] = {}, ["finf4g2"] = {},
		},
	func = function(args, data)
		handle_gender(args, data)
		handle_all_infl(args, data, "f", "feminine")
	end
}

pos_functions["noun plural forms"] = {
	params = {
		["g"] = {},
		["g2"] = {},
		
		["cons"]  = {}, ["constr"]  = {}, ["consg"]  = {}, ["consg2"]  = {},
		["cons2"] = {}, ["cons2tr"] = {}, ["cons2g"] = {}, ["cons2g2"] = {},
		["cons3"] = {}, ["cons3tr"] = {}, ["cons3g"] = {}, ["cons3g2"] = {},
		["cons4"] = {}, ["cons4tr"] = {}, ["cons4g"] = {}, ["cons4g2"] = {},
		
		["def"]  = {}, ["deftr"]  = {}, ["defg"]  = {}, ["defg2"]  = {},
		["def2"] = {}, ["def2tr"] = {}, ["def2g"] = {}, ["def2g2"] = {},
		["def3"] = {}, ["def3tr"] = {}, ["def3g"] = {}, ["def3g2"] = {},
		["def4"] = {}, ["def4tr"] = {}, ["def4g"] = {}, ["def4g2"] = {},
		
		["obl"]  = {}, ["obltr"]  = {}, ["oblg"]  = {}, ["oblg2"]  = {},
		["obl2"] = {}, ["obl2tr"] = {}, ["obl2g"] = {}, ["obl2g2"] = {},
		["obl3"] = {}, ["obl3tr"] = {}, ["obl3g"] = {}, ["obl3g2"] = {},
		["obl4"] = {}, ["obl4tr"] = {}, ["obl4g"] = {}, ["obl4g2"] = {},
		
		["inf"]  = {}, ["inftr"]  = {}, ["infg"]  = {}, ["infg2"]  = {},
		["inf2"] = {}, ["inf2tr"] = {}, ["inf2g"] = {}, ["inf2g2"] = {},
		["inf3"] = {}, ["inf3tr"] = {}, ["inf3g"] = {}, ["inf3g2"] = {},
		["inf4"] = {}, ["inf4tr"] = {}, ["inf4g"] = {}, ["inf4g2"] = {},
		},
	func = function(args, data)
		prepend_cat(data, "plurals")
		--prepend_cat(data, "noun forms")
		handle_gender(args, data, "p")
		handle_all_infl(args, data, "", "") -- handle cons, def, obl, inf
	end
}

pos_functions["adjective feminine forms"] = {
	params = {
		["g"] = {},
		["g2"] = {},
		},
	func = function(args, data)
		--prepend_cat(data, "feminines")
		--prepend_cat(data, "adjective forms")
		handle_gender(args, data, "f")
	end
}

pos_functions["noun dual forms"] = {
	params = {
		["g"] = {},
		["g2"] = {},
		},
	func = function(args, data)
		prepend_cat(data, "duals")
		--prepend_cat(data, "noun forms")
		handle_gender(args, data, "m-d")
	end
}

pos_functions["adjective plural forms"] = {
	params = {
		["g"] = {},
		["g2"] = {},
		},
	func = function(args, data)
		prepend_cat(data, "plurals")
		--prepend_cat(data, "adjective forms")
		handle_gender(args, data, "m-p")
	end
}

pos_functions["adjective dual forms"] = {
	params = {
		["g"] = {},
		["g2"] = {},
		},
	func = function(args, data)
		prepend_cat(data, "duals")
		--prepend_cat(data, "adjective forms")
		handle_gender(args, data, "m-d")
	end
}

pos_functions["plurals"] = {
	params = {
		["g"] = {},
		["g2"] = {},
		},
	func = function(args, data)
		handle_gender(args, data, "p")
	end
}

pos_functions["noun forms"] = {
	params = {
		["g"] = {},
		["g2"] = {},
		},
	func = function(args, data)
		handle_gender(args, data)
	end
}

local valid_forms = list_to_set(
	{"I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII",
	 "XIII", "XIV", "XV", "Iq", "IIq", "IIIq", "IVq"})

local function handle_conj_form(args, data)
	local form = ine(args[2])
	if form then
		if not valid_forms[form] then
			error("Invalid verb conjugation form " .. form)
		end
		
		table.insert(data.inflections, {label = '[[Appendix:Arabic verbs#Form ' .. form .. '|form ' .. form .. ']]'})
	end
end

pos_functions["verb forms"] = {
	params = {
		[2] = {},
		},
	func = function(args, data)
		handle_conj_form(args, data)
	end
}

pos_functions["active participles"] = {
	params = {
		[2] = {},
		},
	func = function(args, data)
		prepend_cat(data, "participles")
		handle_conj_form(args, data)
	end
}

pos_functions["passive participles"] = {
	params = {
		[2] = {},
		},
	func = function(args, data)
		prepend_cat(data, "participles")
		handle_conj_form(args, data)
	end
}

return export

-- For Vim, so we get 4-space tabs
-- vim: set ts=4 sw=4 noet:
