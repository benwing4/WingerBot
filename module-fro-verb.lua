--[[

    module-fro-verb.lua is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

Author: User:benwing

Todo:

1. Possibly, make it possible to specify multiple stems to stem parameters
   separated by commas. This is easiest for fut= but gets trickier for all the
   rest because there are multiple parameters per stem.
2. Should write a routine that extracts the present stems (pres, press, ier,
   plus equivalent for 2 .. 9, and handles the special-casing for 'pres/steme'
   and 'ier', and checks to make sure a multipart spec wasn't given, and uses
   the corresponding prese if so), and uses them in handle_imperfect() and
   handle_pres_part(). Also need to handle 'prese' in the subjunctive and
   imperative code, which should probably be rewritten along the lines of
   handle_imperfect().
3. Create separate categories for verbs ending in various consonants, e.g.
   g, c, ch, ill, gn, etc.
4. Figure out how to create a category for verbs that are missing their
   conjugation (but are still identified as verbs because of {{head|fro|verb}},
   which puts them into Category:Old French verbs). Possibly this isn't
   possible except using a bot.
5. Intro to Old French by Kibler claims that -lm requires a supporting vowel.
   Possibly -ln as well. What about -lf? Evidently -ld does not require a
   supporting vowel, due to 'chaud' < 'calidus'. Should we try to handle -lm
   specially? We might want to also handle -aum, -eum (but not -oum as in
   'noumer', where 'ou' represents earlier 'o' rather than an 'l'). These
   verbs are rare enough, though, and hard enough to handle correctly that
   perhaps we should just require explicitly specifying supe= (or equivalently,
   using {{temp|fro-conj-er-e}} etc.).
--]]

local m_links = require("Module:links")
local m_utilities = require("Module:utilities")

local lang = require("Module:languages").getByCode("fro")

local export = {}

-- Functions that do the actual inflecting by creating the forms of a basic term.
local inflections = {}

local rfind = mw.ustring.find
local rsub = mw.ustring.gsub
local rmatch = mw.ustring.match
local usub = mw.ustring.sub

local function ine(x) -- If Not Empty
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

-- Given the stem as it appears before e/i, generate the corresponding
-- stem for a/o.
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

-- Given the stem as it appears before a/o, generate the corresponding
-- stem for e/i.
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

-- Given the stem as it appears before a/o, generates the corresponding
-- stem for u.
function stema_to_stemu(stema)
	if rfind(stema, "qu$") then
		-- Need to assign to a var because rsub returns 2 values, and
		-- assigning to one var fetches only the first one
		local stemu = rsub(stema, "qu$", "c")
		return stemu
	elseif rfind(stema, "gu$") then
		local stemu = rsub(stema, "gu$", "g")
		return stemu
	else
		return stema
	end
end

-- Given the stem as it appears before e/i, generates the corresponding
-- stem for u.
function steme_to_stemu(steme)
	return stema_to_stemu(steme_to_stema(steme))
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
local function get_stem_from_inf(inf, ier, ir)
	local nsub = 0
	-- if 'ier' arg given and stem ends in -ier, strip it off.
	if ier then
		stem, nsub = rsub(inf, "ier$", "")
		if nsub > 0 then
			return stem, "ier", true
		end
	end
	-- Check for -er, -oir, -eir, -ir, -ïr, -re in sequence.
	-- Must check for -oir, -eir before -ir.
	stem, nsub = rsub(inf, "er$", "")
	if nsub > 0 then
		return stem, "er", true
	end
	if not ir then
		stem, nsub = rsub(inf, "oir$", "")
		if nsub > 0 then
			return stem, "oir", false
		end
		stem, nsub = rsub(inf, "eir$", "")
		if nsub > 0 then
			return stem, "eir", true
		end
	end
	stem, nsub = rsub(inf, "ir$", "")
	if nsub > 0 then
		return stem, "ir", true
	end
	stem, nsub = rsub(inf, "ïr$", "")
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
	local stem = ine(frame.args[1])
	-- if stem passed in and non-blank, use it.
	if stem then
		return stem
	end
	local inf = mw.title.getCurrentTitle().text
	local ier = ine(frame.args["ier"])
	local ir = ine(frame.args["ir"])
	local stem, ending, is_soft = get_stem_from_inf(inf, ier, ir)
	return stem
end

-- External entry point for get_stem_from_frame(). Optional stem is first
-- argument, optional 'ier' argument is used for -ier verbs (see
-- get_stem_from_frame()).
function export.get_stem(frame)
	return get_stem_from_frame(frame)
end

-- Joins a stem to an ending, automatically handling the stem changes needed
-- before different vowels (steme/stema/stemu), and automatically adding umlauts
-- to the stem and/or ending when necessary. The stem form passed in is steme
-- (the form before e/i).
function join(stem, ending)
	local firstend = usub(ending, 1, 1)
	-- change the stem as appropriate
	if firstend == "a" or firstend == "o" then
		stem = steme_to_stema(stem)
	elseif firstend == "u" then
		stem = steme_to_stemu(stem)
	end
	-- add an umlaut to i or u at beginning of ending if there's a vowel
	-- at the end of the stem, unless it's the same vowel, or a diphthong
	-- ending in i/u, or gu/qu.
	if firstend == "i" and
		(rfind(stem, "[aeoü]$") or
		 rfind(stem, "u$") and not rfind(stem, "[gqaäeëéiïoö]u$")) then
		ending = rsub(ending, "^i", "ï")
	elseif firstend == "u" and
		(rfind(stem, "[aeïo]$") or
		 rfind(stem, "i$") and not rfind(stem, "[aäeëéoöuü]i$")) then
		ending = rsub(ending, "^u", "ü")
	-- add an umlaut to i or u at end of stem if ending begins with e/é and
	-- stem doesn't end in diphthong, or gu/qu.
	elseif firstend == "e" or firstend == "é" then
		if rfind(stem, "i$") and not rfind(stem, "[aäeëéoöuü]i$") then
			stem = rsub(stem, "i$", "ï")
		elseif rfind(stem, "u$") and not rfind(stem, "[gqaäeëéiïoö]u$") then
			stem = rsub(stem, "u$", "ü")
		end
	end
	return stem .. ending
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
-- is inferred automatically from the stem). If OLD is specified, don't
-- convert l before consonant to u.
local function get_endings(stem, ier, supe, old)
	local ret = {"", "", "s", "t", ""}
	local ending = nil
	-- canonicalize ngn to gn when after vowel or r, l
	if rfind(stem, "[aeiouyäëïöüÿrl]ngn$") then
		ending = "ngn"
		stem = rsub(stem, "ngn$", "gn")
	end
	-- canonicalize double letter to single after vowel, except for l
	-- we need to treat Cill and Cil differently
	if rfind(stem, "[aeéiouyäëïöüÿ]([bcdfghjkmnpqrstvwxz])%1$") then
		ending = rmatch(stem, "(..)$")
		stem = rsub(stem, "([bcdfghjkmnpqrstvwxz])%1$", "%1")
	end
	if supe then
		ret = supporting_e("")
	elseif rfind(stem, "mb$") then
		ret = mod3("mb", "mp", "ns", "nt")
	elseif rfind(stem, "mp$") then
		ret = mod3("mp", "mp", "ns", "nt")
	elseif rfind(stem, "([aeéiouyäëïöüÿrlmn])[bpdtḍṭfvczk]$") then
		local lastchar = rmatch(stem, "(.)$")
		ending = ending or lastchar
		if lastchar == "b" or lastchar == "p" then
			ret = mod3(ending, "p", "s", "t")
		elseif lastchar == "d" or lastchar == "t" then
			ret = mod3(ending, "t", "z", "t")
		elseif lastchar == "ḍ" or lastchar == "ṭ" then
			ret = mod3(ending, "ṭ", "z", "t")
		elseif lastchar == "f" or lastchar == "v" then
			ret = mod3(ending, "f", "s", "t")
		elseif lastchar == "c" then
			ret = mod3(ending, "z", "z", "zt")
			ret[5] = ret[5] .. "In addition, ''c'' becomes ''ç'' before an ''a, o'' or ''u'' to keep the /ts/ sound intact. "
		-- at least in bauptizer, 'z' appears to represent /z/, like 's'
		-- in the same position
		elseif lastchar == "z" then
			ret = mod3(ending, "s", "s", "st")
		elseif lastchar == "k" then
			ret = mod3(ending, "k", "s", "t")
		else
			error("Logic error! Unhandled case for character '" .. lastchar .. "'")
		end
	elseif rfind(stem, "([aeéiouyäëïöüÿrlmn])c?qu$") then
		ending = rmatch(stem, "(c?qu)$")
		ret = mod3(ending, "c", "s", "t")
	elseif rfind(stem, "([aeéiouyäëïöüÿrlmn])g?gu$") then
		ending = rmatch(stem, "(g?gu)$")
		ret = mod3(ending, "c", "s", "t")
	elseif rfind(stem, "([aeéiouyäëïöüÿrlmn])ct$") then
		-- convicter, paincter. Best guess here
		ret = mod3("ct", "ct", "cz", "ct")
	elseif rfind(stem, "([aeéiouyäëïöüÿrlmn])s[bpdtczk]$") then
		local lastchar = rmatch(stem, "(.)$")
		ending = "s" .. (ending or lastchar)
		if lastchar == "b" or lastchar == "p" then
			-- Best guess here, esp. for 'sb'
			ret = mod3(ending, "sp", "s", "st")
		elseif lastchar == "d" or lastchar == "t" then
			-- croster, etc.
			-- brosder. Best guess here
			ret = mod3(ending, "st", "z", "st")
		elseif lastchar == "c" or lastchar == "z" then
			-- drescier, laiszier(?). Best guess here
			ret = mod3(ending, "z", "z", "zt")
			if lastchar == "c" then
				ret[5] = ret[5] .. "In addition, ''c'' becomes ''ç'' before an ''a, o'' or ''u'' to keep the /ts/ sound intact. "
			end
		elseif lastchar == "k" then
			ret = mod3(ending, "sk", "s", "st")
		else
			error("Logic error! Unhandled case for character '" .. lastchar .. "'")
		end
	elseif rfind(stem, "([aeéiouyäëïöüÿrlmn])s[qg]u$") then
		-- Best guess here
		ending = rmatch(stem, "(s[qg]u)$")
		ret = mod3(ending, "sc", "s", "st")
	elseif old and (rfind(stem, "([aeéouäëöü])[iy]ll?$") or (rfind(stem, "[aeéouäëöü]ll?$") and ier)) then
		ending = rmatch(stem, "(.[iy]?ll?)$")
		local prev = rmatch(stem, "(.[iy]?)ll?$")
		ret = mod3(ending, prev .. "l", prev .. "lz", prev .. "lt")
	elseif rfind(stem, "([aeéoäëö])[iy]ll?$") or (rfind(stem, "[aeéoäëö]ll?$") and ier) then
		ending = rmatch(stem, "(.[iy]?ll?)$")
		local i = ine(rmatch(stem, "([iy]?)ll?$")) or "i"
		local prev = rmatch(stem, "(.)[iy]?ll?$")
		ret = mod3(ending, prev .. i .. "l", prev .. "uz", prev .. "ut")
	elseif rfind(stem, "[uü][iy]ll?$") or (rfind(stem, "[uü]ll?$") and ier) then
		ending = rmatch(stem, "([uü][iy]?ll?)$")
		local i = ine(rmatch(stem, "([iy]?)ll?$")) or "i"
		local u = rmatch(stem, "([uü])[iy]?ll?$")
		ret = mod3(ending, u .. i .. "l", u .. "z", u .. "t")
	elseif rfind(stem, "[iïyÿ]ll$") or (rfind(stem, "[iïyÿ]l$") and ier) then
		ending = rmatch(stem, "([iïyÿ]ll?)$")
		local i = rmatch(stem, "([iïyÿ])ll?$")
		ret = old and mod3(ending, i .. "l", i .. "lz", i .. "lt")
			or mod3(ending, i .. "l", i .. "z", i .. "t")
	elseif rfind(stem, "([^iu])[eé]ll?$") or rfind(stem, "ëll?$") then
		-- first rfind() above should not have ïü or ë in it
		ending = rmatch(stem, "([eéë]ll?)$")
		local e = rmatch(stem, "([eéë])ll?$")
		-- FIXME: Should this be eals, ealt when old?
		ret = old and mod3(ending, e .. "l", e .. "ls", e .. "lt")
			or mod3(ending, e .. "l", e .. "aus", e .. "aut")
	elseif rfind(stem, "([aeéoäö])ll?$") then -- not ë, handled above
		-- first rmatch below should not have ïü or ë in it
		ending = rmatch(stem, "([iu][eé]ll?)$") or rmatch(stem, "([aoäö]ll?)$")
		local prev = rmatch(stem, "([iu][eé])ll?$") or rmatch(stem, "([aoäö])ll?$")
		ret = old and mod3(ending, prev .. "l", prev .. "ls", prev .. "lt")
			or mod3(ending, prev .. "l", prev .. "us", prev .. "ut")
	elseif rfind(stem, "([iuyïüÿ])ll?$") then
		ending = rmatch(stem, "(.ll?)$")
		local prev = rmatch(stem, "(.)ll?$")
		ret = old and mod3(ending, prev .. "l", prev .. "ls", prev .. "lt")
			or mod3(ending, prev .. "l", prev .. "s", prev .. "t")
	elseif rfind(stem, "[iyïÿl]gn$") then
		local prev = rmatch(stem, "([iyïÿl])gn$")
		ret = mod3(prev .. (ending or "gn"), prev .. "ng", prev .. "nz", prev .. "nt")
	elseif rfind(stem, "rgn$") then
		ret = mod3("r" .. (ending or "gn"), "rng", "rz", "rt")
	elseif rfind(stem, "([aeéouäëöü])gn$") then
		local prev = rmatch(stem, "(.)gn$")
		ret = mod3(prev .. (ending or "gn"), prev .. "ing", prev .. "inz", prev .. "int")
	elseif rfind(stem, "rm$") then
		ret = mod3("rm", "rm", "rs", "rt")
	elseif rfind(stem, "rn$") then
		ret = mod3("rn", "rn", "rz", "rt")
	elseif rfind(stem, "[aeéiouyäëïöüÿl]m$") then
		ret = mod3(ending or "m", "m", "ns", "nt")
	elseif rfind(stem, "s$") then
		ret = mod3(ending or "s", "s", "s", "st")
	elseif rfind(stem, "g$") then
		ret = supporting_e("In addition, ''g'' becomes ''j'' before an ''a'' or an ''o'' to keep the /dʒ/ sound intact. ")
	elseif rfind(stem, "j$") or rfind(stem, "x$")
			or rfind(stem, "[^aeéiouyäëïöüÿ][bcdfghjklmnpqrtvwxz]$") then
		ret = supporting_e("")
	elseif ending then
		-- doubled rr, nn, hh
		local lastchar = rmatch(stem, "(.)$")
		ret = mod3(ending, lastchar, lastchar .. "s", lastchar .. "t")
	end
	return ret
