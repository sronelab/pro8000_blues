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
        self.maxI=[158.0,155.4,157.5]
        self.lockI=[158.0,155.4,157.5]
        self.lockps=[-1,-1,-1]

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
    
    def ramp_blue(self,slot,start_current,end_current,steps=100 ,delay=.1):
        slot_ind=slot-4
        #Ramp current while measuring power
        rm = pyvisa.ResourceManager()
        inst = rm.open_resource('ASRL4::INSTR')
        inst.baud_rate=19200
        inst.write(':SLOT ' + str(slot) + '\n')

        print(start_current)
        print(end_current)

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

        ILDs=[]
        DPs=[]
        for i in range(steps):
            vals=inst.query(':ELCH:TRIG?', delay=delay).split(',')
            time.sleep(delay/2)
            dp=float(vals[1])/.2*1e3
            ild=float(vals[0])*1e3
            ILDs.append(ild)
            DPs.append(dp) #monitor powers in mW as read on the diode controller
            #check for max
            if dp>self.lockps[slot_ind]:
                self.lockps[slot_ind]=dp
                self.lockI[slot_ind]=ild

        inst.write("&GTL")

    #def fine_tune

    def GTL(blues): #VISA error GTL
        rm = pyvisa.ResourceManager()
        inst = rm.open_resource('ASRL4::INSTR')
        inst.baud_rate=19200
        inst.write("&GTL")

    
