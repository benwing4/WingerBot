local m_utilities = require("Module:utilities")
local m_links = require("Module:links")

local lang = require("Module:languages").getByCode("ar")
local u = mw.ustring.char
local rfind = mw.ustring.find
local rsub = mw.ustring.gsub
local rmatch = mw.ustring.match
local rsplit = mw.text.split

-- hamza variants
local HAMZA            = u(0x0621) -- hamza on the line (stand-alone hamza) = ء
local HAMZA_OVER_ALIF  = u(0x0623)
local HAMZA_OVER_WAW   = u(0x0624)
local HAMZA_UNDER_ALIF = u(0x0625)
local HAMZA_OVER_YA    = u(0x0626)
local HAMZA_ANY = "[" .. HAMZA .. HAMZA_OVER_ALIF .. HAMZA_UNDER_ALIF .. HAMZA_OVER_WAW .. HAMZA_OVER_YA .. "]"

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
local II    = I .. YA
local UU    = U .. WAW
local AY    = A .. YA
local AW    = A .. WAW
local AYSK  = AY .. SK
local AWSK  = AW .. SK
local NA    = NUN .. A
local NI    = NUN .. I
local AANI  = AA .. NI
local AYNI  = AYSK .. NI
local AWNA  = AWSK .. NA
local AYNA  = AYSK .. NA
local AYAAT = A .. YA .. AA .. TA

-- optional diacritics/letters
local AMAY = A .. "?"
local AAMAY = A .. "?" .. ALIF
local IMAY = I .. "?"
local UMAY = U .. "?"
local UNMAY = UN .. "?"
local SKMAY = SK .. "?"

local consonants_needing_vowels = "بتثجحخدذرزسشصضطظعغفقكلمنهپچڤگڨڧأإؤئءةﷲ"
-- consonants on the right side; includes alif madda
local rconsonants = consonants_needing_vowels .. "ويآ"
-- consonants on the left side; does not include alif madda
local lconsonants = consonants_needing_vowels .. "وي"
local CONS = "[" .. lconsonants .. "]"

local export = {}

-- Functions that do the actual inflecting by creating the forms of a basic term.
local inflections = {}

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

-- The main entry point.
-- This is the only function that can be invoked from a template.
function export.show(frame)
	local args = frame:getParent().args
	
	local sg_type, sg_stem, pl_type, pl_stem
	if ine(args[4]) then
		sg_type = args[1] or (mw.title.getCurrentTitle().nsText == "Template" and "tri") or ""; if sg_type == "" then error("Parameter 1 (singular inflection type) may not be empty.") end
		sg_stem = args[2] or (mw.title.getCurrentTitle().nsText == "Template" and "{{{2}}}") or ""; if sg_stem == "" then error("Parameter 2 (singular stem) may not be empty.") end
		pl_type = args[3] or (mw.title.getCurrentTitle().nsText == "Template" and "tri") or ""; if pl_type == "" then error("Parameter 3 (plural inflection type) may not be empty.") end
		pl_stem = args[4] or (mw.title.getCurrentTitle().nsText == "Template" and "{{{4}}}") or ""; if pl_stem == "" then error("Parameter 4 (plural stem) may not be empty.") end
	else
		if not args[1] and not args[2] and mw.title.getCurrentTitle().nsText == "Template" then
			sg_type = "tri"
			sg_stem = "{{{1}}}"
			pl_type = "tri"
			pl_stem = "{{{2}}}"
		else
			if not ine(args[1]) then error("Parameter 1 (singular inflection) may not be empty.") end
			if not ine(args[2]) then error("Parameter 2 (plural inflection) may not be empty.") end
			sg_stem, sg_type = export.stem_and_class(args[1], args[1], false)
			pl_stem, pl_type = export.stem_and_class(args[2], sg_stem, true)
		end
	end

	local data = {forms = {}, title = nil, categories = {}}
	
	-- Generate the singular and dual forms
	if not inflections[sg_type] then
		error("Unknown inflection type '" .. sg_type .. "'")
	end
	
	inflections[sg_type](sg_stem, data, "sg")
	
	-- Generate the plural forms
	if not inflections[pl_type] then
		error("Unknown inflection type '" .. pl_type .. "'")
	end
	
	inflections[pl_type](pl_stem, data, "pl")
	
	-- Make the table
	return make_table(data) .. m_utilities.format_categories(data.categories, lang)
end


-- Inflection functions

