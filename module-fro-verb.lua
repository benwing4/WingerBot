local m_links = require("Module:links")
local m_utilities = require("Module:utilities")

local lang = require("Module:languages").getByCode("fro")

local export = {}

-- Functions that do the actual inflecting by creating the forms of a basic term.
local inflections = {}

local rfind = mw.ustring.find
local rsub = mw.ustring.gsub
local rmatch = mw.ustring.match

local function ine(x) -- If Not Empty
	if x == "" then
		return nil
	else
		return x
	end
end

local function ined(x) -- If Not Empty or Dash
	if x == "" or x == "-" then
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

----------------------------------------------------------------------------
-- Functions for working with stems

-- Given the stem as it appears before a soft-vowel ending (e/i), generate
-- the corresponding stem for a hard-vowel ending (a/o/u).
function steme_to_stema(steme)
	if rfind(steme, "c$") then
		-- Need to assign to a var because rsub returns 2 values, and
		-- assigning to one var fetches only the first one
		local stema = rsub(steme, "c$", "ç")
		return stema
	elseif rfind(steme, "g$") then
		local stema = rsub(steme, "g$", "j")
		return stema
	else
		return steme
	end
end

-- Given the stem as it appears before a hard-vowel ending, generate
-- the corresponding stem for a soft-vowel ending.
function stema_to_steme(stema)
	if rfind(stema, "c$") then
		-- Need to assign to a var because rsub returns 2 values, and
		-- assigning to one var fetches only the first one
		local steme = rsub(stema, "c$", "qu")
		return steme
	elseif rfind(stema, "g$") then
		local steme = rsub(stema, "g$", "gu")
		return steme
	elseif rfind(stema, "ç$") then
		local steme = rsub(stema, "ç$", "c")
		return steme
	else
		return stema
	end
end

-- Get the stem from the infinitive. Return stem and whether stem is
-- soft-vowel (true except for -re and -oir verbs).
--
-- Currently we rely on the IER argument being set in order to remove
-- -ier from an infinitive. An alternative is to always check for -ier
-- and assume that cases like 'signifier' which is an '-er' verb with a
-- stem 'signifi' are handled by explicitly specifying the stem. (We
-- assume this anyway in the case of any '-ir' verb whose stem ends
-- in '-o', such as 'oir' "to hear".)
local function get_stem_from_inf(inf, ier)
	local nsub = 0
	-- if 'ier' arg given and stem ends in -ier, strip it off.
	if ier then
		stem, nsub = rsub(inf, "ier$", "")
		if nsub > 0 then
			return stem, "ier", true
		end
	end
	-- Check for -er, -oir, -eir, -ir, -re in sequence.
	-- Must check for -oir, -eir before -ir.
	stem, nsub = rsub(inf, "er$", "")
	if nsub > 0 then
		return stem, "er", true
	end
	stem, nsub = rsub(inf, "oir$", "")
	if nsub > 0 then
		return stem, "oir", false
	end
	stem, nsub = rsub(inf, "eir$", "")
	if nsub > 0 then
		return stem, "eir", true
	end
	stem, nsub = rsub(inf, "ir$", "")
	if nsub > 0 then
		return stem, "ir", true
	end
	stem, nsub = rsub(inf, "re$", "")
	if nsub > 0 then
		return stem, "re", false
	end
	error("Unrecognized infinitive '" .. inf .. "'")
end

-- Get the present stem, either explicitly passed in as the first arg or
-- implicitly through the page name, assumed to be the same as the
-- infinitive. Currently we rely on the 'ier' argument being set in
-- order to remove -ier from an infinitive. An alternative is to
-- always check for -ier an assume that cases like 'signifier' which
-- is an '-er' verb with a stem 'signifi' are handled by explicitly
-- specifying the stem. (We assume this anyway in the case of any '-ir'
-- verb whose stem ends in '-o', such as 'oir' "to hear".)
local function get_stem_from_frame(frame)
	local stem = frame.args[1]
	-- if stem passed in and non-blank, use it.
	if ine(stem) then
		return stem
	end
	local inf = mw.title.getCurrentTitle().text
	local ier = ine(frame.args["ier"])
	local stem, ending, is_soft = get_stem_from_inf(inf, ier)
	return stem
end

-- External entry point for get_stem_from_frame(). Optional stem is first
-- argument, optional 'ier' argument is used for -ier verbs (see
-- get_stem_from_frame()).
function export.get_stem(frame)
	return get_stem_from_frame(frame)
end

----------------------------------------------------------------------------
-- Functions for generating arrays of endings

-- Generate an ending array (five-element, see below), where a supporting ''e''
-- is needed.
local function supporting_e(extra)
local text = "In the present tense an extra supporting ''e'' is needed in the first-person singular indicative and throughout the singular subjunctive, and the third-person singular subjunctive ending ''-t'' is lost. "
	text = text .. extra
	return {"", "e", "es", "e", text}
end

-- Generate a general ending array (five-element, see below).
local function mod3(ending, zero, s, t)
	local text = nil
	if ending == zero then
		text = string.format("The forms that would normally end in *''-%ss'', *''-%st'' are modified to ''%s'', ''%s''. ",
		ending, ending, s, t)
	else
		text = string.format("The forms that would normally end in *''-%s'', *''-%ss'', *''-%st'' are modified to ''%s'', ''%s'', ''%s''. ",
		ending, ending, ending, zero, s, t)
	end
	return {ending, zero, s, t, text}
end

