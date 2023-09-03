# Script for temperature - current vs power plot
# 2023-09-01 Kyungtae

import pyvisa
import time
from tqdm.auto  import tqdm
import json
from datetime import datetime
import os

# Measurement parameters
I_range = 4e-3 # value of the current we want to sweep from its maximum value. [A]
N_I_points = 200 # Number of points to measure for each current ramps
t_Imax_hold = 10 # Imax hold time
t_Tset_hold = 20 # Time waiting for temperature to settle.
Delta_T_list = [-0.4, -0.2, 0, 0.2, 0.4] # temperature to modulate

# constants
lasers = [
    {"name":"2DMOT", "Islot":4, "Tslot":2, "T_init":26.84},
    {"name":"MOT", "Islot":5, "Tslot":1, "T_init":28.1},
    {"name":"ZS", "Islot":6, "Tslot":3, "T_init":29.0},
]
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