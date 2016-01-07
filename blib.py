#!/usr/bin/env python
#coding: utf-8

# Author: CodeCat for MewBot; fixes by Benwing

#    blib.py is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import pywikibot, mwparserfromhell, re, sys, urllib2, datetime, json, argparse
from arabiclib import reorder_shadda

site = pywikibot.Site()


def msg(text):
  #pywikibot.output(text.encode('utf-8'), toStdout = True)
  print text.encode('utf-8')

def msgn(text):
  #pywikibot.output(text.encode('utf-8'), toStdout = True)
  print text.encode('utf-8'),

def errmsg(text):
  #pywikibot.output(text.encode('utf-8'))
  print >> sys.stderr, text.encode('utf-8')

def errmsgn(text):
  print >> sys.stderr, text.encode('utf-8'),

def display(page):
  errmsg(u'# [[{0}]]'.format(page.title()))

def dump(page):
  old = page.get(get_redirect=True)
  msg(u'Contents of [[{0}]]:\n{1}\n----------'.format(page.title(), old))

def parse(page):
  return parse_text(page.text)

def parse_text(text):
  return mwparserfromhell.parser.Parser().parse(text,
    skip_style_tags=True)

def getparam(template, param):
  if template.has(param):
    return unicode(template.get(param).value)
  else:
    return ""

def addparam(template, param, value, showkey=None, before=None):
  if re.match("^[0-9]+", param):
    template.add(param, value, preserve_spacing=False, showkey=showkey,
        before=before)
  else:
    template.add(param, value, showkey=showkey, before=before)

def rmparam(template, param):
  if template.has(param):
    template.remove(param)

def getrmparam(template, param):
  val = getparam(template, param)
  rmparam(template, param)
  return val

def expand_text(tempcall, pagetitle, pagemsg, verbose):
  if verbose:
    pagemsg("Expanding text: %s" % tempcall)
  result = site.expand_text(tempcall, title=pagetitle)
  if verbose:
    pagemsg("Raw result is %s" % result)
  if result.startswith('<strong class="error">'):
    result = re.sub("<.*?>", "", result)
    if not verbose:
      pagemsg("Expanding text: %s" % tempcall)
    pagemsg("WARNING: Got error: %s" % result)
    return False
  return result

def do_edit(page, index, func=None, null=False, save=False, verbose=False):
  title = page.title()
  def pagemsg(text):
    msg("Page %s %s: %s" % (index, title, text))
  while True:
    try:
      if func:
        if verbose:
          pagemsg("Begin processing")
        new, comment = func(page, index, parse(page))

        if new:
          new = unicode(new)

          # Canonicalize shaddas when comparing pages so we don't do saves
          # that only involve different shadda orders.
          if reorder_shadda(page.text) != reorder_shadda(new):
            if verbose:
              pagemsg('Replacing [[%s]] with [[%s]]' % (page.text, new))
            page.text = new
            if save:
              pagemsg("Saving with comment = %s" % comment)
              page.save(comment = comment)
            else:
              pagemsg("Would save with comment = %s" % comment)
          elif null:
            pagemsg('Purged page cache')
            page.purge(forcelinkupdate = True)
          else:
            pagemsg('Skipped, no changes')
        elif null:
          pagemsg('Purged page cache')
          page.purge(forcelinkupdate = True)
        else:
          pagemsg('Skipped: %s' % comment)
      else:
        pagemsg('Purged page cache')
        page.purge(forcelinkupdate = True)
    except (pywikibot.LockedPage, pywikibot.NoUsername):
      errmsg(u'Page %s %s: Skipped, page is protected' % (index, title))
    except urllib2.HTTPError as e:
      if e.code != 503:
        raise
    except:
      errmsg(u'Page %s %s: Error' % (index, title))
      raise

    break

def do_process_text(pagetitle, pagetext, index, func=None, verbose=False):
  def pagemsg(text):
    msg("Page %s %s: %s" % (index, pagetitle, text))
  while True:
    try:
      if func:
        if verbose:
          pagemsg("Begin processing")
        new, comment = func(pagetitle, index, parse_text(pagetext))

        if new:
          new = unicode(new)

          # Canonicalize shaddas when comparing pages so we don't do saves
          # that only involve different shadda orders.
          if reorder_shadda(pagetext) != reorder_shadda(new):
            if verbose:
              pagemsg('Replacing [[%s]] with [[%s]]' % (pagetext, new))
            #if save:
            #  pagemsg("Saving with comment = %s" % comment)
            #  page.save(comment = comment)
            #else:
            pagemsg("Would save with comment = %s" % comment)
          else:
            pagemsg('Skipped, no changes')
        else:
          pagemsg('Skipped: %s' % comment)
    except:
      errmsg(u'Page %s %s: Error' % (index, pagetitle))
      raise

    break