end

----------------------------------------------------------------------------
-- Functions for handling particular sorts of endings

-- Convert a stressed verb stem to the form used with a zero ending
-- (1st sing pres indic, also, 1st sing pres subj of -er verbs).
-- See get_endings() for meaning of IER and SUPE.
function add_zero(stem, ier, supe, old)
	local e = get_endings(stem, ier, supe, old)
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
-- not /ts/). See get_endings() for meaning of IER, SUPE and OLD.
function add_s(stem, ier, supe, old)
	local e = get_endings(stem, ier, supe, old)
	-- We need to assign to a variable here because rsub() returns multiple
	-- values and we want only the first returned. Return rsub() directly
	-- and all values get returned and appended to the string.
	local ret, nsub = rsub(stem, e[1] .. "$", e[3])
	assert(nsub == 1)
	return ret
end

-- Convert a stressed verb stem to the form used with a -t ending
-- (3rd sing pres indic of -ir/-oir/-re verbs, 3rd sing pres subj of
-- -er verbs). See get_endings() for meaning of IER, SUPE and OLD.
function add_t(stem, ier, supe, old)
	local e = get_endings(stem, ier, supe, old)
	-- We need to assign to a variable here because rsub() returns multiple
	-- values and we want only the first returned. Return rsub() directly
	-- and all values get returned and appended to the string.
	local ret, nsub = rsub(stem, e[1] .. "$", e[4])
	assert(nsub == 1)
	return ret
end

-- Add -r, for the group-iii future
function add_r(stem, old)
	local ret = stem .. "r"
	if rfind(stem, "ss$") then
		ret = rsub(stem, "ss$", "str")
	elseif rfind(stem, "is$") then
		ret = rsub(stem, "is$", "ir")
	elseif rfind(stem, "ïs$") then
		ret = rsub(stem, "ïs$", "ïr")
	elseif rfind(stem, "s$") then
		ret = stem .. "dr"
	elseif rfind(stem, "g?n$") then
		ret = rsub(stem, "g?n$", "ndr")
	elseif rfind(stem, "m$") then
		ret = stem .. "br"
	elseif rfind(stem, "i?ll?$") then
		ret = old and rsub(stem, "ll?$", "ldr") or rsub(stem, "i?ll?$", "udr")
	elseif rfind(stem, "qu$") then
		ret = rsub(stem, "qu$", "cr")
	elseif rfind(stem, "gu$") then
		ret = rsub(stem, "gu$", "gr")
	elseif rfind(stem, "[^aeiouäëïöü]r$") then
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
		if k == "pres" and rfind(v, "/") or
				k ~= "pres" and k ~= "prese" and k ~= "presa" and
				k ~= "ier" and k ~= "supe" and k ~= "aux" and k ~= "refl" and
				k ~= "repl" and k ~= "prefix" and k ~= "suffix" and
				k ~= "old" and k ~= "ei" and k ~= "ir" and
				k ~= "impers" and k ~= "inf" and k ~= "comment" and
				not contains(skip, k) and v ~= '' then
			return true
		end
	end
	return false
end

-- Return comment describing phonetic changes to the verb in the present
-- tense. Appears near the top of the conjugation chart. STEM is the stressed
-- stem. See get_endings() for meaning of IER, SUPE and OLD.
function phonetic_verb_comment(stem, ier, supe, old)
	local e = get_endings(stem, ier, supe, old)
	return e[5]
end

-- Return comment describing phonetic and stem changes to the verb in the
-- present tense. Appears near the top of the conjugation chart. STEME is
-- the unstressed stem before e/i, STEMS the stressed stem.
-- See get_endings() for meaning of IER, SUPE and OLD.
function verb_comment(args, group, steme, stems, ier, supe, old)
	if args["comment"] then
		return args["comment"] .. " "
	end
	local com = group == "i" and phonetic_verb_comment(stems, ier, supe, old) or ""
	local irreg = irreg_verb(args, 'press')
	if steme ~= stems then
		if args["repl"] then
			-- If there's a search/replace, it might change the stressed or
			-- unstressed stems. FIXME: apply search/replace to the stems
			-- themselves.
			com = com .. "This verb has a distinct stressed present stem"
		else
			com = com .. "This verb has a stressed present stem ''" ..
			    (args["prefix"] or "") .. stems .. (args["suffix"] or "") ..
				"'' distinct from the unstressed stem ''" .. 
				(args["prefix"] or "") .. steme .. (args["suffix"] or "") .. "''"
		end
		com = com ..
			(irreg and ", as well as other irregularities. " or ". ")
	elseif irreg then
		com = com .. "This verb has irregularities in its conjugation. "
	end
	return com
end

----------------------------------------------------------------------------
-- Main inflection-handling functions

