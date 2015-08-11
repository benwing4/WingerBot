local export = {}

local form_types = {
	{key = "cardinal", display = "[[cardinal number|Cardinal]]"},
	{key = "ordinal", display = "[[ordinal number|Ordinal]]"},
	{key = "adverbial", display = "[[adverbial number|Adverbial]]"},
	{key = "multiplier", display = "[[multiplier|Multiplier]]"},
	{key = "distributive", display = "[[distributive number|Distributive]]"},
	{key = "collective", display = "[[collective number|Collective]]"},
	{key = "fractional", display = "[[fractional|Fractional]]"},
}

function export.show_box(frame)
	local m_links = require("Module:links")
	
	local params = {
		[1] = {required = true},
		[2] = {required = true, type = "number"},
	}
	
	local args = require("Module:parameters").process(frame:getParent().args, params)
	
	local lang = args[1] or "und"
	local cur_num = args[2] or 2
	lang = require("Module:languages").getByCode(lang) or error("The language code \"" .. lang .. "\" is not valid.")
	
	-- Get the data from the data module
	local m_data = require("Module:number list/data/" .. lang:getCode())
	local cur_data = m_data.numbers[cur_num]
	
	-- Go over each number and make links
	local forms = {}
	local cur_type
	
	-- Insert text for each type of number. An individual entry is either
	-- a string or a list of elements, each of which is either a string or
	-- a two-element list {TEXT, TR} for specified text and transliteration.
	local function insert_form(key, display)
		local entries = cur_data[key]
		if entries then
			if type(entries) ~= "table" then
				entries = {entries}
			end
			local links = {}
			for _, entry in ipairs(entries) do
				local link, tr
				if type(entry) == "string" then
					link = entry
				else
					link = entry[1]
					tr = entry[2]
				end
				table.insert(links, m_links.full_link(link, nil, lang, nil,
					nil, nil, {tr = tr}, false))
				-- If this number is the current page, then store the key
				-- for later use
				if lang:makeEntryName(link) == mw.title.getCurrentTitle().fullText then
					cur_type = key
				end
			end
			table.insert(forms, " &nbsp;&nbsp;&nbsp; ''" .. display ..
				"'' : " .. table.concat(links, ", "))
			
		end
	end

	for _, form_type in ipairs(form_types) do
		insert_form(form_type.key, form_type.display)
	end
	insert_form("other", cur_data["other_title"])
	for i=2,9 do
		insert_form("other" .. i, cur_data["other" .. i .. "_title"])
	end

	if not cur_type and mw.title.getCurrentTitle().nsText ~= "Template" then
		error("The current page name does not match any of the numbers listed in the data module for " .. cur_num .. ". Check the data module or the spelling of the page.")
	end
	
	-- Current number in header
	local cur_display = m_links.full_link(nil, cur_num, lang, sc, nil, nil, {tr = "-"}, false)
	
	if cur_data["numeral"] then
		cur_display = m_links.full_link(nil, cur_data["numeral"], lang, nil, nil, nil, {tr = "-"}, false) .. "<br/><span style=\"font-size: smaller;\">" .. cur_display .. "</span>"
	end
	
	local function first_entry(entries)
		if type(entries) == "string" then
			return entries
		end
		if type(entries[1]) == "string" then
			return entries[1]
		end
		return entries[1][1]
	end
	
	-- Link to previous number
	local prev_data = m_data.numbers[cur_num - 1]
	local prev_display = ""
	
	if prev_data and prev_data[cur_type] then
		prev_display = m_links.full_link(first_entry(prev_data[cur_type]), "&nbsp;&lt;&nbsp;&nbsp;" .. (cur_num - 1), lang, nil, nil, nil, {tr = "-"}, false)
	end
	
	-- Link to next number
	local next_data = m_data.numbers[cur_num + 1]
	local next_display = ""
	
	if next_data and next_data[cur_type] then
		next_display = m_links.full_link(first_entry(next_data[cur_type]), (cur_num + 1) .. "&nbsp;&nbsp;&gt;&nbsp;", lang, nil, nil, nil, {tr = "-"}, false)
	end
	
	-- Link to number times ten and divided by ten
	-- Show this only if the number is a power of ten times a number 1-9 (that is, of the form x000...)
	local up_display
	local down_display
	
	-- This test *could* be done numerically, but this is nice and simple and it works.
	if mw.ustring.find(tostring(cur_num), "^[1-9]0*$") then
		local up_data = m_data.numbers[cur_num * 10]
		
		if up_data and up_data[cur_type] then
			up_display = m_links.full_link(first_entry(up_data[cur_type]), (cur_num * 10), lang, nil, nil, nil, {tr = "-"}, false)
		end
		
		-- Only divide by 10 if the number is at least 10
		if cur_num >= 10 then
			local down_data = m_data.numbers[cur_num / 10]
			
			if down_data and down_data[cur_type] then
				down_display = m_links.full_link(first_entry(down_data[cur_type]), (cur_num / 10), lang, nil, nil, nil, {tr = "-"}, false)
			end
		end
	end
	
	return [=[{| class="floatright" cellpadding="5" cellspacing="0" style="background: #ffffff; border: 1px #aaa solid; border-collapse: collapse; margin-top: .5em;" rules="all" 
|+ ''']=] .. lang:getCanonicalName() .. [=[ numbers'''
]=] .. (up_display and [=[|- style="text-align: center; background:#dddddd;"
|
| style="font-size:smaller;" | ]=] .. up_display .. [=[

|
]=] or "") .. [=[|- style="text-align: center;"
| style="min-width: 6em; font-size:smaller; background:#dddddd;" | ]=] .. prev_display .. [=[

! style="min-width: 6em; font-size:larger;" | ]=] .. cur_display .. [=[

| style="min-width: 6em; font-size:smaller; background:#dddddd;" | ]=] .. next_display .. [=[

]=] .. (down_display and [=[|- style="text-align: center; background:#dddddd;"
|
| style="font-size:smaller;" | ]=] .. down_display .. [=[

|
]=] or "") .. [=[|-
| colspan="3" | ]=] .. table.concat(forms, "<br/>") .. [=[

|}]=]	
end