ignore_prefixes = ["User:", "Talk:",
    "Wiktionary:Beer parlour", "Wiktionary:Translation requests",
    "Wiktionary:Grease pit", "Wiktionary:Etymology scriptorium",
    "Wiktionary:Information desk"]

def iter_pages(pageiter, startsort = None, endsort = None, key = None):
  i = 0
  t = None
  steps = 50

  for current in pageiter:
    i += 1

    if startsort != None and isinstance(startsort, int) and i < startsort:
      continue

    if key:
      keyval = key(current)
      pagetitle = keyval
    elif isinstance(current, basestring):
      keyval = current
      pagetitle = keyval
    else:
      keyval = current.title(withNamespace=False)
      pagetitle = unicode(current.title())
    if endsort != None:
      if isinstance(endsort, int):
        if i > endsort:
          break
      else:
        if keyval >= endsort:
          break

    if not t and isinstance(endsort, int):
      t = datetime.datetime.now()

    # Ignore user pages, talk pages and certain Wiktionary pages
    is_ignore_prefix = False
    for ip in ignore_prefixes:
      if pagetitle.startswith(ip):
        is_ignore_prefix = True
    if " talk:" in pagetitle:
      is_ignore_prefix = True
    if not is_ignore_prefix:
      yield current, i

    if i % steps == 0:
      tdisp = ""

      if isinstance(endsort, int):
        told = t
        t = datetime.datetime.now()
        pagesleft = (endsort - i) / steps
        tfuture = t + (t - told) * pagesleft
        tdisp = ", est. " + tfuture.strftime("%X")

      errmsg(str(i) + "/" + str(endsort) + tdisp)


def references(page, startsort = None, endsort = None, namespaces = None, includelinks = False):
  if isinstance(page, basestring):
    page = pywikibot.Page(site, page)
  pageiter = page.getReferences(onlyTemplateInclusion = not includelinks,
      namespaces = namespaces)
  for pageind in iter_pages(pageiter, startsort, endsort):
    yield pageind

def cat_articles(page, startsort = None, endsort = None):
  if type(page) is str:
    page = page.decode("utf-8")
  if isinstance(page, basestring):
    page = pywikibot.Category(site, "Category:" + page)
  pageiter = page.articles(startsort = startsort if not isinstance(startsort, int) else None)
  for pageind in iter_pages(pageiter, startsort, endsort):
    yield pageind

def cat_subcats(page, startsort = None, endsort = None):
  if type(page) is str:
    page = page.decode("utf-8")
  if isinstance(page, basestring):
    page = pywikibot.Category(site, "Category:" + page)
  pageiter = page.subcategories() #no startsort; startsort = startsort if not isinstance(startsort, int) else None)
  for pageind in iter_pages(pageiter, startsort, endsort):
    yield pageind

def prefix(prefix, startsort = None, endsort = None, namespace = None):
  pageiter = site.prefixindex(prefix, namespace)
  for pageind in iter_pages(pageiter, startsort, endsort):
    yield pageind

def stream(st, startsort = None, endsort = None):
  i = 0

  for name in st:
    i += 1

    if startsort != None and i <= startsort:
      continue
    if endsort != None and i > endsort:
      break

    if type(name) is str:
      name = str.decode(name, "utf-8")

    name = re.sub(ur"^[#*] *\[\[(.+)]]$", ur"\1", name, flags=re.UNICODE)

    yield pywikibot.Page(site, name)


def get_args(args = sys.argv[1:]):
  startsort = None
  endsort = None

  if len(args) >= 1:
    startsort = args[0]
  if len(args) >= 2:
    endsort = args[1]
  return parse_start_end(startsort, endsort)

