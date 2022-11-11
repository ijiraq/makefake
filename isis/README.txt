
# Steps to run ISIS image subtraction, relies on SWARP:

# PUT 'single extension fits' images into a directory using the `populate.py` script

for image_filename in fk*.fits
do
/arc/home/jkavelaars/classy-pipeline/vevn/python /arc/projects/classy/pipeline/populate.py  image_filename
done

# I'm going to assume the artificial source added images start with 'fk' adjust this script as needed

# Put the names of images to use for the reference image (ie the best 1/3rd of images) into file named 'ref_list.txt'

# Start a SWARP container and go to the directory where populate.py put the fk images

/arc/projects/classy/pipeline/swarp.sh fk*.fits   #  This will create interp_ and ref.fits images.. these are aligned and rectified images

# Start an ISIS container and go to the directory where you just ran swarp.sh

/arc/projects/classy/pipeline/diff.sh fk*.fits

# This produces a bunch of images names 'conv_interp_{image}.fits' where {image} is the name of the images craeted by populate.py 

# Now we put the masks (made in the swarp step) and the subtracted images into an MEF.. this is also the step where we 'invert' the difference images as 'ISIS' subtracts from the ref image and we want to have subtracted the ref image.

/arc/home/jkavelaars/classy-pipeline/build_DIFFEXP.sh fk*.fits

