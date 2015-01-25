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

-- The main entry point.
function export.show(frame)
	local args = frame:getParent().args
	local poscat = frame.args[1] or error("Part of speech has not been specified. Please pass parameter 1 to the module invocation.")

	-- Gather parameters
	local heads = {}
	local translits = {}
	local genders = {}
	local infls = {}
	local cats = {"Arabic " .. poscat}

	local head = args["head"] or args[1] or ""
	local translit = ine(args["tr"])
	local i = 1

	while head do
		if head then
			table.insert(heads, head)
			translits[#heads] = translit
			track_form("head", head, translit, poscat)
		end

		i = i + 1
		head = ine(args["head" .. i])
		translit = ine(args["tr" .. i])
	end

	if pos_functions[poscat] then
		pos_functions[poscat](args, genders, infls, cats)
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

	return require("Module:headword").full_headword(lang, nil, heads, translits, genders, infls, cats, nil)
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
-- INFLS. Optional DEFGENDER is default gender to insert if gender
-- isn't given; otherwise, no gender is inserted. (This is used for
-- singulative forms of collective nouns, and collective forms of singulative
-- nouns, which have different gender from the base form(s).)
local function handle_infl(args, infls, argpref, label, defgender)
	local newinfls = params(args, argpref, defgender)
	newinfls.label = label

	if #newinfls > 0 then
		table.insert(infls, newinfls)
	end
end

-- Handle a basic inflection (e.g. plural, feminine) along with the construct
-- and oblique variants of this inflection. If NOBASE, skip the base inflection.
local function handle_all_infl(args, infls, argpref, label, nobase)
	if not nobase then
		handle_infl(args, infls, argpref, label)
	end
	handle_infl(args, infls, argpref .. "cons", label .. " construct state")
	handle_infl(args, infls, argpref .. "obl", label .. " oblique")
end

local function prepend_cat(cats, pos)
	table.insert(cats, 1, lang:getCanonicalName() .. " " .. pos)
end

local function append_cat(cats, pos)
	table.insert(cats, lang:getCanonicalName() .. " " .. pos)
end

-- Handle the case where pl=-, indicating an uncountable noun.
local function handle_noun_plural(args, infls, cats)
	if args["pl"] == "-" then
		table.insert(infls, {label = "usually [[Appendix:Glossary#uncountable|uncountable]]"})
		append_cat(cats, "uncountable nouns")
	else
		handle_infl(args, infls, "pl", "plural")
	end
end

local valid_genders = list_to_set(
	{"m", "f", "m-s", "f-s", "m-d", "f-d", "p", "m-p", "f-p"})

-- Handle gender in unnamed param 2 and a second gender in param g2,
-- inserting into the list of genders in GENDER. Also insert categories
-- into CATS if the gender is unexpected for the form of the noun
-- or if multiple genders occur. If gender unspecified, default to
-- DEFAULT, which may be omitted.
local function handle_gender(args, genders, cats, default)
	local g = ine(args[2]) or default
	local g2 = ine(args["g2"])

	local function process_gender(g)
		if not g then
			table.insert(genders, "?")
		elseif valid_genders[g] then
			table.insert(genders, g)
		else
			error("Unrecognized gender: " .. g)
		end
	end

	process_gender(g)
	if g2 then
		process_gender(g2)
	end

	if g and g2 then
		append_cat(cats, "terms with multiple genders")
	elseif g == "m" or g == "f" then
		local head = ine(args["head"]) or ine(args[1])
		if head then
			head = rsub(reorder_shadda(head), UNU .. "?$", "")
			local ends_with_tam = rfind(head, TAM .. "$")
			if g == "m" and ends_with_tam then
				append_cat(cats, "masculine terms with feminine ending")
			elseif g == "f" and not ends_with_tam then
				append_cat(cats, "feminine terms lacking feminine ending")
			end
		end
	end
end

-- Part-of-speech functions

pos_functions["adjectives"] = function(args, genders, infls, cats)
	local function infl(argpref, label)
		handle_infl(args, infls, argpref, label)
	end
	local function allinfl(argpref, label)
		handle_all_infl(args, infls, argpref, label)
	end
	infl("cons", "construct state")
	infl("obl", "oblique")
	allinfl("f", "feminine")
	allinfl("d", "dual")
	allinfl("cpl", "common plural")
	allinfl("pl", "masculine plural")
	allinfl("fpl", "feminine plural")
	infl("el", "elative")
end