def parse_start_end(startsort, endsort):
  if startsort != None:
    try:
      startsort = int(startsort)
    except ValueError:
      startsort = str.decode(startsort, "utf-8")
  if endsort != None:
    try:
      endsort = int(endsort)
    except ValueError:
      endsort = str.decode(endsort, "utf-8")

  return (startsort, endsort)

def init_argparser(desc):
  pa = argparse.ArgumentParser(description=desc)
  pa.add_argument("-s", "--save", action='store_true',
      help="Save changed pages")
  pa.add_argument("-v", "--verbose", action='store_true',
      help="Show changes in detail")
  pa.add_argument("start", nargs="?", help="First page to work on")
  pa.add_argument("end", nargs="?", help="Last page to work on")
  return pa

def remove_links(text):
  text = re.sub(r"\[\[[^|\]]*?\|", "", text)
  text = re.sub(r"\[\[", "", text)
  text = re.sub(r"\]\]", "", text)
  return text

languages = None
languages_byCode = None
languages_byCanonicalName = None

families = None
families_byCode = None
families_byCanonicalName = None

scripts = None
scripts_byCode = None
scripts_byCanonicalName = None

etym_languages = None
etym_languages_byCode = None
etym_languages_byCanonicalName = None

wm_languages = None
wm_languages_byCode = None
wm_languages_byCanonicalName = None


def getData():
  getLanguageData()
  getFamilyData()
  getScriptData()
  getEtymLanguageData()

def getLanguageData():
  global languages, languages_byCode, languages_byCanonicalName

  languages = json.loads(site.expand_text("{{#invoke:User:MewBot|getLanguageData}}"))
  languages_byCode = {}
  languages_byCanonicalName = {}

  for lang in languages:
    languages_byCode[lang["code"]] = lang
    languages_byCanonicalName[lang["canonicalName"]] = lang


def getFamilyData():
  global families, families_byCode, families_byCanonicalName

  families = json.loads(site.expand_text("{{#invoke:User:MewBot|getFamilyData}}"))
  families_byCode = {}
  families_byCanonicalName = {}

  for fam in families:
    families_byCode[fam["code"]] = fam
    families_byCanonicalName[fam["canonicalName"]] = fam


def getScriptData():
  global scripts, scripts_byCode, scripts_byCanonicalName

  scripts = json.loads(site.expand_text("{{#invoke:User:MewBot|getScriptData}}"))
  scripts_byCode = {}
  scripts_byCanonicalName = {}

  for sc in scripts:
    scripts_byCode[sc["code"]] = sc
    scripts_byCanonicalName[sc["canonicalName"]] = sc


def getEtymLanguageData():
  global etym_languages, etym_languages_byCode, etym_languages_byCanonicalName

  etym_languages = json.loads(site.expand_text("{{#invoke:User:MewBot|getEtymLanguageData}}"))
  etym_languages_byCode = {}
  etym_languages_byCanonicalName = {}

  for etyl in etym_languages:
    etym_languages_byCode[etyl["code"]] = etyl
    etym_languages_byCanonicalName[etyl["canonicalName"]] = etyl

