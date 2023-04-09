import numpy as np
from seabreeze.spectrometers import Spectrometer
from obis_laser import Obis
from time import sleep, time
from scipy.ndimage import gaussian_filter1d, median_filter
import os
from colorama import Fore, Style

#!NOTE: make sure that you closed oceanview and laser control programs before start

#================================ SETTINGS ====================================

FOLDER_NAME = "FAMACsPbBr09I01_1-microcrystal_04-07-2023" # folder for data to be saved
SAVE_FOLDER = r"E:\\Spectroscopy data" # no need to change

LASER_POWER_FOR_RUN = [1, 20] # should be in [0, 110] range  
RUN_DELAY = [0] # pause between runs in SECONDS (len(LASER_POWER_FOR_RUN) - 1)

NUM_OF_STEPS_IN_RUN = [120, 120] # number of steps in EACH run
STEP_DELAY = [4.5, 4.9] # delay between steps in EACH runin SECONDS

# settings for ocean optics
INTEGRATION_TIMES = [500, 100] # for EACH run_num in MILLIS
START_WAVELEN    = 480 # in nm
FINISH_WAVELEN   = 820 # in nm

#================================ /SETTINGS ===================================

# calculate number of runs
NUM_OF_RUNS = len(LASER_POWER_FOR_RUN)
MAX_NUMBER_OF_STEPS_IN_RUN = np.amax(NUM_OF_STEPS_IN_RUN)

# some checkings
conditions = []
conditions.append(len(LASER_POWER_FOR_RUN) == len(INTEGRATION_TIMES) == len(NUM_OF_STEPS_IN_RUN) == len(STEP_DELAY))
conditions.append(len(RUN_DELAY) == (len(LASER_POWER_FOR_RUN) - 1))

if not all(conditions):
    print(Fore.RED)
    print("Error in settings! Check them again.")
    print(Style.RESET_ALL)
    exit()

# init ocean optics
spec = Spectrometer.from_first_available()
spec.integration_time_micros(INTEGRATION_TIMES[0] * 1000)
WAVELENS = spec.wavelengths()

# init obis laser
obis = Obis()
obis.laserOff()

# shorten wavelen range
ind_start = np.searchsorted(WAVELENS, START_WAVELEN)
ind_finish = np.searchsorted(WAVELENS, FINISH_WAVELEN)
WAVELENS = WAVELENS[ind_start:ind_finish]

# take background for different integration times
background = np.zeros((len(INTEGRATION_TIMES), len(WAVELENS)))

print("\nTaking background... ", end="")

for i, int_time in enumerate(INTEGRATION_TIMES):
    spec.integration_time_micros(int_time * 1000) 
    background[i] = spec.intensities()[ind_start:ind_finish]
    
print("Done.")

# init array for data storage
spectra_array = np.zeros((NUM_OF_RUNS, MAX_NUMBER_OF_STEPS_IN_RUN, len(WAVELENS)))
time_array = np.zeros((NUM_OF_RUNS, MAX_NUMBER_OF_STEPS_IN_RUN))

# set yellow color for terminal
print(Fore.YELLOW)

#! for Halyna
# arrays for maximum intensity and wavelength
max_waven_arr = np.zeros((NUM_OF_RUNS, MAX_NUMBER_OF_STEPS_IN_RUN))
max_intensity_arr = np.zeros((NUM_OF_RUNS, MAX_NUMBER_OF_STEPS_IN_RUN))

st = time() # current time in sec

