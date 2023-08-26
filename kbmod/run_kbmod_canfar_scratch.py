import numpy as np
import sys, os, glob, pickle, gc
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import warnings
from create_stamps import CreateStamps, CNNFilter, VisualizeResults, load_stamps
from run_search import run_search
from  astropy import time
from astropy.io import fits


#for near-opposition data we want
#+-0.35 for the angle, and rates -4 to -1 "/hr
#
#for near quadrature data we want
#+-0.6 and rates 0.2-3.0 "/hr


n_cores = 8



useSplitData = True

chipNum = 46
visit = '03072'
ref_im_num = '0218638'

if len(sys.argv)>3:
    chipNum = int(float(sys.argv[1]))
    visit = sys.argv[2]
    ref_im_num = '{:07d}'.format(int(float(sys.argv[3])))

v_min = 70. # Pixels/day
v_max = 564.

v_steps = 35 #for full range of rates
ang_steps = 8 #for half angles # 15 for full angles


do_split_ind = 0
if '-0' in sys.argv:
    do_split_ind = 0
elif '-1' in sys.argv:
    do_split_ind = 1
elif '-2' in sys.argv:
    do_split_ind = 2
elif '-3' in sys.argv:
    do_split_ind = 3
elif '-4' in sys.argv:
    do_split_ind = 4

n_splits = 1

im_filepath=(
    f"/scratch/fraserw/warps/" +
    f"{visit}/{str(chipNum).zfill(3)}")

res_filepath_upper=(
    f"/arc/projects/NewHorizons/JJK_kbmod/kbmod_results/{visit}/results_{str(chipNum).zfill(3)}_upper")
results_suffix_upper = "UPPER"
res_filepath_lower=(
    f"/arc/projects/NewHorizons/JJK_kbmod/kbmod_results/{visit}/results_{str(chipNum).zfill(3)}_upper")
results_suffix_lower = "LOWER"
time_file=(
    f"/arc/projects/NewHorizons/DATA/kbmod_times_files/{visit}/times_c{str(chipNum).zfill(3)}.dat")


mask_num_images = 70
psf_val = 2.5
num_obs = 50

if visit == '03072':
    likelihood_limit = 7.
    if chipNum == 16:
        likelihood_limit = 12.
elif visit == '03071':
    likelihood_limit = 7.
elif visit == '03093':
    likelihood_limit = 7.0
    if chipNum == 89:
        likelihood_limit = 10.
elif visit == '03148':
    likelihood_limit = 7.0
elif visit == '03447':
    likelihood_limit = 7.0
elif visit == '03455':
    likelihood_limit = 7.0
elif visit == '03473':
    likelihood_limit = 7.0
elif visit == '03805':
    likelihood_limit = 7.0
elif visit == '03806':
    likelihood_limit = 7.0
elif visit == '03832':
    likelihood_limit = 7.0
elif visit == '03833':
    likelihood_limit = 7.0
    if chipNum in [66,75,95]:
        likelihood_limit=10.0
elif visit == '03945':
    likelihood_limit = 5.0
    mask_num_images = 40
    psf_val = 3.3
    num_obs = 25
elif visit == '03946':
    likelihood_limit = 5.0
    mask_num_images = 40
    psf_val = 3.3
    num_obs = 25
    v_min = 28. # Pixels/day
    v_max = 423.


