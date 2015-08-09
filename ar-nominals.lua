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

-- This is used in place of a transliteration when no manual
-- translit is specified and we're unable to automatically generate
-- one (typically because some vowel diacritics are missing).
local BOGUS_CHAR = u(0xFFFD)

-- hamza variants
local HAMZA            = u(0x0621) -- hamza on the line (stand-alone hamza) = ء
local HAMZA_ON_ALIF    = u(0x0623)
local HAMZA_ON_W       = u(0x0624)
local HAMZA_UNDER_ALIF = u(0x0625)
local HAMZA_ON_Y       = u(0x0626)
local HAMZA_ANY = "[" .. HAMZA .. HAMZA_ON_ALIF .. HAMZA_UNDER_ALIF .. HAMZA_ON_W .. HAMZA_ON_Y .. "]"
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

-- lists of consonants
-- exclude tāʾ marbūṭa because we don't want it treated as a consonant
-- in patterns like أَفْعَل
local consonants_needing_vowels_no_tam = "بتثجحخدذرزسشصضطظعغفقكلمنهپچڤگڨڧأإؤئء"
-- consonants on the right side; includes alif madda
local rconsonants_no_tam = consonants_needing_vowels_no_tam .. "ويآ"
-- consonants on the left side; does not include alif madda
local lconsonants_no_tam = consonants_needing_vowels_no_tam .. "وي"
local CONS = "[" .. lconsonants_no_tam .. "]"
local CONSPAR = "([" .. lconsonants_no_tam .. "])"

local LRM = u(0x200E) --left-to-right mark

-- First syllable or so of elative/color-defect adjective
local ELCD_START = "^" .. HAMZA_ON_ALIF .. AOPT .. CONSPAR

local export = {}

--------------------
-- Utility functions
--------------------

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

-- version of rsub() that asserts that a match occurred
function assert_rsub(term, foo, bar)
	local retval, numsub = rsubn(term, foo, bar)
	assert(numsub > 0)
	return retval
end

function make_link(arabic)
	--return m_links.full_link(nil, arabic, lang, nil, "term", nil, {tr = "-"}, false)
	return m_links.full_link(nil, arabic, lang, nil, "term", nil, {}, false)
end

function track(page)
	require("Module:debug").track("ar-nominals/" .. page)
	return true
end

-------------------------------------
-- Functions for building inflections
-------------------------------------

-- Functions that do the actual inflecting by creating the forms of a basic term.
local inflections = {}

local max_mods = 9 -- maximum number of modifiers
local mod_list = {"mod"} -- list of "mod", "mod2", "mod3", ...
for i=2,max_mods do
	table.insert(mod_list, "mod" .. i)
end

-- Create and return the 'data' structure that will hold all of the
-- generated declensional forms, as well as other ancillary information
-- such as the possible numbers, genders and cases the the actual numbers
-- and states to store (in 'data.numbers' and 'data.states' respectively).
function init_data()
	-- FORMS contains a table of forms for each inflectional category,
	-- e.g. "nom_sg_ind" for nouns or "nom_m_sg_ind" for adjectives. The value
	-- of an entry is an array of alternatives (e.g. different plurals), where
	-- each alternative is either a string of the form "ARABIC" or
	-- "ARABIC/TRANSLIT", or an array of such strings (this is used for
	-- alternative spellings involving different hamza seats,
	-- e.g. مُبْتَدَؤُون or مُبْتَدَأُون). Alternative hamza spellings are separated
	-- in display by an "inner separator" (/), while alternatives on
	-- the level of different plurals are separated by an "outer separator" (;).
	return {forms = {}, title = nil, categories = {},
		allgenders = {"m", "f"},
		allstates = {"ind", "def", "con"},
		allnumbers = {"sg", "du", "pl"},
		states = {}, -- initialized later
		numbers = {}, -- initialized later
		engnumbers = {sg="singular", du="dual", pl="plural",
			coll="collective", sing="singulative", pauc="paucal"},
		engnumberscap = {sg="Singular", du="Dual", pl="Plural",
			coll="Collective", sing="Singulative", pauc="Paucal (3-10)"},
		allcases = {"nom", "acc", "gen", "inf"},
		allcases_with_lemma = {"nom", "acc", "gen", "inf", "lemma"},
		-- index into endings array indicating correct ending for given
		-- combination of state and case
		statecases = {
			ind = {nom = 1, acc = 2, gen = 3, inf = 10, lemma = 13},
			def = {nom = 4, acc = 5, gen = 6, inf = 11, lemma = 14},
			-- used for a definite adjective modifying a construct-state noun
			defcon = {nom = 4, acc = 5, gen = 6, inf = 11, lemma = 14},
			con = {nom = 7, acc = 8, gen = 9, inf = 12, lemma = 15},
		},
	}
end

-- Initialize and return ARGS, ORIGARGS and DATA (see init_data()).
-- ARGS is a table of user-supplied arguments, massaged from the original
-- arguments by converting empty-string arguments to nil and appending
-- translit arguments to their base arguments with a separating slash.
-- ORIGARGS is the original table of arguments.
function init(origargs)
	-- Massage arguments by converting empty arguments to nil, and
	--  "" or '' arguments to empty.
	local args = {}
	for k, v in pairs(origargs) do
		args[k] = ine(v)
	end

	-- Further massage arguments by appending translit arguments to the
	-- corresponding base arguments, with a slash separator, as is expected
	-- in the rest of the code.
	--
	-- FIXME: We should consider separating translit and base arguments by the
	-- separators ; , | (used in overrides; see handle_lemma_and_overrides())
	-- and matching up individual parts, to allow separate translit arguments
	-- to be specified for overrides. But maybe not; the point of allowing
	-- separate translit arguments is for compatibility with headword
	-- templates such as "ar-noun" and "ar-adj", and those templates don't
	-- handle override arguments.

	local function dotr(arg, argtr)
		if not args[arg] then
			error("Argument '" .. argtr .."' specified but not corresponding base argument '" .. arg .. "'")
		end
		args[arg] = args[arg] .. "/" .. args[argtr]
	end

	-- By convention, corresponding to arg 1 is tr; corresponding to
	-- head2, head3, ... is tr2, tr3, ...; corresponding to
	-- modhead2, modhead3, ... is modtr2, modtr3, ...; corresponding to
	-- modNhead2, modNhead3, ... is modNtr2, modNtr3, ..; corresponding to
	-- all other arguments FOO, FOO2, ... is FOOtr, FOO2tr, ...
	for k, v in pairs(args) do
		if k == "tr" then
			dotr(1, "tr")
		elseif rfind(k, "tr[0-9]+$") then
			dotr(assert_rsub(k, "tr([0-9]+)$", "head%1"), k)
		elseif rfind(k, "tr$") then
			dotr(assert_rsub(k, "tr$", ""), k)
		end
	end

	-- Construct data.
	local data = init_data()

	return args, origargs, data
end