-- Return the stem and an array of five elements. In the array, the first
-- is the ending to be substitute, the second is the add_zero ending to
-- substitute, the third is the add_s ending to substitute, the fourth is
-- the add_t ending to substitute and the fifth is the text going into the
-- comment at the top of the conj table. IER should be specified for -ier
-- verbs, which only occur with palatal(ized) final consonants, and causes
-- a different interpretation of certain consonants, esp. final l.
-- If SUPE is specified, force a supporting -e to be added (normally this
-- is inferred automatically from the stem).
local function get_endings(stem, ier, supe)
	local ret = {"", "", "s", "t", ""}
	local ending = nil
	local prev = nil
	-- canonicalize ngn to gn when after vowel or r, l
	if rfind(stem, "[aeiourl]ngn$") then
		ending = "ngn"
		stem = rsub(stem, "ngn$", "gn")
	end
	-- canonicalize double letter to single after vowel, except for l
	-- we need to treat Cill and Cil differently
	if rfind(stem, "[aeiou]([bcdfghjkmnpqrstvwxz])%1$") then
		ending = rmatch(stem, "(..)$")
		stem = rsub(stem, "([bcdfghjkmnpqrstvwxz])%1$", "%1")
	end
	if supe then
		ret = supporting_e("")
	elseif rfind(stem, "mb$") then
		ret = mod3("mb", "mp", "ns", "nt")
	elseif rfind(stem, "mp$") then
		ret = mod3("mp", "mp", "ns", "nt")
	elseif rfind(stem, "([aeiourlmn])b$") then
		ret = mod3(ending or "b", "p", "s", "t")
	elseif rfind(stem, "([aeiourlmn])v$") then
		ret = mod3(ending or "v", "f", "s", "t")
	elseif rfind(stem, "([aeiourlmn])d$") then
		ret = mod3(ending or "d", "t", "z", "t")
	elseif rfind(stem, "([aeiourlmn])c$") then
		ret = mod3(ending or "c", "z", "z", "zt")
		ret[5] = ret[5] .. "In addition, ''c'' becomes ''ç'' before an ''a'' or an ''o'' to keep the /ts/ sound intact. "
	elseif rfind(stem, "([aeiourlmn])[pfk]$") then
		local lastchar = rmatch(stem, "(.)$")
		ret = mod3(ending or lastchar, lastchar, "s", "t")
	elseif rfind(stem, "([aeiourlmn])t$") then
		ret = mod3(ending or "t", "t", "z", "t")
	elseif rfind(stem, "([aeiourlmn])z$") then
		ret = mod3(ending or "z", "z", "z", "zt")
	elseif rfind(stem, "([aeiourlmn])c?qu$") then
		ending = rmatch(stem, "(c?qu)$")
		ret = mod3(ending, "c", "s", "t")
	elseif rfind(stem, "([aeiourlmn])g?gu$") then
		ending = rmatch(stem, "(g?gu)$")
		ret = mod3(ending, "c", "s", "t")
	elseif rfind(stem, "([aeiourlmn])ct$") then
		-- convicter, paincter. Best guess here
		ret = mod3("ct", "ct", "cz", "ct")
	elseif rfind(stem, "([aeiourlmn])st$") then
		ret = mod3("st", "st", "z", "st")
	elseif rfind(stem, "([aeiourlmn])sd$") then
		-- brosder. Best guess here
		ret = mod3("sd", "st", "z", "st")
	elseif rfind(stem, "([aeo])ill?$") or (rfind(stem, "[aeo]ll?$") and ier) then
		ending = rmatch(stem, "([aeo]i?ll?)$")
		prev = rmatch(stem, "([aeo])i?ll?$")
		ret = mod3(ending, prev .. "il", prev .. "uz", prev .. "ut")
	elseif rfind(stem, "uill?$") or (rfind(stem, "ull?$") and ier) then
		ending = rmatch(stem, "(ui?ll?)$")
		ret = mod3(ending, "uil", "uz", "ut")
	elseif rfind(stem, "ill$") or (rfind(stem, "il$") and ier) then
		ending = rmatch(stem, "(ill?)$")
		ret = mod3(ending, "il", "iz", "it")
	elseif rfind(stem, "([^iu])ell?$") then
		ending = rmatch(stem, "(ell?)$")
		ret = mod3(ending, "el", "eaus", "eaut")
	elseif rfind(stem, "([aeo])ll?$") then
		ending = rmatch(stem, "([iu]ell?)$") or rmatch(stem, "([ao]ll?)$")
		prev = rmatch(stem, "([iu]e)ll?$") or rmatch(stem, "([ao])ll?$")
		ret = mod3(ending, prev .. "l", prev .. "us", prev .. "ut")
	elseif rfind(stem, "([iu])ll?$") then
		ending = rmatch(stem, "([iu]ll?)$")
		prev = rmatch(stem, "([iu])ll?$")
		ret = mod3(ending, prev .. "l", prev .. "s", prev .. "t")
	elseif rfind(stem, "ign$") then
		ret = mod3("i" .. (ending or "gn"), "ing", "inz", "int")
	elseif rfind(stem, "lgn$") then
		ret = mod3("l" .. (ending or "gn"), "lng", "lnz", "lnt")
	elseif rfind(stem, "rgn$") then
		ret = mod3("r" .. (ending or "gn"), "rng", "rz", "rt")
	elseif rfind(stem, "([aeou])gn$") then
		prev = rmatch(stem, "([aeou])gn$")
		ret = mod3(prev .. (ending or "gn"), prev .. "ing", prev .. "inz", prev .. "int")
	elseif rfind(stem, "rm$") then
		ret = mod3("rm", "rm", "rs", "rt")
	elseif rfind(stem, "rn$") then
		ret = mod3("rn", "rn", "rz", "rt")
	elseif rfind(stem, "[aeioul]m$") then
		ret = mod3(ending or "m", "m", "ns", "nt")
	elseif rfind(stem, "s$") then
		ret = mod3(ending or "s", "s", "s", "st")
	elseif rfind(stem, "g$") then
		ret = supporting_e("In addition, ''g'' becomes ''j'' before an ''a'' or an ''o'' to keep the /dʒ/ sound intact. ")
	elseif rfind(stem, "j$")
	or rfind(stem, "[^aeiou][bcdfghjklmnpqrtvwxz]$") then
		ret = supporting_e("")
	end
	return ret
end

----------------------------------------------------------------------------
-- Functions for handling particular sorts of endings

-- Convert a stressed verb stem to the form used with a zero ending
-- (1st sing pres indic, also, 1st sing pres subj of -er verbs).
-- See get_endings() for meaning of IER and SUPE.
function add_zero(stem, ier, supe)
	local e = get_endings(stem, ier, supe)
	-- We need to assign to a variable here because rsub() returns multiple
	-- values and we want only the first returned. Return rsub() directly
	-- and all values get returned and appended to the string.
	local ret, nsub = rsub(stem, e[1] .. "$", e[2])
	assert(nsub == 1)
	return ret
end

-- Convert a stressed verb stem to the form used with a -s ending
-- (2nd sing pres indic of -ir/-oir/-re verbs, 2nd sing pres subj of
-- -er verbs). Same code could be used to add -s to nouns except that
-- handling of -c stems needs to be different (need to treat as hard /k/
-- not /ts/). See get_endings() for meaning of IER and SUPE.
function add_s(stem, ier, supe)
	local e = get_endings(stem, ier, supe)
	-- We need to assign to a variable here because rsub() returns multiple
	-- values and we want only the first returned. Return rsub() directly
	-- and all values get returned and appended to the string.
	local ret, nsub = rsub(stem, e[1] .. "$", e[3])
	assert(nsub == 1)
	return ret
end

-- Convert a stressed verb stem to the form used with a -t ending
-- (3rd sing pres indic of -ir/-oir/-re verbs, 3rd sing pres subj of
-- -er verbs). See get_endings() for meaning of IER and SUPE.
function add_t(stem, ier, supe)
	local e = get_endings(stem, ier, supe)
	-- We need to assign to a variable here because rsub() returns multiple
	-- values and we want only the first returned. Return rsub() directly
	-- and all values get returned and appended to the string.
	local ret, nsub = rsub(stem, e[1] .. "$", e[4])
	assert(nsub == 1)
	return ret
end

-- External entry point for add_zero(). Optional stem is first argument,
-- optional 'ier' and 'supe' arguments are as in get_ending().
function export.add_zero(frame)
	local stem = get_stem_from_frame(frame)
	local ier = ine(frame.args["ier"])
	local supe = ine(frame.args["supe"])
	return add_zero(stem, ier, supe)
end

-- External entry point for add_s(). Optional stem is first argument,
-- optional 'ier' and 'supe' arguments are as in get_ending().
function export.add_s(frame)
	local stem = get_stem_from_frame(frame)
	local ier = ine(frame.args["ier"])
	local supe = ine(frame.args["supe"])
	return add_s(stem, ier, supe)
end

-- External entry point for add_t(). Optional stem is first argument,
-- optional 'ier' and 'supe' arguments are as in get_ending().
function export.add_t(frame)
	local stem = get_stem_from_frame(frame)
	local ier = ine(frame.args["ier"])
	local supe = ine(frame.args["supe"])
	return add_t(stem, ier, supe)
end