if useSplitData:
    for split_ind in range(do_split_ind, do_split_ind+1):
        new_im_filepath = im_filepath+f'/splitims_{split_ind}_{n_splits}/'

        respath = res_filepath_lower+f'_{split_ind}'
        if not os.path.isdir(respath):
            os.system('mkdir '+respath)

        ### lower half started at 12:09
        ang_below = -np.pi + 0.35 #Angle below ecliptic, the bugged value used for the 03072,03148 processing was 0.35*pi
        ang_above = np.pi # Angle above ecliptic

        v_arr = [v_min, v_max, v_steps]
        ang_arr = [ang_below, ang_above, ang_steps]

        input_parameters_lower = {
            'custom_bit_mask': {
                'BAD': 0, 'SAT': 1, 'INTRP': 2, 'EDGE': 4, 'DETECTED': 5,
                'DETECTED_NEGATIVE': 6, 'SUSPECT': 7, 'NO_DATA': 8, 'CROSSTALK': 9,
                'NOT_BLENDED': 10, 'UNMASKEDNAN': 11, 'BRIGHT_OBJECT': 12,
                'CLIPPED': 13, 'INEXACT_PSF': 14, 'REJECTED': 15,
                'SENSOR_EDGE': 16}, # same as the HSC hard coded one used in the 2020/21/22 NH search
            'custom_flag_keys': [], #['EDGE', 'NO_DATA', 'SAT', 'INTRP', 'REJECTED'],
            'im_filepath':new_im_filepath,
            'res_filepath':respath,
            'time_file':time_file,
            'output_suffix':results_suffix_lower,
            'v_arr':v_arr,
            'ang_arr':ang_arr,

            'num_cores': n_cores,

            'num_obs':num_obs,
            'do_mask':True, # check performance on vs. off
            'lh_level':likelihood_limit,
            'sigmaG_lims':[25,75], # maybe try [15,60]
            'mom_lims':[37.5,37.5,2.5,2.0,2.0],
            'psf_val':psf_val,
            'peak_offset':[3.0,3.0],
            'chunk_size':1000000,
            'stamp_type':'parallel_sum', #can be cpp_median or parallel_sum
            'eps':0.0025*max(1, n_splits-1.0),
            'gpu_filter':True, #nominally True. on GPU lightcurve filter, verify that having this off makes things worse.
            'clip_negative':True,
            'sigmaG_filter_type':'both',
            'file_format':'DIFFEXP-{:07d}-'+ref_im_num+'-'+str(chipNum).zfill(3)+'.fits',
            'visit_in_filename':[8,15],
            'cluster_type':'mid_position',
            'mask_num_images':mask_num_images,
            'chunk_start_index': 0,
            'chunks_to_consider': 40,
            }

        print(f"{input_parameters_lower}")
        respath = res_filepath_upper+f'_{split_ind}'
        if not os.path.isdir(respath):
            os.system('mkdir '+respath)

        ang_below = -np.pi  # Angle below ecliptic
        #ang_above = np.pi + 0.35*np.pi # Angle above ecliptic, bugged value used for 03072 and 03148 processing
        ang_above = np.pi + 0.35 # Angle above ecliptic

        v_arr = [v_min, v_max, v_steps]
        ang_arr = [ang_below, ang_above, ang_steps]

        input_parameters_upper = {
            'custom_bit_mask': {
                'BAD': 0, 'SAT': 1, 'INTRP': 2, 'EDGE': 4, 'DETECTED': 5,
                'DETECTED_NEGATIVE': 6, 'SUSPECT': 7, 'NO_DATA': 8, 'CROSSTALK': 9,
                'NOT_BLENDED': 10, 'UNMASKEDNAN': 11, 'BRIGHT_OBJECT': 12,
                'CLIPPED': 13, 'INEXACT_PSF': 14, 'REJECTED': 15,
                'SENSOR_EDGE': 16}, # same as the HSC hard coded one used in the 2020/21/22 NH search
            'custom_flag_keys': [], #['EDGE', 'NO_DATA', 'SAT', 'INTRP', 'REJECTED'],
            'im_filepath':new_im_filepath,
            'res_filepath':respath,
            'time_file':time_file,
            'output_suffix':results_suffix_upper,
            'v_arr':v_arr,
            'ang_arr':ang_arr,

            'num_cores': n_cores,

            'num_obs':num_obs,
            'do_mask':True, # check performance on vs. off
            'lh_level':likelihood_limit,
            'sigmaG_lims':[25,75], # maybe try [15,60]
            'mom_lims':[37.5,37.5,2.5,2.0,2.0],
            'psf_val':psf_val,
            'peak_offset':[3.0,3.0],
            'chunk_size':1000000,
            'stamp_type':'parallel_sum', #can be cpp_median or parallel_sum
            'eps':0.0025*max(1, n_splits-1.0),
            'gpu_filter':True, #nominally True. on GPU lightcurve filter, verify that having this off makes things worse.
            'clip_negative':True,
            'sigmaG_filter_type':'both',
            'file_format':'DIFFEXP-{:07d}-'+ref_im_num+'-'+str(chipNum).zfill(3)+'.fits',
            'visit_in_filename':[8,15],
            'cluster_type':'mid_position',
            'mask_num_images':mask_num_images,
            'chunk_start_index': 0,
            'chunks_to_consider': 40,
        }


        rs = run_search(input_parameters_lower)
        rs.run_search()
        
        del rs
        gc.collect()

        rs = run_search(input_parameters_upper)
        rs.run_search()

        del rs
        gc.collect()

        exit()
        
