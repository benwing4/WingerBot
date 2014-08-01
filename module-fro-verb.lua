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

----------------------------------------------------------------------------
-- Functions for working with stems

-- Given the stem as it appears before a soft-vowel ending (e/i), generate
-- the corresponding stem for a hard-vowel ending (a/o/u).
function stemv_to_stemc(stemv)
	if rfind(stemv, "c$") then
		-- Need to assign to a var because rsub returns 2 values, and
		-- assigning to one var fetches only the first one
		local stemc = rsub(stemv, "c$", "ç")
		return stemc
	elseif rfind(stemv, "g$") then
		local stemc = rsub(stemv, "g$", "j")
		return stemc
	else
		return stemv
	end
end

-- Given the stem as it appears before a hard-vowel ending, generate
-- the corresponding stem for a soft-vowel ending.
function stemc_to_stemv(stemc)
	if rfind(stemc, "c$") then
		-- Need to assign to a var because rsub returns 2 values, and
		-- assigning to one var fetches only the first one
		local stemv = rsub(stemc, "c$", "qu")
		return stemv
	elseif rfind(stemc, "g$") then
		local stemv = rsub(stemc, "g$", "gu")
		return stemv
	elseif rfind(stemc, "ç$") then
		local stemv = rsub(stemc, "ç$", "c")
		return stemv
	else
		return stemc
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

-- Get the stem, either explicitly passed in as the first arg or
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

----------------------------------------------------------------------------
-- Functions for handling comments at the top of conjugation tables

-- Return true if this is an irregular verb, due to stems or particular
-- forms being explicitly specified
function irreg_verb(args)
	for k,v in pairs(args) do
		if k ~= 'stemv' and k ~= 'stemc' and k ~= 'aux' and k ~= 'ier' and
				k ~= 'supe' and k ~= 'refl' and k ~= 'inf' and
				k ~= 'comment' and k ~= 1 and k ~= 2 and
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
-- present tense. Appears near the top of the conjugation chart. STEMV is
-- the unstressed stem before e/i, STEMC the unstressed stem before a/o/u,
-- STEMS the stressed stem. See get_endings() for meaning of IER and SUPE.
function full_verb_comment(args, stemv, stemc, stems, ier, supe)
	if ine(args["comment"]) then
		return mw.text.trim(args["comment"]) .. " "
	end
	local com = verb_comment(stems, ier, supe)
	local irreg = irreg_verb(args)
	if stemv ~= stems and irreg then
		com = com .. "In addition, it has a stressed stem ''" .. stems .. "'' distinct from the unstressed stem ''" .. stemv .. "'', as well as other irregularities. "
	elseif stemv ~= stems then
		com = com .. "In addition, it has a stressed stem ''" .. stems .. "'' distinct from the unstressed stem ''" .. stemv .. "''. "
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

	-- Set the soft ('stemv') and hard ('stemc') vowel infinitive stems.
	-- They can be explicitly set using 'stemv' and 'stemc' params.
	-- If one is set, the other is inferred from it. If neither is set,
	-- both are inferred from the infinitive.
	data.stemv = ine(args["stemv"]) or ine(args[1]) -- for compatibility
	data.stemc = ine(args["stemc"])
	local inf_stem, inf_ending, inf_is_soft =
		get_stem_from_inf(data.forms.infinitive[1], data.ier)
	if not data.stemv and not data.stemc then
		if inf_is_soft then
			data.stemv = inf_stem
		else
			data.stemc = inf_stem
		end
	end
	if not data.stemv then data.stemv = stemc_to_stemv(data.stemc) end
	if not data.stemc then data.stemc = stemv_to_stemc(data.stemv) end

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
function get_args(args, argbase)
	local theargs = {args[argbase] or ""}
	for j = 2, 9 do
		table.insert(theargs, args[argbase .. j] or "")
	end
	return theargs
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

-- Add to DATA the inflections for the tense indicated by TENSE (the prefix
-- in the data.forms names, e.g. 'impf_subj'), formed by combining the STEMS
-- (either a single string or a sequence of six strings) with the
-- ENDINGS (a sequence of six values, each of which is either a string
-- or a sequence of one or more possible endings). If existing
-- inflections already exist, they will be added to, not overridden.
function inflect_tense(data, tense, stems, endings)
	local pnums = {"1sg", "2sg", "3sg", "1pl", "2pl", "3pl"}

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
			table.insert(data.forms[tense .. "_" .. pnums[i]], stem .. ending)
		end
	end
end

