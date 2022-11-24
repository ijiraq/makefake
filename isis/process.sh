# Steps to run ISIS image subtraction, relies on SWARP:

# define where the image database is and which VERSION and PREFIX we are processing.
export DBIMAGES=${DBIMAGES:-/arc/projects/classy/dbimages/}
export PREFIX=${PREFIX:-fk}
export VERSION=${VERSION:-p}
export exp_list=${exp_list:-list.txt}
export ref_list=${ref_list:-ref_list.txt}

# for this processing script we need the input reference lists
export exp_list=$(realpath ${exp_list})
export ref_list=$(realpath ${ref_list})

# which CCD are we doing
export ccd=${ccd:-0}


##### The rest of the script does not need to be editted to start a new run

# Expects the artificial source added images start with 'fk' adjust this script as needed
# Put the exposure numbers of all the images for a block in list.txt 
# Put the expousre numbers of exposures that should go into reference image in ref_list.txt

# PUT 'single extension fits' images into a directory using the `populate.py` script 
# this only needs to be run once per list of files as each CCD is done in one loop.
#  cd ${DBIMAGES}
#  echo "# INFO: Working in $(pwd)"
#  for expnum in $(cat ${exp_list})
#  do
#     cd ${expnum}
#     image_filname=${PREFIX}${expnum}${VERSION}.fits 
#     /arc/home/jkavelaars/classy-pipeline/venv/bin/python /arc/projects/classy/pipeline/populate.py  image_filename
#     cd ${DBIMAGES}
#  done


# SWARP images to a common reference system and make a coAdd image 
# we can run that command repeatedly until all 'swarps' succeed. 
# here we just do it once

assembleCoadd.sh -l INFO ${exp_list} ${ref_list} ${ccd}

# now we do the image differencing
# this can also be run repeatedly also, until all frames succeed.  
# each chip directory should have a file like conv_interp_fkXXXXXXXpYY.OK to indicate success
run_imageDifference.sh -l INFO $(head -n 1 ${ref_list}) ${exp_list} ${ccd}

# Next we build a mask of the differenced image to help kbmod find KBOs instead of bad columns
run_makeMask.sh -l INFO ${exp_list} ${ccd}
# wait until the last job finishes 

# Now we put the difference, masks  and variance (made internall) into an MEF
# this is also the step where we 'invert' the difference images as 'ISIS' subtracts from the ref
run_assembleDIFFEXP.sh -l INFO ${exp_list} ${ccd} 

# DONE
