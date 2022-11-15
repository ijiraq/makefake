# Steps to run ISIS image subtraction, relies on SWARP:

# define where the image database is
export DBIMAGES=/arc/projects/classy/dbimages/
export exp_list=list.txt
export ref_list=ref_list.txt
export ccd=0

# Expects the artificial source added images start with 'fk' adjust this script as needed
# Put the exposure numbers of all the images for a block in list.txt 
# Put the expousre numbers of exposures that should go into reference image in ref_list.txt

# PUT 'single extension fits' images into a directory using the `populate.py` script 
# this only needs to be run once per list of files as each CCD is done in one loop.
cd ${DBIMAGES}
for expnum in $(cat list.txt)
do
cd ${expnum}
image=
/arc/home/jkavelaars/classy-pipeline/vevn/python /arc/projects/classy/pipeline/populate.py  image_filename
done


# Start a SWARP container and go to the directory where populate.py put the fk images

assembleCoadd.sh $(head -1 ${ref_list}) ${exp_list} ${ref_list} ${ccd}
# run that command repeatedly until all 'swarps' succeed. Each chip directory should now have a
# file with a name like interp_fkXXXXXXXXpYY.OK which indicates that the swarp step succeeded.

# now we do the image differencing
run_imageDifference.sh $(head -1 ref_list.txt) ${exp_list} ${ccd}
# this can be run repeatedly also, until all frames succeed.  
# each chip directory should have a file like conv_interp_fkXXXXXXXpYY.OK to indicate success

# Next we build a mask of the differenced image to help kbmod find KBOs instead of bad columns
run_makeMask.sh ${exp_list} ${ccd}

# Now we put the difference, masks  and variance (made internall) into an MEF
# this is also the step where we 'invert' the difference images as 'ISIS' subtracts from the ref
run_assembleDIFFEXP.sh ${exp_list} ${ccd} 

# DONE
