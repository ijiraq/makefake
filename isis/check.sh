#!/bin/bash
for expnum in $(cat $1)
do
	for ccd in $(seq 0 21)
	do
		diff="$(printf "${expnum}/ccd%02.0f/DIFFEXP-${expnum}-%02.0f.fits" ${ccd} ${ccd})"
		[ -f ${diff} ] || echo "missing ${diff}"
	done
done
