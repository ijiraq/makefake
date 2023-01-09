#!/bin/bash
cd $1
mkdir old
for filename in DIFFEXP-2773*
do
	echo ${filename}
	python3 /arc/home/jkavelaars/findMoving/src/daomop/augment_mask.py ${filename} --maskfile ${filename%%.fits} --maskbits BRIGHT_OBJECT --log-level INFO
	mv ${filename} old/
	mv mask_${filename} ${filename}
done