function export.show_box_manual(frame)
	local m_links = require("Module:links")
	local num_type = frame.args["type"]
	
	local args = {}
	--cloning parent's args while also assigning nil to empty strings
	for pname, param in pairs(frame:getParent().args) do
		if param == "" then args[pname] = nil
        else args[pname] = param
        end
	end
	
	local lang = args[1] or (mw.title.getCurrentTitle().nsText == "Template" and "und") or error("Language code has not been specified. Please pass parameter 1 to the template.")
	local sc = args["sc"]; 
	local headlink = args["headlink"]
	local wplink = args["wplink"]
	local alt = args["alt"]
	local tr = args["tr"]
	
	local function inetrim(val)
		if val and mw.text.trim(val) == "" then
			return nil
		else
			return val
		end
	end

	local prev_symbol = inetrim(args[2])
	local cur_symbol = inetrim(args[3])
	local next_symbol = inetrim(args[4])
	
	local prev_term = inetrim(args[5])
	local next_term = inetrim(args[6])

	local cardinal_term = args["card"]; local cardinal_alt = args["cardalt"]; local cardinal_tr = args["cardtr"]
	
	local ordinal_term = args["ord"]; local ordinal_alt = args["ordalt"]; local ordinal_tr = args["ordtr"]
	
	local adverbial_term = args["adv"]; local adverbial_alt = args["advalt"]; local adverbial_tr = args["advtr"]
	
	local multiplier_term = args["mult"]; local multiplier_alt = args["multalt"]; local multiplier_tr = args["multtr"]
	
	local distributive_term = args["dis"]; local distributive_alt = args["disalt"]; local distributive_tr = args["distr"]
	
	local collective_term = args["coll"]; local collective_alt = args["collalt"]; local collective_tr = args["colltr"]
	
	local fractional_term = args["frac"]; local fractional_alt = args["fracalt"]; local fractional_tr = args["fractr"]
	
	local optional1_title = args["opt"]
	local optional1_term = args["optx"]; local optional1_alt = args["optxalt"]; local optional1_tr = args["optxtr"]
	
	local optional2_title = args["opt2"]
	local optional2_term = args["opt2x"]; local optional2_alt = args["opt2xalt"]; local optional2_tr = args["opt2xtr"]
	

	lang = require("Module:languages").getByCode(lang) or error("The language code \"" .. lang .. "\" is not valid.")
	sc = (sc and (require("Module:scripts").getByCode(sc) or error("The script code \"" .. sc .. "\" is not valid.")) or nil)
	
	require("Module:debug").track("number list/" .. lang:getCode())
	
	if sc then
		require("Module:debug").track("number list/sc")
	end
	
	if headlink then
		require("Module:debug").track("number list/headlink")
	end
	
	if wplink then
		require("Module:debug").track("number list/wplink")
	end
	
	if alt then
		require("Module:debug").track("number list/alt")
	end
	
	if cardinal_alt or ordinal_alt or adverbial_alt or multiplier_alt or distributive_alt or collective_alt or fractional_alt or optional1_alt or optional2_alt then
		require("Module:debug").track("number list/xalt")
	end
	
	local is_reconstructed = lang:getType() == "reconstructed" or (lang:getType() ~= "appendix-constructed" and mw.title.getCurrentTitle().nsText == "Appendix")
	alt = alt or (is_reconstructed and "*" or "") .. mw.title.getCurrentTitle().subpageText
	
	if num_type == "cardinal" then
		cardinal_term = (is_reconstructed and "*" or "") .. mw.title.getCurrentTitle().subpageText
		cardinal_alt = alt
		cardinal_tr = tr
	elseif num_type == "ordinal" then
		ordinal_term = (is_reconstructed and "*" or "") .. mw.title.getCurrentTitle().subpageText
		ordinal_alt = alt
		ordinal_tr = tr
	end
	
	local header = lang:getCanonicalName() .. " " .. num_type .. " numbers"
	
	if headlink then
		header = "[[" .. headlink .. "|" .. header .. "]]"
	end
	
	local previous = ""

	local function make_link(page, text, tr)
		return m_links.full_link(page, text, lang, sc, nil, nil, {tr = tr}, false)
	end
	
	if prev_term or prev_symbol then
		previous = make_link(prev_term, "&nbsp;&lt;&nbsp;&nbsp;" .. prev_symbol, "-")
	end
	
	local current = make_link(nil, cur_symbol, "-")
	
	local next = ""
	
	if next_term or next_symbol then
		next = make_link(next_term, next_symbol .. "&nbsp;&nbsp;&gt;&nbsp;", "-")
	end
	
	local forms = {}
	
	if cardinal_term then
		table.insert(forms, " &nbsp;&nbsp;&nbsp; ''[[cardinal number|Cardinal]]'' : " .. make_link(cardinal_term, cardinal_alt, cardinal_tr))
	end
	
	if ordinal_term then
		table.insert(forms, " &nbsp;&nbsp;&nbsp; ''[[ordinal number|Ordinal]]'' : " .. make_link(ordinal_term, ordinal_alt, ordinal_tr))
	end
	
	if adverbial_term then
		table.insert(forms, " &nbsp;&nbsp;&nbsp; ''[[adverbial number|Adverbial]]'' : " .. make_link(adverbial_term, adverbial_alt, adverbial_tr))
	end
	
	if multiplier_term then
		table.insert(forms, " &nbsp;&nbsp;&nbsp; ''[[multiplier|Multiplier]]'' : " .. make_link(multiplier_term, multiplier_alt, multiplier_tr))
	end
	
	if distributive_term then
		table.insert(forms, " &nbsp;&nbsp;&nbsp; ''[[distributive number|Distributive]]'' : " .. make_link(distributive_term, distributive_alt, distributive_tr))
	end
	
	if collective_term then
		table.insert(forms, " &nbsp;&nbsp;&nbsp; ''[[collective number|Collective]]'' : " .. make_link(collective_term, collective_alt, collective_tr))
	end
	
	if fractional_term then
		table.insert(forms, " &nbsp;&nbsp;&nbsp; ''[[fractional|Fractional]]'' : " .. make_link(fractional_term, fractional_alt, fractional_tr))
	end
	
	if optional1_title then
		table.insert(forms, " &nbsp;&nbsp;&nbsp; ''" .. optional1_title .. "'' : " .. make_link(optional1_term, optional1_alt, optional1_tr))
	end
	
	if optional2_title then
		table.insert(forms, " &nbsp;&nbsp;&nbsp; ''" .. optional2_title .. "'' : " .. make_link(optional2_term, optional2_alt, optional2_tr))
	end
	
	local footer = ""
	
	if wplink then
		footer =
			"[[w:" .. lang:getCode() .. ":Main Page|" .. lang:getCanonicalName() .. " Wikipedia]] article on " ..
			make_link("w:" .. lang:getCode() .. ":" .. wplink, alt, tr)
	end
	
	return [=[{| class="floatright" cellpadding="5" cellspacing="0" style="background: #ffffff; border: 1px #aaa solid; border-collapse: collapse; margin-top: .5em;" rules="all" 
|+ ''']=] .. header .. [=['''
|-
| style="width: 64px; background:#dddddd; text-align: center; font-size:smaller;" | ]=] .. previous .. [=[

! style="width: 98px; text-align: center; font-size:larger;" | ]=] .. current .. [=[

| style="width: 64px; text-align: center; background:#dddddd; font-size:smaller;" | ]=] .. next .. [=[

|-
| colspan="3" | ]=] .. table.concat(forms, "<br/>") .. [=[

|-
| colspan="3" style="text-align: center; background: #dddddd;" | ]=] .. footer .. [=[

|}]=]
end

return export

-- For Vim, so we get 4-space tabs
-- vim: set ts=4 sw=4 noet:
