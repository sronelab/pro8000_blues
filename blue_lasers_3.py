import sys
import datetime
import pyvisa
import time
import os
import pandas as pd
import numpy as np
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

class blue_lasers():

    #Constructor
    def __init__(self, delay=.1):
        self.currents = [-1,-1,-1]
        self.powers = [-1,-1,-1]
        self.slots = [4,5,6] #Slots for TC, MOT, ZS
        self.maxI=[158.2,156.97,158.2]
        self.lockI=[158.2,156.4,156.0]
        self.lockps=[-1,-1,-1]

        self.P_setpoint = [7.22, 9.65, 11.21]

        rm = pyvisa.ResourceManager()
        inst = rm.open_resource('ASRL4::INSTR')
        inst.baud_rate=19200

        for ii in range(len(self.slots)):
            inst.write(':SLOT ' + str(self.slots[ii]) + '\n')
        # print(inst.query(":SLOT?", delay=delay))
            self.currents[ii] = float(inst.query(":ILD:SET?", delay=delay).split(" ")[-1])*1e3
            self.powers[ii] = float(inst.query(":POPT:ACT?", delay=delay).split(" ")[-1])*1e3
            self.lockps[ii]=self.powers[ii]
            self.lockI[ii]=self.currents[ii]
        inst.write("&GTL") #seems to close communication?


    def read_blues(self,delay=.1):
        #update currents and powers
        rm = pyvisa.ResourceManager()
        inst = rm.open_resource('ASRL4::INSTR')
        inst.baud_rate=19200
    # print(inst.query("*IDN?", delay=delay))
        inst.query("*IDN?", delay=delay)
        for ii in range(len(self.slots)):
            inst.write(':SLOT ' + str(self.slots[ii]) + '\n')
        # print(inst.query(":SLOT?", delay=delay))
            self.currents[ii] = float(inst.query(":ILD:SET?", delay=delay).split(" ")[-1])*1e3
            self.powers[ii] = float(inst.query(":POPT:ACT?", delay=delay).split(" ")[-1])*1e3
        inst.write("&GTL") #seems to close communication?

    def set_blue(self, slot, set_current, delay=.1):
        #set current directly for fine tuning.
        #slot_ind=slot-4
        rm = pyvisa.ResourceManager()
        inst = rm.open_resource('ASRL4::INSTR')
        inst.baud_rate=19200

        inst.write(':SLOT ' + str(slot) + '\n')
        inst.write(':ILD:SET ' + str(set_current) + 'e-3\n')

        inst.write("&GTL")

    
    def ramp_blue(self,slot,start_current,end_current,steps=45 ,delay=.1, sweep=False):
        slot_ind=slot-4
        #Ramp current while measuring power
        rm = pyvisa.ResourceManager()
        inst = rm.open_resource('ASRL4::INSTR')
        inst.baud_rate=19200
        inst.write(':SLOT ' + str(slot) + '\n')

        print(f"ramping. start: {start_current} end: {end_current}")

        #configure current sweep
        inst.write(':ILD:START ' + str(start_current) + 'e-3\n')
        inst.write(':ILD:STOP ' + str(end_current) + 'e-3\n')
        inst.write(':ELCH:STEPS ' + str(steps))

        #configure ELCH measurement
        inst.write(':ELCH:MEAS 1') #measurements per step
        inst.write(':IMD:MEAS 1')

        #Begin ELCH measurement
        inst.write(':ELCH:RESET 0') #Reset data
        inst.write(':ELCH:RUN 2') #Run discrete measurement--for some reason GETALL? Not working

        if start_current == self.maxI[slot_ind]: #if we are ramping down from the max current.
            time.sleep(30) #pause at the max current to ensure power rises as we decrease current

        ILDs=[self.lockI[slot_ind]]
        DPs=[self.lockps[slot_ind]]
        for i in range(steps):
            vals=inst.query(':ELCH:TRIG?', delay=delay).split(',')
            time.sleep(delay)
            dp=float(vals[1])/.2*1e3
            ild=float(vals[0])*1e3

            ILDs.append(ild)
            DPs.append(dp) #monitor powers in mW as read on the diode controlle
            #print(ild)
            #update check for max if sweeping, but not if just resetting to not mess up vaues
            if sweep:
                #print('sweep')
                if dp>(self.lockps[slot_ind]-.15): #.15 to be consistent with other function
                    print(f"power: {dp}")
                    print(f"current: {ild}")
                    #dont go right up to threshold--too unstable
                    self.lockps[slot_ind]=DPs[-2]
                    self.lockI[slot_ind]=ILDs[-2]
        #print(DPs)
        #print(ILDs)

        inst.write("&GTL")

    #def fine_tune

    def GTL(blues): #VISA error GTL
        rm = pyvisa.ResourceManager()
        inst = rm.open_resource('ASRL4::INSTR')
        inst.baud_rate=19200
        inst.write("&GTL")

    