# Process link-like templates, on pages from STARTFROM to (but not including)
# UPTO, either page names or 0-based integers. Save changes if SAVE is true.
# VERBOSE is passed to blib.do_edit and will (e.g.) show exact changes.
# PROCESS_PARAM is the function called, which is called with five arguments:
# The page, its index (an integer), the template on the page, the param in the
# template containing the foreign text and the param containing the Latin
# transliteration, or None if there is no such parameter. NOTE: The param may
# be an array ["page title", PARAM] for a case where the param value should be
# fetched from the page title and saved to PARAM. It should return a list of
# changelog strings if changes were made, and something else otherwise
# (e.g. False). Changelog strings for all templates will be joined together
# using JOIN_ACTIONS; if not supplied, they will be separated by a semi-colon.
#
# LANG should be a short language code (e.g. 'ru', 'ar', 'grc'), and LONGLANG
# the canonical language name (e.g. "Russian", "Arabic", "Ancient Greek").
# CATTYPE is either 'vocab' (do lemmas and non-lemma pages for the language),
# 'borrowed' (do pages for terms borrowed from the language), 'translation'
# (do pages containing references to any of the 5 standard translation
# templates), 'pagetext' (do the pages in PAGES_TO_DO, a list of (TITLE, TEXT)
# entries); for doing off-line runs; nothing saved), or 'pages' (do the
# pages in PAGES_TO_DO, a list of page titles).
#
# If SPLIT_TEMPLATES, then if the transliteration contains multiple entries
# separated the regex in SPLIT_TEMPLATES with optional spaces on either end,
# the template is split into multiple copies, each with one of the entries,
# and the templates are comma-separated.
#
# If QUIET, don't output the list of processed templates at the end.
def process_links(save, verbose, lang, longlang, cattype, startFrom, upTo,
    process_param, join_actions=None, split_templates="[,]",
    pages_to_do=[], quiet=False):
  templates_changed = {}
  templates_seen = {}

  # Process the link-like templates on the page with the given title and text,
  # calling PROCESSFN for each pair of foreign/Latin. Return a list of
  # changelog actions.
  def do_process_one_page_links(pagetitle, index, text, processfn):
    def pagemsg(text):
      msg("Page %s %s: %s" % (index, pagetitle, text))

    actions = []
    for template in text.filter_templates():
      def doparam(param, trparam="tr", noadd=False):
        if not noadd:
          templates_seen[tempname] = templates_seen.get(tempname, 0) + 1
        result = processfn(pagetitle, index, template, param, trparam)
        if result and isinstance(result, list):
          actions.extend(result)
          if not noadd:
            templates_changed[tempname] = templates_changed.get(tempname, 0) + 1
          return True
        return False
      def getp(param):
        return getparam(template, param)
      tempname = unicode(template.name)

      did_template = False
      if lang == "grc":
        # Special-casing for Ancient Greek
        did_template = True
        def dogrcparam(trparam):
          if getp("head"):
            doparam("head", trparam)
          else:
            doparam(["page title", "head"], trparam)
        if tempname in ["grc-noun-con"]:
          dogrcparam("5")
        elif tempname in ["grc-proper noun", "grc-noun"]:
          dogrcparam("4")
        elif tempname in ["grc-adj-1&2", "grc-adj-1&3", "grc-part-1&3"]:
          dogrcparam("3")
        elif tempname in ["grc-adj-2nd", "grc-adj-3rd", "grc-adj-2&3"]:
          dogrcparam("2")
        elif tempname in ["grc-num"]:
          dogrcparam("1")
        elif tempname in ["grc-verb"]:
          dogrcparam("tr")
        else:
          did_template = False
      elif lang == "ru":
        # Special-casing for Russian
        if tempname == "ru-participle of":
          if getp("2"):
            doparam("2")
          else:
            doparam("1")
          did_template = True
        elif tempname == "ru-xlit":
          doparam("1", None)
          did_template = True
        elif tempname == "ru-ux":
          doparam("1")
          did_template = True

      # Skip {{attention|ar|FOO}} or {{etyl|ar|FOO}} or {{audio|FOO|lang=ar}}
      # or {{lb|ar|FOO}} or {{context|FOO|lang=ar}} or {{Babel-2|ar|FOO}}
      # or various others, where FOO is not Arabic
      if (tempname in [
        "attention",
        "audio", "audio-IPA",
        "catlangcode", "C", "catlangname",
        "commonscat",
        "etyl", "etym",
        "gloss",
        "label", "lb", "context", "cx",
        "non-gloss definition", "non-gloss", "non gloss", "n-g",
        "qualifier", "qual", "i", "italbrac",
        "rfe", "rfinfl",
        "sense", "italbrac-colon",
        "senseid",
        "given name",
        "+preo", "IPA", "phrasebook", "PIE root", "surname", "Q", "was fwotd"]
        or "Babel" in tempname):
        pass
      elif did_template:
        pass
      # Look for {{head|ar|...|head=<ARABIC>}}
      elif tempname == "head":
        if getp("1") == lang:
          if getp("head"):
            doparam("head")
          else:
            doparam(["page title", "head"])
      # Look for {{t|ar|<PAGENAME>|alt=<ARABICTEXT>}}
      elif tempname in ["t", "t+", "t-", "t+check", "t-check"]:
        if getp("1") == lang:
          if getp("alt"):
            doparam("alt")
          else:
            doparam("2")
      # Look for {{suffix|ar|<PAGENAME>|alt1=<ARABICTEXT>|<PAGENAME>|alt2=...}}
      # or  {{suffix|ar|<ARABICTEXT>|<ARABICTEXT>|...}}
      elif (tempname in ["suffix", "suffix2", "prefix", "confix", "affix",
          "circumfix", "infix", "compound"]):
        if getp("lang") == lang:
          templates_seen[tempname] = templates_seen.get(tempname, 0) + 1
          anychanged = False
          # Don't just do cases up through where there's a numbered param
          # because there may be holes.
          for i in xrange(1, 11):
            if getp("alt" + str(i)):
              changed = doparam("alt" + str(i), "tr" + str(i), noadd=True)
            else:
              changed = doparam(str(i), "tr" + str(i), noadd=True)
            anychanged = anychanged or changed
          if anychanged:
            templates_changed[tempname] = templates_changed.get(tempname, 0) + 1
      elif tempname == "form of":
        if getp("lang") == lang:
          if getp("3"):
            doparam("3")
          else:
            doparam("2")
      # Templates where we don't check for alternative text because
      # the following parameter is used for the translation.
      elif tempname in ["ux", "lang"]:
        if getp("1") == lang:
          doparam("2")
      elif tempname == "usex":
        if getp("lang") == lang:
          doparam("1")
      elif tempname == "cardinalbox":
        if getp("1") == lang:
          pagemsg("WARNING: Encountered cardinalbox, check params carefully: %s"
              % unicode(template))
          # FUCKME: This is a complicated template, might be doing it wrong
          doparam("5", None)
          doparam("6", None)
          for p in ["card", "ord", "adv", "mult", "dis", "coll", "frac",
              "optx", "opt2x"]:
            if getp(p + "alt"):
              doparam(p + "alt", p + "tr")
            else:
              doparam(p, p + "tr")
          if getp("alt"):
            doparam("alt")
          else:
            doparam("wplink", None)
      elif tempname in ["der2", "der3", "der4", "der5", "rel2", "rel3", "rel4",
          "rel5", "hyp2", "hyp3", "hyp4", "hyp5"]:
        if getp("lang") == lang:
          i = 1
          while getp(str(i)):
            doparam(str(i), None)
            i += 1
      elif tempname == "elements":
        if getp("lang") == lang:
          doparam("2", None)
          doparam("4", None)
          doparam("next2", None)
          doparam("prev2", None)
      elif tempname == "w":
        if getp("lang") == lang:
          doparam("w", None)
      elif tempname in ["bor", "borrowing"] and getp("lang"):
        if getp("1") == lang:
          if getp("alt"):
            doparam("alt")
          elif getp("3"):
            doparam("3")
          else:
            doparam("2")
      elif tempname in ["der", "derived", "inh", "inherited", "bor", "borrowing"]:
        if getp("2") == lang:
          if getp("alt"):
            doparam("alt")
          elif getp("4"):
            doparam("4")
          else:
            doparam("3")
      # Look for any other template with lang as first argument
      elif (#tempname in ["l", "link", "m", "mention"] and
          # If "1" matches, don't do templates with a lang= as well,
          # e.g. we don't want to do {{hyphenation|ru|men|lang=sh}} in
          # Russian because it's actually lang sh.
          getp("1") == lang and not getp("lang")):
        # Look for:
        #   {{m|ar|<PAGENAME>|<ARABICTEXT>}}
        #   {{m|ar|<PAGENAME>|alt=<ARABICTEXT>}}
        #   {{m|ar|<ARABICTEXT>}}
        if getp("alt"):
          doparam("alt")
        elif getp("3"):
          doparam("3")
        elif tempname != "transliteration":
          doparam("2")
      # Look for any other template with "lang=ar" in it. But beware of
      # {{borrowing|en|<ENGLISHTEXT>|lang=ar}}.
      elif (#tempname in ["term", "plural of", "definite of", "feminine of", "diminutive of"] and
          getp("lang") == lang):
        # Look for:
        #   {{term|lang=ar|<PAGENAME>|<ARABICTEXT>}}
        #   {{term|lang=ar|<PAGENAME>|alt=<ARABICTEXT>}}
        #   {{term|lang=ar|<ARABICTEXT>}}
        if getp("alt"):
          doparam("alt")
        elif getp("2"):
          doparam("2")
        else:
          doparam("1")
    return actions

  # Process the link-like templates on the given page with the given text.
  # Returns the changed text along with a changelog message.
  def process_one_page_links(pagetitle, index, text):
    actions = []
    newtext = [unicode(text)]

    def pagemsg(text):
      msg("Page %s %s: %s" % (index, pagetitle, text))

    # First split up any templates with commas in the Latin
    if split_templates:
      def process_param_for_splitting(pagetitle, index, template, param, paramtr):
        if isinstance(param, list):
          fromparam, toparam = param
        else:
          fromparam = param
        if fromparam == "page title":
          foreign = pagetitle
        else:
          foreign = getparam(template, fromparam)
        latin = getparam(template, paramtr)
        if (re.search(split_templates, latin) and not
            re.search(split_templates, foreign)):
          trs = re.split("\\s*" + split_templates + "\\s*", latin)
          oldtemp = unicode(template)
          newtemps = []
          for tr in trs:
            addparam(template, paramtr, tr)
            newtemps.append(unicode(template))
          newtemp = ", ".join(newtemps)
          old_newtext = newtext[0]
          pagemsg("Splitting template %s into %s" % (oldtemp, newtemp))
          new_newtext = old_newtext.replace(oldtemp, newtemp)
          if old_newtext == new_newtext:
            pagemsg("WARNING: Unable to locate old template when splitting trs on commas: %s"
                % oldtemp)
          elif len(new_newtext) - len(old_newtext) != len(newtemp) - len(oldtemp):
            pagemsg("WARNING: Length mismatch when splitting template on tr commas, may have matched multiple templates: old=%s, new=%s" % (
              oldtemp, newtemp))
          newtext[0] = new_newtext
          return ["split %s=%s" % (paramtr, latin)]
        return []

      actions += do_process_one_page_links(pagetitle, index, text,
          process_param_for_splitting)
      text = parse_text(newtext[0])

    actions += do_process_one_page_links(pagetitle, index, text, process_param)
    if not join_actions:
      changelog = '; '.join(actions)
    else:
      changelog = join_actions(actions)
    #if len(terms_processed) > 0:
    pagemsg("Change log = %s" % changelog)
    return text, changelog

  def process_one_page_links_wrapper(page, index, text):
    return process_one_page_links(unicode(page.title()), index, text)

  if "," in cattype:
    cattypes = cattype.split(",")
  else:
    cattypes = [cattype]
  for cattype in cattypes:
    if cattype in ["translation", "links"]:
      if cattype == "translation":
        templates = ["t", "t+", "t-", "t+check", "t-check"]
      else:
        templates = ["l", "m", "term", "link", "mention"]
      for template in templates:
        msg("Processing template %s" % template)
        errmsg("Processing template %s" % template)
        for page, index in references("Template:%s" % template, startFrom, upTo):
          do_edit(page, index, process_one_page_links_wrapper, save=save,
              verbose=verbose)
    elif cattype == "pages":
      for pagename, index in iter_pages(pages_to_do, startFrom, upTo):
        page = pywikibot.Page(site, pagename)
        do_edit(page, index, process_one_page_links_wrapper, save=save,
            verbose=verbose)
    elif cattype == "pagetext":
      for current, index in iter_pages(pages_to_do, startFrom, upTo,
          key=lambda x:x[0]):
        pagetitle, pagetext = current
        do_process_text(pagetitle, pagetext, index, process_one_page_links,
            verbose=verbose)
    else:
      if cattype == "vocab":
        cats = ["%s lemmas" % longlang, "%s non-lemma forms" % longlang]
      elif cattype == "borrowed":
        cats = [subcat for subcat, index in
            cat_subcats("Terms derived from %s" % longlang)]
      else:
        raise ValueError("Category type '%s' should be 'vocab', 'borrowed', 'translation', 'links', 'pages' or 'pagetext'")
      for cat in cats:
        msg("Processing category %s" % unicode(cat))
        errmsg("Processing category %s" % unicode(cat))
        for page, index in cat_articles(cat, startFrom, upTo):
          do_edit(page, index, process_one_page_links_wrapper, save=save,
              verbose=verbose)
  if not quiet:
    msg("Templates seen:")
    for template, count in sorted(templates_seen.items(), key=lambda x:-x[1]):
      msg("  %s = %s" % (template, count))
    msg("Templates processed:")
    for template, count in sorted(templates_changed.items(), key=lambda x:-x[1]):
      msg("  %s = %s" % (template, count))