-- Add -r, for the group-iii future
function add_r(stem)
	local ret = stem .. "r"
	if rfind(stem, "ss$") then
		ret = rsub(stem, "ss$", "str")
	elseif rfind(stem, "is$") then
		ret = rsub(stem, "is$", "ir")
	elseif rfind(stem, "s$") then
		ret = stem .. "dr"
	elseif rfind(stem, "g?n$") then
		ret = rsub(stem, "g?n$", "ndr")
	elseif rfind(stem, "m$") then
		ret = stem .. "br"
	elseif rfind(stem, "i?ll?$") then
		ret = rsub(stem, "i?ll?$", "udr")
	elseif rfind(stem, "[^aeiou]r$") then
		ret = stem .. "er"
	end
	return ret
end

----------------------------------------------------------------------------
-- Functions for handling comments at the top of conjugation tables

-- Return true if this is an irregular verb, due to stems or particular
-- forms being explicitly specified
function irreg_verb(args, skip)
	if skip == nil then skip = {}
	elseif type(skip) == "string" then skip = {skip}
	end
	
	for k,v in pairs(args) do
		if k == 'pres' and rfind(v, "/") or
				k ~= 'pres' and k ~= 'prese' and k ~= 'presa' and
				k ~= 'ier' and k ~= 'supe' and k ~= 'aux' and k ~= 'refl' and
				k ~= 'inf' and k ~= 'comment' and
				-- for compatibility:
				k ~= 'stemv' and k ~= 1 and k ~= 2 and
				not contains(skip, k) and
				mw.text.trim(v) ~= '' then
			return true
		end
	end
	return false
end

-- Return comment describing phonetic changes to the verb in the present
-- tense. Appears near the top of the conjugation chart. STEM is the stressed
-- stem. See get_endings() for meaning of IER and SUPE.
function verb_comment(stem, ier, supe)
	local e = get_endings(stem, ier, supe)
	return e[5]
end

-- Return comment describing phonetic and stem changes to the verb in the
-- present tense. Appears near the top of the conjugation chart. STEME is
-- the unstressed stem before e/i, STEMA the unstressed stem before a/o/u,
-- STEMS the stressed stem. See get_endings() for meaning of IER and SUPE.
function full_verb_comment(args, steme, stema, stems, ier, supe)
	if ine(args["comment"]) then
		return mw.text.trim(args["comment"]) .. " "
	end
	local com = verb_comment(stems, ier, supe)
	local irreg = irreg_verb(args, 'press')
	if steme ~= stems and irreg then
		com = com .. "In addition, it has a stressed present stem ''" .. stems .. "'' distinct from the unstressed stem ''" .. steme .. "'', as well as other irregularities. "
	elseif steme ~= stems then
		com = com .. "In addition, it has a stressed present stem ''" .. stems .. "'' distinct from the unstressed stem ''" .. steme .. "''. "
	elseif irreg then
		com = com .. "In addition, it has irregularities in its conjugation. "
	end
	return com
end

-- External entry point for verb_comment(). Optional stem is first argument,
-- optional 'ier' and 'supe' arguments are as in get_ending().
function export.verb_comment(frame)
	local stem = get_stem_from_frame(frame)
	local ier = ine(frame.args["ier"])
	local supe = ine(frame.args["supe"])
	return verb_comment(stem, ier, supe)
end

----------------------------------------------------------------------------
-- Main inflection-handling functions

-- Main entry point
function export.froconj(frame)
	local args = frame:getParent().args

	-- Create the forms
	local data = {forms = {}, categories = {}, comment = "",
	refl = ine(args["refl"]),
	ier = ine(args["ier"]) or ine(frame.args["ier"]),
	supe = ine(args["supe"]) or ine(frame.args["supe"])
	}

	-- allow aux to be specified as second unnamed param for compatibility
	data.forms.aux = {data.refl and "estre" or mw.text.trim(ine(args["aux"]) or ine(args[2]) or "avoir")}

	data.forms.infinitive =
		{ine(args["inf"]) or mw.title.getCurrentTitle().text}

	-- Set the soft vowel ('pres') and hard vowel ('presa') present stems.
	-- They can be explicitly set using 'pres' and 'presa' params.
	-- If one is set, the other is inferred from it. If neither is set,
	-- both are inferred from the infinitive.
	data.prese = ine(args["pres"]) and not rfind(args["pres"], "/") and args["pres"] or
		ine(args["prese"]) or
		ine(args["stemv"]) or ine(args[1]) -- for compatibility
	data.presa = ine(args["presa"])
	local inf_stem, inf_ending, inf_is_soft =
		get_stem_from_inf(data.forms.infinitive[1], data.ier)
	if not data.prese and not data.presa then
		if inf_is_soft then
			data.prese = inf_stem
		else
			data.presa = inf_stem
		end
	end
	if not data.prese then data.prese = stema_to_steme(data.presa) end
	if not data.presa then data.presa = steme_to_stema(data.prese) end

	-- Find what type of verb is it (hard-coded in the template).
	-- Generate standard conjugated forms for each type of verb.
	local infl_type = frame.args["type"]
	if not ine(infl_type) then
		error("Verb type (infl_type) not specified.")
	elseif inflections[infl_type] then
		inflections[infl_type](args, data)
	else
		error("Verb type " .. infl_type .. " not supported.")
	end

	table.insert(data.categories, "Old French " .. data.group .. " group verbs")
	table.insert(data.categories, "Old French verbs ending in -" .. inf_ending)

	-- Get overridden forms
	process_overrides(args, data)

	-- Add links
	add_links(args, data)

	-- Add reflexive pronouns
	if data.refl then
		add_reflexive_pronouns(args, data)
	end

	return make_table(data) .. m_utilities.format_categories(data.categories, lang)
end

-- Version of main entry point meant for calling from the debug console.
function export.froconj2(args, parargs)
	local frame = {args = args, getParent = function() return {args = parargs} end}
	return export.froconj(frame)
end

-- If ARGBASE == "foo", return an array of
-- {args["foo"],args["foo2"],...,args["foo9"]}.
-- If ARGBASE is a sequence of strings, return an array of sequences, e.g.
-- if ARGBASE == {"foo", "bar"}, return an array of
-- {{args["foo"],args["bar"]},{args["foo2"],args["bar2"]},...,{args["foo9"],args["bar9"]}}
function get_args(args, argbase)
	if type(argbase) == "string" then
		local theargs = {args[argbase] or ""}
		for j = 2, 9 do
			table.insert(theargs, args[argbase .. j] or "")
		end
		return theargs
	else
		local theargs = {}
		local onearg = {}
		for i, item in ipairs(argbase) do
			table.insert(onearg, args[item] or "")
		end
		table.insert(theargs, onearg)
		for j = 2, 9 do
			onearg = {}
			for i, item in ipairs(argbase) do
				table.insert(onearg, args[item .. j] or "")
			end
			table.insert(theargs, onearg)
		end
		return theargs
	end
end

