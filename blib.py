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

def iter_pages(pageiter, startsort = None, endsort = None, key = None):
  i = 0
  t = None
  steps = 50

  for current in pageiter:
    i += 1

    if startsort != None and isinstance(startsort, int) and i < startsort:
      continue

    if endsort != None:
      if isinstance(endsort, int):
        if i > endsort:
          break
      else:
        if key:
          keyval = key(current)
        elif isinstance(current, basestring):
          keyval = current
        else:
          keyval = current.title(withNamespace=False)
        if keyval >= endsort:
          break

    if not t and isinstance(endsort, int):
      t = datetime.datetime.now()

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
  pageiter = page.subcategories(startsort = startsort if not isinstance(startsort, int) else None)
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
# template containing the Arabic and the param containing the Latin
# transliteration. It should return a changelog string if changes were made,
# and something else otherwise (e.g. False). Changelog strings for all
# templates will be joined together, separated by a semi-colon.
def process_links(save, verbose, cattype, startFrom, upTo, process_param,
    join_actions=None):
  templates_changed = {}

  # Process the link-like templates on the given page with the given text.
  # Returns the changed text along with a changelog message.
  def process_one_page_links(page, index, text):
    actions = []
    for template in text.filter_templates():
      result = None
      tempname = unicode(template.name)
      if tempname == "head" and getparam(template, "1") == "ar":
        result = process_param(page, index, template, "head", "tr")
      elif (tempname == "m" and getparam(template, "1") == "ar" and
          getparam(template, "3")):
        result = process_param(page, index, template, "3", "tr")
      elif (tempname == "term" and getparam(template, "lang") == "ar" and
          getparam(template, "2")):
        result = process_param(page, index, template, "2", "tr")
      elif (#tempname in ["l", "m"] and
          getparam(template, "1") == "ar"):
        # Try to process 2=
        result = process_param(page, index, template, "2", "tr")
      elif (#tempname in ["term", "plural of", "definite of", "feminine of", "diminutive of"] and
          tempname != "borrowing" and
          getparam(template, "lang") == "ar"):
        # Try to process 1=
        result = process_param(page, index, template, "1", "tr")
      if isinstance(result, list):
        actions.extend(result)
        templates_changed[tempname] = templates_changed.get(tempname, 0) + 1
    if not join_actions:
      changelog = '; '.join(actions)
    else:
      changelog = join_actions(actions)
    #if len(terms_processed) > 0:
    msg("Page %s %s: Change log = %s" % (index, page.title(), changelog))
    return text, changelog

  if cattype == "arabic":
    cats = ["Arabic lemmas", "Arabic non-lemma forms"]
  elif cattype == "borrowed":
    cats = ["%s terms derived from Arabic" % x for x in ["Alviri-Vidari",
      "Andalusian Arabic", "Azeri", "Baluchi", "Central Kurdish",
      "Egyptian Arabic", "Laki", "Libyan Arabic", "Malay", "Mazanderani",
      "Ottoman Turkish", "Pashto", "Persian", "Urdu"]]
  else:
    raise ValueError("Category type '%s' should be 'arabic' or 'borrowed'")
  for cat in cats:
    for page, index in cat_articles(cat, startFrom, upTo):
      do_edit(page, index, process_one_page_links, save=save, verbose=verbose)
  msg("Templates processed:")
  for template, count in sorted(templates_changed.items(), key=lambda x:-x[1]):
    msg("  %s = %s" % (template, count))

