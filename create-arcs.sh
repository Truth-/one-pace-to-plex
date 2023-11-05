#!/usr/bin/sh
set -e

BASEDIR=$(dirname "$0")
echo "$BASEDIR"

i=0

while read p; do
  if [ $i -lt 2 ]; then
    i=$((i+1))
    continue
  fi
  if [ -n "$p" ]; then
    mkdir -p "$p"
    cp -f "$BASEDIR/tvdb4.mapping" "$p/tvdb4.mapping"
  fi
done <  "$BASEDIR/arcs-directories.txt"

