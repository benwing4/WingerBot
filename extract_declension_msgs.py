#!/bin/bash

grep '^Page ' "$@" | perl -pe 's/Page (.*?):/Page :/;' \
    -e 's/[^\x00-\x7F]//g;' \
    -e 's/(\{\{ar-[a-z- ]*)\|.*?\}\}.*/$1\}\}/g;' \
    -e 's/ manual translit [^ \n]*/ $1/g;' \
    -e 's/\[\[\|?\]\]//g;' \
    | sort | uniq -c | sort -nr
#grep '^Page ' "$@" | perl -pe 's/Page (.*?):/Page :/;' \
#    -e 's/ (head|from|manual translit|of) [^ \n]*/ $1/g;' \
#    -e "s/(Can't find headword template in text), skipping:"'/$1:/g;' \
#    -e 's/(skipping:).*/$1/g;' \
#    -e 's/(\{\{ar-[a-z- ]*)\|.*?\}\}.*/$1\}\}/g;' \
#    -e 's/(head) .*? (has space)/$1 $2/g;' \
#    -e 's/(Declension already found for head) .*? (skipping):/$1 $2:/g;' \
#    | sort | uniq -c | sort -nr
