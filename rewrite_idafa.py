#!/usr/bin/env python

import re

import blib
from blib import msg, getparam, addparam

# FIXME! Finish writing this, based on other .py files.

def rewrite_one_page_idafa(page, index, text):
  def pagemsg(txt):
    msg("Page %s %s: %s" % (index, page, txt))
  num_new_style = 0
  num_modhead_changed = 0
  idafa_added = []
  for t in text.filter_templates():
    if t.name == "ar-decl-noun":
      changed = False

      # Change old-style ʾidāfa (state=con) to new-style (basestate=con)
      oldt = unicode(t)
      if (getparam(t, "state") == "con" and getparam(t, "modcase") and
          not getparam(t, "basestate"))
        modstate = getparam(t, "modstate")
        addparam(t, "basestate", "con")
        addparam(t, "modidafa", "yes")
        if not modstate:
          t.remove("state")
        else:
          addparam(t, "state", modstate)
        pagemsg("Replacing %s with %s" % (oldt, unicode(t)))
        changed = True

      # Remove manual ʾidāfa params when possible and substitute idafa=
      oldt = unicode(t)
      if getparam(t, "basestate") == "con" and getparam(t, "modcase") == "gen":
        idafa = ""
        modnumber = getparam(t, "modnumber")
        if not modnumber:
          pagemsg("WARNING: Missing modnumber= in idafa template: %s" %
              unicode(t))
        else:
          modstate = getparam(t, "modstate")
          state = getparam(t, "state")
          if not modstate:
            if state:
              pagemsg("WARNING: Extraneous state= in idafa template: %s" %
                  unicode(t))
            idafa = modnumber
          elif state != modstate:
            pagemsg("WARNING: modstate= in idafa template but state= doesn't match: %s"
                % unicode(t))
          else:
            idafa = "%s-%s" % (modstate, modnumber)
            t.remove("state")
            t.remove("modstate")
          if idafa:
            t.remove("basestate")
            t.remove("modcase")
            t.remove("modidafa")
            m = re.match("^(.*?)-sg$", idafa)
            if m:
              idafa = m.group(1)
            if idafa == "sg":
              idafa = "yes"
            addparam(t, "idafa", idafa)
            pagemsg("Replacing %s with %s" % (oldt, unicode(t)))
            idafa_added.append(idafa)
          elif changed:
            num_new_style += 1
      if (getparam(t, "basestate") or getparam(t, "modcase") or
          getparam(t, "modstate") or getparam(t, "modnumber") or
          getparam(t, "modidafa")):
        pagemsg("WARNING: idafa params remain after processing: %s" %
            unicode(t))

      # Change modN into modheadN
      oldt = unicode(t)
      changed = False
      for i in xrange(2, 20):
        modn = getparam(t, "mod" + str(i))
        if modn:
          t.remove("mod" + str(i))
          addparam(t, "modhead" + str(i), modn)
          changed = True
      if changed:
        pagemsg("Replacing %s with %s" % (oldt, unicode(t)))
        num_modhead_changed += 1

  if idafa_added or num_new_style or num_modhead_changed:
    actions = []
    if idata_added:
      actions.append(u"Replaced ʾidāfa params with idafa= param: %s" % (
          ", ".join(idafa_added)))
    if num_new_style:
      actions.append(u"Corrected %s old-style ʾidāfa param(s) to new-style"
          % num_new_style)
    if num_modhead_changed:
      actions.append(u"Changed modN to modheadN")
    changelog = "; ".join(actions)
    pagemsg("Changelog = %s" % changelog)
    return changelog, text
  return "", text

def rewrite_idafa(save, verbose, startFrom, upTo):
  for page, index in blib.references("Template:ar-decl-noun", startFrom, upTo):
    blib.do_edit(page, index, rewrite_one_page_idafa, save=save,
        verbose=verbose)
