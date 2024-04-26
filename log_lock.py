import sys
import datetime
import pyvisa
import time
import os
import pandas as pd
import numpy as np
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from blue_lasers_3 import blue_lasers

DATA_FOLDER = "data"

# database info
import db_info

def log_lock(blues):
    #blues=blue_lasers()

    #read values
    blues.read_blues()


    #Relocking, (Coarse, first check if a laser is unlocked)
    relock=False
    for ii in range(len(blues.slots)):
        # if blues.lockps[ii]>(blues.powers[ii]+.15): #.15 arbitrary threshold
        if blues.P_setpoint[ii]>(blues.powers[ii]+.05): #.15 arbitrary threshold
            relock=True
            slot=blues.slots[ii]
            print("relocking laser" +str(slot) )
            #ramp and update values
            blues.ramp_blue(slot,blues.maxI[ii],blues.currents[ii]-.5,sweep=True)
            #ramp to optimum
            blues.ramp_blue(slot,blues.maxI[ii],blues.lockI[ii])
            #rerecord values if we had to relock
            blues.read_blues()
            break #can only relock one per cycle to not run in to timing errors


    #fine tuning if we didnt need to relock
    if relock==False:
        for ii in range(len(blues.slots)):
            if blues.lockps[ii]>(blues.powers[ii]+.02): #.01 arbitrary threshold
                slot=blues.slots[ii]
                print("adjusting current for laser " +str(slot) )
                #decrease current by a small amount. Power seems sensitive on the .05 mA or smaller scale 
                new_current=blues.currents[ii] - .1
                blues.set_blue(slot, new_current, delay=.1)
                #rerecord values if we had to adjust
                #blues.read_blues()

    #logging
    data={}
    for ii in range(len(blues.slots)):
        data["I_{}".format(ii)] = blues.currents[ii]
        data["P_{}".format(ii)] = blues.powers[ii]
    
    DATA_DIR = os.path.join(DATA_FOLDER, "{}.csv".format(str(datetime.datetime.today().date())))
    df = pd.DataFrame(data, index = [datetime.datetime.now()])
    df.index.name = "time"
    if os.path.exists(DATA_DIR):
        df.to_csv(DATA_DIR, header=False, mode="a+")
    else:
        df.to_csv(DATA_DIR, mode="a")

    df.index = pd.to_datetime(df.index, unit='s')

    with InfluxDBClient(url=db_info.url, token=db_info.token, org=db_info.org, debug=False) as client:
        write_api = client.write_api(write_options=SYNCHRONOUS)
        for k, v in data.items():
            write_api.write(db_info.bucket, db_info.org, "Blues,Channel={} Value={}".format(k, v))
        client.close()
    print(df)
        



"""Main loop"""
if __name__ == "__main__":
    blues=blue_lasers()
    try:
        while True:
            try:
                log_lock(blues)
            except pyvisa.errors.VisaIOError:
                print("VISA Error detected. Closing communication Until next cycle")
                blues.GTL()
            time.sleep(30)
    except KeyboardInterrupt:
        pass    


