import os, sys

visit = sys.argv[1]

with open(f'/arc/projects/NewHorizons/{visit}/{visit}_template_visit_list.txt') as han:
    data = han.readlines()

comm = 'ds9 '
for i in range(len(data)):
    s = data[i].split()
    fn = f'/arc/projects/NewHorizons/HSC_21_June-lsst/rerun/{visit}_warpCompare/deepCoadd/HSC-R2/0/{'
    comm += s[0]+' '
os.system(comm)