-- Main entry point
function export.show(frame)
	local origargs = frame:getParent().args
	local args = {}
	-- Convert empty arguments to nil, and "" or '' arguments to empty
	for k, v in pairs(origargs) do
		args[k] = ine(v)
	end

	-- Create the forms
	local data = {forms = {}, categories = {}, group = {}, comment = "",
	refl = args["refl"],
	impers = args["impers"],
	ier = args["ier"] or ine(frame.args["ier"]),
	supe = args["supe"] or ine(frame.args["supe"])
	}

	data.forms.infinitive =
		{args["inf"] or mw.title.getCurrentTitle().text}
	data.inf_from_title = not args["inf"]
	data.inf_no_affix = data.forms.infinitive[1]
	if args["prefix"] and data.inf_from_title then
		data.inf_no_affix = rsub(data.inf_no_affix, "^" .. args["prefix"], "")
	end
	if args["suffix"] and data.inf_from_title then
		data.inf_no_affix = rsub(data.inf_no_affix, args["suffix"] .. "$", "")
	end
	
	

	-- Set the soft vowel ('pres') and hard vowel ('presa') present stems.
	-- They can be explicitly set using 'pres' and 'presa' params.
	-- If one is set, the other is inferred from it. If neither is set,
	-- both are inferred from the infinitive.
	data.prese = args["pres"] and not rfind(args["pres"], "/") and args["pres"] or
		args["prese"]
	local inf_stem, inf_ending, inf_is_soft =
		get_stem_from_inf(data.inf_no_affix, data.ier, args["ir"])
	if not data.prese then
		if inf_is_soft then
			data.prese = inf_stem
		else
			data.prese = stema_to_steme(inf_stem)
		end
	end

	data.old = args["old"]
	data.ei = args["ei"] or data.old or inf_ending == "eir"
	data.forms.aux = {data.refl and "estre" or args["aux"] or
		data.ei and "aveir" or "avoir"}

	-- Find what type of verb is it (hard-coded in the template).
	-- Generate standard conjugated forms for each type of verb.
	local infl_type = ine(frame.args["type"])
	if not infl_type then
		error("Verb type ('type' arg) not specified.")
	elseif inflections[infl_type] then
		inflections[infl_type](args, data)
	else
		error("Verb type '" .. infl_type .. "' not supported.")
	end

	for _, group in ipairs(data.group) do
		table.insert(data.categories, "Old French " .. group .. " group verbs")
	end
	table.insert(data.categories, "Old French verbs ending in -" .. inf_ending)
	if data.impers then
		table.insert(data.categories, "Old French impersonal verbs")
	end

	-- Get overridden forms
	process_overrides(args, data)

	-- Add a prefix if specified
	if args["prefix"] then
		add_affix(data, args["prefix"], true)
	end

	-- Add a suffix if specified
	if args["suffix"] then
		add_affix(data, args["suffix"], false)
	end

	-- Apply any replacements
	local repl = args["repl"]
	if repl then
		replace_all(data, repl)
	end

	-- Add links
	add_links(data)

	-- Add reflexive pronouns
	if data.refl then
		add_reflexive_pronouns(args, data)
	end

	return make_table(data) .. m_utilities.format_categories(data.categories, lang)
end

-- Version of main entry point meant for calling from the debug console.
function export.show2(args, parargs)
	local frame = {args = args, getParent = function() return {args = parargs} end}
	return export.show(frame)
end

-- If ARGBASE == "foo", return an array of
-- {{args["foo"]},{args["foo2"]},...,{args["foo9"]}}.
-- If ARGBASE is a sequence of strings, return an array of sequences, e.g.
-- if ARGBASE == {"foo", "bar"}, return an array of
-- {{{args["foo"]},{args["bar"]}},{{args["foo2"]},{args["bar2"]}},...,{{args["foo9"]},{args["bar9"]}}}
-- There is an extra level of {}'s because nil can't be inserted into an array
function get_args(args, argbase)
	if type(argbase) == "string" then
		local theargs = {{args[argbase]}}
		for j = 2, 9 do
			table.insert(theargs, {args[argbase .. j]})
		end
		return theargs
	else
		local theargs = {}
		local onearg = {}
		for i, item in ipairs(argbase) do
			table.insert(onearg, {args[item]})
		end
		table.insert(theargs, onearg)
		for j = 2, 9 do
			onearg = {}
			for i, item in ipairs(argbase) do
				table.insert(onearg, {args[item .. j]})
			end
			table.insert(theargs, onearg)
		end
		return theargs
	end
end

-- Replaces terms with overridden ones that are given as additional named parameters.
function process_overrides(args, data)
	-- Each term in current is overridden by one in overN, if it exists.
	local function override(current, over)
		current = current or {}
		local ret = {}

		local i = 1

		local function getover(n)
			return args[over .. n]
		end
		
		-- Insert an override entry, possibly splitting on commas and
		-- inserting multiple forms.
		local function insert_override(entry)
			if entry ~= "-" then
				if rfind(entry, ",") then
					local forms = mw.text.split(entry, ",")
					for _, form in ipairs(forms) do
						table.insert(ret, form)
					end
				else
					table.insert(ret, entry)
				end
			end
		end

		-- Look for overrides at the beginning
		if getover(0) then
			insert_override(getover(0))
		end
		
		-- Look for override of all current forms
		if getover("") then
			current = {}
			insert_override(getover(""))
		end
		
		-- See if any of the existing items in current have an override specified.
		while current[i] do
			if getover(i) then
				insert_if_not(data.categories, "Old French verbs with partial overrides")
				insert_override(getover(i))
			else
				table.insert(ret, current[i])
			end

			i = i + 1
		end

		-- We've reached the end of current.
		-- Look in the override list to see if there are any extra forms to
		-- add on to the end. NOTE: We've deprecated this and made it an error.
		-- Use ...n to insert forms at the end.
		while i <= 9 do
			if getover(i) then
				error("Attempt to partially override a non-existent form: arg "
					.. over .. i .. "=" .. getover(i) ..
					": use " .. over .. "n=" .. getover(i) .. " instead.")
				-- insert_override(getover(i))
			end

			i = i + 1
		end

		-- Look for overrides at the end
		if getover("n") then
			insert_override(getover("n"))
		end
		
		return ret
	end

	-- Mark terms with any additional parameters as irregular, except for
	-- certain ones that we consider normal variants.
	if irreg_verb(args) then
		table.insert(data.categories, "Old French irregular verbs")
	end
	--[[
	This function replaces former code like this:

	data.forms.pret_indc_1sg = override(data.forms.pret_indc_1sg, "pret1s")
	data.forms.pret_indc_2sg = override(data.forms.pret_indc_2sg, "pret2s")
	data.forms.pret_indc_3sg = override(data.forms.pret_indc_3sg, "pret3s")
	data.forms.pret_indc_1pl = override(data.forms.pret_indc_1pl, "pret1p")
	data.forms.pret_indc_2pl = override(data.forms.pret_indc_2pl, "pret2p")
	data.forms.pret_indc_3pl = override(data.forms.pret_indc_3pl, "pret3p")
	--]]
	local function handle_tense_override(tense, short)
		local pnums = {"1sg", "2sg", "3sg", "1pl", "2pl", "3pl"}
		local pnums_short = {"1s", "2s", "3s", "1p", "2p", "3p"}
		for pn = 1, #pnums do
			local pnum = pnums[pn]
			local pnum_short = pnums_short[pn]
			local tensepnum = tense .. "_" .. pnum
			data.forms[tensepnum] =
				override(data.forms[tensepnum], short .. pnum_short)
		end
	end


	-- Non-finite forms
	-- data.forms.infinitive = override(data.forms.infinitive, "inf")
	data.forms.pres_ptc = override(data.forms.pres_ptc, "presp")
	data.forms.past_ptc = override(data.forms.past_ptc, "pastp")

	handle_tense_override("pres_indc", "pres") -- Present
	handle_tense_override("impf_indc", "imperf") -- Imperfect
	handle_tense_override("pret_indc", "pret") -- Preterite
	handle_tense_override("futr_indc", "fut") -- Future
	handle_tense_override("cond", "cond") -- Conditional
	handle_tense_override("pres_subj", "sub") -- Present subjunctive
	handle_tense_override("impf_subj", "impsub") -- Imperfect subjunctive

	-- Imperative
	data.forms.impr_2sg = override(data.forms.impr_2sg, "imp2s")
	data.forms.impr_1pl = override(data.forms.impr_1pl, "imp1p")
	data.forms.impr_2pl = override(data.forms.impr_2pl, "imp2p")