-- Replaces terms with overridden ones that are given as additional named parameters.
function process_overrides(args, data)
	-- Each term in current is overridden by one in override, if it exists.
	local function override(current, override)
		current = current or {}
		local ret = {}

		local i = 1

		-- First see if any of the existing items in current have an override specified.
		while current[i] do
			if ine(override[i]) then
				if override[i] ~= "-" then
					table.insert(ret, override[i])
				end
			else
				table.insert(ret, current[i])
			end

			i = i + 1
		end

		-- We've reached the end of current.
		-- Look in the override list to see if there are any extra forms to add on to the end.
		while override[i] do
			if ine(override[i]) and override[i] ~= "-" then
				table.insert(ret, override[i])
			end

			i = i + 1
		end

		return ret
	end

	-- Mark terms with any additional parameters as irregular, except for
	-- certain ones that we consider normal variants.
	if irreg_verb(args) then
		table.insert(data.categories, 'Old French irregular verbs')
	end

	--[[

	This function replaces former code like this:

	data.forms.pret_indc_1sg = override(data.forms.pret_indc_1sg, {args["pret1s"], args["pret1s2"], args["pret1s3"]})
	data.forms.pret_indc_2sg = override(data.forms.pret_indc_2sg, {args["pret2s"], args["pret2s2"], args["pret2s3"]})
	data.forms.pret_indc_3sg = override(data.forms.pret_indc_3sg, {args["pret3s"], args["pret3s2"], args["pret3s3"]})
	data.forms.pret_indc_1pl = override(data.forms.pret_indc_1pl, {args["pret1p"], args["pret1p2"], args["pret1p3"]})
	data.forms.pret_indc_2pl = override(data.forms.pret_indc_2pl, {args["pret2p"], args["pret2p2"], args["pret2p3"]})
	data.forms.pret_indc_3pl = override(data.forms.pret_indc_3pl, {args["pret3p"], args["pret3p2"], args["pret3p3"]})

	except that there are 9 overrides for each tense-person-number combo,
	not just 2 or 3.
	--]]
	local function handle_tense_override(tense, short)
		local pnums = {"1sg", "2sg", "3sg", "1pl", "2pl", "3pl"}
		local pnums_short = {"1s", "2s", "3s", "1p", "2p", "3p"}
		for pn = 1, #pnums do
			local pnum = pnums[pn]
			local pnum_short = pnums_short[pn]
			local theargs = get_args(args, short .. pnum_short)
			local tensepnum = tense .. "_" .. pnum
			data.forms[tensepnum] = override(data.forms[tensepnum], theargs)
		end
	end


	-- Non-finite forms
	data.forms.infinitive = override(data.forms.infinitive, {args["inf"]})
	data.forms.pres_ptc = override(data.forms.pres_ptc, get_args(args, "presp"))
	data.forms.past_ptc = override(data.forms.past_ptc, get_args(args, "pastp"))

	handle_tense_override("pres_indc", "pres") -- Present
	handle_tense_override("impf_indc", "imperf") -- Imperfect
	handle_tense_override("pret_indc", "pret") -- Preterite
	handle_tense_override("futr_indc", "fut") -- Future
	handle_tense_override("cond", "cond") -- Conditional
	handle_tense_override("pres_subj", "sub") -- Present subjunctive
	handle_tense_override("impf_subj", "impsub") -- Imperfect subjunctive

	-- Imperative
	data.forms.impr_2sg = override(data.forms.impr_2sg, get_args(args, "imp2s"))
	data.forms.impr_1pl = override(data.forms.impr_1pl, get_args(args, "imp1p"))
	data.forms.impr_2pl = override(data.forms.impr_2pl, get_args(args, "imp2p"))
end

-- Adds reflexive pronouns to the appropriate forms
function add_reflexive_pronouns(args, data)
	-- Gather pronoun parameters
	local cprons = {}
	local vprons = {}

	cprons["1sg"] = ine(args["me"]) or "me "
	cprons["2sg"] = ine(args["te"]) or "te "
	cprons["3sg"] = ine(args["se"]) or "se "
	cprons["1pl"] = ine(args["nos"]) or "nos "
	cprons["2pl"] = ine(args["vos"]) or "vos "
	cprons["3pl"] = cprons["3sg"]

	vprons["1sg"] = ine(args["me"]) or "m'"
	vprons["2sg"] = ine(args["te"]) or "t'"
	vprons["3sg"] = ine(args["se"]) or "s'"
	vprons["1pl"] = ine(args["nos"]) or "nos "
	vprons["2pl"] = ine(args["vos"]) or "vos "
	vprons["3pl"] = vprons["3sg"]

	function add_refl(person, form)
		mw.log(form)
		-- FIXME! YUCK! This hard-codes knowledge of how the links are formatted.
		-- Perhaps we should go back to the old way of having the reflexive code
		-- also insert links.
		if rfind(form, "^<span.*>[^a-zA-Z]*[aeiouAEIOU]") then
			return vprons[person] .. form
		else
			return cprons[person] .. form
		end
	end

	-- Go over all the forms in the list
	for key, subforms in pairs(data.forms) do
		-- Extract the person/number from the last 3 characters of the key
		local person = key:sub(-3)

		-- Skip these three, as they already had pronouns added earlier
		if cprons[person] and key ~= "impr_2sg" and key ~= "impr_1pl" and key ~= "impr_2pl" then
			-- Go through each of the alternative subforms and add the pronoun
			for key2, subform in ipairs(subforms) do
				data.forms[key][key2] = add_refl(person, subform)
			end
		end

	end

	-- Handle infinitive
	for key, subform in ipairs(data.forms.infinitive) do
		data.forms.infinitive[key] = add_refl("3sg", subform)
	end

	-- Handle imperatives
	for key, subform in ipairs(data.forms.impr_2sg) do
		data.forms.impr_2sg[key] = subform .. "-toi"
	end
	for key, subform in ipairs(data.forms.impr_1pl) do
		data.forms.impr_1pl[key] = subform .. "-nos"
	end
	for key, subform in ipairs(data.forms.impr_2pl) do
		data.forms.impr_2pl[key] = subform .. "-vos"
	end
end

-- Adds links to appropriate forms
function add_links(args, data)
	-- Go over all the forms in the list
	for key, subforms in pairs(data.forms) do
		-- Go through each of the alternative subforms and add the pronoun
		for key2, subform in ipairs(subforms) do
			data.forms[key][key2] = make_link(subform)
		end
	end
end

-- Inflection functions

-- Implementation of inflect_tense(). See that function. Also used directly
-- to add the imperative, which has only three forms.
function inflect_tense_1(data, tense, stems, endings, pnums)

	-- First, initialize any nil entries to sequences.
	for i, pnum in ipairs(pnums) do
		if data.forms[tense .. "_" .. pnum] == nil then
			data.forms[tense .. "_" .. pnum] = {}
		end
	end

	-- Now add entries
	for i = 1, #pnums do
		-- Extract endings for this person-number combo
		local ends = endings[i]
		if type(ends) == "string" then ends = {ends} end
		-- Extract stem for this person-number combo
		local stem = stems
		if type(stem) == "table" then stem = stem[i] end
		-- Add entries for stem + endings
		for j, ending in ipairs(ends) do
			local form = stem .. ending
			if ine(form) and form ~= "-" then
				table.insert(data.forms[tense .. "_" .. pnums[i]], form)
			end
		end
	end
end

-- Add to DATA the inflections for the tense indicated by TENSE (the prefix
-- in the data.forms names, e.g. 'impf_subj'), formed by combining the STEMS
-- (either a single string or a sequence of six strings) with the
-- ENDINGS (a sequence of six values, each of which is either a string
-- or a sequence of one or more possible endings). If existing
-- inflections already exist, they will be added to, not overridden.
function inflect_tense(data, tense, stems, endings)
	local pnums = {"1sg", "2sg", "3sg", "1pl", "2pl", "3pl"}
	inflect_tense_1(data, tense, stems, endings, pnums)
end

-- Like inflect_tense() but for the imperative, which has only three forms
-- instead of six.
function inflect_tense_impr(data, tense, stems, endings)
	local pnums = {"2sg", "1pl", "2pl"}
	inflect_tense_1(data, tense, stems, endings, pnums)
end