-- Parse the user-specified state spec and other related arguments. The
-- user can specify, using idafaN=, how modifiers are related to previous
-- words. The user can also manually specify which states are to appear;
-- whether to omit the definite article in the definite state; and
-- how/whether to restrict modifiers to a particular state, case or number.
-- Normally the modN_* parameters and basestate= do not need to be set
-- directly; instead, use idafaN=. It may be necessary to explicitly
-- specify state= in the presence of proper nouns or definite-only
-- adjectival expressions. NOTE: At the time this function is called,
-- data.numbers has not yet been initialized.
function parse_state_etc_spec(data, args)
	local function check(arg, dataval, allvalues)
		if args[arg] then
			if not contains(allvalues, args[arg]) then
				error("For " .. arg .. "=, value '" .. args[arg] .. "' should be one of " ..
					table.concat(allvalues, ", "))
			end
			data[dataval] = args[arg]
		end
	end

	local function check_boolean(arg, dataval)
		check(arg, dataval, {"yes", "no"})
		if data[dataval] == "yes" then
			data[dataval] = true
		elseif data[dataval] == "no" then
			data[dataval] = false
		end
	end

	-- Make sure no holes in mod values
	for i=1,(#mod_list)-1 do
		if args[mod_list[i+1]] and not args[mod_list[i]] then
			error("Hole in modifier arguments -- " .. mod_list[i+1] ..
				" present but not " .. mod_list[i])
		end
	end
	
	-- FIXME! Remove this once we're sure there are no instances of mod2
	-- that haven't been converted to modhead2.
	if args["mod2"] then
		track("mod2")
	end

	-- Set default value; may be overridden e.g. by arg["state"] or
	-- by idafaN=.
	data.states = data.allstates

	-- List of pairs of idafaN/modN parameters
	local idafa_mod_list = {{"idafa", "mod"}}
	for i=2,max_mods do
		table.insert(idafa_mod_list, {"idafa" .. i, "mod" .. i})
	end

	-- True if the value of an |idafa= param is a valid adjectival modifier
	-- value.
	local function valid_adjectival_idafaval(idafaval)
		return idafaval == "adj" or idafaval == "adj-base" or
			idafaval == "adj-mod" or rfind(idafaval, "^adj%-mod[0-9]+$")
	end

	-- Extract the referent (base or modifier) of an adjectival |idafa= param.
	-- Assumes the value is valid.
	local function adjectival_idafaval_referent(idafaval)
		if idafaval == "adj" then
			return "base"
		end
		return assert_rsub(idafaval, "^adj%-", "")
	end

	-- Convert a base/mod spec to an index: 0=base, 1=mod, 2=mod2, etc.
	local function basemod_to_index(basemod)
		if basemod == "base" then return 0 end
		if basemod == "mod" then return 1 end
		return tonumber(assert_rsub(basemod, "^mod", ""))
	end

	-- Recognize idafa spec and handle it.
	-- We do the following:
	-- (1) Check that if idafaN= is given, then modN= is also given.
	-- (2) Check that adjectival modifiers aren't followed by idafa modifiers.
	-- (3) Check that adjectival modifiers are modifying the base or an
	--     ʾidāfa modifier, not another adjectival modifier.
	-- (4) Support idafa values "adj-base", "adj-mod", "adj-mod2", "adj"
	--     (="adj-base") etc. and check that we're referring to an earlier
	--     word.
	-- (5) For ʾidāfa modifiers, set basestate=con, set modN_case=gen,
	--     set modN_idafa=true, and set modN_number to the number specified
	--     in the parameter value (e.g. 'sg' or 'def-pl'); and if the
	--     parameter value specifies a state (e.g. 'def' or 'ind-du'),
	--     set modN_state= to this value, and if this is the last ʾidāfa
	--     modifier, also set state= to this value; if this is not the last
	--     ʾidāfa modifier, set modN_state=con and disallow a state to be
	--     specified in the parameter value.
	-- (6) For adjectival modifiers of the base, do nothing.
	-- (7) For adjectival modifiers of ʾidāfa modifiers, set modN_case=gen;
	--     set modN_idafa=false; and set modN_number=, modN_numgen= and
	--     modN_state= to match the values of the idafa modifier.

	-- error checking and find last ʾidāfa modifier
	local last_is_idafa = true
	local last_idafa_mod = "base"
	for _, idafa_mod in ipairs(idafa_mod_list) do
		local idafaparam = idafa_mod[1]
		local mod = idafa_mod[2]
		local idafaval = args[idafaparam]

		if idafaval then
			local paramval = idafaparam .. "=" .. idafaval
			if not args[mod] then
				error("'" .. idafaparam .. "' parameter without corresponding '"
					.. mod .. "' parameter")
			end
			if not valid_adjectival_idafaval(idafaval) then
				-- We're a construct (ʾidāfa) modifier
				if not last_is_idafa then
					error("ʾidāfa modifier " .. paramval .. " follows adjectival modifier")
				end
				last_idafa_mod = mod
			else
				last_is_idafa = false
				local adjref = adjectival_idafaval_referent(idafaval)
				if adjref ~= "base" then
					if basemod_to_index(adjref) >= basemod_to_index(mod) then
						error(paramval .. " can only refer to an earlier element")
					end
					local idafaref = assert_rsub(adjref, "^mod", "idafa")
					if not args[idafaref] then
						error(paramval .. " cannot refer to a missing modifier")
					elseif valid_adjectival_idafaval(args[idafaref]) then
						error(paramval .. " cannot refer to an adjectival modifier")
					end
				end
			end
		end
	end

	-- Now go through and set all the modN_ data values appropriately.
	for _, idafa_mod in ipairs(idafa_mod_list) do
		local idafaparam = idafa_mod[1]
		local mod = idafa_mod[2]
		local idafaval = args[idafaparam]

		if idafaval then
			local paramval = idafaparam .. "=" .. idafaval
			local bad_idafa = true
			if idafaval == "yes" then
				idafaval = "sg"
			end
			if idafaval == "ind-def" or contains(data.allstates, idafaval) then
				idafaval = idafaval .. "-sg"
			end
			if not idafaval then
				bad_idafa = false
			elseif valid_adjectival_idafaval(idafaval) then
				local adjref = adjectival_idafaval_referent(idafaval)
				if adjref ~= "base" then
					data[mod .. "_case"] = "gen"
					data[mod .. "_state"] = data[adjref .. "_state"]
					-- if agreement is with ind-def, make it def
					if data[mod .. "_state"] == "ind-def" then
						data[mod .. "_state"] = "def"
					end
					data[mod .. "_number"] = data[adjref .. "_number"]
					data[mod .. "_numgen"] = data[adjref .. "_numgen"]
					data[mod .. "_idafa"] = false
				end
				bad_idafa = false
			elseif contains(data.allnumbers, idafaval) then
				data.basestate = "con"
				data[mod .. "_case"] = "gen"
				data[mod .. "_number"] = idafaval
				data[mod .. "_idafa"] = true
				if mod ~= last_idafa_mod then
					data[mod .. "_state"] = "con"
				end
				bad_idafa = false
			elseif rfind(idafaval, "%-") then
				local state_num = rsplit(idafaval, "%-")
				-- Support ind-def as a possible value. We set modstate to
				-- ind-def, which will signal definite agreement with adjectival
				-- modifiers; then later on we change the value to ind.
				if #state_num == 3 and state_num[1] == "ind" and state_num[2] == "def" then
					state_num[1] = "ind-def"
					state_num[2] = state_num[3]
					table.remove(state_num)
				end
				if #state_num == 2 then
					local state = state_num[1]
					local num = state_num[2]
					if (state == "ind-def" or contains(data.allstates, state))
							and contains(data.allnumbers, num) then
						if mod == last_idafa_mod then
							if state == "ind-def" then
								data.states = {"def"}
							else
								data.states = {state}
							end
						else
							error(paramval .. " cannot specify a state because it is not the last ʾidāfa modifier")
						end
						data.basestate = "con"
						data[mod .. "_case"] = "gen"
						data[mod .. "_state"] = state
						data[mod .. "_number"] = num
						data[mod .. "_idafa"] = true
						bad_idafa = false
					end
				end
			end
			if bad_idafa then
				error(paramval .. " should be one of yes, def, sg, def-sg, adj, adj-base, adj-mod, adj-mod2 or similar")
			end
		end
	end

	if args["state"] == "ind-def" then
		data.states = {"def"}
		data.basestate = "ind"
	elseif args["state"] then
		data.states = rsplit(args["state"], ",")
		for _, state in ipairs(data.states) do
			if not contains(data.allstates, state) then
				error("For state=, value '" .. state .. "' should be one of " ..
					table.concat(data.allstates, ", "))
			end
		end
	end

	-- Now process explicit settings, so that they can override the
	-- settings based on idafaN=.
	check("basestate", "basestate", data.allstates)
	check_boolean("noirreg", "noirreg")
	check_boolean("omitarticle", "omitarticle")
	data.prefix = args.prefix

	for _, mod in ipairs(mod_list) do
		check(mod .. "state", mod .. "_state", data.allstates)
		check(mod .. "case", mod .. "_case", data.allcases)
		check(mod .. "number", mod .. "_number", data.allnumgens)
		check(mod .. "numgen", mod .. "_numgen", data.allnumgens)
		check_boolean(mod .. "idafa", mod .. "_idafa")
		check_boolean(mod .. "omitarticle", mod .. "_omitarticle")
		data[mod .. "_prefix"] = args[mod .. "prefix"]
	end

	-- Make sure modN_numgen is initialized, to modN_number if necessary.
	-- This simplifies logic in certain places, e.g. call_inflections().
	-- Also convert ind-def to ind.
	for _, mod in ipairs(mod_list) do
		data[mod .. "_numgen"] = data[mod .. "_numgen"] or data[mod .. "_number"]
		if data[mod .. "_state"] == "ind-def" then
			data[mod.. "_state"] = "ind"
		end
	end
end

-- Parse the user-specified number spec. The user can manually specify which
-- numbers are to appear. Return true if |number= was specified.
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

-- Determine which numbers will appear using the logic for nouns.
-- See comment just below.
function determine_noun_numbers(data, args, pls)
	-- Can manually specify which numbers are to appear, and exactly those
	-- numbers will appear. Otherwise, if any plurals given, duals and plurals
	-- appear; else, only singular (on the assumption that the word is a proper
	-- noun or abstract noun that exists only in the singular); however,
	-- singular won't appear if "-" given for singular, and similarly for dual.
	if not parse_number_spec(data, args) then
		data.numbers = {}
		local sgarg1 = args[1]
		local duarg1 = args["d"]
		if sgarg1 ~= "-" then
			table.insert(data.numbers, "sg")
		end
		if #pls["base"] > 0 then
			-- Dual appears if either: explicit dual stem (not -) is given, or
			-- default dual is used and explicit singular stem (not -) is given.
			if (duarg1 and duarg1 ~= "-") or (not duarg1 and sgarg1 ~= "-") then
				table.insert(data.numbers, "du")
			end
			table.insert(data.numbers, "pl")
		elseif duarg1 and duarg1 ~= "-" then
			-- If explicit dual but no plural given, include it. Useful for
			-- dual tantum words.
			table.insert(data.numbers, "du")
		end
	end
end

-- For stem STEM, convert to stem-and-type format and insert stem and type
-- into RESULTS, checking to make sure it's not already there. SGS is the
-- list of singular items to base derived forms off of (masculine or feminine
-- as appropriate), an array of length-two arrays of {COMBINED_STEM, TYPE} as
-- returned by stem_and_type(); ISFEM is true if this is feminine gender;
-- NUM is "sg", "du" or "pl". POS is the part of speech, generally "noun" or
-- "adjective".
function insert_stems(stem, results, sgs, isfem, num, pos)
	if stem == "-" then
		return
	end
	for _, sg in ipairs(sgs) do
		local combined_stem, ty = export.stem_and_type(stem,
			sg[1], sg[2], isfem, num, pos)
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

	local function do_overrides(mod)
		for _, numgen in ipairs(data.allnumgens) do
			for _, state in ipairs(data.allstates) do
				for _, case in ipairs(data.allcases) do
					local arg = mod .. case .. "_" .. numgen .. "_" .. state
					handle_override(arg)
					if args[arg] and not data.noirreg then
						insert_cat(data, mod, numgen,
							"Arabic NOUNs with irregular SINGULAR",
							"SINGULAR of irregular NOUN")
					end
				end
			end
		end
	end

	do_overrides("")
	for _, mod in ipairs(mod_list) do
		do_overrides(mod .. "_")
	end

	local function get_lemma(mod)
		for _, numgen in ipairs(data.numgens()) do
			for _, state in ipairs(data.states) do
				local arg = mod .. "lemma_" .. numgen .. "_" .. state
				if data.forms[arg] and #data.forms[arg] > 0 then
					return data.forms[arg]
				end
			end
		end
		return nil
	end

	data.forms["lemma"] = get_lemma("")
	for _, mod in ipairs(mod_list) do
		data.forms[mod .. "_lemma"] = get_lemma(mod .. "_")
	end
	handle_override("lemma")
	for _, mod in ipairs(mod_list) do
		handle_override(mod .. "_lemma")
	end
end

-- Return the part of speech based on the part of speech contained in
-- data.pos and MOD (either "", "mod_", "mod2_", etc., same as in
-- do_gender_number_1()). If we're a modifier, don't use data.pos but
-- instead choose based on whether modifier is adjectival or nominal
-- (ʾiḍāfa).
function get_pos(data, mod)
	local ismod = mod ~= ""
	if not ismod then
		return data.pos
	elseif data[mod .. "idafa"] then
		return "noun"
	else
		return "adjective"
	end
end

-- Find the stems associated with a particular gender/number combination.
-- ARGS is the set of all arguments. ARGPREFS is an array of argument prefixes
-- (e.g. "f" for the actual arguments "f", "f2", ..., for the feminine
-- singular; we allow more than one to handle "cpl"). SGS is a
-- "stem-type list" (see do_gender_number()), and is the list of stems to
-- base derived forms off of (masculine or feminine as appropriate), an array
-- of length-two arrays of {COMBINED_STEM, TYPE} as returned by
-- stem_and_type(). DEFAULT, ISFEM and NUM are as in do_gender_number().
-- MOD is either "", "mod_", "mod2_", etc. depending if we're working on a
-- base or modifier argument (in the latter case, basically if the argument
-- begins with "mod").
function do_gender_number_1(data, args, argprefs, sgs, default, isfem, num, mod)
	local results = {}
	local function handle_stem(stem)
		insert_stems(stem, results, sgs, isfem, num, get_pos(data, mod))
	end

	-- If no arguments specified, use the default instead.
	need_default = true
	for _, argpref in ipairs(argprefs) do
		if args[argpref] then
			need_default = false
			break
		end
	end
	if need_default then
		if not default then
			return results
		end
		handle_stem(default)
		return results
	end

	-- For explicitly specified arguments, make sure there's at least one
	-- stem to generate off of; otherwise specifying e.g. 'sing=- pauc=فُلَان'
	-- won't override paucal.
	if #sgs == 0 then
		sgs = {{"", ""}}
	end
	for _, argpref in ipairs(argprefs) do
		if args[argpref] then
			handle_stem(args[argpref])
		end
		local i = 2
		while args[argpref .. i] do
			handle_stem(args[argpref .. i])
			i = i + 1
		end
	end
	return results
end

-- For a given gender/number combination, parse and return the full set
-- of stems for both base and modifier. The return value is a
-- "stem specification", i.e. table with a "base" key for the base, a
-- "mod" key for the first modifier (see below), a "mod2" key for the
-- second modifier, etc. listing all stems for both the base and modifier(s).
-- The value of each key is a "stem-type list", i.e. an array of stem-type
-- pairs, where each element is a size-two array of {COMBINED_STEM, STEM_TYPE}.
-- COMBINED_STEM is a stem with attached transliteration in the form
-- STEM/TRANSLIT (where the transliteration is either manually specified in
-- the stem argument, e.g. 'pl=لُورْدَات/lordāt', or auto-transliterated from
-- the Arabic, with BOGUS_CHAR substituting for the transliteration if
-- auto-translit fails). STEM_TYPE is the declension of the stem, either
-- manually specified, e.g. 'بَبَّغَاء:di' for manually-specified diptote, or
-- auto-detected (see stem_and_type() and detect_type()).
--
-- DATA and ARGS are as in init(). ARGPREFS is an array of the prefixes for
-- the argument(s) specifying the stem (and optional translit and declension
-- type). For a given ARGPREF, we check ARGPREF, ARGPREF2, ARGPREF3, ... in
-- turn for the base, and modARGPREF, modARGPREF2, modARGPREF3, ... in turn
-- for the first modifier, and mod2ARGPREF, mod2ARGPREF2, mod2ARGPREF3, ...
-- for the second modifier, etc. SGS is a stem specification (see above),
-- giving the stems that are used to base derived forms off of (e.g. if a stem
-- type "smp" appears in place of a stem, the sound masculine plural of the
-- stems in SGS will be derived). DEFAULT is a single stem (i.e. a string) that
-- is used when no stems were explicitly given by the user (typically either
-- "f", "m", "d" or "p"), or nil for no default. ISFEM is true if we're
-- accumulating stems for a feminine number/gender category, and NUM is the
-- number (expected to be "sg", "du" or "pl") of the number/gender category
-- we're accumulating stems for.
--
-- About bases and modifiers: Note that e.g. in the noun phrase يَوْم الاِثْنَيْن
-- the head noun يَوْم is the base and the noun الاِثْنَيْن is the modifier.
-- In a noun phrase like البَحْر الأَبْيَض المُتَوَسِّط, there are two modifiers.
-- Note that modifiers come in two varieties, adjectival modifiers and
-- construct (ʾidāfa) modifiers. The first above noun phrase is an example
-- of a noun phrase with a construct modifier, where the base is fixed in
-- the construct state and the modifier is fixed in number and case
-- (which is always genitive) and possibly in state. The second above noun
-- phrase is an example of a noun phrase with two adjectival modifiers.
-- A construct modifier is generally a noun, whereas an adjectival modifier
-- is an adjective that usually agrees in state, number and case with the
-- base noun. (Note that in the case of multiple modifiers, it is possible
-- for e.g. the second modifier to be an adjectival modifier that agrees
-- with the first, construct, modifier, in which case its case will be fixed
-- to genitive, its number will be fixed to the same number as the first
-- modifier and its state will vary or not depending on whether the first
-- modifier's state varies. It is not possible in general to distinguish
-- adjectival and construct modifiers by looking at the values of
-- modN_state, modN_case or modN_number, since e.g. a third modifier could
-- have all of them specified and be either kind. Thus we have modN_idafa,
-- which is true for a construct modifier, false otherwise.)
function do_gender_number(data, args, argprefs, sgs, default, isfem, num)
	local results = do_gender_number_1(data, args, argprefs, sgs["base"],
		default, isfem, num, "")
	basemodtable = {base=results}
	for _, mod in ipairs(mod_list) do
		local modn_argprefs = {}
		for _, argpref in ipairs(argprefs) do
			table.insert(modn_argprefs, mod .. argpref)
		end
		local modn_results = do_gender_number_1(data, args, modn_argprefs,
			sgs[mod] or {}, default, isfem, num, mod .. "_")
		basemodtable[mod] = modn_results
	end
	return basemodtable
end

-- Generate inflections for the given combined stem and type, for MOD
-- (either "" if we're working on the base or "mod_", "mod2_", etc. if we're
-- working on a modifier) and NUMGEN (number or number-gender combination,
-- of the sort that forms part of the keys in DATA.FORMS).
function call_inflection(combined_stem, ty, data, mod, numgen)
	if ty == "-" then
		return
	end

	if not inflections[ty] then
		error("Unknown inflection type '" .. ty .. "'")
	end
	
	local ar, tr = split_arabic_tr(combined_stem)
	inflections[ty](ar, tr, data, mod, numgen)
end

-- Generate inflections for the stems of a given number/gender combination
-- and for either the base or the modifier. STEMTYPES is a stem-type list
-- (see do_gender_number()), listing all the stems and corresponding
-- declension types. MOD is either "", "mod_", "mod2_", etc. depending on
-- whether we're working on the base or a modifier. NUMGEN is the number or
-- number-gender combination we're working on, of the sort that forms part
-- of the keys in DATA.FORMS, e.g. "sg" or "m_sg".
function call_inflections(stemtypes, data, mod, numgen)
	local mod_with_modnumgen = mod ~= "" and data[mod .. "numgen"]
	-- If modN_numgen= is given, do nothing if NUMGEN isn't the same
	if mod_with_modnumgen and data[mod .. "numgen"] ~= numgen then
		return
	end
	-- always call inflection() if mod_with_modnumgen since it may affect
	-- other numbers (cf. يَوْم الاِثْنَيْن)
	if mod_with_modnumgen or contains(data.numbers, rsub(numgen, "^.*_", "")) then
		for _, stemtype in ipairs(stemtypes) do
			call_inflection(stemtype[1], stemtype[2], data, mod, numgen)
		end
	end
end

-- Generate the entire set of inflections for a noun or adjective.
-- Also handle any manually-specified part of speech and any manual
-- inflection overrides. The value of INFLECTIONS is an array of stem
-- specifications, one per number, where each element is a size-two
-- array of a stem specification (containing the set of stems and
-- corresponding declension types for the base and any modifiers;
-- see do_gender_number()) and a NUMGEN string, i.e. a string identifying
-- the number or number/gender in question (e.g. "sg", "du", "pl",
-- "m_sg", "f_pl", etc.).
function do_inflections_and_overrides(data, args, inflections)
	-- do this before generating inflections so POS change is reflected in
	-- categories
	if args["pos"] then
		data.pos = args["pos"]
	end

	for _, inflection in ipairs(inflections) do
		call_inflections(inflection[1]["base"] or {}, data, "", inflection[2])
		for _, mod in ipairs(mod_list) do
			call_inflections(inflection[1][mod] or {}, data,
				mod .. "_", inflection[2])
		end
	end

	handle_lemma_and_overrides(data, args)
end

-- Helper function for get_heads(). Parses the stems for either the
-- base or the modifier (see do_gender_number()). ARG1 is the argument
-- for the first stem and ARGN is the prefix of the arguments for the
-- remaining stems. For example, for the singular base, ARG1=1 and
-- ARGN="head"; for the first singular modifier, ARG1="mod" and
-- ARGN="modhead"; for the plural base, ARG1=ARGN="pl". The arguments
-- other than the first are numbered 2, 3, ..., which is appended to
-- ARGN. MOD is either "", "mod_", "mod2_", etc. depending if we're
-- working on a base or modifier argument. The returned value is an
-- array of stems, where each element is a size-two array of
-- {COMBINED_STEM, STEM_TYPE}. See do_gender_number().
function get_heads_1(data, args, arg1, argn, mod)
	if not args[arg1] then
		return {}
	end
	local heads
	if args[arg1] == "-" then
		heads = {{"", "-"}}
	else
		heads = {}
		insert_stems(args[arg1], heads, {{args[arg1], ""}}, false, "sg",
			get_pos(data, mod))
	end
	local i = 2
	while args[argn .. i] do
		local arg = args[argn .. i]
		insert_stems(arg, heads, {{arg, ""}}, false, "sg",
			get_pos(data, mod))
		i = i + 1
	end
	return heads
end

-- Very similar to do_gender_number(), and returns the same type of
-- structure, but works specifically for the stems of the head (the
-- most basic gender/number combiation, e.g. singular for nouns,
-- masculine singular for adjectives and gendered nouns, collective
-- for collective nouns, etc.), including both base and modifier.
-- See do_gender_number(). Note that the actual return value is
-- two items, the first of which is the same type of structure
-- returned by do_gender_number() and the second of which is a boolean
-- indicating whether we were called from within a template documentation
-- page (in which case no user-specified arguments exist and we
-- substitute sample ones). The reason for this boolean is to indicate
-- whether sample arguments need to be substituted for other numbers
-- as well.
function get_heads(data, args, headtype)
	if not args[1] and mw.title.getCurrentTitle().nsText == "Template" then
		return {base={{"{{{1}}}", "tri"}}}, true
	end

	if not args[1] then error("Parameter 1 (" .. headtype .. " stem) may not be empty.") end
	local base = get_heads_1(data, args, 1, "head", "")
	basemodtable = {base=base}
	for _, mod in ipairs(mod_list) do
		local modn = get_heads_1(data, args, mod, mod .. "head", mod .. "_")
		basemodtable[mod] = modn
	end
	return basemodtable, false
end

-- The main entry point for noun tables.
function export.show_noun(frame)
	local args, origargs, data = init(frame:getParent().args)
	data.pos = "noun"
	data.numgens = function() return data.numbers end
	data.allnumgens = data.allnumbers

	local sgs, is_template = get_heads(data, args, "singular")
	local pls = is_template and {base={{"{{{pl}}}", "tri"}}} or
		do_gender_number(data, args, {"pl", "cpl"}, sgs, nil, false, "pl")
	-- always do dual so cases like يَوْم الاِثْنَيْن work -- a singular with
	-- a dual modifier, where data.number refers only the singular
	-- but we need to go ahead and compute the dual so it parses the
	-- "modd" modifier dual argument. When the modifier dual argument
	-- is parsed, it will store the resulting dual declension for اِثْنَيْن
	-- in the modifier slot for all numbers, including specifically
	-- the singular.
	local dus = do_gender_number(data, args, {"d"}, sgs, "d", false, "du")

	parse_state_etc_spec(data, args)

	determine_noun_numbers(data, args, pls)

	do_inflections_and_overrides(data, args,
		{{sgs, "sg"}, {dus, "du"}, {pls, "pl"}})

	-- Make the table
	return make_noun_table(data)
end

function any_feminine(data, stem_spec)
	for basemod, stemtypelist in pairs(stem_spec) do
		-- Only check modifiers if modN_numgen= not given. If not given, the
		-- modifier needs to be declined for all numgens; else only for the
		-- given numgen, which should be explicitly specified.
		if not (basemod ~= "base" and data[basemod .. "_numgen"]) then
			for _, stemtype in ipairs(stemtypelist) do
				if rfind(stemtype[1], TAM .. UNUOPT .. "/") then
					return true
				end
			end
		end
	end
	return false
end

function all_feminine(data, stem_spec)
	for basemod, stemtypelist in pairs(stem_spec) do
		-- Only check modifiers if modN_numgen= not given. If not given, the
		-- modifier needs to be declined for all numgens; else only for the
		-- given numgen, which should be explicitly specified.
		if not (basemod ~= "base" and data[basemod .. "_numgen"]) then
			for _, stemtype in ipairs(stemtypelist) do
				if not rfind(stemtype[1], TAM .. UNUOPT .. "/") then
					return false
				end
			end
		end
	end
	return true
end

-- The main entry point for collective noun tables.
function export.show_coll_noun(frame)
	local args, origargs, data = init(frame:getParent().args)
	data.pos = "noun"
	data.allnumbers = {"coll", "sing", "du", "pauc", "pl"}
	data.engnumberscap["pl"] = "Plural of variety"
	data.numgens = function() return data.numbers end
	data.allnumgens = data.allnumbers

	local colls, is_template = get_heads(data, args, "collective")
	local pls = is_template and {base={{"{{{pl}}}", "tri"}}} or
		do_gender_number(data, args, {"pl", "cpl"}, colls, nil, false, "pl")

	parse_state_etc_spec(data, args)

	-- If collective noun is already feminine in form, don't try to
	-- form a feminine singulative
	local collfem = any_feminine(data, colls)

	local sings = do_gender_number(data, args, {"sing"}, colls,
		not already_feminine and "f" or nil, true, "sg")
	local singfem = all_feminine(data, sings)
	local dus = do_gender_number(data, args, {"d"}, sings, "d", singfem, "du")
	local paucs = do_gender_number(data, args, {"pauc"}, sings, "paucp",
		singfem, "pl")

	-- Can manually specify which numbers are to appear, and exactly those
	-- numbers will appear. Otherwise, if any plurals given, plurals appear,
	-- and if singulative given, dual and paucal appear.
	if not parse_number_spec(data, args) then
		data.numbers = {}
		if args[1] ~= "-" then
			table.insert(data.numbers, "coll")
		end
		if #sings["base"] > 0 then
			table.insert(data.numbers, "sing")
		end
		if #dus["base"] > 0 then
			table.insert(data.numbers, "du")
		end
		if #paucs["base"] > 0 then
			table.insert(data.numbers, "pauc")
		end
		if #pls["base"] > 0 then
			table.insert(data.numbers, "pl")
		end
	end

	-- Generate the collective, singulative, dual, paucal and plural forms
	do_inflections_and_overrides(data, args,
		{{colls, "coll"}, {sings, "sing"}, {dus, "du"}, {paucs, "pauc"}, {pls, "pl"}})

	-- Make the table
	return make_noun_table(data)
end

-- The main entry point for singulative noun tables.
function export.show_sing_noun(frame)
	local args, origargs, data = init(frame:getParent().args)
	data.pos = "noun"
	data.allnumbers = {"sing", "coll", "du", "pauc", "pl"}
	data.engnumberscap["pl"] = "Plural of variety"
	data.numgens = function() return data.numbers end
	data.allnumgens = data.allnumbers

	parse_state_etc_spec(data, args)

	local sings, is_template = get_heads(data, args, "singulative")

	-- If all singulative nouns feminine in form, form a masculine collective
	local singfem = all_feminine(data, sings)

	local colls = do_gender_number(data, args, {"coll"}, sings,
		singfem and "m" or nil, false, "sg")
	local dus = do_gender_number(data, args, {"d"}, sings, "d", singfem, "du")
	local paucs = do_gender_number(data, args, {"pauc"}, sings, "paucp",
		singfem, "pl")
	local pls = is_template and {base={{"{{{pl}}}", "tri"}}} or
		do_gender_number(data, args, {"pl", "cpl"}, colls, nil, false, "pl")

	-- Can manually specify which numbers are to appear, and exactly those
	-- numbers will appear. Otherwise, if any plurals given, plurals appear;
	-- if singulative given or derivable, it and dual and paucal will appear.
	if not parse_number_spec(data, args) then
		data.numbers = {}
		if args[1] ~= "-" then
			table.insert(data.numbers, "sing")
		end
		if #colls["base"] > 0 then
			table.insert(data.numbers, "coll")
		end
		if #dus["base"] > 0 then
			table.insert(data.numbers, "du")
		end
		if #paucs["base"] > 0 then
			table.insert(data.numbers, "pauc")
		end
		if #pls["base"] > 0 then
			table.insert(data.numbers, "pl")
		end
	end

	-- Generate the singulative, collective, dual, paucal and plural forms
	do_inflections_and_overrides(data, args,
		{{sings, "sing"}, {colls, "coll"}, {dus, "du"}, {paucs, "pauc"}, {pls, "pl"}})

	-- Make the table
	return make_noun_table(data)
end

-- The implementation of the main entry point for adjective and
-- gendered noun tables.
function show_gendered(frame, isadj, pos)
	local args, origargs, data = init(frame:getParent().args)
	data.pos = pos
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

	parse_state_etc_spec(data, args)

	local msgs = get_heads(data, args, 'masculine singular')
	-- Always do all of these so cases like يَوْم الاِثْنَيْن work.
	-- See comment in show_noun().
	local fsgs = do_gender_number(data, args, {"f"}, msgs, "f", true, "sg")
	local mdus = do_gender_number(data, args, {"d"}, msgs, "d", false, "du")
	local fdus = do_gender_number(data, args, {"fd"}, fsgs, "d", true, "du")
	local mpls = do_gender_number(data, args, {"pl", "cpl"}, msgs,
		isadj and "p" or nil, false, "pl")
	local fpls = do_gender_number(data, args, {"fpl", "cpl"}, fsgs, "fp",
		true, "pl")

	if isadj then
		parse_number_spec(data, args)
	else
		determine_noun_numbers(data, args, mpls)
	end

	-- Generate the singular, dual and plural forms
	do_inflections_and_overrides(data, args,
		{{msgs, "m_sg"}, {fsgs, "f_sg"}, {mdus, "m_du"}, {fdus, "f_du"},
		 {mpls, "m_pl"}, {fpls, "f_pl"}})

	-- Make the table
	if isadj then
		return make_adj_table(data)
	else
		return make_gendered_noun_table(data)
	end
end

-- The main entry point for gendered noun tables.
function export.show_gendered_noun(frame)
	return show_gendered(frame, false, "noun")
end

-- The main entry point for numeral tables. Same as using show_gendered_noun()
-- with pos=numeral.
function export.show_numeral(frame)
	return show_gendered(frame, false, "numeral")
end

-- The main entry point for adjective tables.
function export.show_adj(frame)
	return show_gendered(frame, true, "adjective")
end

-- Inflection functions

function do_translit(term)
	return lang:transliterate(term) or track("cant-translit") and BOGUS_CHAR
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

-- Combine PREFIX, AR/TR, and ENDING in that order. PREFIX and ENDING
-- can be of the form ARABIC/TRANSLIT. The Arabic and translit parts are
-- separated out and grouped together, resulting in a string of the
-- form ARABIC/TRANSLIT (TRANSLIT will always be present, computed
-- automatically if not present in the source). The return value is actually a
-- list of ARABIC/TRANSLIT strings because hamza resolution is applied to
-- ARABIC, which may produce multiple outcomes (all of which will have the
-- same TRANSLIT).
function combine_with_ending(prefix, ar, tr, ending)
	local prefixar, prefixtr = split_arabic_tr(prefix)
	local endingar, endingtr = split_arabic_tr(ending)
	-- When calling hamza_seat(), leave out prefixes, which we expect to be
	-- clitics like وَ. (In case the prefix is a separate word, it won't matter
	-- whether we include it in the text passed to hamza_seat().)
	allar = hamza_seat(ar .. endingar)
	-- Convert ...īān to ...iyān in case of stems ending in -ī or -ū
	-- (e.g. kubrī "bridge").
	if rfind(endingtr, "^[aeiouāēīōū]") then
		if rfind(tr, "ī$") then
			tr = rsub(tr, "ī$", "iy")
		elseif rfind(tr, "ū$") then
			tr = rsub(tr, "ū$", "uw")
		end
	end
	tr = prefixtr .. tr .. endingtr
	allartr = {}
	for _, arval in ipairs(allar) do
		table.insert(allartr, prefixar .. arval .. "/" .. tr)
	end
	return allartr
end

-- Combine PREFIX, STEM/TR and ENDING in that order and insert into the
-- list of items in DATA[KEY], initializing it if empty and making sure
-- not to insert duplicates. ENDING can be a list of endings, will be
-- distributed over the remaining parts. PREFIX and/or ENDING can be
-- of the form ARABIC/TRANSLIT (the stem is already split into Arabic STEM
-- and Latin TR). Note that what's inserted into DATA[KEY] is actually a
-- list of ARABIC/TRANSLIT strings; if more than one is present in the list,
-- they represent hamza variants, i.e. different ways of writing a hamza
-- sound, such as مُبْتَدَؤُون vs. مُبْتَدَأُون (see init_data()).
function add_inflection(data, key, prefix, stem, tr, ending)
	if data.forms[key] == nil then
		data.forms[key] = {}
	end
	if type(ending) ~= "table" then
		ending = {ending}
	end
	for _, endingval in ipairs(ending) do
		insert_if_not(data.forms[key],
			combine_with_ending(prefix, stem, tr, endingval))
	end
end

-- Form inflections from combination of STEM, with transliteration TR,
-- and ENDINGS (and definite article where necessary, plus any specified
-- prefixes) and store in DATA, for the number or gender/number
-- determined by MOD ("", "mod_", "mod2_", etc.; see call_inflection()) and
-- NUMGEN ("sg", "du", "pl", or "m_sg", "f_pl", etc. for adjectives). ENDINGS
-- is an array of 15 values, each of which is a string or array of
-- alternatives. The order of ENDINGS is indefinite nom, acc, gen; definite
-- nom, acc, gen; construct-state nom, acc, gen; informal indefinite, definite,
-- construct; lemma indefinite, definite, construct. (Normally the lemma is
-- based off of the indefinite, but if the inflection has been restricted to
-- particular states, it comes from one of those states, in the order
-- indefinite, definite, construct.) See also add_inflection() for more info
-- on exactly what is inserted into DATA.
function add_inflections(stem, tr, data, mod, numgen, endings)
	stem = canon_hamza(stem)
	assert(#endings == 15)
	local ismod = mod ~= ""
	-- If working on modifier and modN_numgen= is given, it better agree with
	-- NUMGEN; the case where it doesn't agree should have been caught in
	-- call_inflections().
	if ismod and data[mod .. "numgen"] then
		assert(data[mod .. "numgen"] == numgen)
	end
	-- Return a list of combined of ar/tr forms, with the ending tacked on.
	-- There may be more than one form because of alternative hamza seats that
	-- may be supplied, e.g. مُبْتَدَؤُون or مُبْتَدَأُون (mubtadaʾūn "(grammatical) subjects").
	local defstem, deftr
	if stem == "?" or data[mod .. "omitarticle"] then
		defstem = stem
		deftr = tr
	else
		defstem = "ال" .. stem
		-- apply sun-letter assimilation
		deftr = rsub("al-" .. tr, "^al%-([sšṣtṯṭdḏḍzžẓnrḷ])", "a%1-%1")
	end
	
	-- For a given MOD spec, is the previous word (base or modifier) a noun?
	-- We assume the base is always a noun in this case, and otherwise
	-- look at the value of modN_idafa.
	local function prev_mod_is_noun(mod)
		if mod == "mod_" then
			return true
		end
		if mod == "mod2_" then
			return data["mod_idafa"]
		end
		modnum = assert_rsub(mod, "^mod([0-9]+)_$", "%1")
		modnum = modnum - 1
		return data["mod" .. modnum .. "_idafa"]
	end

	local numgens = ismod and data[mod .. "numgen"] and data.numgens() or {numgen}
	-- "defcon" means definite adjective modifying construct state noun. We
	-- add a ... before the adjective (and after the construct-state noun) to
	-- indicate that a nominal modifier would go between noun and adjective.
	local stems = {ind = stem, def = defstem, con = stem,
	  defcon = "... " .. defstem}
	local trs = {ind = tr, def = deftr, con = tr, defcon = "... " .. deftr}
	for _, ng in ipairs(numgens) do
		for _, state in ipairs(data.allstates) do
			for _, case in ipairs(data.allcases_with_lemma) do
				-- We are generating the inflections for STATE, but sometimes
				-- we want to use the inflected form of a different state, e.g.
				-- if modN_state= or basestate= is set to some particular state.
				-- If we're dealing with an adjectival modifier, then in
				-- place of "con" we use "defcon" if immediately after a noun
				-- (see comment above), else "def".
				local thestate = ismod and data[mod .. "state"] or
					ismod and not data[mod .. "idafa"] and state == "con" and
				  		(prev_mod_is_noun(mod) and "defcon" or "def") or
					not ismod and data.basestate or
					state
				local is_lemmainf = case == "lemma" or case == "inf"
				-- Don't substitute value of modcase for lemma/informal "cases"
				local thecase = is_lemmainf and case or
					ismod and data[mod .. "case"] or case
				add_inflection(data, mod .. case .. "_" .. ng .. "_" .. state,
					data[mod .. "prefix"] or "",
					stems[thestate], trs[thestate],
					endings[data.statecases[thestate][thecase]])
			end
		end
	end
end	

-- Insert into a category and a type variable (e.g. m_sg_type) for the
-- declension type of a particular declension (e.g. masculine singular for
-- adjectives). MOD and NUMGEN are as in call_inflection(). CATVALUE is the
-- category and ENGVALUE is the English description of the declension type.
-- In these values, NOUN is replaced with either "noun" or "adjective",
-- SINGULAR is replaced with the English equivalent of the number in NUMGEN
-- (e.g. "singular", "dual" or "plural") while BROKSING is the same but uses
-- "broken plural" in place of "plural" and "broken paucal" in place of
-- "paucal".
function insert_cat(data, mod, numgen, catvalue, engvalue)
	local singpl = data.engnumbers[rsub(numgen, "^.*_", "")]
	assert(singpl ~= nil)
	local broksingpl = rsub(singpl, "plural", "broken plural")
	broksingpl = rsub(broksingpl, "paucal", "broken paucal")
	if rfind(broksingpl, "broken plural") and (rfind(catvalue, "BROKSING") or
			rfind(engvalue, "BROKSING")) then
		table.insert(data.categories, "Arabic " .. data.pos .. "s with broken plural")
	end
	if rfind(catvalue, "irregular") or rfind(engvalue, "irregular") then
		table.insert(data.categories, "Arabic irregular " .. data.pos .. "s")
	end
	catvalue = rsub(catvalue, "NOUN", data.pos)
	catvalue = rsub(catvalue, "SINGULAR", singpl)
	catvalue = rsub(catvalue, "BROKSING", broksingpl)
	engvalue = rsub(engvalue, "NOUN", data.pos)
	engvalue = rsub(engvalue, "SINGULAR", singpl)
	engvalue = rsub(engvalue, "BROKSING", broksingpl)
	if mod == "" and catvalue ~= "" then
		insert_if_not(data.categories, catvalue)
	end
	if engvalue ~= "" then
		local key = mod .. numgen .. "_type"
		if data.forms[key] == nil then
			data.forms[key] = {}
		end
		insert_if_not(data.forms[key], engvalue)
	end
end

-- Return true if we're handling modifier inflections and the modifier's
-- case is limited to an oblique case (gen or acc; typically genitive,
-- in an ʾidāfa construction). This is used when returning lemma
-- inflections -- the modifier part of the lemma should agree in case
-- with modifier's case if it's restricted in case.
function mod_oblique(mod, data)
	return mod ~= "" and data[mod .. "case"] and (
		data[mod .. "case"] == "acc" or data[mod .. "case"] == "gen")
end

-- Similar to mod_oblique but specifically when the modifier case is
-- limited to the accusative (which is rare or nonexistent in practice).
function mod_acc(mod, data)
	return mod ~= "" and data[mod .. "case"] and data[mod .. "case"] == "acc"
end

-- Handle triptote and diptote inflections
function triptote_diptote(stem, tr, data, mod, numgen, is_dip, lc)
	-- Remove any case ending
	if rfind(stem, "[" .. UN .. U .. "]$") then
		stem = rsub(stem, "[" .. UN .. U .. "]$", "")
		tr = rsub(tr, "un?$", "")
	end

	-- special-case for صلوة pronounced ṣalāh; check translit
	local is_aah = rfind(stem, TAM .. "$") and rfind(tr, "āh$")

	if rfind(stem, TAM .. "$") then
		if rfind(tr, "h$") then
			tr = rsub(tr, "h$", "t")
		elseif not rfind(tr, "t$") then
			tr = tr .. "t"
		end
	end

	add_inflections(stem, tr, data, mod, numgen,
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
	-- since we're checking translit for -āh we probably don't need to
	-- check stem too
	if is_aah or rfind(stem, "[" .. AMAD .. ALIF .. "]" .. TAM .. "$") then
		add_inflections(stem, rsub(tr, "t$", ""), data, mod, numgen,
			{{}, {}, {},
			 {}, {}, {},
			 {}, {}, {},
			 "/t", "/t", "/t", -- informal pron. is -āt
			 "/h", "/h", "/t", -- lemma uses -āh
			})
		insert_cat(data, mod, numgen, cat_prefix .. " in -āh",
			singpl_tote .. " in " .. make_link(HYPHEN .. AAH))
	elseif rfind(stem, TAM .. "$") then
		add_inflections(stem, rsub(tr, "t$", ""), data, mod, numgen,
			{{}, {}, {},
			 {}, {}, {},
			 {}, {}, {},
			 "", "", "/t",
			 "", "", "/t",
			})
		insert_cat(data, mod, numgen, cat_prefix .. " in -a",
			singpl_tote .. " in " .. make_link(HYPHEN .. AH))
	elseif lc then
		add_inflections(stem, tr, data, mod, numgen,
			{{}, {}, {},
			 {}, {}, {},
			 {}, {}, {},
			 "", "", UU,
			 "", "", UU,
			})
		insert_cat(data, mod, numgen, cat_prefix,
			singpl_tote)
	else
		-- also special-case the nisba ending, which has an informal
		-- pronunciation.
		if rfind(stem, IY .. SH .. "$") then
			local infstem = rsub(stem, SH .. "$", "")
			local inftr = rsub(tr, "iyy$", "ī")
			-- add informal and lemma inflections separately
			add_inflections(infstem, inftr, data, mod, numgen,
				{{}, {}, {},
				 {}, {}, {},
				 {}, {}, {},
				 "", "", "",
				 {}, {}, {},
				})
			add_inflections(stem, tr, data, mod, numgen,
				{{}, {}, {},
				 {}, {}, {},
				 {}, {}, {},
				 {}, {}, {},
				 "", "", "",
				})
		else
			add_inflections(stem, tr, data, mod, numgen,
				{{}, {}, {},
				 {}, {}, {},
				 {}, {}, {},
				 "", "", "",
				 "", "", "",
				})
		end
		insert_cat(data, mod, numgen, "Arabic NOUNs with basic " .. tote .. " BROKSING",
			"basic " .. singpl_tote)
	end
end

-- Regular triptote
inflections["tri"] = function(stem, tr, data, mod, numgen)
	triptote_diptote(stem, tr, data, mod, numgen, false)
end

-- Regular diptote
inflections["di"] = function(stem, tr, data, mod, numgen)
	triptote_diptote(stem, tr, data, mod, numgen, true)
end

-- Elative and color/defect adjective: usually same as diptote,
-- might be invariable
function elative_color_defect(stem, tr, data, mod, numgen)
	if rfind(stem, "[" .. ALIF .. AMAQ .. "]$") then
		invariable(stem, tr, data, mod, numgen)
	else
		triptote_diptote(stem, tr, data, mod, numgen, true)
	end
end

-- Elative: usually same as diptote, might be invariable
inflections["el"] = function(stem, tr, data, mod, numgen)
	elative_color_defect(stem, tr, data, mod, numgen)
end

-- Color/defect adjective: Same as elative
inflections["cd"] = function(stem, tr, data, mod, numgen)
	elative_color_defect(stem, tr, data, mod, numgen)
end

-- Triptote with lengthened ending in the construct state
inflections["lc"] = function(stem, tr, data, mod, numgen)
	triptote_diptote(stem, tr, data, mod, numgen, false, true)
end

function in_defective(stem, tr, data, mod, numgen, tri)
	if not rfind(stem, IN .. "$") then
		error("'in' declension stem should end in -in: '" .. stem .. "'")
	end

	stem = rsub(stem, IN .. "$", "")
	tr = rsub(tr, "in$", "")

	local acc_ind_ending = tri and IY .. AN .. ALIF or IY .. A
	add_inflections(stem, tr, data, mod, numgen,
		{IN, acc_ind_ending, IN,
		 II, IY .. A, II,
		 II, IY .. A, II,
		 II, II, II,
		 -- FIXME: What should happen with the lemma when modifier case
		 -- is limited to the accusative and modifier state is e.g. definite?
		 -- Should the lemma end in -iya or -ī? In practice this will rarely
		 -- if ever happen.
		 mod_acc(mod, data) and acc_ind_ending or IN, II, II,
		})
	local tote = tri and "triptote" or "diptote"

	insert_cat(data, mod, numgen, "Arabic NOUNs with " .. tote .. " BROKSING in -in",
		"BROKSING " .. tote .. " in " .. make_link(HYPHEN .. IN))
end

function detect_in_type(stem, ispl)
	if ispl and rfind(stem, "^" .. CONS .. AOPT .. CONS .. AOPTA .. CONS .. IN .. "$") then -- layālin
		return "diin"
	else -- other -in words
		return "triin"
	end
end

-- Defective in -in
inflections["in"] = function(stem, tr, data, mod, numgen)
	in_defective(stem, tr, data, mod, numgen,
		detect_in_type(stem, rfind(numgen, "pl")) == "triin")
end

-- Defective in -in, force "triptote" variant
inflections["triin"] = function(stem, tr, data, mod, numgen)
	in_defective(stem, tr, data, mod, numgen, true)
end

-- Defective in -in, force "diptote" variant
inflections["diin"] = function(stem, tr, data, mod, numgen)
	in_defective(stem, tr, data, mod, numgen, false)
end

-- Defective in -an (comes in two variants, depending on spelling with tall alif or alif maqṣūra)
inflections["an"] = function(stem, tr, data, mod, numgen)
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
		add_inflections(stem, tr, data, mod, numgen,
			{AN .. ALIF, AN .. ALIF, AN .. ALIF,
			 AA, AA, AA,
			 AA, AA, AA,
			 AA, AA, AA,
			 AN .. ALIF, AA, AA,
			})
	else
		add_inflections(stem, tr, data, mod, numgen,
			{AN .. AMAQ, AN .. AMAQ, AN .. AMAQ,
			 AAMAQ, AAMAQ, AAMAQ,
			 AAMAQ, AAMAQ, AAMAQ,
			 AAMAQ, AAMAQ, AAMAQ,
			 AN .. AMAQ, AAMAQ, AAMAQ,
			})
	end

	-- FIXME: Should we distinguish between tall alif and alif maqṣūra?
	insert_cat(data, mod, numgen, "Arabic NOUNs with BROKSING in -an",
		"BROKSING in " .. make_link(HYPHEN .. AN .. (tall_alif and ALIF or AMAQ)))
end

function invariable(stem, tr, data, mod, numgen)
	add_inflections(stem, tr, data, mod, numgen,
		{"", "", "",
		 "", "", "",
		 "", "", "",
		 "", "", "",
		 "", "", "",
		})
	
	insert_cat(data, mod, numgen, "Arabic NOUNs with invariable BROKSING",
		"BROKSING invariable")
end

-- Invariable in -ā (non-loanword type)
inflections["inv"] = function(stem, tr, data, mod, numgen)
	invariable(stem, tr, data, mod, numgen)
end

-- Invariable in -ā (loanword type, behaving in the dual as if ending in -a, I think!)
inflections["lwinv"] = function(stem, tr, data, mod, numgen)
	invariable(stem, tr, data, mod, numgen)
end

-- Duals
inflections["d"] = function(stem, tr, data, mod, numgen)
	if rfind(stem, ALIF .. NI .. "?$") then
		stem = rsub(stem, AOPTA .. NI .. "?$", "")
	elseif rfind(stem, AMAD .. NI .. "?$") then
		stem = rsub(stem, AMAD .. NI .. "?$", HAMZA_PH)
	else
		error("Dual stem should end in -ān(i): '" .. stem .. "'")
	end
	tr = rsub(tr, "āni?$", "")
	local mo = mod_oblique(mod, data)
	add_inflections(stem, tr, data, mod, numgen,
		{AANI, AYNI, AYNI,
		 AANI, AYNI, AYNI,
		 AA, AYSK, AYSK,
		 AYN, AYN, AYSK,
		 mo and AYN or AAN, mo and AYN or AAN, mo and AYSK or AA,
		})
	insert_cat(data, mod, numgen, "", "dual in " .. make_link(HYPHEN .. AANI))
end

-- Sound masculine plural
inflections["smp"] = function(stem, tr, data, mod, numgen)
	if not rfind(stem, UUNA .. "?$") then
		error("Sound masculine plural stem should end in -ūn(a): '" .. stem .. "'")
	end
	stem = rsub(stem, UUNA .. "?$", "")
	tr = rsub(tr, "ūna?$", "")
	local mo = mod_oblique(mod, data)
	add_inflections(stem, tr, data, mod, numgen,
		{UUNA, IINA, IINA,
		 UUNA, IINA, IINA,
		 UU,   II,   II,
		 IIN,  IIN,  II,
		 mo and IIN or UUN, mo and IIN or UUN, mo and II or UU,
		})
	-- use SINGULAR because conceivably this might be used with the paucal
	-- instead of plural
	insert_cat(data, mod, numgen, "Arabic NOUNs with sound masculine SINGULAR",
		"sound masculine SINGULAR")
end

-- Sound feminine plural
inflections["sfp"] = function(stem, tr, data, mod, numgen)
	if not rfind(stem, "[" .. ALIF .. AMAD .. "]" .. T .. UN .. "?$") then
		error("Sound feminine plural stem should end in -āt(un): '" .. stem .. "'")
	end
	stem = rsub(stem, UN .. "$", "")
	tr = rsub(tr, "un$", "")
	add_inflections(stem, tr, data, mod, numgen,
		{UN, IN, IN,
		 U,  I,  I,
		 U,  I,  I,
		 "", "", "",
		 "", "", "",
		})
	-- use SINGULAR because this might be used with the paucal
	-- instead of plural
	insert_cat(data, mod, numgen, "Arabic NOUNs with sound feminine SINGULAR",
		"sound feminine SINGULAR")
end

-- Plural of defective in -an
inflections["awnp"] = function(stem, tr, data, mod, numgen)
	if not rfind(stem, AWNA .. "?$") then
		error("'awnp' plural stem should end in -awn(a): '" .. stem .. "'")
	end
	stem = rsub(stem, AWNA .. "?$", "")
	tr = rsub(tr, "awna?$", "")
	local mo = mod_oblique(mod, data)
	add_inflections(stem, tr, data, mod, numgen,
		{AWNA, AYNA, AYNA,
		 AWNA, AYNA, AYNA,
		 AWSK, AYSK, AYSK,
		 AYN, AYN, AYSK,
		 mo and AYN or AWN, mo and AYN or AWN, mo and AYSK or AWSK,
		})
	-- use SINGULAR because conceivably this might be used with the paucal
	-- instead of plural
	insert_cat(data, mod, numgen, "Arabic NOUNs with sound SINGULAR in -awna",
		"sound SINGULAR in " .. make_link(HYPHEN .. AWNA))
end

-- Unknown
inflections["?"] = function(stem, tr, data, mod, numgen)
	add_inflections("?", "?", data, mod, numgen,
		{"", "", "",
		 "", "", "",
		 "", "", "",
		 "", "", "",
		 "", "", "",
		})
	
	insert_cat(data, mod, numgen, "Arabic NOUNs with unknown SINGULAR",
		"SINGULAR unknown")
end

-- Detect declension of noun or adjective stem or lemma. We allow triptotes,
-- diptotes and sound plurals to either come with ʾiʿrāb or not. We detect
-- some cases where vowels are missing, when it seems fairly unambiguous to
-- do so. ISFEM is true if we are dealing with a feminine stem (not
-- currently used and needs to be rethought). NUM is "sg", "du", or "pl",
-- depending on the number of the stem.
--
-- POS is the part of speech, generally "noun" or "adjective". Used to
-- distinguish nouns and adjectives of the فَعْلَان type. There are nouns of
-- this type and they generally are triptotes, e.g. قَطْرَان "tar"
-- and شَيْطَان "devil". An additional complication is that the user can set
-- the POS to something else, like "numeral". We don't use this POS for
-- modifiers, where we determine whether they are noun-like or adjective-like
-- according to whether mod_idafa= is true.
--
-- Some unexpectedly diptote nouns/adjectives:
--
-- jiʿrān in ʾabū jiʿrān "dung beetle"
-- distributive numbers: ṯunāʾ "two at a time", ṯulāṯ/maṯlaṯ "three at a time",
--   rubāʿ "four at a time" (not a regular diptote pattern, cf. triptote
--   junāḥ "misdemeanor, sin", nujār "origin, root", nuḥām "flamingo")
-- jahannam (f.) "hell"
-- many names: jilliq/jillaq "Damascus", judda/jidda "Jedda", jibrīl (and
--   variants) "Gabriel", makka "Mecca", etc.
-- jibriyāʾ "pride"
-- kibriyāʾ "glory, pride"
-- babbaḡāʾ "parrot"
-- ʿayāyāʾ "incapable, tired"
-- suwaidāʾ "black bile, melancholy"
-- Note also: ʾajhar "day-blind" (color-defect) and ʾajhar "louder" (elative)
function export.detect_type(stem, isfem, num, pos)
	local function dotrack(word)
		track(word)
		track(word .. "/" .. pos)
		return true
	end
	-- Not strictly necessary because the caller (stem_and_type) already
	-- reorders, but won't hurt, and may be necessary if this function is
	-- called from an external caller.
	stem = reorder_shadda(stem)
	local origstem = stem
	-- So that we don't get tripped up by alif madda, we replace alif madda
	-- with the sequence hamza + fatḥa + alif before the regexps below.
	stem = rsub(stem, AMAD, HAMZA .. AA)
	if num == "du" then
		if rfind(stem, ALIF .. NI .. "?$") then
			return "d"
		else
			error("Malformed stem for dual, should end in the nominative dual ending -ān(i): '" .. origstem .. "'")
		end
	end
	if rfind(stem, IN .. "$") then -- -in words
		return detect_in_type(stem, num == "pl")
	elseif rfind(stem, AN .. "[" .. ALIF .. AMAQ .. "]$") then
		return "an"
	elseif rfind(stem, AN .. "$") then
		error("Malformed stem, fatḥatan should be over second-to-last letter: " .. origstem)
	elseif num == "pl" and rfind(stem, AW .. SKOPT .. N .. AOPT .. "$") then
		return "awnp"
	elseif num == "pl" and rfind(stem, ALIF .. T .. UNOPT .. "$") and
		-- Avoid getting tripped up by plurals like ʾawqāt "times",
		-- ʾaḥwāt "fishes", ʾabyāt "verses", ʾazyāt "oils", ʾaṣwāt "voices",
		-- ʾamwāt "dead (pl.)".
		not rfind(stem, HAMZA_ON_ALIF .. A .. CONS .. SK .. CONS .. AAT .. UNOPT .. "$") then
		return "sfp"
	elseif num == "pl" and rfind(stem, W .. N .. AOPT .. "$") and
		-- Avoid getting tripped up by plurals like ʿuyūn "eyes",
		-- qurūn "horns" (note we check for U between first two consonants
		-- so we correctly ignore cases like sinūn "hours" (from sana),
		-- riʾūn "lungs" (from riʾa) and banūn "sons" (from ibn).
		not rfind(stem, "^" .. CONS .. U .. CONS .. UUN .. AOPT .. "$") then
		return "smp"
	elseif rfind(stem, UN .. "$") then -- explicitly specified triptotes (we catch sound feminine plurals above)
		return "tri"
	elseif rfind(stem, U .. "$") then -- explicitly specified diptotes
		return "di"
	elseif -- num == "pl" and
		( -- various diptote plural patterns; these are diptote even in the singular (e.g. yanāyir "January", falāfil "falafel", tuʾabāʾ "yawn, fatigue"
		  -- currently we sometimes end up with such plural patterns in the "singular" in a singular
		  -- ʾidāfa construction with plural modifier. (FIXME: These should be fixed to the correct number.)
		rfind(stem, "^" .. CONS .. AOPT .. CONS .. AOPTA .. CONS .. IOPT .. Y .. "?" .. CONS .. "$") and dotrack("fawaakih") or -- fawākih, daqāʾiq, makātib, mafātīḥ
		rfind(stem, "^" .. CONS .. AOPT .. CONS .. AOPTA .. CONS .. SH .. "$")
			and not rfind(stem, "^" .. T) and dotrack("mawaadd") or -- mawādd, maqāmm, ḍawāll; exclude t- so we don't catch form-VI verbal nouns like taḍādd (HACK!!!)
		rfind(stem, "^" .. CONS .. U .. CONS .. AOPT .. CONS .. AOPTA .. HAMZA .. "$") and dotrack("wuzaraa") or -- wuzarāʾ "ministers", juhalāʾ "ignorant (pl.)"
		rfind(stem, ELCD_START .. SKOPT .. CONS .. IOPT .. CONS .. AOPTA .. HAMZA .. "$") and dotrack("asdiqaa") or -- ʾaṣdiqāʾ
		rfind(stem, ELCD_START .. IOPT .. CONS .. SH .. AOPTA .. HAMZA .. "$") and dotrack("aqillaa") -- ʾaqillāʾ, ʾajillāʾ "important (pl.)", ʾaḥibbāʾ "lovers"
		) then
		return "di"
	elseif num == "sg" and ( -- diptote singular patterns (nouns/adjectives)
		rfind(stem, "^" .. CONS .. A .. CONS .. SK .. CONS .. AOPTA .. HAMZA .. "$") and dotrack("qamraa") or -- qamrāʾ "moon-white, moonlight"; baydāʾ "desert"; ṣaḥrāʾ "desert-like, desert"; tayhāʾ "trackless, desolate region"; not pl. to avoid catching e.g. ʾabnāʾ "sons", ʾaḥmāʾ "fathers-in-law", ʾamlāʾ "steppes, deserts" (pl. of malan), ʾanbāʾ "reports" (pl. of nabaʾ)
		rfind(stem, ELCD_START .. SK .. CONS .. A .. CONS .. "$") and dotrack("abyad") or -- ʾabyaḍ "white", ʾakbar "greater"; FIXME nouns like ʾaʿzab "bachelor", ʾaḥmad "Ahmed" but not ʾarnab "rabbit", ʾanjar "anchor", ʾabjad "abjad", ʾarbaʿ "four", ʾandar "threshing floor" (cf. diptote ʾandar "rarer")
		rfind(stem, ELCD_START .. A .. CONS .. SH .. "$") and dotrack("alaff") or -- ʾalaff "plump", ʾaḥabb "more desirable"
		-- do the following on the origstem so we can check specifically for alif madda
		rfind(origstem, "^" .. AMAD .. CONS .. A .. CONS .. "$") and dotrack("aalam") -- ʾālam "more painful", ʾāḵar "other"
		) then
		return "di"
	elseif num == "sg" and pos == "adjective" and ( -- diptote singular patterns (adjectives)
		rfind(stem, "^" .. CONS .. A .. CONS .. SK .. CONS .. AOPTA .. N .. "$") and dotrack("kaslaan") or -- kaslān "lazy", ʿaṭšān "thirsty", jawʿān "hungry", ḡaḍbān "angry", tayhān "wandering, perplexed"; but not nouns like qaṭrān "tar", šayṭān "devil", mawtān "plague", maydān "square"
		-- rfind(stem, "^" .. CONS .. A .. CONS .. SH .. AOPTA .. N .. "$") and dotrack("laffaa") -- excluded because of too many false positives e.g. ḵawwān "disloyal", not to mention nouns like jannān "gardener"; only diptote example I can find is ʿayyān "incapable, weary" (diptote per Lane but not Wehr)
		rfind(stem, "^" .. CONS .. A .. CONS .. SH .. AOPTA .. HAMZA .. "$") and dotrack("laffaa") -- laffāʾ "plump (fem.)"; but not nouns like jarrāʾ "runner", ḥaddāʾ "camel driver", lawwāʾ "wryneck"
		) then
		return "di"
	elseif rfind(stem, AMAQ .. "$") then -- kaslā, ḏikrā (spelled with alif maqṣūra)
		return "inv"
	elseif rfind(stem, "[" .. ALIF .. SK .. "]" .. Y .. AOPTA .. "$") then -- dunyā, hadāyā (spelled with tall alif after yāʾ)
		return "inv"
	elseif rfind(stem, ALIF .. "$") then -- kāmērā, lībiyā (spelled with tall alif; we catch dunyā and hadāyā above)
		return "lwinv"
	elseif rfind(stem, II .. "$") then -- cases like كُوبْرِي kubrī "bridge" and صَوَانِي ṣawānī pl. of ṣīniyya; modern words that would probably end with -in
		dotrack("ii")
		return "inv"
	elseif rfind(stem, UU .. "$") then -- FIXME: Does this occur? Check the tracking
		dotrack("uu")
		return "inv"
	else
		return "tri"
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
-- is present, it is a sound plural type ("sf", "sm" or "awn"),
-- in which case the stem and translit are generated from the singular by
-- regular rules. SG may be of the form ARABIC/TR or ARABIC. ISFEM is true
-- if WORD is a feminine stem. NUM is either "sg", "du" or "pl" according to
-- the number of the stem. The return value will be in the ARABIC/TR format.
--
-- POS is the part of speech, generally "noun" or "adjective". Used to
-- distinguish nouns and adjectives of the فَعْلَان type. There are nouns of
-- this type and they generally are triptotes, e.g. قَطْرَان "tar"
-- and شَيْطَان "devil". An additional complication is that the user can set
-- the POS to something else, like "numeral". We don't use this POS for
-- modifiers, where we determine whether they are noun-like or adjective-like
-- according to whether mod_idafa= is true.
function export.stem_and_type(word, sg, sgtype, isfem, num, pos)
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

	if (num ~= "sg" or not isfem) and (word == "elf" or word == "cdf" or word == "intf" or word == "rf" or word == "f") then
		error("Inference of form for inflection type '" .. word .. "' only allowed in singular feminine")
	end
	
	if num ~= "du" and word == "d" then
		error("Inference of form for inflection type '" .. word .. "' only allowed in dual")
	end
	
	if num ~= "pl" and (word == "sfp" or word == "smp" or word == "awnp" or word == "cdp" or word == "sp" or word == "fp" or word == "p") then
		error("Inference of form for inflection type '" .. word .. "' only allowed in plural")
	end

	local function is_intensive_adj(ar)
		return rfind(ar, "^" .. CONS .. A .. CONS .. SK .. CONS .. AOPTA .. N .. UOPT .. "$") or
			rfind(ar, "^" .. CONS .. A .. CONS .. SK .. AMAD .. N .. UOPT .. "$") or
			rfind(ar, "^" .. CONS .. A .. CONS .. SH .. AOPTA .. N .. UOPT .. "$")
	end
		
	local function is_feminine_cd_adj(ar)
		return pos == "adjective" and
			(rfind(ar, "^" .. CONS .. A .. CONS .. SK .. CONS .. AOPTA .. HAMZA .. UOPT .. "$") or -- ʾḥamrāʾ/ʿamyāʾ/bayḍāʾ
			rfind(ar, "^" .. CONS .. A .. CONS .. SH .. AOPTA .. HAMZA .. UOPT .. "$") -- laffāʾ
			)
	end

	local function is_elcd_adj(ar)
		return rfind(ar, ELCD_START .. SK .. CONS .. A .. CONS .. UOPT .. "$") or -- ʾabyaḍ "white", ʾakbar "greater"
			rfind(ar, ELCD_START .. A .. CONS .. SH .. UOPT .. "$") or -- ʾalaff "plump", ʾaqall "fewer"
			rfind(ar, ELCD_START .. SK .. CONS .. AAMAQ .. "$") or -- ʾaʿmā "blind", ʾadnā "lower"
			rfind(ar, "^" .. AMAD .. CONS .. A .. CONS .. UOPT .. "$") -- ʾālam "more painful", ʾāḵar "other"
	end

	if word == "?" or
			(rfind(word, "^[a-z][a-z]*$") and sgtype == "?") then
		--if 'word' is a type, actual value inferred from sg; if sgtype is ?,
		--propagate it to all derived types
		return "", "?"
	end

	if word == "intf" then
		if not is_intensive_adj(sgar) then
			error("Singular stem not in CACCān form: " .. sgar)
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
			sub(ELCD_START .. SK .. CONSPAR .. AAMAQ .. "$",
				"%1" .. U .. "%2" .. SK .. Y .. ALIF, "ʾa(.)(.)ā", "%1u%2yā") or -- ʾadnā
			sub("^" .. AMAD .. CONSPAR .. A .. CONSPAR .. UOPT .. "$",
				HAMZA_ON_ALIF .. U .. "%1" .. SK .. "%2" .. AMAQ, "ʾā(.)a(.)u?", "ʾu%1%2ā") -- ʾālam "more painful", ʾāḵar "other"
		)
		if not ret then
			error("Singular stem not an elative adjective: " .. sgar)
		end
		return ret, "inv"
	end

	if word == "cdf" then
		local ret = (
			sub(ELCD_START .. SK .. CONSPAR .. A .. CONSPAR .. UOPT .. "$",
				"%1" .. A .. "%2" .. SK .. "%3" .. AA .. HAMZA, "ʾa(.)(.)a(.)u?", "%1a%2%3āʾ") or -- ʾaḥmar
			sub(ELCD_START .. A .. CONSPAR .. SH .. UOPT .. "$",
				"%1" .. A .. "%2" .. SH .. AA .. HAMZA, "ʾa(.)a(.)%2u?", "%1a%2%2āʾ") or -- ʾalaff
			sub(ELCD_START .. SK .. CONSPAR .. AAMAQ .. "$",
				"%1" .. A .. "%2" .. SK .. Y .. AA .. HAMZA, "ʾa(.)(.)ā", "%1a%2yāʾ") -- ʾaʿmā
		)
		if not ret then
			error("Singular stem not a color/defect adjective: " .. sgar)
		end
		return ret, "cd" -- so plural will be correct
	end

	-- Regular feminine -- add ة, possibly with stem modifications
	if word == "rf" then
		sgar = canon_hamza(sgar)
	
		if rfind(sgar, TAM .. UNUOPT .. "$") then
			--Don't do this or we have problems when forming singulative from
			--collective with a construct modifier that's feminine
			--error("Singular stem is already feminine: " .. sgar)
			return sgar .. "/" .. sgtr, "tri"
		end

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
			return export.stem_and_type("cdf", sg, sgtype, true, "sg", pos)
		elseif sgtype == "el" then
			return export.stem_and_type("elf", sg, sgtype, true, "sg", pos)
		elseif sgtype =="di" and is_intensive_adj(sgar) then
			return export.stem_and_type("intf", sg, sgtype, true, "sg", pos)
		elseif sgtype == "di" and is_elcd_adj(sgar) then
			-- If form is elative or color-defect, we don't know which of
			-- the two it is, and each has a special feminine which isn't
			-- the regular "just add ة", so shunt to unknown. This will
			-- ensure that ?'s appear in place of the inflection -- also
			-- for dual and plural.
			return export.stem_and_type("?", sg, sgtype, true, "sg", pos)
		else
			return export.stem_and_type("rf", sg, sgtype, true, "sg", pos)
		end
	end

	if word == "rm" then
		sgar = canon_hamza(sgar)
	
		--Don't do this or we have problems when forming collective from
		--singulative with a construct modifier that's not feminine,
		--e.g. شَجَرَة التُفَّاح
		--if not rfind(sgar, TAM .. UNUOPT .. "$") then
		--	error("Singular stem is not feminine: " .. sgar)
		--end

		local ret = (
			sub(AAH .. UNUOPT .. "$", AN .. AMAQ, "ātun?$", "an", "ā[ht]$", "an") or -- in -āh
			sub(IY .. AH .. UNUOPT .. "$", IN, "iyatun?$", "in", "iya$", "in") or -- ends in -iya
			sub(AOPT .. TAM .. UNUOPT .. "$", "", "atun?$", "", "a$", "") or --ends in -a
			sub("$", "", "$", "") -- do nothing
		)
		return ret, "tri"
	end

	if word == "m" then
		-- FIXME: handle cd (color-defect)
		-- FIXME: handle el (elative)
		-- FIXME: handle int (intensive)
		return export.stem_and_type("rm", sg, sgtype, false, "sg", pos)
	end

	-- The plural used for feminine adjectives. If the singular type is
	-- color/defect or it looks like a feminine color/defect adjective,
	-- use color/defect plural. Otherwise shunt to sound feminine plural.
	if word == "fp" then
		if sgtype == "cd" or is_feminine_cd_adj(sgar) then
			return export.stem_and_type("cdp", sg, sgtype, true, "pl", pos)
		else
			return export.stem_and_type("sfp", sg, sgtype, true, "pl", pos)
		end
	end

	if word == "sp" then
		if sgtype == "cd" then
			return export.stem_and_type("cdp", sg, sgtype, isfem, "pl", pos)
		elseif isfem then
			return export.stem_and_type("sfp", sg, sgtype, true, "pl", pos)
		elseif sgtype == "an" then
			return export.stem_and_type("awnp", sg, sgtype, false, "pl", pos)
		else
			return export.stem_and_type("smp", sg, sgtype, false, "pl", pos)
		end
	end

	-- Conservative plural, as used for masculine plural adjectives.
	-- If singular type is color-defect, shunt to color-defect plural; else
	-- shunt to unknown, so ? appears in place of the inflections.
	if word == "p" then
		if sgtype == "cd" then
			return export.stem_and_type("cdp", sg, sgtype, isfem, "pl", pos)
		else
			return export.stem_and_type("?", sg, sgtype, isfem, "pl", pos)
		end
	end

	-- Special plural used for paucal plurals of singulatives. If ends in -ة
	-- (most common), use strong feminine plural; if ends with -iyy (next
	-- most common), use strong masculine plural; ends default to "p"
	-- (conservative plural).
	if word == "paucp" then
		if rfind(sgar, TAM .. UNUOPT .. "$") then
			return export.stem_and_type("sfp", sg, sgtype, true, "pl", pos)
		elseif rfind(sgar, IY .. SH .. UNUOPT .. "$") then
			return export.stem_and_type("smp", sg, sgtype, false, "pl", pos)
		else
			return export.stem_and_type("p", sg, sgtype, isfem, "pl", pos)
		end
	end

	if word == "d" then
		sgar = canon_hamza(sgar)
		local ret = (
			sub(AN .. "[" .. ALIF .. AMAQ .. "]$", AY .. AAN, "an$", "ayān") or -- ends in -an
			sub(IN .. "$", IY .. AAN, "in$", "iyān") or -- ends in -in
			sgtype == "lwinv" and sub(AOPTA .. "$", AT .. AAN, "[āa]$", "atān") or -- lwinv, ends in alif; allow translit with short -a
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

	-- Strong feminine plural in -āt, possibly with stem modifications
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
				sub(AOPTA .. "$", AAT, "[āa]$", "āt") -- loanword ending in tall alif; allow translit with short -a
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

	-- Color/defect plural; singular must be masculine or feminine
	-- color/defect adjective
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
			sub(ELCD_START .. SK .. CONSPAR .. AAMAQ .. "$",
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

	return artr, export.detect_type(ar, isfem, num, pos)
end

-- local outersep = " <small style=\"color: #888\">or</small> "
-- need LRM here so multiple Arabic plurals end up agreeing in order with
-- the transliteration
local outersep = LRM .. "; "
local innersep = LRM .. "/"

-- Subfunction of show_form(), used to implement recursively generating
-- all combinations of elements from FORM and from each of the items in
-- LIST_OF_MODS, both of which are either arrays of strings or arrays of
-- arrays of strings, where the strings are in the form ARABIC/TRANSLIT,
-- as described in show_form(). TRAILING_ARTRMODS is an array of ARTRMOD
-- items, each of which is a two-element array of ARMOD (Arabic) and TRMOD
-- (transliteration), accumulating all of the suffixes generated so far
-- in the recursion process. Each time we recur we take the last MOD item
-- off of LIST_OF_MODS, separate each element in MOD into its Arabic and
-- Latin parts and to each Arabic/Latin pair we add all elements in
-- TRAILING_ARTRMODS, passing the newly generated list of ARTRMOD items
-- down the next recursion level with the shorter LIST_OF_MODS. We end up
-- returning a string to insert into the Wiki-markup table.
function show_form_1(form, list_of_mods, trailing_artrmods, use_parens)
	if #list_of_mods == 0 then
		local arabicvals = {}
		local latinvals = {}
		local parenvals = {}
		
		-- Accumulate separately the Arabic and transliteration into
		-- ARABICVALS and LATINVALS, then concatenate each down below.
		-- However, if USE_PARENS, we put each transliteration directly
		-- after the corresponding Arabic, in parens, and put the results
		-- in PARENVALS, which get concatenated below. (This is used in the
		-- title of the declension table.)
		for _, artrmod in ipairs(trailing_artrmods) do
			assert(#artrmod == 2)
			local armod = artrmod[1]
			local trmod = artrmod[2]
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
						tr_subspan = (rfind(translit, BOGUS_CHAR) or rfind(trmod, BOGUS_CHAR)) and "?" or
							"<span style=\"color: #888\">" .. translit .. trmod .. "</span>"
						-- implement elision of al- after vowel
						tr_subspan = rsub(tr_subspan, "([aeiouāēīōū][ %-])a([sšṣtṯṭdḏḍzžẓnrḷl]%-)", "%1%2")
						tr_subspan = rsub(tr_subspan, "([aeiouāēīōū][ %-])a(llāh)", "%1%2")

						if arabic:find("{{{") then
							ar_subspan = m_links.full_link(nil, arabic .. armod, lang, nil, nil, nil, {tr = "-"}, false)
						else
							ar_subspan = m_links.full_link(arabic .. armod, nil, lang, nil, nil, nil, {tr = "-"}, false)
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
		end

		if use_parens then
			return table.concat(parenvals, outersep)
		else
			local arabic_span = table.concat(arabicvals, outersep)
			local latin_span = table.concat(latinvals, outersep)
			return arabic_span .. "<br />" .. latin_span
		end
	else
		local last_mods = table.remove(list_of_mods)
		local artrmods = {}
		for _, mod in ipairs(last_mods) do
			if type(mod) ~= "table" then
				mod = {mod}
			end
			for _, submod in ipairs(mod) do
				local armod, trmod = split_arabic_tr(submod)
				-- If the value is -, we need to create a blank entry
				-- rather than skipping it; if we have no entries at any
				-- level, then there will be no overall entries at all
				-- because the inside of the loop at the next level will
				-- never be executed.
				if armod == "-" then
					armod = ""
					trmod = ""
				end
				if armod ~= "" then armod = ' ' .. armod end
				if trmod ~= "" then trmod = ' ' .. trmod end
				for _, trailing_artrmod in ipairs(trailing_artrmods) do
					local trailing_armod = trailing_artrmod[1]
					local trailing_trmod = trailing_artrmod[2]
					armod = armod .. trailing_armod
					trmod = trmod .. trailing_trmod
					artrmod = {armod, trmod}
					table.insert(artrmods, artrmod)
				end
			end
		end
		return show_form_1(form, list_of_mods, artrmods, use_parens)
	end
end

-- Generate a string to substitute into a particular form in a Wiki-markup
-- table. FORM is the set of inflected forms corresponding to the base,
-- either an array of strings (referring e.g. to different possible plurals)
-- or an array of arrays of strings (the first level referring e.g. to
-- different possible plurals and the inner level referring typically to
-- hamza-spelling variants). LIST_OF_MODS is an array of MODS elements, one
-- per modifier. Each MODS element is the set of inflected forms corresponding
-- to the modifier and is of the same form as FORM, i.e. an array of strings
-- or an array of arrays of strings. Each string is typically of the form
-- "ARABIC/TRANSLIT", i.e. an Arabic string and a Latin string separated
-- by a slash. We loop over all possible combinations of elements from
-- each array; this requires recursion.
function show_form(form, list_of_mods, use_parens)
	if not form then
		return "&mdash;"
	elseif type(form) ~= "table" then
		error("a non-table value was given in the list of inflected forms.")
	end
	if #form == 0 then
		return "&mdash;"
	end

	-- We need to start the recursion with the third parameter containing
	-- one blank element rather than no elements, otherwise no elements
	-- will be propagated to the next recursion level.
	return show_form_1(form, list_of_mods, {{"", ""}}, use_parens)
end

-- Create a Wiki-markup table using the values in DATA and the template in
-- WIKICODE.
function make_table(data, wikicode)
	-- Function used as replace arg of call to rsub(). Replace the
	-- specified param with its (HTML) value. The param references appear
	-- as {{{PARAM}}} in the wikicode.
	local function repl(param)
		if param == "pos" then
			return data.pos
		elseif param == "info" then
			return data.title and " (" .. data.title .. ")" or ""
		elseif rfind(param, "type$") then
			return table.concat(data.forms[param] or {"&mdash;"}, outersep)
		else
			local list_of_mods = {}
			for _, mod in ipairs(mod_list) do
				local mods = data.forms[mod .. "_" .. param]
				if not mods or #mods == 0 then
					-- We need one blank element rather than no element,
					-- otherwise no elements will be propagated from one
					-- recursion level to the next.
					mods = {""}
				end
				table.insert(list_of_mods, mods)
			end
			return show_form(data.forms[param], list_of_mods, param == "lemma")
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

	return rsub(wikicode, "{{{([a-z_]+)}}}", repl) .. m_utilities.format_categories(data.categories, lang)
end

-- Generate part of the noun table for a given number spec NUM (e.g. sg)
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

	for _, num in ipairs(data.numbers) do
		if num == "du" then
			wikicode = wikicode .. [=[|-
! style="background: #CDCDCD;" | Dual
]=] .. generate_noun_num("du")
		else
			wikicode = wikicode .. [=[|-
! style="background: #CDCDCD;" rowspan=2 | ]=] .. data.engnumberscap[num] .. "\n" .. [=[
! style="background: #CDCDCD;" colspan=3 | {{{]=] .. num .. [=[_type}}}
|-
]=] .. generate_noun_num(num)
		end
	end
	wikicode = wikicode .. [=[|}
</div>
</div>]=]

	return make_table(data, wikicode)
end

-- Generate part of the gendered-noun table for a given numgen spec
-- NUM (e.g. m_sg)
function generate_gendered_noun_num(num)
	return [=[|-
! style="background: #CDCDCD;" | Indefinite
! style="background: #CDCDCD;" | Definite
! style="background: #CDCDCD;" | Construct
! style="background: #CDCDCD;" | Indefinite
! style="background: #CDCDCD;" | Definite
! style="background: #CDCDCD;" | Construct
|-
! style="background: #EFEFEF;" | Informal
| {{{inf_m_]=] .. num .. [=[_ind}}}
| {{{inf_m_]=] .. num .. [=[_def}}}
| {{{inf_m_]=] .. num .. [=[_con}}}
| {{{inf_f_]=] .. num .. [=[_ind}}}
| {{{inf_f_]=] .. num .. [=[_def}}}
| {{{inf_f_]=] .. num .. [=[_con}}}
|-
! style="background: #EFEFEF;" | Nominative
| {{{nom_m_]=] .. num .. [=[_ind}}}
| {{{nom_m_]=] .. num .. [=[_def}}}
| {{{nom_m_]=] .. num .. [=[_con}}}
| {{{nom_f_]=] .. num .. [=[_ind}}}
| {{{nom_f_]=] .. num .. [=[_def}}}
| {{{nom_f_]=] .. num .. [=[_con}}}
|-
! style="background: #EFEFEF;" | Accusative
| {{{acc_m_]=] .. num .. [=[_ind}}}
| {{{acc_m_]=] .. num .. [=[_def}}}
| {{{acc_m_]=] .. num .. [=[_con}}}
| {{{acc_f_]=] .. num .. [=[_ind}}}
| {{{acc_f_]=] .. num .. [=[_def}}}
| {{{acc_f_]=] .. num .. [=[_con}}}
|-
! style="background: #EFEFEF;" | Genitive
| {{{gen_m_]=] .. num .. [=[_ind}}}
| {{{gen_m_]=] .. num .. [=[_def}}}
| {{{gen_m_]=] .. num .. [=[_con}}}
| {{{gen_f_]=] .. num .. [=[_ind}}}
| {{{gen_f_]=] .. num .. [=[_def}}}
| {{{gen_f_]=] .. num .. [=[_con}}}
]=]
end

-- Make the gendered noun table
function make_gendered_noun_table(data)
	local wikicode = [=[<div class="NavFrame">
<div class="NavHead">Declension of {{{pos}}} {{{lemma}}}</div>
<div class="NavContent">
{| class="inflection-table" style="border-width: 1px; border-collapse: collapse; background:#F9F9F9; text-align:center; width:100%;"
]=]

	for _, num in ipairs(data.numbers) do
		if num == "du" then
			wikicode = wikicode .. [=[|-
! style="background: #CDCDCD;" rowspan=2 | Dual
! style="background: #CDCDCD;" colspan=3 | Masculine
! style="background: #CDCDCD;" colspan=3 | Feminine
]=] .. generate_gendered_noun_num("du")
		else
			wikicode = wikicode .. [=[|-
! style="background: #CDCDCD;" rowspan=3 | ]=] .. data.engnumberscap[num] .. "\n" .. [=[
! style="background: #CDCDCD;" colspan=3 | Masculine
! style="background: #CDCDCD;" colspan=3 | Feminine
|-
! style="background: #CDCDCD;" colspan=3 | {{{m_]=] .. num .. [=[_type}}}
! style="background: #CDCDCD;" colspan=3 | {{{f_]=] .. num .. [=[_type}}}
]=] .. generate_gendered_noun_num(num)
		end
	end
	wikicode = wikicode .. [=[|}
</div>
</div>]=]

	return make_table(data, wikicode)
end

-- Generate part of the adjective table for a given numgen spec NUM (e.g. m_sg)
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
]=] .. generate_adj_num("sg")
	end
	if contains(data.numbers, "du") then
		wikicode = wikicode .. [=[|-
! style="background: #CDCDCD;" rowspan=2 | Dual
! style="background: #CDCDCD;" colspan=2 | Masculine
! style="background: #CDCDCD;" colspan=2 | Feminine
]=] .. generate_adj_num("du")
	end
	if contains(data.numbers, "pl") then
		wikicode = wikicode .. [=[|-
! style="background: #CDCDCD;" rowspan=3 | Plural
! style="background: #CDCDCD;" colspan=2 | Masculine
! style="background: #CDCDCD;" colspan=2 | Feminine
|-
! style="background: #CDCDCD;" colspan=2 | {{{m_pl_type}}}
! style="background: #CDCDCD;" colspan=2 | {{{f_pl_type}}}
]=] .. generate_adj_num("pl")
	end
	wikicode = wikicode .. [=[|}
</div>
</div>]=]

	return make_table(data, wikicode)
end

return export

-- For Vim, so we get 4-space tabs
-- vim: set ts=4 sw=4 noet:
