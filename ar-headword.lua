local lang = require("Module:languages").getByCode("ar")

local export = {}
local pos_functions = {}

-- diacritics
local u = mw.ustring.char
local U  = u(0x064F) -- ḍamma
local UN = u(0x064C) -- ḍammatān (ḍamma tanwīn)

local track = require("Module:debug").track

-- The main entry point.
function export.show(frame)
	local args = frame:getParent().args
	local poscat = frame.args[1] or error("Part of speech has not been specified. Please pass parameter 1 to the module invocation.")
	
	-- Gather parameters
	local heads = {}
	local translits = {}
	local genders = {}
	local inflections = {}
	local categories = {"Arabic " .. poscat}
	
	local head = args["head"] or args[1] or ""
	local translit = args["tr"]; if translit == "" then translit = nil end
	local i = 1
	
	while head do
		if head then
			table.insert(heads, head)
			translits[#heads] = translit
		end
		
		i = i + 1
		head = args["head" .. i]; if head == "" then head = nil end
		translit = args["tr" .. i]; if translit == "" then translit = nil end
	end

	for _, h in ipairs(heads) do
		if mw.ustring.find(h, "[" .. UN .. U .. "]$") then
			track("ar-head/i3rab")
		end
	end

	if pos_functions[poscat] then
		pos_functions[poscat](args, genders, inflections, categories)
	end
	
	if args[3] or args[4] or args[5] or args[6] or args[7] or args[8] or args[9] then
		track("ar-head/num")
	end
	
	if args["head"] then
		track("ar-head/head")
	end
	
	if args["g"] then
		track("ar-head/g")
	end
	
	return require("Module:headword").full_headword(lang, nil, heads, translits, genders, inflections, categories, nil)
end


-- If Not Empty
local function ine(arg)
	if arg == "" then
		return nil
	else
		return arg
	end
end


-- Get a list of inflections
local function params(args, argpref, defgender)
	-- Gather parameters
	local forms = {}
	
	local form = ine(args[argpref])
	local translit = ine(args[argpref .. "tr"])
	local gender = ine(args[argpref .. "g"])
	local gender2 = ine(args[argpref .. "g2"])
	local i = 1
	
	while form do
		local genderlist = (gender or gender2) and {gender, gender2} or defgender and {defgender} or nil
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
-- prefix ARGPREF, label with LABEL and insert into inflections list
-- INFLECTIONS. Optional DEFGENDER is a default gender to specify; used for
-- singulative forms of collective nouns, and collective forms of singulative
-- nouns.
local function get_forms(args, argpref, label, defgender)
	local infls = params(args, argpref, defgender)
	infls.label = label
	
	if #infls > 0 then
		return infls
	else
		return nil
	end
end

-- Handle the case where pl=-, indicating an uncountable noun.
local function handle_noun_plural(args, inflections, categories)
	if args["pl"] == "-" then
		table.insert(inflections, {label = "usually [[Appendix:Glossary#uncountable|uncountable]]"})
		table.insert(categories, lang:getCanonicalName() .. " uncountable nouns")
	else
		table.insert(inflections, get_forms(args,  "pl", "plural"))
	end
end

local valid_genders = {
	["m"] = true,
	["f"] = true,
	["m-s"] = true,
	["f-s"] = true,
	["m-d"] = true,
	["f-d"] = true,
	["p"] = true,
	["m-p"] = true,
	["f-p"] = true,
}

-- Handle gender in unnamed param 2 and a second gender in param g2,
-- inserting into the list of genders in GENDER. If gender unspecified,
-- default to DEFAULT.
local function handle_gender(args, genders, default)
	local g = ine(args[2])
	local g2 = ine(args["g2"])
	g = g or default

	if valid_genders[g] then
		table.insert(genders, g)
	else
		table.insert(genders, "?")
	end
	
	if valid_genders[g2] then
		table.insert(genders, g2)
	elseif g2 then
		table.insert(genders, "?")
	end
end	

-- Part-of-speech functions

pos_functions["adjectives"] = function(args, genders, inflections, categories)
	table.insert(inflections, get_forms(args, "cons", "construct state"))
	table.insert(inflections, get_forms(args, "obl", "oblique"))
	table.insert(inflections, get_forms(args, "f", "feminine"))
	table.insert(inflections, get_forms(args, "fcons", "feminine construct state"))
	table.insert(inflections, get_forms(args, "fobl", "feminine oblique"))
	table.insert(inflections, get_forms(args, "d", "dual"))
	table.insert(inflections, get_forms(args, "dobl", "dual oblique"))
	table.insert(inflections, get_forms(args, "cpl", "common plural"))
	table.insert(inflections, get_forms(args, "cplcons", "common plural construct state"))
	table.insert(inflections, get_forms(args, "cplobl", "common plural oblique"))
	table.insert(inflections, get_forms(args, "pl", "masculine plural"))
	table.insert(inflections, get_forms(args, "plcons", "masculine plural construct state"))
	table.insert(inflections, get_forms(args, "plobl", "masculine plural oblique"))
	table.insert(inflections, get_forms(args, "fpl", "feminine plural"))
	table.insert(inflections, get_forms(args, "fplcons", "feminine plural construct state"))
	table.insert(inflections, get_forms(args, "fplobl", "feminine plural oblique"))
	table.insert(inflections, get_forms(args, "el", "elative"))
end

function handle_sing_coll_noun_inflections(args, inflections, categories)
	table.insert(inflections, get_forms(args, "cons", "construct state"))
	table.insert(inflections, get_forms(args, "obl", "oblique"))
	table.insert(inflections, get_forms(args, "d", "dual"))
	table.insert(inflections, get_forms(args, "dobl", "dual oblique"))
	table.insert(inflections, get_forms(args, "pauc", "paucal"))
	handle_noun_plural(args, inflections, categories)
	table.insert(inflections, get_forms(args, "plcons", "plural construct state"))
	table.insert(inflections, get_forms(args, "plobl", "plural oblique"))
end

pos_functions["collective nouns"] = function(args, genders, inflections, categories)
	table.insert(categories, 1, lang:getCanonicalName() .. " nouns")
	table.insert(inflections, {label = "collective"})
	
	local g = ine(args[2]) or "m"
	if g ~= "m" then
		track("ar-head/coll nm")
	end

	handle_gender(args, genders, "m")

	-- Singulative
	table.insert(inflections, get_forms(args, "sing", "singulative", "f"))
	local singg = ine(args["singg"])
	if singg then
		track("ar-head/singg")
		
		if singg == "m" or singg == "f" then
			track("ar-head/singg/" .. singg)
		else
			track("ar-head/singg/-")
		end
	end

	handle_sing_coll_noun_inflections(args, inflections, categories)
end

pos_functions["singulative nouns"] = function(args, genders, inflections, categories)
	table.insert(categories, 1, lang:getCanonicalName() .. " nouns")
	table.insert(inflections, {label = "singulative"})

	local g = ine(args[2]) or "f"
	if g ~= "f" then
		track("ar-head/sing nf")
	end

	handle_gender(args, genders, "f")

	-- Collective
	table.insert(inflections, get_forms(args, "coll", "collective", "m"))
	local collg = ine(args["collg"])
	if collg then
		track("ar-head/collg")
		
		if collg == "m" or collg == "f" then
			track("ar-head/collg/" .. collg)
		else
			track("ar-head/collg/-")
		end
	end

	handle_sing_coll_noun_inflections(args, inflections, categories)
end

function handle_noun_inflections(args, inflections, categories, singonly)
	table.insert(inflections, get_forms(args, "cons", "construct state"))
	table.insert(inflections, get_forms(args, "obl", "oblique"))
	if not singonly then
		table.insert(inflections, get_forms(args, "d", "dual"))
		table.insert(inflections, get_forms(args, "dobl", "dual oblique"))
		handle_noun_plural(args, inflections, categories)
		table.insert(inflections, get_forms(args, "plcons", "plural construct state"))
		table.insert(inflections, get_forms(args, "plobl", "plural oblique"))
	end
	table.insert(inflections, get_forms(args, "f", "feminine"))
	table.insert(inflections, get_forms(args, "fcons", "feminine construct state"))
	table.insert(inflections, get_forms(args, "fobl", "feminine oblique"))
	table.insert(inflections, get_forms(args, "m", "masculine"))
	table.insert(inflections, get_forms(args, "mcons", "masculine construct state"))
	table.insert(inflections, get_forms(args, "mobl", "masculine oblique"))
end

pos_functions["nouns"] = function(args, genders, inflections, categories)
	handle_gender(args, genders)

	handle_noun_inflections(args, inflections, categories)
end

pos_functions["numerals"] = function(args, genders, inflections, categories)
	table.insert(categories, lang:getCanonicalName() .. " cardinal numbers")
	handle_gender(args, genders)
	
	handle_noun_inflections(args, inflections, categories)
end


pos_functions["proper nouns"] = function(args, genders, inflections, categories)
	handle_gender(args, genders)

	handle_noun_inflections(args, inflections, categories, "singular only")
end


pos_functions["verbal nouns"] = function(args, genders, inflections, categories)
	table.insert(categories, 1, lang:getCanonicalName() .. " nouns")
	handle_gender(args, genders)
	
	handle_noun_inflections(args, inflections, categories)
end

pos_functions["pronouns"] = function(args, genders, inflections, categories)
	handle_gender(args, genders)
end

pos_functions["noun plural forms"] = function(args, genders, inflections, categories)
	table.insert(categories, 1, lang:getCanonicalName() .. " plurals")
	--table.insert(categories, 1, lang:getCanonicalName() .. " noun forms")
	handle_gender(args, genders, "p")
end

pos_functions["noun dual forms"] = function(args, genders, inflections, categories)
	table.insert(categories, 1, lang:getCanonicalName() .. " duals")
	--table.insert(categories, 1, lang:getCanonicalName() .. " noun forms")
	handle_gender(args, genders, "m-d")
end

pos_functions["adjective plural forms"] = function(args, genders, inflections, categories)
	table.insert(categories, 1, lang:getCanonicalName() .. " plurals")
	--table.insert(categories, 1, lang:getCanonicalName() .. " adjective forms")
	handle_gender(args, genders, "m-p")
end

pos_functions["adjective dual forms"] = function(args, genders, inflections, categories)
	table.insert(categories, 1, lang:getCanonicalName() .. " duals")
	--table.insert(categories, 1, lang:getCanonicalName() .. " adjective forms")
	handle_gender(args, genders, "m-d")
end

pos_functions["plurals"] = function(args, genders, inflections, categories)
	handle_gender(args, genders, "p")
end

pos_functions["noun forms"] = function(args, genders, inflections, categories)
	handle_gender(args, genders)
end

return export