function inflect_pres(data, tense, group, steme, stema, stems, ier, supe)
	local i = ine(ier) and "i" or ""
	if tense == "impr" and group == "i" then
		inflect_tense_impr(data, tense,
			{stems, stema, steme},
			{"e", "ons", i .. "ez"})
	elseif tense == "impr" and group == "iii" then
		inflect_tense_impr(data, tense,
			{add_zero(stems, ier, supe), stema, steme},
			{"", "ons", i .. "ez"})
	elseif tense == "pres_indc" and group == "i" then
		inflect_tense(data, tense,
			{add_zero(stems, ier, supe), stems, stems, stema, steme, stems},
			{"", "es", "e", "ons", i .. "ez", "ent"})
	elseif tense == "pres_subj" and group == "iii" then
		inflect_tense(data, tense,
			{stems, stems, stems, stema, steme, stems},
			{"e", "es", "e", "ons", i .. "ez", "ent"})
	else
		inflect_tense(data, tense,
			{add_zero(stems, ier, supe), add_s(stems, ier, supe),
			 add_t(stems, ier, supe), stema, steme, stems},
			{"", "", "", "ons", i .. "ez", "ent"})
	end
end

-- Split a string into entries separated by slashes, each representing one
-- of the possible person/number combinations. Each entry in turn may consist
-- of one or more forms, separated by commas.
function split_multipart(str)
	local entries = mw.text.split(str, "/")
	for i, entry in ipairs(entries) do
		if rfind(entry, ",") then
			entries[i] = mw.text.split(entry, ",")
		else
			entries[i] = {entry}
		end
	end
	return entries
end

function handle_pres(args, data, group, steme, stema, stems, ier, supe)
	if ine(args["pres"]) and rfind(args["pres"], "/") then
		inflect_tense(data, "pres_indc", "", split_multipart(args["pres"]))
	else
		inflect_pres(data, "pres_indc", group, steme, stema, stems, ier, supe)
	end
	-- If subv or subc set, derive one from the other if necessary.
	-- Else, derive both from the indicative.
	-- If subs not set, derive from subv if either subv or subc set, else
	-- derive from the indicative.
	local sub_steme = ine(args["sub"])
	local sub_stema = ine(args["suba"])
	local sub_dash = sub_steme == "-" or sub_stema == "-"
	local sub_specified = sub_steme or sub_stema
	if sub_steme and rfind(sub_steme, "/") then
		inflect_tense(data, "pres_subj", "", split_multipart(sub_steme))
	elseif not sub_dash then
		if not sub_specified then
			sub_steme = steme
			sub_stema = stema
		end
		if not sub_steme then sub_steme = stema_to_steme(sub_stema) end
		if not sub_stema then sub_stema = steme_to_stema(sub_steme) end
		local sub_stems = ine(args["subs"])
		if not sub_stems then
			sub_stems = sub_specified and sub_steme or stems
		end
		inflect_pres(data, "pres_subj", group, sub_steme, sub_stema, sub_stems,
			ine(args["subier"]) or (not sub_specified and ier),
			ine(args["subsupe"]) or (not sub_specified and supe))
	end

	-- Repeat exactly for the imperative.
	local imp_steme = ine(args["imp"])
	local imp_stema = ine(args["impa"])
	local imp_dash = imp_steme == "-" or imp_stema == "-"
	local imp_specified = imp_steme or imp_stema
	if imp_steme and rfind(imp_steme, "/") then
		inflect_tense_impr(data, "impr", "", split_multipart(imp_steme))
	elseif not imp_dash then
		if not imp_specified then
			imp_steme = steme
			imp_stema = stema
		end
		if not imp_steme then imp_steme = stema_to_steme(imp_stema) end
		if not imp_stema then imp_stema = steme_to_stema(imp_steme) end
		local imp_stems = ine(args["imps"])
		if not imp_stems then
			imp_stems = imp_specified and imp_steme or stems
		end
		inflect_pres(data, "impr", group, imp_steme, imp_stema, imp_stems,
			ine(args["impier"]) or (not imp_specified and ier),
			ine(args["impsupe"]) or (not imp_specified and supe))
	end

	-- If indic stem specified, we add indic values, and also corresponding
	-- subj values if separate subj stem not specified.
	for i = 2, 9 do
		steme = ine(args["pres" .. i])
		stema = ine(args["presa" .. i])
		local multi_indic = steme and rfind(steme, "/")
		local indic_specified = not multi_indic and (steme or stema)
		if multi_indic then
			inflect_tense(data, "pres_indc", "", split_multipart(steme))
		elseif indic_specified then
			if not steme then steme = stema_to_steme(stema) end
			if not stema then stema = steme_to_stema(steme) end
			stems = ine(args["press" .. i]) or steme
			ier = ine(args["ier" .. i])
			supe = ine(args["supe" .. i])
			inflect_pres(data, "pres_indc", group, steme, stema, stems, ier, supe)
		end

		-- Handle subjunctive as above.
		sub_steme = ine(args["sub" .. i])
		sub_stema = ine(args["suba" .. i])
		sub_dash = sub_steme == "-" or sub_stema == "-"
		sub_specified = sub_steme or sub_stema
		if sub_steme and rfind(sub_steme, "/") then
			inflect_tense(data, "pres_subj", "", split_multipart(sub_steme))
		elseif not sub_dash and (indic_specified or sub_specified) then
			if not sub_specified then
				sub_steme = steme
				sub_stema = stema
			end
			if not sub_steme then sub_steme = stema_to_steme(sub_stema) end
			if not sub_stema then sub_stema = steme_to_stema(sub_steme) end
			sub_stems = ine(args["subs" .. i])
			if not sub_stems then
				sub_stems = sub_specified and sub_steme or stems
			end
			inflect_pres(data, "pres_subj", group, sub_steme, sub_stema,
				sub_stems,
				ine(args["subier" .. i]) or (not sub_specified and ier),
				ine(args["subsupe" .. i]) or (not sub_specified and supe))
		end

		-- Repeat for the imperative.
		imp_steme = ine(args["imp" .. i])
		imp_stema = ine(args["impa" .. i])
		imp_dash = imp_steme == "-" or imp_stema == "-"
		imp_specified = imp_steme or imp_stema
		if imp_steme and rfind(imp_steme, "/") then
			inflect_tense_impr(data, "impr", "", split_multipart(imp_steme))
		elseif not imp_dash and (indic_specified or imp_specified) then
			if not imp_specified then
				imp_steme = steme
				imp_stema = stema
			end
			if not imp_steme then imp_steme = stema_to_steme(imp_stema) end
			if not imp_stema then imp_stema = steme_to_stema(imp_steme) end
			imp_stems = ine(args["imps" .. i])
			if not imp_stems then
				imp_stems = imp_specified and imp_steme or stems
			end
			inflect_pres(data, "impr", group, imp_steme, imp_stema,
				imp_stems,
				ine(args["impier" .. i]) or (not imp_specified and ier),
				ine(args["impsupe" .. i]) or (not imp_specified and supe))
		end
	end
end

