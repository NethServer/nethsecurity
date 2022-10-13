#!/bin/bash

# parent path
ppath="../packages/"
# destination path
dpath="packages"

[ -d "$dpath" ] && rm -rf "$dpath"

mkdir -p $dpath
for path in $(find $ppath -name \*.md);
do
    # use readme parent path as file name
    readme=$(dirname "${path#"$ppath"}")
    if [ "$readme" = "." ]; then
        dst_file="$dpath/index.md"
        (
           echo "---"
           echo "layout: default"
           echo "has_children: true"
           echo "title: Packages"
           echo "nav_order: 10"
           echo "---"
        ) > $dst_file
    else
        dst_file="$dpath/$readme.md"
        (
           echo "---"
           echo "layout: default"
           echo "parent: Packages"
           echo "---"
        ) > $dst_file
    fi
    cat $path >> $dst_file
done

