#!/bin/bash
if [[ 0 -gt 10 ]]
then
for filename in *.plantList 
do 
  expnum=${filename%%pccd*}
  newname=$(echo $filename | sed -e 's/ccd//') 
  ccd=${filename##${expnum}p}
  ccd=${ccd%%.plantList}
  ccdno=${ccd##ccd}
  cp -v ${filename} ../dbimages/${expnum}/${ccd}/${expnum}p${ccdno}.plantList
done
fi

for filename in *.fits
do 
  expnum=${filename%%p.fits}
  cp -v ${filename} ../dbimages/${expnum}/fk${filename}
done
