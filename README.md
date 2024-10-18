# makefake
Some fortran and python code to generate a distribution of Keplarian orbits
appropriate for use as the basis for adding artificial TNOs to images.

MakeFake and ClassyMakeFake are meant to be used to generate sets of orbits
that can be used to generate locations on the sky at a given observational
epoch form a given reference frame.  These positions are then given to programs
like GalSim to add those sources to images to calibrate the detection 
efficiency of the detection software given the specific imaging conditions.