for run_num in range(NUM_OF_RUNS):
    
    # set laser power
    obis.setPower(LASER_POWER_FOR_RUN[run_num])
    obis.laserOn()
    
    int_time = INTEGRATION_TIMES[run_num]
    
    for step in range(NUM_OF_STEPS_IN_RUN[run_num]): 
        
        
        # needed for proper time synchronization
        spec.integration_time_micros(int_time * 1000)
    
        # get current spectrum
        spectrum = spec.intensities()[ind_start:ind_finish] - background[run_num]
        
        # additional time spent on these two steps (from line 91 to 94) is about 15 millis
        
        #! for Halyna
        # get maximum intensity and wavelength
        # use smoothed data
        smoothed_spectrum = gaussian_filter1d(median_filter(spectrum, 3), 5)
        max_ind = np.argmax(smoothed_spectrum)
        max_intensity_arr[run_num, step] = smoothed_spectrum[max_ind]
        max_waven_arr[run_num, step] = WAVELENS[max_ind]
        
        # save spectrum
        spectra_array[run_num, step] = spectrum
    
        # get time when spectrum was recorded
        time_array[run_num, step] = round(time() - st, 2)
    
        print(f"RUN: {run_num + 1} of {NUM_OF_RUNS} | STEP: {step + 1} of {NUM_OF_STEPS_IN_RUN[run_num]}")
        if step != NUM_OF_STEPS_IN_RUN[run_num] - 1: # last step, no need to wait
            sleep(STEP_DELAY[run_num])
    
    if RUN_DELAY[np.clip(run_num, 0, NUM_OF_RUNS - 2)]: # not zero pause
        
        # turn off the laser
        obis.laserOff()
        
        if run_num != NUM_OF_RUNS - 1: # last run, no need to wait
            
            print(f"Laser is off. Pause for {RUN_DELAY[np.clip(run_num, 0, NUM_OF_RUNS - 1)]} sec.\n")
            sleep(RUN_DELAY[run_num])
    else:
        print() # to skip a line

# turn off the laser
obis.laserOff()

print(Fore.GREEN) # set green color
print("Experiment is finished.")

# shift times for first measurment to be zero
time_array = time_array - time_array[0, 0]

# negative values are due to substracting. Make them zero.
time_array[time_array < 0] = 0 

# save data
print("Saving data... ", end="")

# create a folder
os.makedirs(f"{SAVE_FOLDER}\\{FOLDER_NAME}", exist_ok=True)

# save each run_num in a separate file
for run_num in range(NUM_OF_RUNS):
    to_take = NUM_OF_STEPS_IN_RUN[run_num] # exclude rows with zeros
    np.savetxt(f"{SAVE_FOLDER}\\{FOLDER_NAME}\\run {run_num + 1}.csv", np.vstack([WAVELENS, spectra_array[run_num, :to_take]]).T,
           fmt="%4.3f", 
           delimiter=",",
           header=f"wavelengths, step 1, step 2, ...",
           comments="")
    
# save times in a separate file
np.savetxt(f"{SAVE_FOLDER}\\{FOLDER_NAME}\\times.csv", time_array.T,
           fmt="%4.3f", 
           delimiter=",",
           header=f"times for run_num 1, times for run_num 2, ...",
           comments="")

#! for Halyna
# save max intensity and wavelebgth
np.savetxt(f"{SAVE_FOLDER}\\{FOLDER_NAME}\\max_intensity_and_wavenegth.csv", np.vstack([max_waven_arr, max_intensity_arr]).T,
           fmt="%4.3f", 
           delimiter=",",
           header=f"max wavength, max intensity",
           comments="")

# save config file
with open(f"{SAVE_FOLDER}\\{FOLDER_NAME}\\config.txt", 'w') as f:
    f.write(f"number of runs: {NUM_OF_RUNS}\n")
    f.write(f"number of steps in each run: {NUM_OF_STEPS_IN_RUN}\n")
    f.write(f"delay between steps: {STEP_DELAY} sec\n")
    f.write(f"delay between runs: {RUN_DELAY} sec\n")
    f.write(f"ocean optics integration times: {INTEGRATION_TIMES} millis\n")
    f.write(f"laser power for runs: {LASER_POWER_FOR_RUN} mW (%)")

print("Done!")
print(Style.RESET_ALL)