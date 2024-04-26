
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
t_Imax_hold = 5 # Imax hold time

delay = 1e-2 #reading delay
rm = pyvisa.ResourceManager()

def ramp_currents(lasers):
    print("Ramping current to lock.")
    inst = rm.open_resource('ASRL4::INSTR', open_timeout=10)        
    inst.baud_rate=19200
    for laser in lasers:
        # Select the current controller
        inst.write(':SLOT ' + str(laser["Islot"]) + '\n')

        # Prepare ramp 
        Imax = float(inst.query(":LIMC:SET?", delay=delay).split(" ")[-1])
        Imin = laser["I_ramp_end"]

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
        time.sleep(0.1)
    inst.write("&GTL")

    return lasers




if __name__ == "__main__":
    lasers = ramp_currents(lasers)
    fig, axes = plt.subplots(3, 1)
    ii = 0
    for laser in lasers:
        axes[ii].plot(laser["I_measured"], laser["P_measured"])
        ii +=1
    fig.tight_layout()

    now = datetime.now()
    dt_string = now.strftime("%Y%m%d_%H%M%S")
    with open(os.path.join(os.path.dirname(__file__), "data", "ramp_currents.output", f"{dt_string}.json") , "w") as outfile:
        json.dump(lasers, outfile)
    plt.show()