end

-- Adds reflexive pronouns to the appropriate forms
function add_reflexive_pronouns(args, data)
	-- Gather pronoun parameters
	local cprons = {}
	local vprons = {}

	cprons["1sg"] = args["me"] or "me "
	cprons["2sg"] = args["te"] or "te "
	cprons["3sg"] = args["se"] or "se "
	cprons["1pl"] = args["nos"] or "nos "
	cprons["2pl"] = args["vos"] or "vos "
	cprons["3pl"] = cprons["3sg"]

	vprons["1sg"] = args["me"] or "m'"
	vprons["2sg"] = args["te"] or "t'"
	vprons["3sg"] = args["se"] or "s'"
	vprons["1pl"] = args["nos"] or "nos "
	vprons["2pl"] = args["vos"] or "vos "
	vprons["3pl"] = vprons["3sg"]

	function add_refl(person, form)
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
		data.forms.impr_2sg[key] = subform .. (data.ei and "-tei" or "-toi")
	end
	for key, subform in ipairs(data.forms.impr_1pl) do
		data.forms.impr_1pl[key] = subform .. "-nos"
	end
	for key, subform in ipairs(data.forms.impr_2pl) do
		data.forms.impr_2pl[key] = subform .. "-vos"
	end
end

-- Add links to all forms
function add_links(data)
	for key, subforms in pairs(data.forms) do
		for key2, subform in ipairs(subforms) do
			data.forms[key][key2] = make_link(subform)
		end
	end
end

-- Add a prefix or suffix to all forms. AFFIX is what to add; IS_PREFIX is
-- true if it's a prefix, otherwise a suffix.
function add_affix(data, affix, is_prefix)
	for key, subforms in pairs(data.forms) do
		-- Don't add affix to aux, nor infinitive
		-- that comes from the page title.
		if key ~= "aux" and (key ~= "infinitive" or not data.inf_from_title) then
			for key2, subform in ipairs(subforms) do
				data.forms[key][key2] =
					(is_prefix and affix .. subform or subform .. affix)
			end
		end
	end
end

-- Apply all replacements
function replace_all(data, repl)
	for splitrepl in mw.text.gsplit(repl, ",") do
		local fromto = mw.text.split(splitrepl, "/")
		if #fromto ~= 2 then
			error("Replace spec '" .. splitrepl .. "' needs exactly one / in it")
		end
		local from = fromto[1]
		local to = fromto[2]
		for key, subforms in pairs(data.forms) do
			-- Don't search/replace on aux, nor on infinitive
			-- that comes from the page title. Don't want e.g. infinitive
			-- 'offrir' to become 'offffrir'.
			if key ~= "aux" and (key ~= "infinitive" or not data.inf_from_title) then
				for key2, subform in ipairs(subforms) do
					data.forms[key][key2] = rsub(data.forms[key][key2], from, to)
				end
			end
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
			local form = join(stem, ending)
			if ine(form) and form ~= "-" and
					(not data.impers or pnums[i] == "3sg") then
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

function inflect_pres(data, tense, group, steme, stems, ier, supe)
	local i = ier and "i" or ""
	if steme ~= stems then
		insert_if_not(data.categories, "Old French verbs with stem alternations")
	end
	local oldt = data.old and "ṭ" or ""
	if tense == "impr" and group == "i" then
		inflect_tense_impr(data, tense,
			{stems, steme, steme},
			{"e", "ons", i .. "ez"})
	elseif tense == "impr" and group == "ii" then
		inflect_tense_impr(data, tense, steme, 
			{"is", "issons", "issez"})
	elseif tense == "impr" and group == "iii" then
		inflect_tense_impr(data, tense,
			{add_zero(stems, ier, supe, data.old), steme, steme},
			{"", "ons", i .. "ez"})
	elseif tense == "pres_indc" and group == "i" then
		inflect_tense(data, tense,
			{add_zero(stems, ier, supe, data.old), stems, stems, steme, steme, stems},
			{"", "es", "e".. oldt, "ons", i .. "ez", "ent"})
	elseif tense == "pres_indc" and group == "ii" then
		inflect_tense(data, tense, steme,
			{"is", "is", "ist", "issons", "issez", "issent"})
	elseif tense == "pres_subj" and group == "ii" then
		inflect_tense(data, tense, steme,
			{"isse", "isses", "isse" .. oldt, "issons", "issez", "issent"})
	elseif tense == "pres_subj" and group == "iii" then
		inflect_tense(data, tense, {stems, stems, stems, steme, steme, stems},
			{"e", "es", "e" .. oldt,
			 ier and {"iens", "ons"} or "ons", i .. "ez", "ent"})
	else -- pres_indc group iii or pres_subj group i
		inflect_tense(data, tense,
			{add_zero(stems, ier, supe, data.old),
			 add_s(stems, ier, supe, data.old),
			 add_t(stems, ier, supe, data.old), steme, steme, stems},
			{"", "", "", "ons", i .. "ez", "ent"})
	end
end

-- Split a string into entries separated by slashes, each representing one
-- of the possible person/number combinations. Each entry in turn may consist
-- of one or more forms, separated by commas. NUMREQ is how many entries need
-- to be present, defaulting to 6.
function split_multipart(str, numreq)
	local entries = mw.text.split(str, "/")

	numreq = numreq or 6
	if #entries ~= numreq then
		error("Expected " .. numreq .. " entries in multipart string '" .. str .. "'")
	end

	for i, entry in ipairs(entries) do
		if rfind(entry, ",") then
			entries[i] = mw.text.split(entry, ",")
		else
			entries[i] = {entry}
		end
	end
		
	return entries
end