function handle_sing_coll_noun_infls(args, infls, cats)
	local function infl(argpref, label)
		handle_infl(args, infls, argpref, label)
	end
	local function allinfl(argpref, label, nobase)
		handle_all_infl(args, infls, argpref, label, nobase)
	end
	infl("cons", "construct state")
	infl("obl", "oblique")
	allinfl("d", "dual")
	allinfl("pauc", "paucal")
	handle_noun_plural(args, infls, cats)
	allinfl("pl", "plural", "nobase")
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

		if otherg == "m" or otherg == "f" then
			track(other .. "g/" .. otherg)
		else
			track(other .. "g/-")
		end
	end
end

pos_functions["collective nouns"] = function(args, genders, infls, cats)
	prepend_cat(cats, "nouns")
	table.insert(infls, {label = "collective"})

	track_coll_sing(args, "coll", "sing", "m")
	handle_gender(args, genders, cats, "m")
	-- Handle sing= (the corresponding singulative noun) and singg= (its gender)
	handle_infl(args, infls, "sing", "singulative", "f")
	handle_sing_coll_noun_infls(args, infls, cats)
end

pos_functions["singulative nouns"] = function(args, genders, infls, cats)
	prepend_cat(cats, "nouns")
	table.insert(infls, {label = "singulative"})

	track_coll_sing(args, "sing", "coll", "f")
	handle_gender(args, genders, cats, "f")
	-- Handle coll= (the corresponding collective noun) and collg= (its gender)
	handle_infl(args, infls, "coll", "collective", "m")
	handle_sing_coll_noun_infls(args, infls, cats)
end

function handle_noun_infls(args, infls, cats, singonly)
	local function infl(argpref, label)
		handle_infl(args, infls, argpref, label)
	end
	local function allinfl(argpref, label, nobase)
		handle_all_infl(args, infls, argpref, label, nobase)
	end
	infl("cons", "construct state")
	infl("obl", "oblique")
	if not singonly then
		allinfl("d", "dual")
		handle_noun_plural(args, infls, cats)
		allinfl("pl", "plural", "nobase")
	end
	allinfl("f", "feminine")
	allinfl("m", "masculine")
end

pos_functions["nouns"] = function(args, genders, infls, cats)
	handle_gender(args, genders, cats)

	handle_noun_infls(args, infls, cats)
end

pos_functions["numerals"] = function(args, genders, infls, cats)
	append_cat(cats, "cardinal numbers")
	handle_gender(args, genders, cats)

	handle_noun_infls(args, infls, cats)
end


pos_functions["proper nouns"] = function(args, genders, infls, cats)
	handle_gender(args, genders, cats)

	handle_noun_infls(args, infls, cats, "singular only")
end


pos_functions["verbal nouns"] = function(args, genders, infls, cats)
	prepend_cat(cats, "nouns")
	handle_gender(args, genders, cats)

	handle_noun_infls(args, infls, cats)
end

pos_functions["pronouns"] = function(args, genders, infls, cats)
	handle_gender(args, genders, cats)
end

pos_functions["noun plural forms"] = function(args, genders, infls, cats)
	prepend_cat(cats, "plurals")
	--prepend_cat(cats, "noun forms")
	handle_gender(args, genders, cats, "p")
end

pos_functions["noun dual forms"] = function(args, genders, infls, cats)
	prepend_cat(cats, "duals")
	--prepend_cat(cats, "noun forms")
	handle_gender(args, genders, cats, "m-d")
end

pos_functions["adjective plural forms"] = function(args, genders, infls, cats)
	prepend_cat(cats, "plurals")
	--prepend_cat(cats, "adjective forms")
	handle_gender(args, genders, cats, "m-p")
end

pos_functions["adjective dual forms"] = function(args, genders, infls, cats)
	prepend_cat(cats, "duals")
	--prepend_cat(cats, "adjective forms")
	handle_gender(args, genders, cats, "m-d")
end

pos_functions["plurals"] = function(args, genders, infls, cats)
	handle_gender(args, genders, cats, "p")
end

pos_functions["noun forms"] = function(args, genders, infls, cats)
	handle_gender(args, genders, cats)
end

local valid_forms = list_to_set(
	{"I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII",
	 "XIII", "XIV", "XV", "Iq", "IIq", "IIIq", "IVq"})

pos_functions["verb forms"] = function(args, genders, infls, cats)
	local form = ine(args[2])
	if not valid_forms[form] then
		error("Invalid verb conjugation form " .. form)
	end
	if form then
		table.insert(infls, {label = '[[Appendix:Arabic verbs#Form ' .. form .. '|form ' .. form .. ']]'})
	end
end

return export

-- For Vim, so we get 4-space tabs
-- vim: set ts=4 sw=4 noet:
