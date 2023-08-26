from reader import DiscoveryFile, TrackingFile
from astropy import units
import argparse
import logging
import sys


def run():
    main_parser = argparse.ArgumentParser()
    main_parser.add_argument('filename', type=str)
    main_parser.add_argument('field', type=str)
    main_parser.add_argument('output', type=str, nargs='?', default=None)
    main_parser.add_argument('--tracking', action="store_true", default=False)
    main_parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'ERROR'], default='INFO')
    args = main_parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level))
    if args.tracking:
        d = TrackingFile(args.field, args.filename)
    else:
        d = DiscoveryFile(args.field, args.filename)
    if args.output is None:
        fobj = sys.stdout
    else:
        fobj = open(args.output, 'w')
    for record in d:
        for dt in [0*units.hour, 1.5*units.hour, 3*units.hour]:
            fobj.write(str(record.offset(dt).observation.to_tnodb())+"\n")


if __name__ == '__main__':
    run()