function handle_pres(args, data, group, steme, stems)
	local ier = data.ier
	local supe = data.supe
	if args["pres"] and rfind(args["pres"], "/") then
		inflect_tense(data, "pres_indc", "", split_multipart(args["pres"]))
	else
		inflect_pres(data, "pres_indc", group, steme, stems, ier, supe)
	end
	-- If sub not set, derive from indicative.
	-- If subs not set, derive from sub if set, else from indicative.
	local sub_steme = args["sub"]
	local sub_dash = sub_steme == "-"
	local sub_specified = sub_steme
	if sub_steme and rfind(sub_steme, "/") then
		inflect_tense(data, "pres_subj", "", split_multipart(sub_steme))
	elseif not sub_dash then
		if not sub_specified then
			sub_steme = steme
		end
		local sub_stems = args["subs"]
		if not sub_stems then
			sub_stems = sub_specified and sub_steme or stems
		end
		inflect_pres(data, "pres_subj", group, sub_steme, sub_stems,
			args["subier"] or (not sub_specified and ier),
			args["subsupe"] or (not sub_specified and supe))
	end

	-- Repeat exactly for the imperative.
	local imp_steme = args["imp"]
	local imp_dash = imp_steme == "-"
	local imp_specified = imp_steme
	if imp_steme and rfind(imp_steme, "/") then
		inflect_tense_impr(data, "impr", "", split_multipart(imp_steme, 3))
	elseif not imp_dash then
		if not imp_specified then
			imp_steme = steme
		end
		local imp_stems = args["imps"]
		if not imp_stems then
			imp_stems = imp_specified and imp_steme or stems
		end
		inflect_pres(data, "impr", group, imp_steme, imp_stems,
			args["impier"] or (not imp_specified and ier),
			args["impsupe"] or (not imp_specified and supe))
	end

	-- If indic stem specified, we add indic values, and also corresponding
	-- subj values if separate subj stem not specified.
	for i = 2, 9 do
		steme = args["pres" .. i]
		local multi_indic = steme and rfind(steme, "/")
		local indic_specified = not multi_indic and steme
		if multi_indic then
			inflect_tense(data, "pres_indc", "", split_multipart(steme))
		elseif indic_specified then
			stems = args["press" .. i] or steme
			ier = args["ier" .. i]
			supe = args["supe" .. i]
			inflect_pres(data, "pres_indc", group, steme, stems, ier, supe)
		end

		-- Handle subjunctive as above.
		sub_steme = args["sub" .. i]
		sub_dash = sub_steme == "-"
		sub_specified = sub_steme
		if sub_steme and rfind(sub_steme, "/") then
			inflect_tense(data, "pres_subj", "", split_multipart(sub_steme))
		elseif not sub_dash and (indic_specified or sub_specified) then
			if not sub_specified then
				sub_steme = steme
			end
			sub_stems = args["subs" .. i]
			if not sub_stems then
				sub_stems = sub_specified and sub_steme or stems
			end
			inflect_pres(data, "pres_subj", group, sub_steme,
				sub_stems,
				args["subier" .. i] or (not sub_specified and ier),
				args["subsupe" .. i] or (not sub_specified and supe))
		end

		-- Repeat for the imperative.
		imp_steme = args["imp" .. i]
		imp_dash = imp_steme == "-"
		imp_specified = imp_steme
		if imp_steme and rfind(imp_steme, "/") then
			inflect_tense_impr(data, "impr", "", split_multipart(imp_steme, 3))
		elseif not imp_dash and (indic_specified or imp_specified) then
			if not imp_specified then
				imp_steme = steme
			end
			imp_stems = args["imps" .. i]
			if not imp_stems then
				imp_stems = imp_specified and imp_steme or stems
			end
			inflect_pres(data, "impr", group, imp_steme,
				imp_stems,
				args["impier" .. i] or (not imp_specified and ier),
				args["impsupe" .. i] or (not imp_specified and supe))
		end
	end
end

-- Add to DATA the endings for the preterite and imperfect
-- subjunctive, with unstressed e/i stem STEME, stressed e/i stem STEMS,
-- conjugation type PTY and corresponding value of IMPSUB.
function inflect_pret_impf_subj(data, stem, pty, pret, pretu, prets, impsub)
	local steme = pretu or pret or stem
	local stems = prets or pretu or pret or stem
	if pret and rfind(pret, "/") then
		inflect_tense(data, "pret_indc", "", split_multipart(pret))
		inflect_impf_subj(data, impsub, nil, nil, nil)
	elseif pty then
		insert_if_not(data.categories, "Old French verbs with " .. pty .. " preterite")
		-- WARNING: If the second person singular of any of these is not a
		-- simple string, you will need to modify the handling below of
		-- the imperfect subjunctive, which relies on this form.
		local oldt = data.old and "ṭ" or ""
		local all_endings =
	pty == "weak-a" and {"ai","as","a" .. oldt,"ames","astes","erent"} or
	pty == "weak-a2" and {"ai","as","a" .. oldt,"ames","astes","ierent"} or
	pty == "weak-i" and {"i","is","i" .. oldt,"imes","istes","irent"} or
	-- FIXME: "Grammatik des Altfranzösischen I-III" (Dr. E. Schwan and
	-- Dr. D. Behrens), p. 229, claims that the old form of the weak-i2
	-- ending is "ieḍrent", e.g. "rendieḍrent" < "rendęderunt", whereas the
	-- early 12th-century forms of E. Einhorn "Old French: A Concise Handbook"
	-- p.43 have only "ierent". I trust the latter because Schwan and Behrens
	-- also have the 3rd-singular as "rendiet" with a hard -t < "rendędit",
	-- but in reality it should be "rendieṭ" (i.e. "rendiéṭ") with a soft -ṭ,
	-- as per Einhorn and also William Kibler "An Introduction to Old French".
	-- Schwan and Behrens' forms would be correct if the underlying Vulgar
	-- Latin forms are correct, but I think haplology has deleted the second
	-- -d- so you should really have 3rd-singular "rendęt" > "rendiéṭ" and
	-- 3rd-plural "rendęrunt" > "rendierent".
	pty == "weak-i2" and {"i","is","ié" .. oldt,"imes","istes","ierent"} or
	pty == "strong-i" and {"","is","t","imes","istes","rent"} or
	pty == "strong-id" and {"","is","t","imes","istes",{"drent","rent"}} or
	pty == "weak-u" and {"ui","us","u" .. oldt,"umes","ustes","urent"} or
	pty == "strong-u" and {"ui","eüs","ut","eümes","eüstes","urent"} or
	pty == "strong-o" and {"oi","eüs","ot","eümes","eüstes","orent"} or
	pty == "strong-st" and {"s","sis","st","simes","sistes","strent"} or
	pty == "strong-sd" and {"s","ṣis","st","ṣimes","ṣistes","sdrent"} or
	error("Unrecognized prettype value '" .. pty .. "'")

		-- Always use one of the weak stems unless we have strong-stem endings
		local all_stems =
rfind(pty, "^strong-") and {stems, steme, stems, steme, steme, stems} or
{steme, steme, steme, steme, steme, steme}

		inflect_tense(data, "pret_indc", all_stems, all_endings)
		inflect_impf_subj(data, impsub, steme,
			join(all_stems[2], all_endings[2]), pty)
	elseif impsub then
		inflect_impf_subj(data, impsub, nil, nil, nil)
	end
end

function inflect_impf_subj(data, impsub, steme, pret2s, pty)
	-- Handle imperfect subj, which follows the same types as the preterite
	-- and is built off of the 2nd person singular form, although we need to
	-- special-case weak-a and weak-a2
	local impsub_endings =
		{"se","ses","t",{"sons","siens"},
			{data.ei and "seiz" or "soiz","sez","siez"},"sent"}
	if impsub and rfind(impsub, "/") then
		inflect_tense(data, "impf_subj", "", split_multipart(impsub))
	elseif impsub == "-" then
		return
	elseif impsub then
		inflect_tense(data, "impf_subj", impsub, impsub_endings)
	-- need the % here to escape the dash, which otherwise stands for a
	-- character range???????
	elseif pty and rfind(pty, "^weak%-a") then
		inflect_tense(data, "impf_subj", steme,
			{"asse","asses","ast", {"issons","issiens"},
				{data.ei and "isseiz" or "issoiz","issez","issiez"},"assent"})
	elseif pty then
		inflect_tense(data, "impf_subj", pret2s, impsub_endings)
	end
