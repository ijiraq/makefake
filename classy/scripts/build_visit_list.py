"""Build a list of visits for a given pointing using ccd 20 as the reference CCD.

Outputs a complete list of visits that are accessible on disk and
provides a of the best 1/2 of the list for tempalte constructions.

"""
import argparse
import lsst.daf.persistence as dafPersist
import numpy
import logging
import os

logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument('basedir', help="base directory where rerun list located")
parser.add_argument('rerun', help="rerun directory to build visit list from")
parser.add_argument('date', help="Date to get visit list for")
parser.add_argument('filter', help="Filter to build list for", default='r2')

args = parser.parse_args()
basedir = args.basedir
date = args.date
filter = args.filter

butler = dafPersist.Butler(inputs=f'{basedir}/rerun/{args.rerun}')

rough_visit_list = butler.queryMetadata('calexp',
                                        ['date', 'visit'],
                                        dataId={
                                            'filter': filter,
                                            'date': date,
                                            'ccd': 22})

visit_list = []
for (visit_date, visit) in rough_visit_list:
    logging.info(f"visit: {visit} date:{visit_date}")
    if visit_date in date:
        visit_list.append(visit)

visit_info = []
for n, visit in enumerate(visit_list):
    try:
        calexp = butler.get('calexp', dataId={'visit': visit, 'ccd': 22})
        psf_radius = (calexp.getPsf().computeShape().getArea() / 3.1415) ** 0.5
        visit_info.append([visit, psf_radius])
    except Exception as ex:
        logging.error(f"{visit} {ex}")

visit_info = numpy.array(visit_info)
sorted_info = visit_info[visit_info[:, 1].argsort()]

# Make sure the visitLists directory exists
try:
    os.mkdir('visitLists')
except FileExistsError:
    pass

point = date.split('/')[-1]
# Make sure the visitLists/{point} directory exists
try:
    os.mkdir(f'visitLists/{date}')
except FileExistsError:
    pass

with open(f'visitLists/{date}/{date}_visit_list.txt', 'w') as vobj:
    for visit in visit_info:
        vobj.write(f'{int(visit[0])}\n')

with open(f'visitLists/{date}/{date}_template_visit_list.txt', 'w') as vobj:
    for visit in sorted_info[:sorted_info.shape[0] // 2]:
        vobj.write(f'{int(visit[0])}\n')
