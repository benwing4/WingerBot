#!/bin/bash

grep 'Page ' "$@" | perl -pe 's/Page (.*?):/Page :/;' \
    -e 's/(''plural of''|with|plural|noun-pl) [^ \n]*/$1/g;' \
    | sort | uniq -c | sort -nr