end

-- Add to DATA the endings for the preterite and imperfect subjunctive,
-- based on the strong and weak stems and preterite ending type(s) given in
-- ARGS. For each weak preterite ending type 'prettypeN' there should be a
-- corresponding stem in 'pretN' (defaulting to STEM) and for each strong
-- preterite ending type 'prettypeN' there should be corresponding unstressed
-- and stressed stems in 'pretuN' and 'pretsN' (defaulting to 'pretN' or STEM).
-- If specifically 'pret' and 'prettype' are unspecified, substitute defaults,
-- specifically the fallback preterite type FBPTY and stressed/unstressed
-- fallback stem FBSTEM.
function handle_pret_impf_subj(args, data, stem, fbstem, fbpty)
	local all_props =
		get_args(args, {"prettype", "pret", "pretu", "prets", "impsub"})
	for i, props in ipairs(all_props) do
		local thestem = stem
		local pty = props[1][1]
		local pret = props[2][1]
		local pretu = props[3][1]
		local prets = props[4][1]
		local impsub = props[5][1]
		if i == 1 and not pty and not pret then
			thestem = fbstem
			pty = fbpty
			pret = fbstem
			pretu = fbstem
			prets = fbstem
		end
		inflect_pret_impf_subj(data, thestem, pty, pret, pretu, prets, impsub)
	end
end

-- Add to DATA the forms for up to one paradigm of the future and conditional,
-- based on the future stem in STEM (possibly nil).
function inflect_future_cond(data, stem)
	if stem then
		if rfind(stem, "/") then
			inflect_tense(data, "futr_indc", "", split_multipart(stem))
		else
			if data.old then
				inflect_tense(data, "futr_indc", stem,
					{"ai","as","aṭ","ons",{"eiz", "ez"},"ont"})
				inflect_tense(data, "cond", stem,
					{"eie","eies","eit", "iiens","iiez","eient"})
			elseif data.ei then
				inflect_tense(data, "futr_indc", stem,
					{"ai","as","a","ons",{"eiz", "ez"},"ont"})
				inflect_tense(data, "cond", stem,
					{"eie","eies","eit",
					{"iiens","iens"},{"iiez","iez"},"eient"})
			else
				inflect_tense(data, "futr_indc", stem,
					{"ai","as","a","ons",{"oiz","eiz", "ez"},"ont"})
				inflect_tense(data, "cond", stem,
					{{"oie","eie"},{"oies","eies"},{"oit","eit"},
					{"iiens","iens"},{"iiez","iez"},{"oient","eient"}})
			end
		end
	end
end

-- Add to DATA all the forms for the future and conditional based on the
-- future stem(s) in ARGS. Use If no future stems given, use STEM.
function handle_future_cond(args, data, stem)
	local fut_args = get_args(args, "fut")
	-- Just override the value from args["fut"] if necessary
	if not args["fut"] then
		fut_args[1][1] = stem
	end
	for _, futarg in ipairs(fut_args) do
		local stem = futarg[1]
		inflect_future_cond(data, stem)
	end
end

-- Add to DATA the forms for up to one imperfect paradigm, corresponding to
-- the imperfect stem in IMPERF (possibly nil), the corresponding ier= value
-- in IMPERFIER, the corresponding present stem in PRES (possibly nil), and
-- its corresponding ier= value in PRESIER. Only do something if either IMPERF
-- or PRES is non-nil.
function inflect_imperfect(data, group, imperf, imperfier, pres, presier)
	if imperf and rfind(imperf, "/") then
		inflect_tense(data, "impf_indc", "", split_multipart(imperf))
	else
		if not imperf and pres and not rfind(pres, "/") then
			imperf = pres
			imperfier = presier
		end
		if imperf and imperf ~= "-" then
			local steme = imperf
			local stema = steme_to_stema(steme)
		    local i = imperfier and "i" or ""
			if group == "i" and data.old then
				inflect_tense(data, "impf_indc", steme,
					{{"eie", "oue", i .. "eve"},
					 {"eies", "oues", i .. "eves"},
					 {"eit", "out", i .. "eveṭ"},
					 {"iiens"},
					 {"iiez"},
					 {"eient", "ouent", i .. "event"}
					})
			elseif group == "i" and data.ei then
				inflect_tense(data, "impf_indc", steme,
					{{"eie", "oe", i .. "eve"},
					 {"eies", "oes", i .. "eves"},
					 {"eit", "ot", i .. "eve"},
					 {"iiens", "iens"},
					 {"iiez", "iez"},
					 {"eient", "oent", i .. "event"}
					})
			elseif group == "i" then
				inflect_tense(data, "impf_indc", steme,
					{{"oie", "eie", "oe", i .. "eve"},
					 {"oies", "eies", "oes", i .. "eves"},
					 {"oit", "eit", "ot", i .. "eve"},
					 {"iiens", "iens"},
					 {"iiez", "iez"},
					 {"oient", "eient", "oent", i .. "event"}
					})
			elseif group == "ii" and data.old then
				inflect_tense(data, "impf_indc", join(steme, "iss"),
					{"eie",
					 "eies",
					 "eit",
					 "iiens",
					 "iiez",
					 "eient"
					})
			elseif group == "ii" and data.ei then
				inflect_tense(data, "impf_indc", join(steme, "iss"),
					{"eie",
					 "eies",
					 "eit",
					 {"iiens", "iens"},
					 {"iiez", "iez"},
					 "eient"
					})
			elseif group == "ii" then
				inflect_tense(data, "impf_indc", join(steme, "iss"),
					{{"oie", "eie"},
					 {"oies", "eies"},
					 {"oit", "eit"},
					 {"iiens", "iens"},
					 {"iiez", "iez"},
					 {"oient", "eient"}
					})
			elseif group == "iii" and data.old then
				inflect_tense(data, "impf_indc", steme,
					{"eie",
					 "eies",
					 "eit",
					 "iiens",
					 "iiez",
					 "eient"
					})
			elseif group == "iii" and data.ei then
				inflect_tense(data, "impf_indc", steme,
					{"eie",
					 "eies",
					 "eit",
					 {"iiens", "iens"},
					 {"iiez", "iez"},
					 "eient"
					})
			elseif group == "iii" then
				inflect_tense(data, "impf_indc", steme,
					{{"oie", "eie"},
					 {"oies", "eies"},
					 {"oit", "eit"},
					 {"iiens", "iens"},
					 {"iiez", "iez"},
					 {"oient", "eient"}
					})
			end
		end
	end
end

-- Add to DATA all the forms for the imperfect based on the
-- imperfect stem(s) in ARGS. If no imperfect stems given, use
-- corresponding present stems if they exist, but use STEME and IER
-- for the first present stem and ier= value, since they're computed
-- specially.
function handle_imperfect(args, data, group, steme, ier)
	local imperf_args = get_args(args, {"imperf","imperfier","pres","ier"})
	-- Just override the values from args["pres"] and args["ier"]
	imperf_args[1][3][1] = steme
	imperf_args[1][4][1] = ier
	for _, stem in ipairs(imperf_args) do
		local imperf = stem[1][1]
		local imperfier = stem[2][1]
		local pres = stem[3][1]
		local presier = stem[4][1]
		inflect_imperfect(data, group, imperf, imperfier, pres, presier)
	end
