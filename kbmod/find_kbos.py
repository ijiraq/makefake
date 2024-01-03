import sys, os, glob, gc
import numpy as np
from astropy.io import fits
import argparse
import shutil
import logging
from astropy.table import Table


def main():
    parser = argparse.ArgumentParser(description=("Look for all files in input-path that match pettern "
                                                  "and copy them to the scratch-path. From that set of files "
                                                  "construct a times.txt file that lists the exposures and the MJD "
                                                  "at which they were taken.  Using this infor we populate parameter "
                                                  "dictionary to pass to run_search. "))
    parser.add_argument('file_format', default='DIFFEXP-{:07d}-{2773118}-01.fits',
                        help="format of filename. When str.format() passes a visit ID to file_format the "
                             "name of a file corresponding to that visit ID is returned (e.g.: %(default)s)")
    parser.add_argument('--input-path', default=os.getcwd(), type=str,
                        help="Directory with input fits files matching --filename-patern to run kbmod on, "
                             "These files return there visit ID following file-format")
    parser.add_argument('--filename-pattern', default="DIFFEXP*.fits",
                        help="Globbing pattern used to match files in input-path to copy to scratch (%(default)s)")
    parser.add_argument('--times', default='times.dat',
                        help='File that maps visit_id to MJD (%(default)s)')
    parser.add_argument('--results-suffix', default="", type=str,
                        help="Suffix to put on result file (%(default)s)")
    parser.add_argument('--likelihood', default=5.0, type=float,
                        help="Likelihood threshold for detection(%(default)s) ")
    parser.add_argument('--scratch-path', default="/scratch",
                        help="Base directory for scratch files on container(%(default)s) ")
    parser.add_argument('--dry-run', default=False, action='store_true',
                        help="Just test to see if script builds (%(default)s)")
    parser.add_argument('--log-level', choices=['INFO', 'ERROR', 'DEBUG'], default='ERROR')
    parser.add_argument('--mask-flags', nargs='*',
                        default=['EDGE', 'NO_DATA', 'SAT', 'INTRP', 'REJECTED', 'NOT_DEBLENDED', 'BRIGHT_OBJECT'],
                        help="BITs to mask when combining images: (%(default)s)")
    parser.add_argument('--v-min', type=float, default=0.5,
                        help="Minimum rate of motion in arcsec/hour (%(default)s) ")
    parser.add_argument('--v-max', type=float, default=5.0,
                        help="Maximum rate of motoin in arcsec/hour (%(default)s)")
    parser.add_argument('--v-steps', type=int, default=50,
                        help="Number of steps in velocity grid. (%(default)s)")
    parser.add_argument('--angle-low', type=float, default=-63,
                        help='Lower limit on trajectories relative to ecliptic (%(default)s).')
    parser.add_argument('--angle-high', type=float, default=63,
                        help='Upper limit on trajectories relative to ecliptic (%(default)s).')
    parser.add_argument('--angle-steps', type=int, default=15,
                        help="Number of steps in angle grid. (%(default)s) ")
    parser.add_argument('--psf-fwhm', type=float, default=0.65,
                        help='FWHM of PSF shape (in arcsec). (%(default)s)')
    parser.add_argument('--eps', type=float, default=8E-4,
                        help='maximum distance between points in x/y/v/ang for use in clustering, units? (%(default)s)')
    parser.add_argument('--sigmaG-low', default=25., type=float,
                        help='Lower limit on sigmaG value used when filtering sources (%(default)s)')
    parser.add_argument('--sigmaG-high', default=75., type=float,
                        help="Upper limit on kbmod sigmaG value used when filter sources (%(default)s)")
    parser.add_argument('--num-obs', default=10, type=int,
                        help="Minimum number of observations for detection (%(default)s)")
    parser.add_argument('--mask_num_images', type=int, default=10,
                        help="Maximum number of masked images in a pixel stack.")

    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level))
    file_format = args.file_format

    logging.debug(f"File format string: {file_format}")
    res_filepath = args.input_path  # this is also where the DIFFEXP files we will process are located.
    if not os.access(res_filepath, os.R_OK & os.X_OK):
        raise FileNotFoundError(res_filepath)
    
    # scratch space on container (copy data here before processsing) 
    scratch_path = args.scratch_path  # this is where we will copy DIFFEXP files to

    if not os.access(scratch_path, os.R_OK & os.W_OK & os.X_OK):
        raise FileNotFoundError(scratch_path)
    im_filepath = os.path.join(scratch_path, 'kbmod')
    os.makedirs(im_filepath, exist_ok=True)
    
    results_suffix = args.results_suffix
    likelihood_limit = args.likelihood
    time_file = args.times

    # copy the DIFF files to the scratch area.
    logging.debug(f"copying DIFFEXP files from {res_filepath} to {im_filepath}")
    visit_ids = Table.read(time_file, format='ascii')['col1']
    if len(visit_ids) == 0:
        raise IOError(f"No files matching {args.pattern} found in {res_filepath}")
    for visit_id in visit_ids:
        filename = file_format.format(visit_id)
        logging.debug(f"Copying {filename} to {im_filepath}")
        if not os.access(os.path.join(im_filepath, os.path.basename(filename)), os.F_OK):
            shutil.copy2(filename, im_filepath)

    # get the bit mask values from those requested by user, just use the last file copied over
    filename = file_format.format(visit_ids[1])
    flag_hdu = fits.open(filename)[2]
    custom_flag_keys = []
    custom_flag_mask = {}
    for keyword in args.mask_flags:
        logging.debug(f"Looking up bit value for {keyword} in {filename}")
        bit = flag_hdu.header.get(f'MP_{keyword}', None)
        if bit is None:
            logging.warning(f"Keyword {keyword} not found in mask for {filename}")
            continue
        custom_flag_mask[keyword] = bit
        custom_flag_keys.append(keyword)
    custom_flag_mask = None

    n_cores = 1  # How many cores to request
    v_min = args.v_min*24/0.185  # minimum rate of motion pixels/day
    v_max = args.v_max*24/0.185  # maximum rate of motion pixels/day
    v_steps = args.v_steps  # set to 50 for full range of rates
    ang_steps = args.angle_steps  # ?? for half angles # 15 for full angles
    num_obs = args.num_obs  # minimum number of images required for source detection
    psf_val = args.psf_fwhm/(2*np.sqrt(2.0*np.log(2.0))) / 0.185
    mask_num_images = args.mask_num_images
    sigma_g_lims = [args.sigmaG_low, args.sigmaG_high]
    eps = args.eps
    ang_below = args.angle_low
    ang_above = args.angle_high
    v_arr = [v_min, v_max, v_steps]
    ang_arr = [ang_below, ang_above, ang_steps]

    input_parameters = {
        'custom_bit_mask': custom_flag_mask,
        'custom_flag_keys': custom_flag_keys,
        'im_filepath': im_filepath,
        'res_filepath': res_filepath,
        'time_file': time_file,
        'output_suffix': results_suffix,
        'v_arr': v_arr,
        'ang_arr': ang_arr,
        'num_cores': n_cores,
        'num_obs': num_obs,  # min number of individual frames include in stack of a candidate to call it a detection
        'do_mask': True,  # check performance on vs. off
        'lh_level': likelihood_limit,
        'sigmaG_lims': sigma_g_lims,  # maybe try [15, 60]
        # 'mom_lims': [50.5, 50.5, 3.5, 3.0, 3.0], 
        'mom_lims': [37.5, 37.5, 2.5, 2.0, 2.0],
        'psf_val': psf_val,
        'peak_offset': [3.0, 3.0],
        'chunk_size': 1000000,
        'stamp_type': 'parallel_sum',  # can be cpp_median or parallel_sum
        'eps': eps,
        'do_clustering': True,
        'gpu_filter': True,  # nominally True. on GPU lightcurve filter, verify that having this off makes things worse.
        'clip_negative': True,
        'sigmaG_filter_type': 'both',
        'file_format': file_format,
        'visit_in_filename': [8, 15],
        'cluster_type': 'mid_position',
        'mask_num_images': mask_num_images,
        'chunk_start_index': 0,
        'chunks_to_consider': 40,
    }

    logging.debug(f"input_parameters:")
    for key in input_parameters:
        logging.debug(f"{key} : {input_parameters[key]}")
        
    if args.dry_run:
        sys.exit()
    else:
        run(input_parameters, scratch_path)


def run(input_parameters, scratch_path):
    from run_search import run_search
    rs = run_search(input_parameters)
    rs.run_search()
    del rs
    gc.collect()
    shutil.rmtree(scratch_path, ignore_errors=True)


if __name__ == '__main__':
    main()
