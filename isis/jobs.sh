#!/bin/bash
source ${HOME}/.bashrc
for filename in 2022-09*_images_list.txt;
do
	echo ${filename}
	date="$(echo ${filename%%_images_list.txt} | sed -e 's/-//g')"
	ref="${filename%%.txt}_ref.txt"
	JOBID=()
	for ccd in $(seq 0 39) 
	do 
		ID=$(sk_launch skaha/terminal:1.1.2 l${date}p${ccd} swarp_isis.sh ${filename} ${ref} ${ccd})  || exit $?
		JOBID+=${ID}
	done
	echo "${JOBID[@]}"
	sk_wait "${JOBID[@]}" 
done
