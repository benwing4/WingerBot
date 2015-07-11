#!/usr/bin/env python
#coding: utf-8

import fileinput
import re

for line in fileinput.input():
  line = line.decode('utf-8')
  if re.search(ur"plural أَ.ْ.َات", line):
    print line
