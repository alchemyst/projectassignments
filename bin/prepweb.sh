#!/bin/bash

if [ $# -ne 2 ]; then
    echo $0 optFile.tar.gz moduledir
    exit 2
fi

# Specify the .tar.gz file from the website as the base file
tarfile=$1
module=$2

webdir=weboutput/
[ -e "$webdir" ] && mkdir "$webdir"

echo -n Deleting previous files...
rm -rf "$webdir"/*
echo " done"
echo -n Unpacking new files...
tar -xzv -C "$webdir" -f "$tarfile"
echo " done"

echo -n Copying files...
cp $webdir/*/{lecturers,preassigned,projects,selections}.csv $module
echo " done"

echo -n Constructing students.csv...
tr -d \" < $webdir/*/students.csv \
    | sed -e 1d \
    | awk -F, 'BEGIN {OFS=","} {print $2,$4" "$3}' \
    | sort \
    | join -t , -a 1 - marks.csv \
    | sed '/.*,.*,.*/!s/$/,50.00/' \
    | cat <( echo Number,Name,Mark ) - > $module/students.csv
echo " done"