-- Add to DATA the endings for the preterite and imperfect
-- subjunctive, with unstressed stem STEMU, stressed stem STEMS,
-- conjugation type PTY and corresponding value of IMPSUB.
function inflect_pret_impf_subj(data, stemu, stems, pty, impsub)
	-- WARNING: If the second person singular of any of these is not a
	-- simple string, you will need to modify the handling below of
	-- the imperfect subjunctive, which relies on this form.
	local all_endings =
	-- FIXME: weak-a (-er) and weak-a2 (-ier) are handled separately by the
	-- handlers for -er and -ier. In any case the code here doesn't
	-- properly handle the steme vs. stema distinction necessary for these
	-- verbs.
	--
	pty == "weak-a" and {"ai","as",{"a","aṭ"},"ames","astes","erent"} or
	pty == "weak-a2" and {"ai","as",{"a","aṭ"},"ames","astes","ierent"} or
	pty == "weak-i" and {"i","is",{"i","iṭ"},"imes","istes","irent"} or
	pty == "weak-i2" and {"i","is",{"ié","iéṭ"},"imes","istes","ierent"} or
	pty == "strong-i" and {"","is","t","imes","istes","rent"} or
	pty == "strong-id" and {"","is","t","imes","istes",{"drent","rent"}} or
	pty == "weak-u" and {"ui","us",{"u","uṭ"},"umes","ustes","urent"} or
	pty == "strong-u" and {"ui","eüs","ut","eümes","eüstes","urent"} or
	pty == "strong-o" and {"oi","eüs","ot","eümes","eüstes","orent"} or
	pty == "strong-st" and {"s","sis","st","simes","sistes","strent"} or
	pty == "strong-sd" and {"s","ṣis","st","ṣimes","ṣistes","sdrent"} or
	ine(pty) and error("Unrecognized prettype value '" .. pty .. "'") or
	error("Unspecified prettype value")

	-- Always use weak stem unless we have strong-stem endings
	local stems =
		(rfind(pty, "^strong-") and {stems, stemu, stems, stemu, stemu, stems}
			or stemu)

	inflect_tense(data, "pret_indc", stems, all_endings)

	-- Handle imperfect subj, which follows the same types as the preterite
	-- and is built off of the 2nd person singular form, although we need to
	-- special-case weak-a and weak-a2
	local impsub_endings =
		{"se","ses","t",{"sons","siens"},{"soiz","sez","siez"},"sent"}
	impsub = ine(impsub)
	if impsub and rfind(impsub, "/") then
		inflect_tense(data, "impf_subj", "", split_multipart(impsub))
	elseif impsub then
		inflect_tense(data, "impf_subj", impsub, impsub_endings)
	elseif pty == "weak-a" or pty == "weak-a2" then
		inflect_tense(data, "impf_subj", stemu,
			{"asse","asses","ast",
			 {"issons","issiens"},{"issoiz","issez","issiez"},"assent"})
	else
		inflect_tense(data, "impf_subj", stemu .. all_endings[2],
			impsub_endings)
	end
end

-- Add to DATA the endings for the preterite and imperfect subjunctive,
-- based on the strong and weak stems and preterite ending type(s) given in
-- ARGS. For each weak preterite ending type 'prettypeN' there should be a
-- corresponding stem in 'pretN' (defaulting to STEM) and for each strong
-- preterite ending type 'prettypeN' there should be corresponding unstressed
-- and stressed stems in 'pretuN' and 'pretsN' (defaulting to 'pretN' or STEM).
-- If no preterite ending types given, default to the preterite type in PTY and
-- stressed/unstressed stem STEM.
function handle_pret_impf_subj(args, data, stem, pty)
	if ine(args["pret"]) and rfind(args["pret"], "/") then
		inflect_tense(data, "pret_indc", "", split_multipart(args["pret"]))
	elseif not ine(args["prettype"]) then
		inflect_pret_impf_subj(data, stem, stem, pty, args["impsub"])
	else
		inflect_pret_impf_subj(data,
			ine(args["pretu"]) or ine(args["pret"]) or stem,
			ine(args["prets"]) or ine(args["pretu"]) or ine(args["pret"]) or stem,
			args["prettype"], args["impsub"])
	end
	for i = 2, 9 do
		if ine(args["pret" .. i]) and rfind(args["pret" .. i], "/") then
			inflect_tense(data, "pret_indc", "", split_multipart(args["pret" .. i]))
		elseif ine(args["prettype" .. i]) then
			inflect_pret_impf_subj(data,
				ine(args["pretu" .. i]) or ine(args["pret" .. i]) or stem,
				ine(args["prets" .. i]) or ine(args["pretu" .. i]) or ine(args["pret" .. i]) or stem,
				args["prettype" .. i], args["impsub" .. i])
		end
	end
end

-- Add to DATA the endings for the future and conditional, with the stems in
-- STEM, a sequence (generally the infinitive or some modified version).
-- Values in STEM that are empty are ignored.
function inflect_future_cond(data, stems)
	for _, stem in ipairs(stems) do
		if ine(stem) and rfind(stem, "/") then
			inflect_tense(data, "futr_indc", "", split_multipart(stem))
		elseif ine(stem) then
			inflect_tense(data, "futr_indc", stem,
				{"ai","as","a","ons",{"ez","eiz"},"ont"})
			inflect_tense(data, "cond", stem,
				{{"oie","eie"},{"oies","eies"},{"oit","eit"},
				{"iens","iiens"},{"iez","iiez"},{"oient","eient"}})
		end
	end
end

-- Add to DATA the endings for the future and conditional based on the
-- future stem(s) in ARGS. If no future stems given, use STEM.
function handle_future_cond(args, data, stem)
	if not ine(args["fut"]) then
		inflect_future_cond(data, {stem})
	else
		inflect_future_cond(data, get_args(args, "fut"))
	end
end

-- Add to DATA the endings for the imperfect, with the stems in
-- STEMS, a sequence. Each entry of the sequence is a sequence of
-- {STEME, STEMA, IER}. Values in STEMS where STEME and STEMA are
-- empty are ignored.
function inflect_imperfect(data, group, stems)
	for _, stem in ipairs(stems) do
		local steme = ine(stem[1])
		local stema = ine(stem[2])
		local ier = ine(stem[3])
	    local i = ier and "i" or ""
		if steme and rfind(steme, "/") then
			inflect_tense(data, "impf_indc", "", split_multipart(steme))
		elseif steme or stema then
			if not steme then steme = stema_to_steme(stema) end
			if not stema then stema = steme_to_stema(steme) end
			if group == "i" then
				inflect_tense(data, "impf_indc", "",
					{
	{stema .. "oie", steme .. "eie", stema .. "oe", steme .. i .. "eve"},
	{stema .. "oies", steme .. "eies", stema .. "oes", steme .. i .. "eves"},
	{stema .. "oit", steme .. "eit", stema .. "ot", steme .. i .. "eve"},
	{steme .. "iiens", steme .. "iens"},
	{steme .. "iiez", steme .. "iez"},
	{stema .. "oient", steme .. "eient", stema .. "oent", steme .. i .. "event"}
					})
			elseif group == "ii" then
				inflect_tense(data, "impf_indc", steme .. "iss",
					{
						{"oie", "eie"},
						{"oies", "eies"},
						{"oit", "eit"},
						{"iiens", "iens"},
						{"iiez", "iez"},
						{"oient", "eient"}
					})
			elseif group == "iii" then
				inflect_tense(data, "impf_indc", "",
					{
						{stema .. "oie", steme .. "eie"},
						{stema .. "oies", steme .. "eies"},
						{stema .. "oit", steme .. "eit"},
						{steme .. "iiens", steme .. "iens"},
						{steme .. "iiez", steme .. "iez"},
						{stema .. "oient", steme .. "eient"}
					})
			end
		end
	end
end