### lower half started at 12:09
ang_below = -np.pi + 0.35*np.pi  # Angle below ecliptic
ang_above = np.pi # Angle above ecliptic

v_arr = [v_min, v_max, v_steps]
ang_arr = [ang_below, ang_above, ang_steps]

if not os.path.isdir(res_filepath_upper):
    os.system('mkdir '+res_filepath_upper)
if not os.path.isdir(res_filepath_lower):
    os.system('mkdir '+res_filepath_lower)


input_parameters_lower = {
    'im_filepath':im_filepath,
    'res_filepath':res_filepath_lower,
    'time_file':time_file,
    'output_suffix':results_suffix_lower,
    'v_arr':v_arr,
    'ang_arr':ang_arr,
    
    'num_cores': n_cores,
    
    'num_obs':num_obs,
    'do_mask':True, # check performance on vs. off
    'lh_level': likelihood_limit,
    'sigmaG_lims':[25,75], # maybe try [15,60]
    'mom_lims':[37.5,37.5,2.5,2.0,2.0],
    'psf_val':2.5,
    'peak_offset':[3.0,3.0],
    'chunk_size':1000000,
    'stamp_type':'parallel_sum', #can be cpp_median or parallel_sum
    'eps':0.0025,
    'gpu_filter':True, #nominally True. on GPU lightcurve filter, verify that having this off makes things worse.
    'clip_negative':True,
    'sigmaG_filter_type':'both',
    'file_format':'DIFFEXP-{:07d}-'+ref_im_num+'-'+str(chipNum).zfill(3)+'.fits',
    'visit_in_filename':[8,15],
    'cluster_type':'mid_position',
    'mask_num_images':70,
    'chunk_start_index': 0,
    'chunks_to_consider': 40,
}

ang_below = -np.pi  # Angle below ecliptic
ang_above = np.pi + 0.35*np.pi # Angle above ecliptic

v_arr = [v_min, v_max, v_steps]
ang_arr = [ang_below, ang_above, ang_steps]

input_parameters_upper = {
    'im_filepath':im_filepath,
    'res_filepath':res_filepath_upper,
    'time_file':time_file,
    'output_suffix':results_suffix_upper,
    'v_arr':v_arr,
    'ang_arr':ang_arr,
    
    'num_cores': n_cores,
    
    'num_obs':num_obs,
    'do_mask':True, # check performance on vs. off
    'lh_level':likelihood_limit,
    'sigmaG_lims':[25,75], # maybe try [15,60]
    'mom_lims':[37.5,37.5,2.5,2.0,2.0],
    'psf_val':2.5,
    'peak_offset':[3.0,3.0],
    'chunk_size':1000000,
    'stamp_type':'parallel_sum', #can be cpp_median or parallel_sum
    'eps':0.0025,
    'gpu_filter':True, #nominally True. on GPU lightcurve filter, verify that having this off makes things worse.
    'clip_negative':True,
    'sigmaG_filter_type':'both',
    'file_format':'DIFFEXP-{:07d}-'+ref_im_num+'-'+str(chipNum).zfill(3)+'.fits',
    'visit_in_filename':[8,15],
    'cluster_type':'mid_position',
    'mask_num_images':70,
    'chunk_start_index': 0,
    'chunks_to_consider': 40,
    
}

if not procUpper:
    rs = run_search(input_parameters_lower)
    rs.run_search()

else:
    rs = run_search(input_parameters_upper)
    rs.run_search()