-- Add to DATA the endings for the preterite and imperfect
-- subjunctive, with unstressed stem STEMU, stressed stem STEMS, and
-- conjugation type PTY.
function inflect_past_impf_subj(data, stemu, stems, pty)
	-- WARNING: If the second person singular of any of these is not a
	-- simple string, you will need to modify the handling below of
	-- the imperfect subjunctive, which relies on this form.
	local all_endings =
	-- weak-a (-er) and weak-a2 (-ier) are handled separately by the
	-- handlers for -er and -ier. In any case the code here doesn't
	-- properly handle the stemv vs. stemc distinction necessary for these
	-- verbs, and the code below to handle the imperfect subjunctive doesn't
	-- work for them because 1pl, 2pl have -is- not -as-.
	--
	--pty == "weak-a" and {"ai","as",{"a","aṭ"},"ames","astes","erent"} or
	--pty == "weak-a2" and {"ai","as",{"a","aṭ"},"ames","astes","ierent"} or
	pty == "weak-i" and {"i","is",{"i","iṭ"},"imes","istes","irent"} or
	pty == "weak-i2" and {"i","is",{"ié","iéṭ"},"imes","istes","ierent"} or
	pty == "strong-i" and {"","is","t","imes","istes","rent"} or
	pty == "strong-id" and {"","is","t","imes","istes",{"drent","rent"}} or
	pty == "weak-u" and {"ui","us",{"u","uṭ"},"umes","ustes","urent"} or
	pty == "strong-u" and {"ui","eüs","ut","eümes","eüstes","urent"} or
	pty == "strong-o" and {"oi","eüs","ot","eümes","eüstes","orent"} or
	pty == "strong-st" and {"s","sis","st","simes","sistes","strent"} or
	pty == "strong-sd" and {"s","ṣis","st","ṣimes","ṣistes","sdrent"} or
	ine(pty) and error("Unrecognized pty value '" .. pty .. "'") or
	error("Unspecified pty value")

	-- Always use weak stem unless we have strong-stem endings
	local stems =
		(rfind(pty, "^strong-") and {stems, stemu, stems, stemu, stemu, stems}
			or stemu)

	inflect_tense(data, "pret_indc", stems, all_endings)

	-- Handle imperfect subj, which follows the same types as the preterite
	-- and is built off of the 2nd person singular form
	inflect_tense(data, "impf_subj", stemu .. all_endings[2],
		{"se","ses","t",{"sons","siens"},{"soiz","sez","siez"},"sent"})
end

-- Add to DATA the endings for the preterite and
-- imperfect subjunctive, based on the strong and weak stems and past ending
-- type(s) given in ARGS. For each weak past ending type 'pasttyN' there
-- should be a corresponding stem in 'pastN' and for each strong past ending
-- type 'pasttyN' there should be corresponding unstressed and stressed stems
-- in 'pastuN' and 'pastsN'. If no past ending types given, default to the
-- past type in PTY and stem in STEM, which serves for both unstressed and
-- stressed stems.
function handle_past_impf_subj(args, data, stem, pty)
	if not ined(args["pastty"]) then
		inflect_past_impf_subj(data, stem, stem, pty)
	else
		if ined(args["pastty"]) then
			inflect_past_impf_subj(data,
				ine(args["pastu"]) or args["past"] or stem,
				ine(args["pasts"]) or ine(args["pastu"]) or args["past"] or stem,
				args["pastty"])
		end
		for i = 2, 9 do
		if ined(args["pastty" .. i]) then
			inflect_past_impf_subj(data,
				ine(args["pastu" .. i]) or args["past" .. i] or stem,
				ine(args["pasts" .. i]) or ine(args["pastu" .. i]) or args["past" .. i] or stem,
				args["pastty" .. i])
		end
		end
	end
end

-- Add to DATA the endings for the future and conditional, with the stems in
-- STEM, a sequence (generally the infinitive or some modified version).
-- Values in STEM that are empty or "-" are ignored.
function inflect_future_cond(data, stems)
	for _, stem in ipairs(stems) do
		if ined(stem) then
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
	if not ined(args["fut"]) then
		inflect_future_cond(data, {stem})
	else
		inflect_future_cond(data, get_args(args, "fut"))
	end
end