-- Add to DATA the endings for the future and conditional based on the
-- future stem(s) in ARGS. If no future stems given, use STEM.
function handle_imperfect(args, data, group, steme, stema, ier)
	if not ine(args["imperf"]) and not ine(args["imperfa"]) then
		inflect_imperfect(data, group, {{steme, stema, ier}})
	else
		inflect_imperfect(data, group, get_args(args, {"imperf","imperfa","imperfier"}))
	end
end

-- Add to DATA the endings for an -er or -ier verb, based on the arguments
-- in ARGS.
inflections["i"] = function(args, data)
	local prese = data.prese
	local presa = data.presa
	local press = ine(args["press"]) or prese
	local i = data.ier and "i" or ""

	if data.ier then
		data.comment = "This verb conjugates as a first-group verb ending in ''-ier'', with a palatal stem. These verbs are conjugated mostly like verbs in ''-er'', but there is an extra ''i'' before the ''e'' of some endings. "
	else
		data.comment = "This verb conjugates as a first-group verb ending in ''-er''. "
	end
	data.comment = data.comment ..
		full_verb_comment(args, prese, presa, press, data.ier, data.supe)
	data.group = "first"
	data.forms.pres_ptc = {presa .. "ant"}
	data.forms.past_ptc = {prese .. i .. "é"}

	handle_pres(args, data, "i", prese, presa, press, data.ier, data.supe)
	handle_imperfect(args, data, "i", prese, presa, data.ier)

	data.forms.pret_indc_1sg = {presa .. "ai"}
	data.forms.pret_indc_2sg = {presa .. "as"}
	data.forms.pret_indc_3sg = {presa .. "a"}
	data.forms.pret_indc_1pl = {presa .. "ames"}
	data.forms.pret_indc_2pl = {presa .. "astes"}
	data.forms.pret_indc_3pl = {prese .. i .. "erent"}

	data.forms.impf_subj_1sg = {presa .. "asse"}
	data.forms.impf_subj_2sg = {presa .. "asses"}
	data.forms.impf_subj_3sg = {presa .. "ast"}
	data.forms.impf_subj_1pl = {prese .. "issons"}
	data.forms.impf_subj_2pl = {prese .. "issez", prese .. "issiez"}
	data.forms.impf_subj_3pl = {presa .. "assent"}

	handle_future_cond(args, data, prese .. "er")
end

-- Add to DATA the endings for a type 2 verb (-ir, with -iss- infix),
-- based on the arguments in ARGS.
inflections["ii"] = function(args, data)
	local prese = data.prese

	data.comment = "This verb conjugates as a second-group verb (ending in ''-ir'', with an ''-iss-'' infix). "
	data.group = "second"

	data.forms.pres_ptc = {prese .. "issant"}
	data.forms.past_ptc = {prese .. "i"}

	data.forms.pres_indc_1sg = {prese .. "is"}
	data.forms.pres_indc_2sg = {prese .. "is"}
	data.forms.pres_indc_3sg = {prese .. "ist"}
	data.forms.pres_indc_1pl = {prese .. "issons"}
	data.forms.pres_indc_2pl = {prese .. "issez"}
	data.forms.pres_indc_3pl = {prese .. "issent"}

	data.forms.pres_subj_1sg = {prese .. "isse"}
	data.forms.pres_subj_2sg = {prese .. "isses"}
	data.forms.pres_subj_3sg = {prese .. "isse"}
	data.forms.pres_subj_1pl = {prese .. "issons"}
	data.forms.pres_subj_2pl = {prese .. "issez"}
	data.forms.pres_subj_3pl = {prese .. "issent"}

	data.forms.impr_2sg = {prese .. "is"}
	data.forms.impr_1pl = {prese .. "issons"}
	data.forms.impr_2pl = {prese .. "issez"}

	handle_imperfect(args, data, "ii", prese, prese, data.ier)
	handle_pret_impf_subj(args, data, prese, "weak-i")
	handle_future_cond(args, data, prese .. "ir")
end

-- Add to DATA the endings for a type 3 verb (-ir without -iss- infix, or
-- -re or -oir), based on the arguments in ARGS.
inflections["iii"] = function(args, data)
	local prese = data.prese
	local presa = data.presa
	local press = ine(args["press"]) or prese
	local i = data.ier and "i" or ""

	data.comment = "This verb conjugates as a third-group verb (mostly irregular). "
	if data.ier then
		data.comment = data.comment .. "This verb ends in a palatal stem, so there is an extra ''i'' before the ''e'' of some endings. "
	end
	data.comment = data.comment ..
		full_verb_comment(args, prese, presa, press, data.ier, data.supe)
	data.group = "third"

	data.forms.pres_ptc = {presa .. "ant"}
	data.forms.past_ptc = {presa .. "u"}

	handle_pres(args, data, "iii", prese, presa, press, data.ier, data.supe)
	handle_imperfect(args, data, "iii", prese, presa, data.ier)
	handle_pret_impf_subj(args, data, prese, "weak-i")
	handle_future_cond(args, data, add_r(presa))
end

