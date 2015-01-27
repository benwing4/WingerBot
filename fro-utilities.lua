--[[
    Utilities for Old French nouns/adjectives
]]--

local export = {}
local links = require("Module:links")

-- local rfind = mw.ustring.find
local rgsub = mw.ustring.gsub
local rsub = mw.ustring.sub
-- local rmatch = mw.ustring.match

-- Return plural form(s) of a word; also used for nominative singular
function export.pluralize(word)
    local plurals = {}
    
    -- Add one or more plurals by changing FROM to TO1, TO2, TO3;
    -- return true if plurals were added 
    local function addpl(from, to1, to2, to3)
        local allto = {to1, to2, to3}
        local didsub = false
        for _, to in ipairs(allto) do
          local pl, nsub = rgsub(word, from, to)
          if nsub > 0 then
              table.insert(plurals, pl)
              didsub = true
          end
        end
        return didsub
    end

    -- canonicalize double letters to single
    word = rgsub(word, '(.)%1$', '%1')
    -- in the following expr, changes to 'plurals' happen by side effect
    local unused_retval =
    -- consonant + iel/uel pluralizes to -ieus/ueus
    -- for this and other cases involving -l, we have alternatives in
    -- -ls and often in -x (= -us after a vowel)
    addpl('([^aäeëeéiïouüyÿ][iu])el$', '%1eus', '%1ex', '%1els') or
    -- other -el pluralizes to -eaus
    addpl('el$', 'eaus', 'eax', 'els') or
    -- -ail/eil/oil pluralizes to -auz/euz/ouz
    addpl('([aeo])il$', '%1uz', '%1ilz') or
    -- -uil pluralizes to -uz
    addpl('uil$', 'uz', 'uilz') or
    -- other -il/ïl pluralizes to -iz/ïz (or sometimes -is/ïs, depending on word!)
    addpl('([iï])l$', '%1z', '%1lz') or
    -- -ul pluralizes to -us
    addpl('([aeio])ul$', '%1us', '%1x', '%1uls') or
    addpl('([uü])l$', '%1s', '%1ls') or
    -- other -l pluralizes to -us
    addpl('l$', 'us', 'x', 'ls') or
    -- -ing pluralizes to -inz
    addpl('([iï])ng$', '%1nz') or
    -- other -ng also pluralizes to -inz, with added -i-
    addpl('ng$', 'inz') or
    -- same for final -gn or -ngn
    addpl('([iï])n?gn$', '%1nz') or
    addpl('n?gn$', 'inz') or
    -- vowel + -in was usually earlier -ing and so pluralizes to -nz
    addpl('([aeou])in$', '%1inz') or
    -- single-syllable word does not need é in -es
    addpl('^([^aäeëéiïoöuüyÿ]*)e[ckgfvpb]$', '%1es') or
    -- other words do
    addpl('e[ckgfvpb]$', 'és') or
    addpl('[ckgfvbp]$', 's') or
    addpl('st$', 'z') or
    addpl('[td]$', 'z') or
    addpl('é$', 'ez') or
    -- add -s unless ending in -s/x/z
    addpl('([^sxz])$', '%1s') or
    -- finally use the word unchanged
    table.insert(plurals, word)

    return plurals
end

-- Return feminine form of a word
function export.feminine(word)
    if type(word) == 'table' then word = word.args[1] end

    if rsub(word, -1) == "e" then
        return word
    elseif rsub(word, -2) == "if" then
        return rsub(word, 1, -2) .. 've'
    else
        word = word .. 'e'
        word = rgsub(word, 'ée$', 'ee')

        return word
    end
end

local function generate_noun_forms(word)
    local forms = {}

    forms.nsm = export.pluralize(word)
    forms.nsf = export.feminine(word)
    forms.osm = word
    forms.osf = export.feminine(word)
    forms.npm = word
    forms.npf = export.pluralize(export.feminine(word))
    forms.opm = export.pluralize(word)
    forms.opf = export.pluralize(export.feminine(word))

    -- wikilink the forms
    forms.nsm = links.annotated_link("[[" .. table.concat(forms.nsm, "]], [[") .. "]]", nil, "fro")
    forms.nsf = links.annotated_link(forms.nsf, nil, "fro")
    forms.osm = links.annotated_link(forms.osm, nil, "fro")
    forms.osf = links.annotated_link(forms.osf, nil, "fro")
    forms.npm = links.annotated_link(forms.npm, nil, "fro")
    forms.npf = links.annotated_link("[[" .. table.concat(forms.npf, "]], [[") .. "]]", nil, "fro")
    forms.opm = links.annotated_link("[[" .. table.concat(forms.opm, "]], [[") .. "]]", nil, "fro")
    forms.opf = links.annotated_link("[[" .. table.concat(forms.opf, "]], [[") .. "]]", nil, "fro")

    return forms
end

function export.generate_noun_decl_table(frame)
    local word = frame:getParent().args[1]
    local forms = generate_noun_forms(word)

    return [=[<div class="NavFrame" style="clear:both;margin-top:1em;display:inline-block;">
<div class="NavHead" align="left">&nbsp;&nbsp;Declension of <span lang="fro">'']=] .. word .. [=[''</span></div>
<div class="NavContent" align="center">
{| style="float:left;border:1px solid #AAAACC;margin-left:0.5em;margin-bottom:0.5em;text-align:left;" rules="all" cellpadding="3" cellspacing="0"
! bgcolor="#EEEEFF" | '''Number'''
! bgcolor="#EEEEFF" | '''Case'''
! bgcolor="#EEEEFF" | '''Masculine'''
! bgcolor="#EEEEFF" | '''Feminine'''
|-
| bgcolor="#EEEEEE" rowspan="2" | '''Singular'''
| bgcolor="#EEEEEE" | '''[[Appendix:Glossary#subject|Subject]]'''
| <span class="inflection-table">]=] .. forms.nsm .. [=[</span>
| <span class="inflection-table">]=] .. forms.nsf .. [=[</span>
|-
| bgcolor="#EEEEEE" | '''[[Appendix:Glossary#oblique|Oblique]]'''
| <span class="inflection-table">]=] .. forms.osm .. [=[</span>
| <span class="inflection-table">]=] .. forms.osf .. [=[</span>
|-
| bgcolor="#EEEEEE" rowspan="2" | '''Plural'''
| bgcolor="#EEEEEE" | '''Subject'''
| <span class="inflection-table">]=] .. forms.npm .. [=[</span>
| <span class="inflection-table">]=] .. forms.npf .. [=[</span>
|-
| bgcolor="#EEEEEE" | '''Oblique'''
| <span class="inflection-table">]=] .. forms.opm .. [=[</span>
| <span class="inflection-table">]=] .. forms.opf .. [=[</span>
|}
</div>
</div>]=]
end

return export
