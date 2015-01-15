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

-- version of mw.ustring.gsub() that discards all but the first return value
function rsub(term, foo, bar)
	local retval = mw.ustring.gsub(term, foo, bar)
	return retval
end

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
	-- code below would fail to detect the -un in سِتٌّ because the shadda
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

function track_form(argname, form, translit)
	form = reorder_shadda(remove_links(form))
	function track_i3rab(arabic, tr)
		if mw.ustring.find(form, arabic .. "$") then
			track("i3rab")
			track("i3rab/" .. argname)
			track("i3rab-" .. tr)
			track("i3rab-" .. tr .. "/" .. argname)
		end
	end
	track_i3rab(UN, "un")
	track_i3rab(U, "u")
	track_i3rab(A, "a")
	track_i3rab(I, "i")
	if not lang:transliterate(form) then
		track("unvocalized")
		track("unvocalized/" .. argname)
		if translit then
			track("unvocalized-manual-translit")
			track("unvocalized-manual-translit/" .. argname)
		else
			track("unvocalized-no-translit")
			track("unvocalized-no-translit/" .. argname)
		end
	end
end

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
	local translit = ine(args["tr"])
	local i = 1
	
	while head do
		if head then
			table.insert(heads, head)
			translits[#heads] = translit
			track_form("head", head, translit)
		end
		
		i = i + 1
		head = ine(args["head" .. i])
		translit = ine(args["tr" .. i])
	end

	if pos_functions[poscat] then
		pos_functions[poscat](args, genders, inflections, categories)
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
	
	return require("Module:headword").full_headword(lang, nil, heads, translits, genders, inflections, categories, nil)
end

-- Get a list of inflections. See handle_infl() for meaning of ARGS, ARGPREF
-- and DEFGENDER.
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
-- INFLECTIONS. Optional DEFGENDER is default gender to insert if gender
-- isn't given; otherwise, no gender is inserted. (This is used for
-- singulative forms of collective nouns, and collective forms of singulative
-- nouns, which have different gender from the base form(s).)
local function handle_infl(args, inflections, argpref, label, defgender)
	local infls = params(args, argpref, defgender)
	infls.label = label
	
	if #infls > 0 then
		table.insert(inflections, infls)
	end
end

-- Handle the case where pl=-, indicating an uncountable noun.
local function handle_noun_plural(args, inflections, categories)
	if args["pl"] == "-" then
		table.insert(inflections, {label = "usually [[Appendix:Glossary#uncountable|uncountable]]"})
		table.insert(categories, lang:getCanonicalName() .. " uncountable nouns")
	else
		handle_infl(args, inflections, "pl", "plural")
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
	local function infl(argpref, label)
		handle_infl(args, inflections, argpref, label)
	end
	infl("cons", "construct state")
	infl("obl", "oblique")
	infl("f", "feminine")
	infl("fcons", "feminine construct state")
	infl("fobl", "feminine oblique")
	infl("d", "dual")
	infl("dobl", "dual oblique")
	infl("cpl", "common plural")
	infl("cplcons", "common plural construct state")
	infl("cplobl", "common plural oblique")
	infl("pl", "masculine plural")
	infl("plcons", "masculine plural construct state")
	infl("plobl", "masculine plural oblique")
	infl("fpl", "feminine plural")
	infl("fplcons", "feminine plural construct state")
	infl("fplobl", "feminine plural oblique")
	infl("el", "elative")
end

function handle_sing_coll_noun_inflections(args, inflections, categories)
	local function infl(argpref, label)
		handle_infl(args, inflections, argpref, label)
	end
	infl("cons", "construct state")
	infl("obl", "oblique")
	infl("d", "dual")
	infl("dobl", "dual oblique")
	infl("pauc", "paucal")
	handle_noun_plural(args, inflections, categories)
	infl("plcons", "plural construct state")
	infl("plobl", "plural oblique")
end

pos_functions["collective nouns"] = function(args, genders, inflections, categories)
	table.insert(categories, 1, lang:getCanonicalName() .. " nouns")
	table.insert(inflections, {label = "collective"})
	
	local g = ine(args[2]) or "m"
	if g ~= "m" then
		track("coll nm")
	end

	handle_gender(args, genders, "m")

	-- Singulative
	handle_infl(args, inflections, "sing", "singulative", "f")
	local singg = ine(args["singg"])
	if singg then
		track("singg")
		
		if singg == "m" or singg == "f" then
			track("singg/" .. singg)
		else
			track("singg/-")
		end
	end

	handle_sing_coll_noun_inflections(args, inflections, categories)
end

pos_functions["singulative nouns"] = function(args, genders, inflections, categories)
	table.insert(categories, 1, lang:getCanonicalName() .. " nouns")
	table.insert(inflections, {label = "singulative"})

	local g = ine(args[2]) or "f"
	if g ~= "f" then
		track("sing nf")
	end

	handle_gender(args, genders, "f")

	-- Collective
	handle_infl(args, inflections, "coll", "collective", "m")
	local collg = ine(args["collg"])
	if collg then
		track("collg")
		
		if collg == "m" or collg == "f" then
			track("collg/" .. collg)
		else
			track("collg/-")
		end
	end

	handle_sing_coll_noun_inflections(args, inflections, categories)
end

function handle_noun_inflections(args, inflections, categories, singonly)
	local function infl(argpref, label)
		handle_infl(args, inflections, argpref, label)
	end
	infl("cons", "construct state")
	infl("obl", "oblique")
	if not singonly then
		infl("d", "dual")
		infl("dobl", "dual oblique")
		handle_noun_plural(args, inflections, categories)
		infl("plcons", "plural construct state")
		infl("plobl", "plural oblique")
	end
	infl("f", "feminine")
	infl("fcons", "feminine construct state")
	infl("fobl", "feminine oblique")
	infl("m", "masculine")
	infl("mcons", "masculine construct state")
	infl("mobl", "masculine oblique")
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

-- For Vim, so we get 4-space tabs
-- vim: set ts=4 sw=4 noet:
