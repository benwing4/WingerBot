local HAMZA_OVER_ALIF = u(0x0623)
local HAMZA_OVER_WAW = u(0x0624)
local HAMZA_UNDER_ALIF = u(0x0625)
local HAMZA_OVER_YA = u(0x0626)
local DAGGER_ALIF = u(0x0670)
local HAMZA_ANY = "[" .. HAMZA .. HAMZA_OVER_ALIF .. HAMZA_UNDER_ALIF .. HAMZA_OVER_WAW .. HAMZA_OVER_YA .. "]"
local DIACRITIC_ANY_BUT_SH = "[" .. A .. I .. U .. AN .. IN .. UN .. SK .. DAGGER_ALIF .. "]"
local AMAY = A .. "?"
local AAMAY = A .. "?" .. ALIF
local IMAY = I .. "?"
local UMAY = U .. "?"
local UNMAY = UN .. "?"
local SKMAY = SK .. "?"
local AYAAT = A .. YA .. AA .. TA

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
		rfind(stem, "^" .. AMAD .. CONS .. A .. CONS .. "$") or -- ʾālam "more painful", ʾāḵar "other"
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
			local ret, _ = r(sg, from, to)
			return ret
		else
			return nil
		end
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

function export.test()
	local ret = ""
	local function test_sc(sg, form, outform, outclass, ispl)
		if outform == nil then
			outform = form
		end
		local oform, oclass = export.stem_and_class(form, sg, ispl)
		local result
		if oform == outform and oclass == outclass then
			result = "Passed"
		else
			result = "Failed"
		end
		ret = ret .. result .. ": .. test_sc(" .. sg .. ", " .. form .. ", " .. outform .. ", " .. outclass .. ", " .. (ispl and "true" or "false") .. ")<br />"
	end

	test_sc("مرْآة", "sf", "مرْأَيَات", "sf")
	test_sc("مراة", "sf", "مرَيَات", "sf")
	test_sc("مَرَاة", "sf", "مَرَيَات", "sf")
	test_sc("مُسْتَشْفًى", "sf", "مُسْتَشْفَيَات", "sf")
	test_sc("كَاتٍ", "sf", "كَاتِيَات", "sf")
	test_sc("ذِكْرَى", "sf", "ذِكْرَيَات", "sf")
	test_sc("دُنْيَا", "sf", "دُنْيَيَات", "sf")
	test_sc("كَامِيرَا", "sf", "كَامِيرَات", "sf")
	test_sc("كُبْء", "sf", "كُبْآت", "sf")
	test_sc("كُوب", "sf", "كُوبَات", "sf")

	test_sc("كَاتٍ", "sm", "كَاتُون", "sm")
	test_sc("كَتَأ", "sm", "كَتَؤُون", "sm")
	test_sc("كَتِئ", "sm", "كَتِئُون", "sm")
	test_sc("كُبْء", "sm", "كُبْؤُون", "sm")
	test_sc("مُسْلِم", "sm", "مُسْلِمُون", "sm")

	test_sc("كَتًى", "awn", "كَتَوْن", "awn")

	test_sc("", "كَاتِب", nil, "tri")

	test_sc("", "دُنْيَا", nil, "inv") -- dunyā "world"
	test_sc("", "هَدَايَا", nil, "inv", true) -- hadāyā "gifts"
	test_sc("", "ذِكْرَى", nil, "inv") -- ḏikrā "remembrance"
	test_sc("", "لِيبِيَا", nil, "lwinv") -- lībiyā "Libya"
	test_sc("", "كَامِيرَا", nil, "lwinv") -- kāmērā "camera"
	test_sc("", "لَيَالٍ", nil, "plin", true) -- layālin "nights"
	test_sc("", "مَآسٍ", nil, "plin", true) -- maʾāsin "tragedies, dramas"
	test_sc("", "أَيْدٍ", nil, "sgin", true) -- ʾaydin "hands"
	test_sc("", "وَادٍ", nil, "sgin") -- wādin "valley"
	test_sc("", "مُسْتَشْفًى", nil, "an") -- mustašfan "hospital"
	test_sc("", "عَصًا", nil, "an") -- ʿaṣan "stick"
	test_sc("", "أَدْنَوْن", nil, "awn", true) -- ʾadnawn "nearer (masc. pl.)"
	test_sc("", "أَدْنَوْنَ", nil, "awn", true) -- ʾadnawna "nearer (masc. pl.)"
	test_sc("", "مُسْلِمُون", nil, "sm", true) -- muslimūn "Muslims"
	test_sc("", "مُسْلِمُونَ", nil, "sm", true) -- muslimūna "Muslims"
	test_sc("", "مُسْلِمَة", nil, "tri") -- muslima "Muslim (fem.)"
	test_sc("", "مُسْلِمَةٌ", nil, "tri") -- muslimatun "Muslim (fem.)"
	test_sc("", "مُسْلِمَات", nil, "sf", true) -- muslimāt "Muslims (fem.)"
	test_sc("", "مُسْلِمَاتٌ", nil, "sf", true) -- muslimāti "Muslims (fem.)"
	test_sc("", "فَوَاكِه", nil, "di", true) -- fawākih "fruits"
	test_sc("", "فَوَاكِهُ", nil, "di", true) -- fawākihu "fruits"
	test_sc("", "مَفَاتِيح", nil, "di", true) -- mafātīḥ "keys"
	test_sc("", "مَقَامّ", nil, "di", true) -- maqāmm "brooms"
	test_sc("", "مَقَامُّ", nil, "di", true) -- maqāmmu "brooms"
	test_sc("", "وُزَرَاء", nil, "di", true) -- wuzarāʾ "ministers"
	test_sc("", "أَصْدِقَاء", nil, "di", true) -- ʾaṣdiqāʾ "friends"
	test_sc("", "أَقِلَّاء", nil, "di", true) -- ʾaqillāʾ "small (masc. pl.)"
	test_sc("", "كَسْلَان", nil, "di") -- kaslān "lazy"
	test_sc("", "قَمْرَاء", nil, "di") -- qamrāʾ "moon-white, moonlight"
	test_sc("", "لَفَّاء", nil, "di") -- laffāʾ "plump (fem.)"
	test_sc("", "أَحْمَر", nil, "di") -- ʾaḥmar "red"
	test_sc("", "أَلَفّ", nil, "di") -- ʾalaff "plump"
	test_sc("", "آلَم", nil, "di") -- ʾālam "more painful"
	test_sc("", "كِتَاب", nil, "tri") -- kitāb "book"
	test_sc("", "كُتُب", nil, "tri", true) -- kutub "books"
	test_sc("", "أَفْلَام", nil, "tri", true) -- ʾaflām "films"

	return ret
end

-- For Vim, so we get 4-space tabs
-- vim: set ts=4 sw=4 noet:
