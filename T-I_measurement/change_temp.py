# Script for temperature - current vs power plot
# 2023-09-01 Kyungtae

import pyvisa
import time
from tqdm.auto  import tqdm
import json
from datetime import datetime
import os
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from default_settings import lasers

# Measurement parameters
I_range = 4e-3 # value of the current we want to sweep from its maximum value. [A]
N_I_points = 200 # Number of points to measure for each current ramps
t_Imax_hold = 10 # Imax hold time
t_Tset_hold = 20 # Time waiting for temperature to settle.

delay = 1e-1 #reading delay
rm = pyvisa.ResourceManager()

def go_T_init(lasers):
    for laser in lasers:
        inst = rm.open_resource('ASRL4::INSTR')        
        inst.baud_rate=19200
        inst.write(':SLOT ' + str(laser["Tslot"]) + '\n')
        inst.write(f':TEMP:SET {laser["T_init"]}')
        inst.write("&GTL")
        time.sleep(1)
        print(f'{laser["name"]} temperature set to T_init:{laser["T_init"]}')



if __name__ == "__main__":
    go_T_init(lasers)
    now = datetime.now()
    dt_string = now.strftime("%Y%m%d_%H%M%S")
    with open(os.path.join(os.path.dirname(__file__), "data", "change_temp.output", f"{dt_string}.json") , "w") as outfile:
        json.dump(lasers, outfile)