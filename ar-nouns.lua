local m_utilities = require("Module:utilities")
local m_links = require("Module:links")

-- example of -an word with tall alif, besides ʿaṣan and riḍan (which can
-- also be spelled with alif maqṣūra):
-- qafan قَفَا "nape" m. and f.; pl. aqfiya/aqfin/aqfāʾ/qufiyy/qifiyy

local lang = require("Module:languages").getByCode("ar")
local u = mw.ustring.char
local rfind = mw.ustring.find
local rsub = mw.ustring.gsub
local rmatch = mw.ustring.match
local rsplit = mw.text.split

local BOGUS_CHAR = u(0xFFFD)
local HAMZA_PLACEHOLDER = u(0xFFF1)

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
local AAT   = AA .. TA
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
	
	local data = {forms = {}, title = nil, categories = {}}

	local sg_type, sg_combined_stem
	local pls = {}
	if not args[1] and not args[2] and mw.title.getCurrentTitle().nsText == "Template" then
		sg_type = "tri"
		sg_combined_stem = "{{{1}}}"
		pls = {{"{{{2}}}", "tri"}}
	else
		if not ine(args[1]) then error("Parameter 1 (singular inflection) may not be empty.") end
		sg_combined_stem, sg_type = export.stem_and_type(args[1], args[1], "", false)
		local i = 2
		while ine(args[i]) do
			local pl_combined_stem, pl_type = export.stem_and_type(args[i], sg_combined_stem, sg_type, true)
			table.insert(pls, {pl_combined_stem, pl_type})
			i = i + 1
		end
	end

	local function call_inflection(ty, combined_stem, data, n)
		if not inflections[ty] then
			error("Unknown inflection type '" .. ty .. "'")
		end
		
		local ar, tr = split_arabic_tr(combined_stem)
		inflections[ty](ar, tr, data, n)
	end


	-- Generate the singular forms
	call_inflection(sg_type, sg_combined_stem, data, "sg")

	-- If any plurals exist, generate duals
	-- Don't do this if no plurals (e.g. proper noun)
	if #pls > 0 then
		local du = ine(args["du"])
		if du == "-" then
			-- No dual
		elseif not du then
			-- Dual based on singular
			call_inflection(sg_type, sg_combined_stem, data, "du")
		else
			-- One or more duals based on stems explicitly given
			local function do_dual(combined_stem)
				local ar, tr = split_arabic_tr(combined_stem)
				if rfind(ar, AANI .. "?$") then
					ar = rsub(ar, AANI .. "?$", "")
					tr = rsub(tr, "āni?$", "")
					add_dual(ar, tr, data)
				else
					error("Dual stem should end in the nominative dual ending -ān(i): '" .. ar .. "'")
				end
			end
			do_dual(du)
			local i = 2
			while ine(args["du" .. i]) do
				do_dual(args["du" .. i])
				i = i + 1
			end
		end
	end
	
	-- Generate the plural forms
	for _, pl in ipairs(pls) do
		local pl_combined_stem = pl[1]
		local pl_type = pl[2]
		call_inflection(pl_type, pl_combined_stem, data, "pl")
	end
	
	-- Make the table
	return make_table(data) .. m_utilities.format_categories(data.categories, lang)
end


-- Inflection functions

function do_translit(term)
	return lang:transliterate(term) or BOGUS_CHAR
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

-- Form inflections from combination of STEM, with transliteration TR,
-- and ENDINGS (and definite article where necessary) and store in DATA,
-- for the number determined by N ("sg", "du", "pl"). ENDINGS is an array
-- of 9 values, each of which is a string or array of alternatives. The
-- order of ENDINGS is indefinite nom, acc, gen; definite nom, acc, gen;
-- construct-state nom, acc, gen.
function add_inflections(stem, tr, data, n, endings)
	assert(#endings == 9)
	local function combine(ar, tr, ending)
		local endingar, endingtr = split_arabic_tr(ending)
		ar = ar .. endingar
		tr = tr .. endingtr
		return ar .. "/" .. tr
	end
	local function add_inflection(key, stem, tr, ending)
		if data.forms[key] == nil then
			data.forms[key] = {}
		end
		if type(ending) == "table" then
			for _, val in ipairs(ending) do
				table.insert(data.forms[key], combine(stem, tr, val))
			end
		else
			table.insert(data.forms[key], combine(stem, tr, ending))
		end
	end
	local defstem = "ال" .. stem
	-- apply sun-letter assimilation
	local deftr = rsub("al-" .. tr, "^al%-([sšṣtṯṭdḏḍzžẓnrḷ])", "a%1-%1")

	add_inflection("nom_" .. n .. "_ind", stem, tr, endings[1])
	add_inflection("acc_" .. n .. "_ind", stem, tr, endings[2])
	add_inflection("gen_" .. n .. "_ind", stem, tr, endings[3])
	add_inflection("nom_" .. n .. "_def", defstem, deftr, endings[4])
	add_inflection("acc_" .. n .. "_def", defstem, deftr, endings[5])
	add_inflection("gen_" .. n .. "_def", defstem, deftr, endings[6])
	add_inflection("nom_" .. n .. "_con", stem, tr, endings[7])
	add_inflection("acc_" .. n .. "_con", stem, tr, endings[8])
	add_inflection("gen_" .. n .. "_con", stem, tr, endings[9])
end	

function add_dual(stem, tr, data)
	add_inflections(stem, tr, data, "du",
		{AANI, AYNI, AYNI,
		 AANI, AYNI, AYNI,
		 AA, AYSK, AYSK,
		})
end

function triptote_diptote(stem, tr, data, n, is_dip, lc)
	-- Remove any case ending
	if rfind(stem, "[" .. UN .. U .. "]$") then
		stem = rsub(stem, "[" .. UN .. U .. "]$", "")
		tr = rsub(tr, "un?$", "")
	end
	if rfind(stem, TA_M .. "$") and not rfind(tr, "t$") then
		tr = tr .. "t"
	end
	if rfind(stem, AAH .. "$") then
		--data.title = "triptote singular in " .. m_links.full_link(nil, HYPHEN .. AAH, lang, nil, "term", nil, {tr = "-"}, false)
	elseif rfind(stem, AH .. "$") then
		--data.title = "triptote singular in " .. m_links.full_link(nil, HYPHEN .. AH, lang, nil, "term", nil, {tr = "-"}, false)
	else
		--data.title = "triptote singular"
	end
	
	if n == "du" then
		local stem_nonfinal = rsub(stem, TA_M .. "$", TA)

		add_dual(stem_nonfinal, tr, data)
	else
		add_inflections(stem, tr, data, n,
			{is_dip and U or UN,
			 is_dip and A or AN .. ((rfind(stem, "[" .. HAMZA_OVER_ALIF .. TA_M .. "]$") or rfind(stem, ALIF .. HAMZA .. "$")) and "" or ALIF),
			 is_dip and A or IN,
			 U, A, I,
			 lc and UU or U,
			 lc and AA or A,
			 lc and II or I,
			})
	end
end

-- Regular triptote
inflections["tri"] = function(stem, tr, data, n)
	triptote_diptote(stem, tr, data, n, false)
end

-- Regular diptote
inflections["di"] = function(stem, tr, data, n)
	triptote_diptote(stem, tr, data, n, true)
end

-- Triptote with lengthened ending in the construct state
inflections["lc"] = function(stem, tr, data, n)
	triptote_diptote(stem, tr, data, n, false, true)
end

-- The word فَم ("mouth"), with alternative irregular construct
inflections["fam"] = function(stem, tr, data, n)
	local FAM = "فَم"
	local F = "ف"
	if n == "du" then
		add_dual(FAM, "fam", data)
	else
		add_inflections("", "", data, n,
			{FAM .. UN, FAM .. AN, FAM .. IN,
			 FAM .. U, FAM .. A, FAM .. I,
			 {FAM .. U, F .. UU}, {FAM .. A, F .. AA}, {FAM .. I, F .. II},
			})
	end
end

-- The word ذُو ("owner", "possessor", construct state only)
inflections["dhu"] = function(stem, tr, data, n)
	local DH = "ذ"
	local DHAW = DH .. AW
	local UL = "أُول"
	data.forms["lemma"] = {DH .. UU}
	if n == "sg" then
		add_inflections("", "", data, "sg",
			{{}, {}, {},
			 {}, {}, {}, 
			 DH .. UU, DH .. AA, DH .. II,
			})
	elseif n == "du" then
		add_inflections("", "", data, "du",
			{{}, {}, {},
			 {}, {}, {}, 
			 DHAW .. AA, DHAW .. AYSK, DHAW .. AYSK,
			})
	else
		add_inflections("", "", data, n,
			{{}, {}, {},
			 {}, {}, {}, 
			 {UL .. UU .. "/ʾulū", DHAW .. UU}, {UL .. II .. "/ʾulī", DHAW .. II},
				{UL .. II .. "/ʾulī", DHAW .. II},
			})
	end
end

-- The word ذَات (feminine of ذُو)
inflections["dhat"] = function(stem, tr, data, n)
	local DH = "ذ"
	local DHAAT = DH .. AAT
	local DHAW = DH .. AW
	local DHAWAAT = DHAW .. AAT
	data.forms["lemma"] = {DH .. UU}
	if n == "sg" then
		add_inflections("", "", data, "sg",
			{{}, {}, {},
			 {}, {}, {}, 
			 DHAAT .. U, DHAAT .. A, DHAAT .. I,
			})
	elseif n == "du" then
		add_inflections("", "", data, "du",
			{{}, {}, {},
			 {}, {}, {}, 
			 DHAWAAT .. AA, DHAWAAT .. AYSK, DHAWAAT .. AYSK,
			})
	else
		add_inflections("", "", data, n,
			{{}, {}, {},
			 {}, {}, {}, 
			 DHAWAAT .. U, DHAWAAT .. I, DHAWAAT .. I,
			})
	end
end

-- The word اِمْرُؤ ("man")
inflections["imru"] = function(stem, tr, data, n)
	if n == "du" then
		add_inflections("", "", data, n,
			{"اِمْرَآنِ", "اِمْرَأَيْنِ", "اِمْرَأَيْنِ",
			 "مَرْآنِ", "مَرْأَيْنِ", "مَرْأَيْنِ",
			 "اِمْرَآ", "اِمْرَأَيْ", "اِمْرَأَيْ",
			})
	else
		add_inflections("", "", data, n,
		{"اِمْرُؤٌ", "اِمْرَأً", "اِمْرِئٍ",
			 "مَرْءُ", "مَرْءَ", "مَرْءِ",
			 "اِمْرُؤُ", "اِمْرَأَ", "اِمْرِئِ",
		 })
	end
end

-- The word اِمْرَأَة ("woman")
inflections["imraa"] = function(stem, tr, data, n)
	local IMRAA = "اِمْرَأَة"
	local IMRAAT = "اِمْرَأَت"
	local MARA = "مَرْأَة"
	local MARAT = "مَرْأَت"
	if n == "du" then
		add_inflections("", "", data, n,
			{IMRAAT .. AANI, IMRAAT .. AYNI, IMRAAT .. AYNI,
			 MARAT .. AANI, MARAT .. AYNI, MARAT .. AYNI,
			 IMRAAT .. AA, IMRAAT .. AYSK, IMRAAT .. AYSK,
			})
	else
		add_inflections("", "", data, n,
			{IMRAA .. UN, IMRAA .. AN, IMRAA .. IN,
			 MARA .. U, MARA .. A, MARA .. I,
			 IMRAA .. U, IMRAA .. A, IMRAA .. I,
			})
	end
end

function in_defective(stem, tr, data, n, sgin)
	stem = rsub(stem, IN .. "$", "")
	tr = rsub(tr, "in$", "")

	if n == "du" then
		add_dual(stem .. II, tr .. "iy", data)
	else
		add_inflections(stem, tr, data, n,
			{IN, sgin and II .. AN or II .. A, IN,
			 II, II .. A, II,
			 II, II .. A, II
			})
	end
end

-- Defective in -in
inflections["in"] = function(stem, tr, data, n)
	in_defective(stem, tr, data, n, n == "sg")
end

-- Defective in -in, force singular variant
inflections["sgin"] = function(stem, tr, data, n)
	in_defective(stem, tr, data, n, true)
end

-- Defective in -in, force plural variant
inflections["plin"] = function(stem, tr, data, n)
	in_defective(stem, tr, data, n, false)
end

-- Defective in -an (comes in two variants, depending on spelling with tall alif or alif maqṣūra)
inflections["an"] = function(stem, tr, data, n)
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

	-- Singular
	if tall_alif then
		if n == "du" then
			add_dual(stem .. AW, tr .. "aw", data)
		else
			add_inflections(stem, tr, data, n,
				{AN .. ALIF, AN .. ALIF, AN .. ALIF,
				 AA, AA, AA,
				 AA, AA, AA,
				})
		end
	else
		if n == "du" then
			add_dual(stem .. AY, tr .. "ay", data)
		else
			add_inflections(stem, tr, data, n,
				{AN .. AMAQ, AN .. AMAQ, AN .. AMAQ,
				 AAMAQ, AAMAQ, AAMAQ,
				 AAMAQ, AAMAQ, AAMAQ,
				})
		end
	end
end

-- Plural of defective in -an
inflections["awn"] = function(stem, tr, data, n)
	stem = rsub(stem, AWNA .. "?$", "")
	tr = rsub(tr, "awna?$", "")
	add_inflections(stem, data, n,
		{AWNA, AYNA, AYNA,
		 AWNA, AYNA, AYNA,
		 AWSK, AYSK, AYSK,
		})
end

-- Invariable in -ā (non-loanword type)
inflections["inv"] = function(stem, tr, data, n)
	if n == "du" then
		local dualstem
		if rfind(stem, AOPTA .. "$") then
			dualstem = rsub(stem, AOPTA .. "$", "")
		elseif rfind(stem, AOPT .. AMAQ .. "$") then
			dualstem = rsub(stem, AOPT .. AMAQ .. "$", "")
		else
			-- error("Don't know how to create dual for 'inv' declension type with this stem: " .. stem)
			-- Just have no dual in this case
			return
		end
		local dualtr = rsub(tr, "ā$", "")
		add_dual(dualstem .. AY, dualtr .. "ay", data)
	else
		add_inflections(stem, tr, data, n,
			{"", "", "",
			 "", "", "",
			 "", "", "",
			})
	end
end

-- Invariable in -ā (loanword type, behaving in the dual as if ending in -a, I think!)
inflections["lwinv"] = function(stem, tr, data, n)
	if n == "du" then
		local dualstem
		if rfind(stem, AOPTA .. "$") then
			dualstem = rsub(stem, AOPTA .. "$", "")
		else
			-- error("Don't know how to create dual for 'lwinv' declension type with this stem: " .. stem)
			-- Just have no dual in this case
			return
		end
		local dualtr = rsub(tr, "ā$", "")
		add_dual(dualstem .. AT, dualtr .. "at", data)
	else
		add_inflections(stem, tr, data, n,
			{"", "", "",
			 "", "", "",
			 "", "", "",
			})
	end
end

-- Sound masculine plural
inflections["sm"] = function(stem, tr, data, n)
	stem = rsub(stem, UU .. NA .. "?$", "")
	tr = rsub(tr, "ūna?$", "")
	add_inflections(stem, tr, data, n,
		{UU .. NA, II .. NA, II .. NA,
		 UU .. NA, II .. NA, II .. NA,
		 UU,       II,       II,
		})
end

-- Sound feminine plural
inflections["sf"] = function(stem, tr, data, n)
	stem = rsub(stem, UN .. "$", "")
	tr = rsub(tr, "un$", "")
	add_inflections(stem, tr, data, n,
		{UN, IN, IN,
		 U,  I,  I,
		 U,  I,  I,
		})
end

-- Detect declension of noun or adjective stem or lemma. We allow triptotes,
-- diptotes and sound plurals to either come with ʾiʿrāb or not. We detect
-- some cases where vowels are missing, when it seems fairly unambiguous to
-- do so. ISPL is true if we are dealing with a plural stem.
function export.detect_type(stem, ispl)
	-- Not strictly necessary because the caller (stem_and_type) already
	-- reorders, but won't hurt, and may be necessary if this function is
	-- called from an external caller.
	stem = reorder_shadda(stem)
	local origstem = stem
	-- So that we don't get tripped up by alif madda, we replace sequences of
	-- consonant + alif with alif madda and then match on alif madda in the
	-- regexps below.
	stem = rsub(stem, CONS .. AOPTA, AMAD)
	if ispl and rfind(stem, "^" .. CONS .. AOPT .. AMAD .. CONS .. IN .. "$") then -- layālin
		return 'plin'
	elseif rfind(stem, IN .. "$") then -- other -in words
		return 'sgin'
	elseif rfind(stem, AN .. "[" .. ALIF .. AMAQ .. "]$") then
		return 'an'
	elseif rfind(stem, AN .. "$") then
		error("Malformed stem, fatḥatan should be over second-to-last letter: " .. stem)
	elseif ispl and rfind(stem, AW .. SKOPT .. NUN .. AOPT .. "$") then
		return 'awn'
	elseif ispl and rfind(stem, AMAD .. TA .. UNOPT .. "$") then
		return 'sf'
	elseif ispl and rfind(stem, WAW .. NUN .. AOPT .. "$") then
		return 'sm'
	elseif rfind(stem, UN .. "$") then -- explicitly specified triptotes (we catch sound feminine plurals above)
		return 'tri'
	elseif rfind(stem, U .. "$") then -- explicitly specified diptotes
		return 'di'
	elseif ispl and ( -- various diptote plural patterns
		rfind(stem, "^" .. CONS .. AOPT .. AMAD .. CONS .. IOPT .. YA .. "?" .. CONS .. "$") or -- fawākih, daqāʾiq, makātib, mafātīḥ
		rfind(stem, "^" .. CONS .. AOPT .. AMAD .. CONS .. SH .. "$") or -- maqāmm
		rfind(stem, "^" .. CONS .. U .. CONS .. AOPT .. AMAD .. HAMZA .. "$") or -- wuzarāʾ
		rfind(stem, "^" .. HAMZA_OVER_ALIF .. AOPT .. CONS .. SKOPT .. CONS .. IOPT .. AMAD .. HAMZA .. "$") or -- ʾaṣdiqāʾ
		rfind(stem, "^" .. HAMZA_OVER_ALIF .. AOPT .. CONS .. IOPT .. CONS .. SH .. AOPTA .. HAMZA .. "$") -- ʾaqillāʾ
	    ) then
		return 'di'
	elseif not ispl and ( -- diptote singular patterns (mostly adjectives)
		rfind(stem, "^" .. CONS .. A .. CONS .. SK .. AMAD .. "[" .. NUN .. HAMZA .. "]$") or -- kaslān "lazy", qamrāʾ "moon-white, moonlight"
		rfind(stem, "^" .. CONS .. A .. CONS .. SH .. AOPTA .. "[" .. NUN .. HAMZA .. "]$") or -- laffāʾ "plump (fem.)"
		rfind(stem, "^" .. HAMZA_OVER_ALIF .. AOPT .. CONS .. SK .. CONS .. A .. CONS .. "$") or -- ʾabyad
		rfind(stem, "^" .. HAMZA_OVER_ALIF .. AOPT .. CONS .. A .. CONS .. SH .. "$") or -- ʾalaff
		-- do the following on the origstem so we can check specifically for alif madda
		rfind(origstem, "^" .. AMAD .. CONS .. A .. CONS .. "$") -- ʾālam "more painful", ʾāḵar "other"
		) then
		return 'di'
	elseif rfind(stem, AMAQ .. "$") then -- kaslā, ḏikrā (spelled with alif maqṣūra)
		return 'inv'
	-- Do the following on the origstem so we can check for YA + ALIF specifically.
	elseif rfind(origstem, "[" .. AMAD .. ALIF .. SK .. "]" .. YA .. AOPTA .. "$") then -- dunyā, hadāyā (spelled with tall alif after yāʾ)
		return 'inv'
	elseif rfind(stem, AMAD .. "$") then -- kāmērā, lībiyā (spelled with tall alif; we catch dunyā and hadāyā above)
		return 'lwinv'
	else
		return 'tri'
	end
end

-- Return stem and type of an argument given the singular stem and whether
-- this is a plural argument. WORD may be of the form ARABIC, ARABIC/TR,
-- ARABIC:TYPE, ARABIC/TR:TYPE, or TYPE, for Arabic stem ARABIC with
-- transliteration TR and of type (i.e. declension) TYPE. If the type
-- is omitted, it is auto-detected using detect_type(). If the transliteration
-- is omitted, it is auto-transliterated from the Arabic. If only the type
-- is present, it is either a type describing a single irregular word, e.g.
-- 'dhu', 'dhat', 'fam', 'imru' or 'imraa' (in which case the stem is
-- immaterial because it is already known) or it is a sound plural type
-- ('sf', 'sm' or 'awn'), in which case the stem and translit are generated
-- from the singular by regular rules. SG may be of the form ARABIC/TR or
-- ARABIC. ISPL is true if WORD is a plural stem. The return value will be
-- either in the ARABIC/TR format.
function export.stem_and_type(word, sg, sgtype, ispl)
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
	local function sub(arfrom, arto, trfrom, trto, trfrom2, trto2)
		if rfind(sgar, arfrom) then
			local arret, _ = rsub(sgar, arfrom, arto)
			local trret = sgtr
			if rfind(sgtr, trfrom) then
				trret, _ = rsub(sgtr, trfrom, trto)
			elseif trfrom2 and rfind(sgtr, trfrom2) then
				trret, _ = rsub(sgtr, trfrom2, trto2)
			elseif not rfind(sgtr, BOGUS_CHAR) then
				error("Transliteration '" .. sgtr .."' does not have same ending as Arabic '" .. sgar .. "'")
			end
			return arret .. "/" .. trret
		else
			return nil
		end
	end

	if not ispl and (word == "sf" or word == "sm" or word == "awn") then
		error("Inference of form for inflection type '" .. word .. "' only allowed in plural")
	end
	
	-- Supply the appropriate hamza seat for a placeholder hamza when
	-- followed by a short a. FIXME: Merge with the code in [[Module:ar-verb]]
	-- that also supplies the appropriate hamza seat, in a more general way.
	-- That code currently has normal hamzas (the on-the-line variety) as the
	-- placeholder, and uses a 'hamza_subst' char to indicate that a hamza
	-- on the line is really desired, which is later replaced with a normal
	-- hamza on the line. In this code we use HAMZA_PLACEHOLDER (whose
	-- construction is analogous to 'hamza_subst') as the placeholder,
	-- which allows us to control which hamzas we want replaced. We should
	-- switch [[Module:ar-verb]] to the same system and modify it so that
	-- it does something reasonable when it encounters a preceding letter
	-- that isn't a wāw, yāʾ or ʾalif (i.e. indicating a missing diacritic,
	-- which should be assumed a sukūn).
	local function hamza_seat(word)
		rsub(word, "([" .. I .. YA .. "]" .. SK .. "?)" .. HAMZA_PLACEHOLDER, "%1" .. HAMZA_OVER_YAA) -- i, ī or ay preceding
		rsub(word, "([" .. ALIF .. WAW .. "]" .. SK .. "?)" .. HAMZA_PLACEHOLDER, "%1" .. HAMZA) -- ā, ū or aw preceding
		rsub(word, U .. HAMZA_PLACEHOLDER, U .. HAMZA_OVER_WAW) -- u preceding
		rsub(word, HAMZA_PLACEHOLDER, HAMZA_OVER_ALIF) -- a, sukūn or missing sukūn preceding
		return word
	end

	if word == "sf" then

		local ret = (
			sub(AMAD .. TA_M .. UNUOPT .. "$", HAMZA_PLACEHOLDER .. AYAAT, "ā[ht]$", "ayāt", "ātun?$", "ayāt") or -- ends in -ʾāh; hamza placeholder will be replaced below
			sub(AOPTA .. TA_M .. UNUOPT .. "$", AYAAT, "ā[ht]$", "ayāt", "ātun?$", "ayāt") or -- ends in -āh
			sub(AOPT .. TA_M .. UNUOPT .. "$", AAT, "a$", "āt", "atun?$", "āt") or -- ends in -a
			sub(AN .. "[" .. ALIF .. AMAQ .. "]$", AYAAT, "an$", "ayāt") or -- ends in -an
			sub(IN .. "$", I .. YA .. AAT, "in$", "iyāt") or -- ends in -in
			sgtype == "inv" and (
				sub(AOPT .. "[" .. ALIF .. AMAQ .. "]$", AYAAT, "ā$", "ayāt") or -- ends in alif or alif maqṣūra
	            sub(AMAD .. "$", HAMZA_PLACEHOLDER .. AYAAT, "ā$", "ayāt") -- ends in ʾā; hamza placeholder will be replaced below
	        ) or
			sgtype == "lwinv" and (
				sub(AOPTA .. "$", AAT, "ā$", "āt") or -- loanword ending in tall alif
				sub(AMAD .. "$", AMAD .. TA, "ā$", "āt") -- loanword ending in ʾā
			) or
			-- We separate the ʾiʿrāb and no-ʾiʿrāb cases even though we can
			-- do a single Arabic regexp to cover both because we want to
			-- remove u(n) from the translit only when ʾiʿrāb is present to
			-- lessen the risk of removing -un in the actual stem. We also
			-- allow for cases where the ʾiʿrāb is present in Arabic but not
			-- in translit.
			sub(HAMZA_ANY .. UNU .. "$", AMAD .. TA, "un?$", "āt", "$", "āt") or -- ends in hamza + -u(n)
			sub(HAMZA_ANY .. "$", AMAD .. TA, "$", "āt") or -- ends in hamza
			-- Same here as above
			sub(UNU .. "$", AAT, "un?$", "āt", "$", "āt") or -- anything else + -u(n)
			sub("$", AAT, "$", "āt") -- anything else
		)
		ret = hamza_seat(ret)
		return ret, "sf"
	end

	if word == "sm" then
		local ret = (
			sub(IN .. "$", UU .. NUN, "in$", "ūn") or -- ends in -in
			-- See comments above for why we have two cases, one for UNU and
			-- one for non-UNU
			sub("[" .. HAMZA .. HAMZA_OVER_ALIF .. "]" .. UNU .. "$", HAMZA_OVER_WAW .. UU .. NUN, "un?$", "ūn", "$", "ūn") or -- ends in hamza + -u(n)
			sub("[" .. HAMZA .. HAMZA_OVER_ALIF .. "]" .. "$", HAMZA_OVER_WAW .. UU .. NUN, "$", "ūn") or -- ends in hamza
			-- Here too we have UNU and non-UNU cases, see above
			sub(UNU .. "$", UU .. NUN, "un?$", "ūn", "$", "ūn") or -- anything else + -u(n)
			sub("$", UU .. NUN, "$", "ūn") -- anything else
		)
		return ret, "sm"
	end

	if word == "awn" then
		local ret = (
			sub(AN .. "[" .. ALIF .. AMAQ .. "]$", AWSK .. NUN, "an$", "awn") -- ends in -an
		)
		if not ret then
			error("For 'awn', singular must end in -an: " .. sgar)
		end
		return ret, "awn"
	end

	if rfind(word, "^[a-z]") then --special nouns like dhu, dhat, fam, imru, imraa
		return "", word
	end
	return artr, export.detect_type(ar, ispl)
end

-- Make the table
function make_table(data)
	local function show_form(form, use_parens)
		if not form then
			return "&mdash;"
		elseif type(form) ~= "table" then
			error("a non-table value was given in the list of inflected forms.")
		end
		if #form == 0 then
			return "&mdash;"
		end
		
		local arabicvals = {}
		local latinvals = {}
		local parenvals = {}
		
		-- Accumulate separately the Arabic and transliteration into
		-- ARABICVALS and LATINVALS, then concatenate each down below.
		-- However, if USE_PARENS, we put each transliteration directly
		-- after the corresponding Arabic, in parens, and put the results
		-- in PARENVALS, which get concatenated below. (This is used in the
		-- title of the declension table.)
		for key, subform in ipairs(form) do
			local ar_span, tr_span
			local arabic, translit = split_arabic_tr(subform)
			if arabic == "-" then
				ar_span = "&mdash;"
				tr_span = "&mdash;"
			else
				if rfind(translit, BOGUS_CHAR) then
					translit = nil
				end
				tr_span = translit and "<span style=\"color: #888\">" .. translit .. "</span>" or "?"

				if arabic:find("{{{") then
					ar_span = m_links.full_link(nil, arabic, lang, nil, nil, nil, {tr = "-"}, false)
				else
					ar_span = m_links.full_link(arabic, nil, lang, nil, nil, nil, {tr = "-"}, false)
				end
				if use_parens then
					table.insert(parenvals, ar_span .. " (" .. tr_span .. ")")
				else
					table.insert(arabicvals, ar_span)
					table.insert(latinvals, tr_span)
				end
			end
		end
	
		local ortext = " <small style=\"color: #888\">or</small> "
		if use_parens then
			return table.concat(parenvals, ortext)
		else
			local arabic_span = table.concat(arabicvals, ortext)
			local latin_span = table.concat(latinvals, ortext)
			return arabic_span .. "<br />" .. latin_span
		end
	end
	
	-- Function used as replace arg of call to rsub(). Replace the
	-- specified param with its (HTML) value. The param references appear
	-- as {{{PARAM}}} in the wikicode below.
	local function repl(param)
		if param == "lemma" then
			return show_form(data.forms["lemma"] or data.forms["nom_sg_ind"], "use parens")
		elseif param == "info" then
			return data.title and " (" .. data.title .. ")" or ""
		else
			return show_form(data.forms[param])
		end
	end
	
	local wikicode = [=[<div class="NavFrame">
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