-- Add to DATA the endings for an -er or -ier verb, based on the arguments
-- in ARGS.
inflections["i"] = function(args, data)
	local stemv = data.stemv
	local stemc = data.stemc
	local stems = ine(args["stems"]) or stemv
	local i = data.ier and "i" or ""

	if data.ier then
		data.comment = "This verb conjugates as a first-group verb ending in ''-ier'', with a palatal stem. These verbs are conjugated mostly like verbs in ''-er'', but there is an extra ''i'' before the ''e'' of some endings. "
	else
		data.comment = "This verb conjugates as a first-group verb ending in ''-er''. "
	end
	data.comment = data.comment ..
		full_verb_comment(args, stemv, stemc, stems, data.ier, data.supe)
	data.group = "first"
	data.forms.pres_ptc = {stemc .. "ant"}
	data.forms.past_ptc = {stemv .. i .. "é"}

	data.forms.pres_indc_1sg = {add_zero(stems, data.ier, data.supe)}
	data.forms.pres_indc_2sg = {stems .. "es"}
	data.forms.pres_indc_3sg = {stems .. "e"}
	data.forms.pres_indc_1pl = {stemc .. "ons"}
	data.forms.pres_indc_2pl = {stemv .. i .. "ez"}
	data.forms.pres_indc_3pl = {stems .. "ent"}

	data.forms.pres_subj_1sg = {add_zero(stems, data.ier, data.supe)}
	data.forms.pres_subj_2sg = {add_s(stems, data.ier, data.supe)}
	data.forms.pres_subj_3sg = {add_t(stems, data.ier, data.supe)}
	data.forms.pres_subj_1pl = {stemc .. "ons"}
	data.forms.pres_subj_2pl = {stemv .. i .. "ez"}
	data.forms.pres_subj_3pl = {stems .. "ent"}

	data.forms.impr_2sg = {stems .. "e"}
	data.forms.impr_1pl = {stemc .. "ons"}
	data.forms.impr_2pl = {stemv .. i .. "ez"}

	data.forms.impf_indc_1sg = {stemc .. "oie", stemv .. "eie", stemc .. "oe", stemv .. i .. "eve"}
	data.forms.impf_indc_2sg = {stemc .. "oies", stemv .. "eies", stemc .. "oes", stemv .. i .. "eves"}
	data.forms.impf_indc_3sg = {stemc .. "oit", stemv .. "eit", stemc .. "ot", stemv .. i .. "eve"}
	data.forms.impf_indc_1pl = {stemv .. "iiens", stemv .. "iens"}
	data.forms.impf_indc_2pl = {stemv .. "iiez", stemv .. "iez"}
	data.forms.impf_indc_3pl = {stemc .. "oient", stemv .. "eient", stemc .. "oent", stemv .. i .. "event"}

	data.forms.pret_indc_1sg = {stemc .. "ai"}
	data.forms.pret_indc_2sg = {stemc .. "as"}
	data.forms.pret_indc_3sg = {stemc .. "a"}
	data.forms.pret_indc_1pl = {stemc .. "ames"}
	data.forms.pret_indc_2pl = {stemc .. "astes"}
	data.forms.pret_indc_3pl = {stemv .. i .. "erent"}

	data.forms.impf_subj_1sg = {stemc .. "asse"}
	data.forms.impf_subj_2sg = {stemc .. "asses"}
	data.forms.impf_subj_3sg = {stemc .. "ast"}
	data.forms.impf_subj_1pl = {stemv .. "issons"}
	data.forms.impf_subj_2pl = {stemv .. "issez", stemv .. "issiez"}
	data.forms.impf_subj_3pl = {stemc .. "assent"}

	handle_future_cond(args, data, stemv .. "er")
end

-- Add to DATA the endings for a type 2 verb (-ir, with -iss- infix),
-- based on the arguments in ARGS.
inflections["ii"] = function(args, data)
	local stemv = data.stemv

	data.comment = "This verb conjugates as a second-group verb (ending in ''-ir'', with an ''-iss-'' infix). "
	data.group = "second"

	data.forms.pres_ptc = {stemv .. "issant"}
	data.forms.past_ptc = {stemv .. "i"}

	data.forms.pres_indc_1sg = {stemv .. "is"}
	data.forms.pres_indc_2sg = {stemv .. "is"}
	data.forms.pres_indc_3sg = {stemv .. "ist"}
	data.forms.pres_indc_1pl = {stemv .. "issons"}
	data.forms.pres_indc_2pl = {stemv .. "issez"}
	data.forms.pres_indc_3pl = {stemv .. "issent"}

	data.forms.pres_subj_1sg = {stemv .. "isse"}
	data.forms.pres_subj_2sg = {stemv .. "isses"}
	data.forms.pres_subj_3sg = {stemv .. "isse"}
	data.forms.pres_subj_1pl = {stemv .. "issons"}
	data.forms.pres_subj_2pl = {stemv .. "issez"}
	data.forms.pres_subj_3pl = {stemv .. "issent"}

	data.forms.impr_2sg = {stemv .. "is"}
	data.forms.impr_1pl = {stemv .. "issons"}
	data.forms.impr_2pl = {stemv .. "issez"}

	data.forms.impf_indc_1sg = {stemv .. "issoie", stemv .. "isseie"}
	data.forms.impf_indc_2sg = {stemv .. "issoies", stemv .. "isseies"}
	data.forms.impf_indc_3sg = {stemv .. "issoit", stemv .. "isseit"}
	data.forms.impf_indc_1pl = {stemv .. "issiiens", stemv .. "issiens"}
	data.forms.impf_indc_2pl = {stemv .. "issiiez", stemv .. "issiez"}
	data.forms.impf_indc_3pl = {stemv .. "issoient", stemv .. "isseient"}

	handle_past_impf_subj(args, data, stemv, "weak-i")
	handle_future_cond(args, data, stemv .. "ir")