-- Form inflections from combination of STEM and ENDINGS (and definite article
-- where necessary) and store in DATA, for the number determined by N
-- ("sg", "du", "pl"). Order of ENDINGS is indefinite nom, acc, gen; definite
-- nom, acc, gen; construct-state nom, acc, gen.
function add_inflections(stem, data, n, endings)
	assert(#endings == 9)
	local function add_inflection(key, value)
		if data.forms[key] == nil then
			data.forms[key] = {value}
		else
			table.insert(data.forms[key], value)
		end
	end
	add_inflection("nom_" .. n .. "_ind", stem .. endings[1])
	add_inflection("acc_" .. n .. "_ind", stem .. endings[2])
	add_inflection("gen_" .. n .. "_ind", stem .. endings[3])
	add_inflection("nom_" .. n .. "_def", "ال" .. stem .. endings[4])
	add_inflection("acc_" .. n .. "_def", "ال" .. stem .. endings[5])
	add_inflection("gen_" .. n .. "_def", "ال" .. stem .. endings[6])
	add_inflection("nom_" .. n .. "_con", stem .. endings[7])
	add_inflection("acc_" .. n .. "_con", stem .. endings[8])
	add_inflection("gen_" .. n .. "_con", stem .. endings[9])
end	

function triptote_diptote(stem, data, n, is_dip, lc)
	if rfind(stem, AAH .. "$") then
		--data.title = "triptote singular in " .. m_links.full_link(nil, HYPHEN .. AAH, lang, nil, "term", nil, {tr = "-"}, false)
	elseif rfind(stem, AH .. "$") then
		--data.title = "triptote singular in " .. m_links.full_link(nil, HYPHEN .. AH, lang, nil, "term", nil, {tr = "-"}, false)
	else
		--data.title = "triptote singular"
	end
	
	-- Singular
	add_inflections(stem, data, n,
		{is_dip and U or UN,
		 is_dip and A or AN .. ((rfind(stem, TA_M .. "$") or rfind(stem, ALIF .. HAMZA .. "$")) and "" or ALIF),
		 is_dip and A or IN,
		 U, A, I,
		 lc and UU or U,
		 lc and AA or A,
		 lc and II or I,
		})

	-- Dual
	if n == "sg" then
		local stem_nonfinal = rsub(stem, TA_M .. "$", TA)

		add_inflections(stem_nonfinal, data, "du",
			{AANI, AYNI, AYNI,
			 AANI, AYNI, AYNI,
			 AA, AYSK, AYSK,
			})
	end
end

-- Regular triptote
inflections["tri"] = function(stem, data, n)
	triptote_diptote(stem, data, n, false)
end

-- Regular diptote
inflections["di"] = function(stem, data, n)
	triptote_diptote(stem, data, n, true)
end

-- Triptote with lengthened ending in the construct state
inflections["lc"] = function(stem, data, n)
	triptote_diptote(stem, data, n, false, true)
end

function in_defective(stem, data, n, sgin)
	stem = rsub(stem, IN .. "$", "")

	-- Singular
	add_inflections(stem, data, n,
		{IN, sgin and II .. AN or II .. A, IN,
		 II, II .. A, II,
		 II, II .. A, II
		})

	-- Dual
	if n == "sg" then
		add_inflections(stem, data, "du",
			{II .. AANI, II .. AYNI, II .. AYNI,
			 II .. AANI, II .. AYNI, II .. AYNI,
			 II .. AA, II .. AYSK, II .. AYSK,
			})
	end
end

-- Defective in -in
inflections["in"] = function(stem, data, n)
	in_defective(stem, data, n, n == "sg")
end

-- Defective in -in, force singular variant
inflections["sgin"] = function(stem, data, n)
	in_defective(stem, data, n, true)
end

-- Defective in -in, force plural variant
inflections["plin"] = function(stem, data, n)
	in_defective(stem, data, n, false)
end

-- Defective in -an (comes in two variants, depending on spelling with tall alif or alif maqṣūra)
inflections["an"] = function(stem, data, n)
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

	-- Singular
	if tall_alif then
		add_inflections(stem, data, n,
			{AN .. ALIF, AN .. ALIF, AN .. ALIF,
			 AA, AA, AA,
			 AA, AA, AA,
			})
		if n == "sg" then
			add_inflections(stem, data, "du",
				{AW .. AANI, AW .. AYNI, AW .. AYNI,
				 AW .. AANI, AW .. AYNI, AW .. AYNI,
				 AW .. AA, AW .. AYSK, AW .. AYSK,
				})
		end
	else
		add_inflections(stem, data, n,
			{AN .. AMAQ, AN .. AMAQ, AN .. AMAQ,
			 AAMAQ, AAMAQ, AAMAQ,
			 AAMAQ, AAMAQ, AAMAQ,
			})
		if n == "sg" then
			add_inflections(stem, data, "du",
				{AY .. AANI, AY .. AYNI, AY .. AYNI,
				 AY .. AANI, AY .. AYNI, AY .. AYNI,
				 AY .. AA, AY .. AYSK, AY .. AYSK,
				})
		end
	end
end

-- Plural of defective in -an
inflections["awn"] = function(stem, data, n)
	add_inflections(stem, data, n,
		{AWNA, AYNA, AYNA,
		 AWNA, AYNA, AYNA,
		 AWSK, AYSK, AYSK,
		})
end

-- Invariable in -ā (non-loanword type)
inflections["inv"] = function(stem, data, n)
	local dualstem
	if rfind(stem, AA .. "$") then
		dualstem = rsub(stem, AA .. "$", "")
	elseif rfind(stem, AAMAQ .. "$") then
		dualstem = rsub(stem, AAMAQ .. "$", "")
	else
		error("Invalid stem for 'inv' declension type: " .. stem)
	end

	-- Singular
	add_inflections(stem, data, n,
		{"", "", "",
		 "", "", "",
		 "", "", "",
		})
	if n == "sg" then
		add_inflections(dualstem, data, "du",
			{AY .. AANI, AY .. AYNI, AY .. AYNI,
			 AY .. AANI, AY .. AYNI, AY .. AYNI,
			 AY .. AA, AY .. AYSK, AY .. AYSK,
			})
	end
end

-- Invariable in -ā (loanword type, behaving in the dual as if ending in -a, I think!)
inflections["lwinv"] = function(stem, data, n)
	if rfind(stem, AA .. "$") then
		stem = rsub(stem, AA .. "$", "")
	else
		error("Invalid stem for 'inv' declension type: " .. stem)
	end

	-- Singular
	add_inflections(stem, data, n,
		{AA, AA, AA,
		 AA, AA, AA,
		 AA, AA, AA,
		})
	if n == "sg" then
		add_inflections(dualstem, data, "du",
			{AT .. AANI, AT .. AYNI, AT .. AYNI,
			 AT .. AANI, AT .. AYNI, AT .. AYNI,
			 AT .. AA, AT .. AYSK, AT .. AYSK,
			})
	end
end

-- Sound masculine plural
inflections["sm"] = function(stem, data, n)
	add_inflections(stem, data, n,
		{UU .. NA, II .. NA, II .. NA,
		 UU .. NA, II .. NA, II .. NA,
		 UU,       II,       II,
		})
end

-- Sound feminine plural
inflections["sf"] = function(stem, data, n)
	add_inflections(stem, data, n,
		{UN, IN, IN,
		 U,  I,  I,
		 U,  I,  I,
		})
end

function reorder_shadda(word)
	-- shadda+short-vowel (including tanwīn vowels, i.e. -an -in -un) gets
	-- replaced with short-vowel+shadda during NFC normalisation, which
	-- MediaWiki does for all Unicode strings; however, it makes the
	-- detection process inconvenient, so undo it.
	word = rsub(word, "(" .. DIACRITIC_ANY_BUT_SH .. ")" .. SH, SH .. "%1")
	return word
end

-- qafan قَفَا with tall alif "nape" m. and f. pl. aqfiya/aqfin/aqfāʾ/qufiyy/qifiyy

-- Detect declension of noun or adjective stem or lemma. We allow triptotes,
-- diptotes and sound plurals to either come with ʾiʿrāb or not. We detect
-- some cases where vowels are missing, when it seems fairly unambiguous to
-- do so. ISPL is true if we are dealing with a plural form.
function export.detect_decl(stem, ispl)
	stem = reorder_shadda(stem)
	local origstem = stem
	-- So that we don't get tripped up by alif madda, we replace sequences of
	-- consonant + alif with alif madda and then match on alif madda in the
	-- regexps below.
	stem = rsub(stem, CONS .. AAMAY, AMAD)
	if ispl and rfind(stem, "^" .. CONS .. AMAY .. AMAD .. CONS .. IN .. "$") then -- layālin
		return 'plin'
	elseif rfind(stem, IN .. "$") then -- other -in words
		return 'sgin'
	elseif rfind(stem, AN .. "[" .. ALIF .. AMAQ .. "]$") then
		return 'an'
	elseif rfind(stem, AN .. "$") then
		error("Malformed stem, fatḥatan should be over second-to-last letter: " .. stem)
	elseif ispl and rfind(stem, AW .. SKMAY .. NUN .. AMAY .. "$") then
		return 'awn'
	elseif ispl and rfind(stem, AMAD .. TA .. UNMAY .. "$") then
		return 'sf'
	elseif ispl and rfind(stem, WAW .. NUN .. AMAY .. "$") then
		return 'sm'
	elseif rfind(stem, UN .. "$") then -- explicitly specified triptotes (we catch sound feminine plurals above)
		return 'tri'
	elseif rfind(stem, U .. "$") then -- explicitly specified diptotes
		return 'di'
	elseif ispl and ( -- various diptote plural patterns
		rfind(stem, "^" .. CONS .. AMAY .. AMAD .. CONS .. IMAY .. YA .. "?" .. CONS .. "$") or -- fawākih, daqāʾiq, makātib, mafātīḥ
		rfind(stem, "^" .. CONS .. AMAY .. AMAD .. CONS .. SH .. "$") or -- maqāmm
		rfind(stem, "^" .. CONS .. U .. CONS .. AMAY .. AMAD .. HAMZA .. "$") or -- wuzarāʾ
		rfind(stem, "^" .. HAMZA_OVER_ALIF .. AMAY .. CONS .. SKMAY .. CONS .. IMAY .. AMAD .. HAMZA .. "$") or -- ʾaṣdiqāʾ
		rfind(stem, "^" .. HAMZA_OVER_ALIF .. AMAY .. CONS .. IMAY .. CONS .. SH .. AAMAY .. HAMZA .. "$") -- ʾaqillāʾ
	    ) then
		return 'di'
	elseif ( -- diptote singular patterns (mostly adjectives)
		rfind(stem, "^" .. CONS .. A .. CONS .. SK .. AMAD .. "[" .. NUN .. HAMZA .. "]$") or -- kaslān "lazy", qamrāʾ "moon-white, moonlight"
		rfind(stem, "^" .. CONS .. A .. CONS .. SH .. AAMAY .. "[" .. NUN .. HAMZA .. "]$") or -- laffāʾ "plump (fem.)"
		rfind(stem, "^" .. HAMZA_OVER_ALIF .. AMAY .. CONS .. SK .. CONS .. A .. CONS .. "$") or -- ʾabyad
		rfind(stem, "^" .. HAMZA_OVER_ALIF .. AMAY .. CONS .. A .. CONS .. SH .. "$") or -- ʾalaff
		-- do the following on the origstem so we can check specifically for alif madda
		rfind(origstem, "^" .. AMAD .. CONS .. A .. CONS .. "$") -- ʾālam "more painful", ʾāḵar "other"
		) then
		return 'di'
	elseif rfind(stem, AMAQ .. "$") then -- kaslā, ḏikrā (spelled with alif maqṣūra)
		return 'inv'
	-- Do the following on the origstem so we can check for YA + ALIF specifically.
	elseif rfind(origstem, "[" .. AMAD .. ALIF .. SK .. "]" .. YA .. AAMAY .. "$") then -- dunyā, hadāyā (spelled with tall alif after yāʾ)
		return 'inv'
	elseif rfind(stem, AMAD .. "$") then -- kāmērā, lībiyā (spelled with tall alif; we catch dunyā and hadāyā above)
		return 'lwinv'
	else
		return 'tri'
	end
end

-- Return stem and class of an argument given the singular form and whether
-- this is a plural argument.
function export.stem_and_class(word, sg, ispl)
	word = reorder_shadda(word)
	sg = reorder_shadda(sg)
	local function sub(from, to)
		if rfind(sg, from) then
			local ret, _ = rsub(sg, from, to)
			return ret
		else
			return nil
		end
	end

	if not ispl and (word == "sf" or word == "sm" or word == "awn") then
		error("Inference of form for inflection type '" .. word .. "' only allowed in plural")
	end
	
	if word == "sf" then
		local ret = (sub(AMAD .. TA_M .. UNMAY .. "$", HAMZA_OVER_ALIF .. AYAAT) or -- ends in -ʾāh
			sub(AMAY .. ALIF .. TA_M .. UNMAY .. "$", AYAAT) or -- ends in -āh
			sub(AMAY .. TA_M .. UNMAY .. "$", AA .. TA) or -- ends in -a
			sub(AN .. "[" .. ALIF .. AMAQ .. "]$", AYAAT) or -- ends in -an
			sub(IN .. "$", I .. YA .. AA .. TA) or -- ends in -in
			sub(AMAY .. AMAQ .. "$", AYAAT) or -- ends in alif maqṣūra
			sub("([" .. AMAD .. ALIF .. SK .. "]" .. YA .. ")" .. AAMAY .. "$", "%1" .. AYAAT) or -- dunyā, hadāyā (spelled with tall alif after yāʾ)
			sub(AAMAY .. "$", AA .. TA) or -- loanword ending in tall alif
			sub(HAMZA_ANY .. "$", AMAD .. TA) or -- ends in hamza
			sub("$", AA .. TA) -- anything else
		)
		return ret, "sf"
	end

	if word == "sm" then
		local ret = (
			sub(IN .. "$", UU .. NUN) or -- ends in -in
			sub("[" .. HAMZA .. HAMZA_OVER_ALIF .. "]$", HAMZA_OVER_WAW .. UU .. NUN) or -- ends in hamza
			sub("$", UU .. NUN) -- anything else
		)
		return ret, "sm"
	end

	if word == "awn" then
		local ret = (
			sub(AN .. "[" .. ALIF .. AMAQ .. "]$", AWSK .. NUN) -- ends in -an
		)
		if not ret then
			error("For 'awn', singular must end in -an: " .. sg)
		end
		return ret, "awn"
	end

	if rfind(word, ":") then
		split = rsplit(word, ":")
		if #split > 2 then
			error("More than one colon found in argument: '" .. word .. "'")
		end
		return split[1], split[2]
	else
		return word, export.detect_decl(word, ispl)
	end
end

-- Make the table
function make_table(data)
	local function show_form(form, use_parens)
		if not form then
			return "&mdash;"
		elseif type(form) ~= "table" then
			error("a non-table value was given in the list of inflected forms.")
		end
		
		local ret = {}
		
		for key, subform in ipairs(form) do
			local translit = lang:transliterate(subform)
			local tr_span = translit and "<span style=\"color: #888\">" .. translit .. "</span>" or ""
			local tr_html = not translit and "" or use_parens and " (" .. tr_span .. ")" or "<br/>" .. tr_span
			if subform:find("{{{") then
				table.insert(ret, m_links.full_link(nil, subform, lang, nil, nil, nil, {tr = "-"}, false) .. tr_html)
			else
				table.insert(ret, m_links.full_link(subform, nil, lang, nil, nil, nil, {tr = "-"}, false) .. tr_html)
			end
		end
		
		return table.concat(ret, "<br/>")
	end
	
	local function repl(param)
		if param == "lemma" then
			return show_form(data.forms["nom_sg_ind"], "use parens")
		elseif param == "info" then
			return data.title and " (" .. data.title .. ")" or ""
		else
			return show_form(data.forms[param])
		end
	end
	
	local wikicode = [=[<div class="NavFrame" style="width: 40%">
<div class="NavHead">Inflection of {{{lemma}}}{{{info}}}</div>
<div class="NavContent">
{| class="inflection-table" style="border-width: 1px; border-collapse: collapse; background:#F9F9F9; text-align:center; width:100%;"
|-
! style="background: #CDCDCD; width:25%;" | Singular
! style="background: #CDCDCD; width:25%;" | Indefinite
! style="background: #CDCDCD; width:25%;" | Definite
! style="background: #CDCDCD; width:25%;" | Construct
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
|-
! style="background: #CDCDCD;" | Dual
! style="background: #CDCDCD;" | Indefinite
! style="background: #CDCDCD;" | Definite
! style="background: #CDCDCD;" | Construct
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
|-
! style="background: #CDCDCD;" | Plural
! style="background: #CDCDCD;" | Indefinite
! style="background: #CDCDCD;" | Definite
! style="background: #CDCDCD;" | Construct
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
|}
</div>
</div>]=]

	return rsub(wikicode, "{{{([a-z_]+)}}}", repl)
end

return export

-- For Vim, so we get 4-space tabs
-- vim: set ts=4 sw=4 noet:
