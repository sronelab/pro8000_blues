# Script for temperature - current vs power plot
# 2023-09-01 Kyungtae

import pyvisa
import time
from tqdm.auto  import tqdm
import json
from datetime import datetime
import os
import numpy as np

# Measurement parameters
I_range = 4e-3 # value of the current we want to sweep from its maximum value. [A]
N_I_points = 100 # Number of points to measure for each current ramps
t_Imax_hold = 10 # Imax hold time
t_Tset_hold = 20 # Time waiting for temperature to settle.
Delta_T_list = np.linspace(-0.2, 0.2, num=10) # temperature to modulate

# constants
lasers = [
    {"name":"2DMOT", "Islot":4, "Tslot":2, "T_init":26.84},
    {"name":"MOT", "Islot":5, "Tslot":1, "T_init":28.12},
    {"name":"ZS", "Islot":6, "Tslot":3, "T_init":29.0},
]
delay = 1e-1 #reading delay
rm = pyvisa.ResourceManager()

def go_T_init(lasers):
    for laser in lasers:
        inst = rm.open_resource('ASRL4::INSTR', open_timeout=10)        
        inst.baud_rate=19200
        inst.write(':SLOT ' + str(laser["Tslot"]) + '\n')
        inst.write(f':TEMP:SET {laser["T_init"]}')
        time.sleep(1)
        inst.write("&GTL")
        time.sleep(1)
        print(f'{laser["name"]} temperature set to T_init:{laser["T_init"]}')

def change_temperature(laser, Delta_T):
    print(f"Changing {laser['name']} temperature")
    inst = rm.open_resource('ASRL4::INSTR', open_timeout=10)
    inst.baud_rate=19200
    inst.write(':SLOT ' + str(laser["Tslot"]) + '\n')
    T_set_now = float(inst.query(':TEMP:SET?', delay=delay).split(" ")[-1])
    # T_act_now = float(inst.query(':TEMP:ACT?', delay=delay).split(" ")[-1])

    T_to_set = laser["T_init"] + Delta_T
    # change temperature
    inst.write(f':TEMP:SET {T_to_set}')
    inst.write("&GTL")
    time.sleep(1)
    print(f"Tempreature set from {T_set_now} to {T_to_set}. Wait for {t_Tset_hold} seconds to stabilized ... ")


def measure_currents(lasers):
    for laser in lasers:
        inst = rm.open_resource('ASRL4::INSTR', open_timeout=10)        
        inst.baud_rate=19200
        # Select the current controller
        inst.write(':SLOT ' + str(laser["Islot"]) + '\n')

        # Prepare ramp 
        Imax = float(inst.query(":LIMC:SET?", delay=delay).split(" ")[-1])
        Imin = Imax-I_range

        #configure current sweep
        inst.write(':ILD:START ' + str(Imax) + '\n')
        inst.write(':ILD:STOP ' + str(Imin) + '\n')
        inst.write(':ELCH:STEPS ' + str(N_I_points))

        #configure ELCH measurement
        inst.write(':ELCH:MEAS 1') #measurements per step
        inst.write(':IMD:MEAS 1')
        #Begin ELCH measurement
        inst.write(':ELCH:RESET 0') #Reset data
        inst.write(':ELCH:RUN 2') #Run discrete measurement--for some reason GETALL? Not working
        print(f"Waiting at Imax for {t_Imax_hold} seconds ...")
        time.sleep(t_Imax_hold) #pause at the max current to ensure power rises as we decrease current
        # reading each steps.
        I_measured = []
        P_measured = []
        for ii in tqdm(range(N_I_points), desc=f"Ramping {laser['name']} current..."):
            vals=inst.query(':ELCH:TRIG?', delay=delay).split(',')
            dp=float(vals[1])/.2*1e3
            ild=float(vals[0])*1e3
            P_measured.append(dp)
            I_measured.append(ild)
        laser["I_measured"] = I_measured
        laser["P_measured"] = P_measured
        # print(I_measured, P_measured)
        time.sleep(1)

        # Measure temperature
        inst.write(':SLOT ' + str(laser["Tslot"]) + '\n')
        T_set = float(inst.query(':TEMP:SET?', delay=delay).split(" ")[-1])
        T_act = float(inst.query(':TEMP:ACT?', delay=delay).split(" ")[-1])
        laser["T_set"] = T_set
        laser["T_measured"] = T_act

        inst.write("&GTL")
        time.sleep(1)

    return lasers




if __name__ == "__main__":
    go_T_init(lasers)
    print("waiting for 30 s ..."); time.sleep(30)

    for Delta_T in Delta_T_list:
        time.sleep(2)
        # Change temperature and wait.
        for laser in lasers:
            change_temperature(laser, Delta_T)
        print("waiting for 30 s ..."); time.sleep(30)
        

        # Sweep current and save data.
        lasers = measure_currents(lasers)
        now = datetime.now()
        dt_string = now.strftime("%Y%m%d_%H%M%S")
        with open(os.path.join(os.path.dirname(__file__), "data", f"{dt_string}.json") , "w") as outfile:
            json.dump(lasers, outfile)

    go_T_init(lasers)