end

-- Add to DATA the endings for a type 3 verb (-ir without -iss- infix, or
-- -re or -oir), based on the arguments in ARGS.
inflections["iii"] = function(args, data)
	local stemv = data.stemv
	local stemc = data.stemc
	local stems = ine(args["stems"]) or stemv
	local i = data.ier and "i" or ""

	data.comment = "This verb conjugates as a third-group verb (mostly irregular). "
	if data.ier then
		data.comment = data.comment .. "This verb ends in a palatal stem, so there is an extra ''i'' before the ''e'' of some endings. "
	end
	data.comment = data.comment ..
		full_verb_comment(args, stemv, stemc, stems, data.ier, data.supe)
	data.group = "third"

	data.forms.pres_ptc = {stemc .. "ant"}
	data.forms.past_ptc = {stemc .. "u"}

	data.forms.pres_indc_1sg = {add_zero(stems, data.ier, data.supe)}
	data.forms.pres_indc_2sg = {add_s(stems, data.ier, data.supe)}
	data.forms.pres_indc_3sg = {add_t(stems, data.ier, data.supe)}
	data.forms.pres_indc_1pl = {stemc .. "ons"}
	data.forms.pres_indc_2pl = {stemv .. i .. "ez"}
	data.forms.pres_indc_3pl = {stems .. "ent"}

	data.forms.pres_subj_1sg = {stems .. "e"}
	data.forms.pres_subj_2sg = {stems .. "es"}
	data.forms.pres_subj_3sg = {stems .. "e"}
	data.forms.pres_subj_1pl = {stemc .. "ons"}
	data.forms.pres_subj_2pl = {stemv .. i .. "ez"}
	data.forms.pres_subj_3pl = {stemv .. "ent"}

	data.forms.impr_2sg = {add_zero(stems, data.ier, data.supe)}
	data.forms.impr_1pl = {stemc .. "ons"}
	data.forms.impr_2pl = {stemv .. i .. "ez"}

	data.forms.impf_indc_1sg = {stemc .. "oie", stemv .. "eie"}
	data.forms.impf_indc_2sg = {stemc .. "oies", stemv .. "eies"}
	data.forms.impf_indc_3sg = {stemc .. "oit", stemv .. "eit"}
	data.forms.impf_indc_1pl = {stemv .. "iiens", stemv .. "iens"}
	data.forms.impf_indc_2pl = {stemv .. "iiez", stemv .. "iez"}
	data.forms.impf_indc_3pl = {stemc .. "oient", stemv .. "eient"}

	handle_past_impf_subj(args, data, stemv, "weak-i")
	handle_future_cond(args, data, stemc .. "r")
end

-- Shows the table with the given forms
function make_table(data)
	return data.comment .. [=[Old French conjugation varies significantly by date and by region. The following conjugation should be treated as a guide.
<div class="NavFrame" style="clear:both;margin-top:1em">
<div class="NavHead" align=left>&nbsp; &nbsp; Conjugation of ]=] .. m_links.full_link(nil, data.forms.infinitive[1], lang, nil, "term", nil, nil, nil) .. [=[
<span style="font-size:90%;">(see also [[Appendix:Old French verbs]])</span></div>
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

-- Shows forms with links, or a dash if empty
function show_form(subforms)
	if not subforms then
		return "&mdash;"
	elseif type(subforms) ~= "table" then
		error("a non-table value was given in the list of inflected forms.")
	elseif #subforms == 0 then
		return "&mdash;"
	end

	local ret = {}

	-- Go over each subform and insert links
	for key, subform in ipairs(subforms) do
		table.insert(ret, subform)
	end

	return table.concat(ret, ", ")
end

return export

-- For Vim, so we get 4-space tabs
-- vim: set ts=4 sw=4 noet:
