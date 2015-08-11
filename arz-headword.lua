-- Authors: Benwing, CodeCat

local lang = require("Module:languages").getByCode("arz")

local export = {}
local pos_functions = {}

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
	
	while head do
		table.insert(data.heads, head)
		data.translits[#data.heads] = translit
		
		i = i + 1
		head = ine(args["head" .. i])
		translit = ine(args["tr" .. i])
	end

	if pos_functions[poscat] then
		pos_functions[poscat].func(args, data)
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
			head = remove_links(head)
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
		handle_infl(args, data, "f", "feminine")
		handle_infl(args, data, "cpl", "common plural")
		handle_infl(args, data, "pl", "masculine plural")
		handle_infl(args, data, "fpl", "feminine plural")
		handle_infl(args, data, "el", "elative")
	end
}

function handle_sing_coll_noun_infls(args, data)
	handle_infl(args, data, "d", "dual")
	handle_infl(args, data, "pauc", "paucal")
	handle_noun_plural(args, data)
end

pos_functions["collective nouns"] = {
	func = function(args, data)
		prepend_cat(data, "nouns")
		table.insert(data.inflections, {label = "collective"})
		
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
		
		handle_gender(args, data, "f")
		-- Handle coll= (the corresponding collective noun) and collg= (its gender)
		handle_infl(args, data, "coll", "collective", "m")
		handle_sing_coll_noun_infls(args, data)
	end
}

function handle_noun_infls(args, data, singonly)
	if not singonly then
		handle_infl(args, data, "d", "dual")
		handle_noun_plural(args, data)
	end
	
	handle_infl(args, data, "f", "feminine")
	handle_infl(args, data, "m", "masculine")
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
		},
	func = function(args, data)
		handle_gender(args, data)
		handle_infl(args, data, "f", "feminine")
	end
}

pos_functions["noun plural forms"] = {
	params = {
		["g"] = {},
		["g2"] = {},
		},
	func = function(args, data)
		prepend_cat(data, "plurals")
		--prepend_cat(data, "noun forms")
		handle_gender(args, data, "p")
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
	{"I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
	 "Iq", "IIq"})

local function handle_conj_form(args, data)
	local form = ine(args[2])
	if form then
		if not valid_forms[form] then
			error("Invalid verb conjugation form " .. form)
		end
		
		table.insert(data.inflections, {label = '[[Appendix:Egyptian Arabic verbs#Form ' .. form .. '|form ' .. form .. ']]'})
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