-- Shows the table with the given forms
function make_table(data)
	return data.comment .. [=[Old French conjugation varies significantly by date and by region. The following conjugation should be treated as a guide.
<div class="NavFrame" style="clear:both;margin-top:1em">
<div class="NavHead" align=left>&nbsp; &nbsp; Conjugation of ]=] .. m_links.full_link(nil, data.forms.infinitive[1], lang, nil, "term", nil, nil, nil) .. [=[
<span style="font-size:90%;"> (see also [[Appendix:Old French verbs]])</span></div>
<div class="NavContent" align=center>
{| style="width: 100%; background:#F0F0F0;border-collapse:separate;border-spacing:2px" class="inflection-table"
|-
! colspan="2" style="background:#e2e4c0" |
! colspan="3" style="background:#e2e4c0" | simple
! colspan="3" style="background:#e2e4c0" | compound
|-
! colspan="2" style="background:#e2e4c0" | infinitive
| colspan="3" |  ]=] .. show_form(data.forms.infinitive) .. [=[

| colspan="3" |  ]=] .. show_form(data.forms.aux) .. " " .. show_form(data.forms.past_ptc) .. [=[

|-
! colspan="2" style="background:#e2e4c0" | gerund
| colspan="3" |  en ]=] .. show_form(data.forms.pres_ptc) .. [=[

| colspan="3" |  Use the gerund of ]=] .. show_form(data.forms.aux) .. [=[ followed by the past participle

|-
! colspan="2" style="background:#e2e4c0" | present participle
| colspan="3" |  ]=] .. show_form(data.forms.pres_ptc) .. [=[

|-
! colspan="2" style="background:#e2e4c0" | past participle
| colspan="3" |  ]=] .. show_form(data.forms.past_ptc) .. [=[

|-
! colspan="2" rowspan="2" style="background:#C0C0C0" | person
! colspan="3" style="background:#C0C0C0" | singular
! colspan="3" style="background:#C0C0C0" | plural
|-
! style="background:#C0C0C0;width:12.5%" | first
! style="background:#C0C0C0;width:12.5%" | second
! style="background:#C0C0C0;width:12.5%" | third
! style="background:#C0C0C0;width:12.5%" | first
! style="background:#C0C0C0;width:12.5%" | second
! style="background:#C0C0C0;width:12.5%" | third
|-
! style="background:#c0cfe4" colspan="2" | indicative
! style="background:#c0cfe4" | jeo, jou
! style="background:#c0cfe4" | tu
! style="background:#c0cfe4" | il
! style="background:#c0cfe4" | nos, nous
! style="background:#c0cfe4" | vos, vous
! style="background:#c0cfe4" | ils
|-
! rowspan="5" style="background:#c0cfe4" | simple<br>tenses
! style="height:3em;background:#c0cfe4" | present
| ]=] .. show_form(data.forms.pres_indc_1sg) .. [=[

| ]=] .. show_form(data.forms.pres_indc_2sg) .. [=[

| ]=] .. show_form(data.forms.pres_indc_3sg) .. [=[

| ]=] .. show_form(data.forms.pres_indc_1pl) .. [=[

| ]=] .. show_form(data.forms.pres_indc_2pl) .. [=[

| ]=] .. show_form(data.forms.pres_indc_3pl) .. [=[

|-
! style="height:3em;background:#c0cfe4" | imperfect
| ]=] .. show_form(data.forms.impf_indc_1sg) .. [=[

| ]=] .. show_form(data.forms.impf_indc_2sg) .. [=[

| ]=] .. show_form(data.forms.impf_indc_3sg) .. [=[

| ]=] .. show_form(data.forms.impf_indc_1pl) .. [=[

| ]=] .. show_form(data.forms.impf_indc_2pl) .. [=[

| ]=] .. show_form(data.forms.impf_indc_3pl) .. [=[

|-
! style="height:3em;background:#c0cfe4" | preterite
| ]=] .. show_form(data.forms.pret_indc_1sg) .. [=[

| ]=] .. show_form(data.forms.pret_indc_2sg) .. [=[

| ]=] .. show_form(data.forms.pret_indc_3sg) .. [=[

| ]=] .. show_form(data.forms.pret_indc_1pl) .. [=[

| ]=] .. show_form(data.forms.pret_indc_2pl) .. [=[

| ]=] .. show_form(data.forms.pret_indc_3pl) .. [=[

|-
! style="height:3em;background:#c0cfe4" | future
| ]=] .. show_form(data.forms.futr_indc_1sg) .. [=[

| ]=] .. show_form(data.forms.futr_indc_2sg) .. [=[

| ]=] .. show_form(data.forms.futr_indc_3sg) .. [=[

| ]=] .. show_form(data.forms.futr_indc_1pl) .. [=[

| ]=] .. show_form(data.forms.futr_indc_2pl) .. [=[

| ]=] .. show_form(data.forms.futr_indc_3pl) .. [=[

|-
! style="height:3em;background:#c0cfe4" | conditional
| ]=] .. show_form(data.forms.cond_1sg) .. [=[

| ]=] .. show_form(data.forms.cond_2sg) .. [=[

| ]=] .. show_form(data.forms.cond_3sg) .. [=[

| ]=] .. show_form(data.forms.cond_1pl) .. [=[

| ]=] .. show_form(data.forms.cond_2pl) .. [=[

| ]=] .. show_form(data.forms.cond_3pl) .. [=[

|-
! rowspan="5" style="background:#c0cfe4" | compound<br>tenses
! style="height:3em;background:#c0cfe4" | present perfect
! colspan="6" style="background:#C0C0C0" |  Use the present tense of ]=] .. show_form(data.forms.aux) .. [=[ followed by the past participle

|-
! style="height:3em;background:#c0cfe4" | pluperfect
! colspan="6" style="background:#C0C0C0" |  Use the imperfect tense of ]=] .. show_form(data.forms.aux) .. [=[ followed by the past participle

|-
! style="height:3em;background:#c0cfe4" | past anterior
! colspan="6" style="background:#C0C0C0" |  Use the preterite tense of ]=] .. show_form(data.forms.aux) .. [=[ followed by the past participle

|-
! style="height:3em;background:#c0cfe4" | future perfect
! colspan="6" style="background:#C0C0C0" |  Use the future tense of ]=] .. show_form(data.forms.aux) .. [=[ followed by the past participle

|-
! style="height:3em;background:#c0cfe4" | conditional perfect
! colspan="6" style="background:#C0C0C0" |  Use the conditional tense of ]=] .. show_form(data.forms.aux) .. [=[ followed by the past participle

|-
! style="background:#c0e4c0" colspan="2" | subjunctive
! style="background:#c0e4c0" | que jeo, jou
! style="background:#c0e4c0" | que tu
! style="background:#c0e4c0" | qu’il
! style="background:#c0e4c0" | que nos, nous
! style="background:#c0e4c0" | que vos, vous
! style="background:#c0e4c0" | qu’ils
|-
! rowspan="2" style="background:#c0e4c0" | simple<br>tenses
! style="height:3em;background:#c0e4c0" | present
| ]=] .. show_form(data.forms.pres_subj_1sg) .. [=[

| ]=] .. show_form(data.forms.pres_subj_2sg) .. [=[

| ]=] .. show_form(data.forms.pres_subj_3sg) .. [=[

| ]=] .. show_form(data.forms.pres_subj_1pl) .. [=[

| ]=] .. show_form(data.forms.pres_subj_2pl) .. [=[

| ]=] .. show_form(data.forms.pres_subj_3pl) .. [=[

|-
! style="height:3em;background:#c0e4c0" rowspan="1" | imperfect
| ]=] .. show_form(data.forms.impf_subj_1sg) .. [=[

| ]=] .. show_form(data.forms.impf_subj_2sg) .. [=[

| ]=] .. show_form(data.forms.impf_subj_3sg) .. [=[

| ]=] .. show_form(data.forms.impf_subj_1pl) .. [=[

| ]=] .. show_form(data.forms.impf_subj_2pl) .. [=[

| ]=] .. show_form(data.forms.impf_subj_3pl) .. [=[

|-
! rowspan="2" style="background:#c0e4c0" | compound<br>tenses
! style="height:3em;background:#c0e4c0" | past
! colspan="6" style="background:#C0C0C0" |  Use the present subjunctive of ]=] .. show_form(data.forms.aux) .. [=[ followed by the past participle

|-
! rowspan="1" style="height:3em;background:#c0e4c0" | pluperfect
! colspan="6" style="background:#C0C0C0" |  Use the imperfect subjunctive of ]=] .. show_form(data.forms.aux) .. [=[ followed by the past participle

|-
! colspan="2" rowspan="2" style="height:3em;background:#e4d4c0" | imperative
! style="background:#e4d4c0" | –
! style="background:#e4d4c0" | tu
! style="background:#e4d4c0" | –
! style="background:#e4d4c0" | nos, nous
! style="background:#e4d4c0" | vos, vous
! style="background:#e4d4c0" | –
|-
| —
| ]=] .. show_form(data.forms.impr_2sg) .. [=[

| —
| ]=] .. show_form(data.forms.impr_1pl) .. [=[

| ]=] .. show_form(data.forms.impr_2pl) .. [=[

| —
|-
|}</div></div>]=]
end

-- Create a link for a form
function make_link(subform)
	return m_links.full_link(subform, nil, lang, nil, nil, nil, {},
		mw.title.getCurrentTitle().prefixedText)
end

-- Shows forms, or a dash if empty
function show_form(subforms)
	if not subforms then
		return "&mdash;"
	elseif type(subforms) ~= "table" then
		error("a non-table value was given in the list of inflected forms.")
	elseif #subforms == 0 then
		return "&mdash;"
	end

	-- Concatenate results, omitting duplicates
	local ret = {}
	for key, subform in ipairs(subforms) do
		insert_if_not(ret, subform)
	end
	return table.concat(ret, ", ")
end

return export

-- For Vim, so we get 4-space tabs
-- vim: set ts=4 sw=4 noet:
