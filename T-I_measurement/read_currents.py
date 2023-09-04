
import pyvisa
import time
from tqdm.auto  import tqdm
import json
from datetime import datetime
import numpy as np
import os
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from default_settings import lasers
import matplotlib.pyplot as plt

# Measurement parameters
N_I_points = 50 # Number of points to measure for each current ramps
t_Imax_hold = 3 # Imax hold time

delay = 1e-2 #reading delay
rm = pyvisa.ResourceManager()

def read_currents(lasers):
    print("Ramping current to lock.")
    inst = rm.open_resource('ASRL4::INSTR', open_timeout=10)        
    inst.baud_rate=19200
    for laser in lasers:
        # Select the current controller
        inst.write(':SLOT ' + str(laser["Islot"]) + '\n')
        print(laser["name"])
        print(inst.query(":ILD:SET?", delay=delay))
        print(inst.query(":POPT:ACT?", delay=delay))
        print("=====")
    inst.write("&GTL")

    return lasers




if __name__ == "__main__":
    lasers = read_currents(lasers)