end

-- Add to DATA up to one form of the present participle based on the
-- present stem in PRES. Only do anything if PRES is non-nil and not a
-- multipart specification.
function inflect_pres_part(data, group, pres)
	if pres and not rfind(pres, "/") then
		if group == "ii" then
			table.insert(data.forms.pres_ptc, join(pres, "issant"))
		else
			table.insert(data.forms.pres_ptc, join(pres, "ant"))
		end
	end
end

-- Add to DATA the forms of the present participle based on the
-- present stem(s) in ARGS. Use STEME for the first present stem,
-- since it's computed specially.
function handle_pres_part(args, data, group, steme)
	if data.forms.pres_ptc == nil then
		data.forms.pres_ptc = {}
	end
	local ppart_args = get_args(args, {"pres"})
	-- Just override the value from args["pres"]
	ppart_args[1][1][1] = steme
	for _, stem in ipairs(ppart_args) do
		local pres = stem[1][1]
		inflect_pres_part(data, group, pres)
	end
end
	
-- Add to DATA the endings for an -er or -ier verb, based on the arguments
-- in ARGS.
inflections["i"] = function(args, data)
	local prese = data.prese
	local press = args["press"] or prese
	local i = data.ier and "i" or ""

	if data.ier then
		data.comment = "This verb conjugates as a first-group verb ending in ''-ier'', with a palatal stem. These verbs are conjugated mostly like verbs in ''-er'', but there is an extra ''i'' before the ''e'' of some endings. "
	else
		data.comment = "This verb conjugates as a first-group verb ending in ''-er''. "
	end
	data.comment = data.comment ..
		verb_comment(args, "i", prese, press, data.ier, data.supe, data.old)
	data.group = {"first"}
	handle_pres_part(args, data, "i", prese)
	data.forms.past_ptc = {join(prese, i .. "é" .. (data.old and "ṭ" or ""))}

	handle_pres(args, data, "i", prese, press)
	handle_imperfect(args, data, "i", prese, data.ier)
	handle_pret_impf_subj(args, data, prese, prese,
		data.ier and "weak-a2" or "weak-a")
	handle_future_cond(args, data, join(prese, "er"))
end

-- Add to DATA the endings for a type 2 verb (-ir, with -iss- infix),
-- based on the arguments in ARGS.
inflections["ii"] = function(args, data)
	local prese = data.prese
	local press = args["press"] or prese

	data.comment = "This verb conjugates as a second-group verb (ending in ''-ir'', with an ''-iss-'' infix). "
	data.group = {"second"}

	handle_pres_part(args, data, "ii", prese)
	local oldt = data.old and "ṭ" or ""
	data.forms.past_ptc = {join(prese, "i" .. oldt)}

	handle_pres(args, data, "ii", prese, press)
	handle_imperfect(args, data, "ii", prese, data.ier)
	handle_pret_impf_subj(args, data, prese, prese, "weak-i")
	handle_future_cond(args, data, join(prese, "ir"))
end

-- Add to DATA the endings for a type 3 verb (-ir without -iss- infix, or
-- -re or -oir), based on the arguments in ARGS.
inflections["iii"] = function(args, data)
	local prese = data.prese
	local press = args["press"] or prese
	local i = data.ier and "i" or ""

	data.comment = "This verb conjugates as a third-group verb. "
	if data.ier then
		data.comment = data.comment .. "This verb ends in a palatal stem, so there is an extra ''i'' before the ''e'' of some endings. "
	end
	data.comment = data.comment ..
		verb_comment(args, "iii", prese, press, data.ier, data.supe, data.old)
	data.group = {"third"}

	handle_pres_part(args, data, "iii", prese)
	-- retrieve the infinitive without any affix, so that when
	-- we put the affix back on, we don't get a doubled affix
	local infinitive = data.inf_no_affix
	local oldt = data.old and "ṭ" or ""
	if rfind(infinitive, "[^eo]ir$") then
		data.forms.past_ptc = {join(prese, "i" .. oldt)}
	elseif rfind(infinitive, "ïr$") then
		data.forms.past_ptc = {join(prese, "ï" .. oldt)}
	else
		data.forms.past_ptc = {join(prese, "u" .. oldt)}
	end

	handle_pres(args, data, "iii", prese, press)
	handle_imperfect(args, data, "iii", prese, data.ier)
	if rfind(infinitive, "[dt]re$") then
		handle_pret_impf_subj(args, data, prese, prese, "weak-i2")
	elseif rfind(infinitive, "re$") then
		local pretstem = add_s(prese, false, false, data.old)
		pretstem = rsub(pretstem, "s$", "")
		handle_pret_impf_subj(args, data, prese, pretstem, "strong-st")
	elseif rfind(infinitive, "[eo]ir$") then
		handle_pret_impf_subj(args, data, prese, prese, "weak-u")
	else
		handle_pret_impf_subj(args, data, prese, prese, "weak-i")
	end
	if rfind(infinitive, "[^eolrs]ir$") then
		handle_future_cond(args, data, join(prese, "ir"))
	else -- -re, -oir, -eir, -ïr, -lir, -sir, -rir
		handle_future_cond(args, data, add_r(prese, data.old))
	end
end

-- Add to DATA the endings for a type 3/2 verb (-ir without or with
-- -iss- infix), based on the arguments in ARGS.
inflections["iii-ii"] = function(args, data)
	local prese = data.prese
	local press = args["press"] or prese
	local i = data.ier and "i" or ""

	data.comment = "This verb conjugates as a third-group or second-group verb (ending in ''-ir'', without or with an ''-iss-'' infix). "
	if data.ier then
		data.comment = data.comment .. "This verb ends in a palatal stem, so there is an extra ''i'' before the ''e'' of some endings. "
	end
	data.comment = data.comment ..
		verb_comment(args, "iii", prese, press, data.ier, data.supe, data.old)
	data.group = {"second", "third"}

	handle_pres_part(args, data, "iii", prese)
	handle_pres_part(args, data, "ii", prese)
	-- retrieve the infinitive without any affix, so that when
	-- we put the affix back on, we don't get a doubled affix
	local infinitive = data.inf_no_affix
	local oldt = data.old and "ṭ" or ""
	if rfind(infinitive, "[^eo]ir$") then
		data.forms.past_ptc = {join(prese, "i" .. oldt)}
	elseif rfind(infinitive, "ïr$") then
		data.forms.past_ptc = {join(prese, "ï" .. oldt)}
	end

	handle_pres(args, data, "iii", prese, press)
	handle_pres(args, data, "ii", prese, press)
	handle_imperfect(args, data, "iii", prese, data.ier)
	handle_imperfect(args, data, "ii", prese, data.ier)
	handle_pret_impf_subj(args, data, prese, prese, "weak-i")
	handle_future_cond(args, data, join(prese, "ir"))
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
