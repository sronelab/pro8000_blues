#Class for blue lasers.
import numpy as np
import matplotlib.pyplot as plt
import serial
import time

#Class for controlling our blue lasers
class blue_lasers():

    #Constructor
    def __init__(self):
        self.currents = [-1,-1,-1]
        self.powers = [-1,-1,-1]
        self.slots = [4,5,6] #Slots for TC, MOT, ZS
        self.address = 'COM4' #Current address for blue controller
        self.baudrate = 19200
        #to record while rMPING
        self.lockps=[7.79,9.4,11.36]
        self.maxp_powers=[0,0,0]
        self.maxp_currents=[153.5,152.65,154.9]
        self.limited_currents=[155.3,155.3,156.2]

        #Open communcation to Pro8000
        ser = serial.Serial(self.address,self.baudrate, timeout =1)
        ser.reset_input_buffer()
        print(self.read_line(ser, b"*IDN?"))

        
    def read_line(self, ser, val_cmd):
        line=[]
        i=0
        while len(line)==0:
            i+=1
            ser.write(val_cmd)
            line=ser.readline()#.split()
            if i>5:
                break
        return line
        
    #Read blue laser currents
    def read_blues(self):

        #Open communcation to Pro8000
        ser = serial.Serial(self.address,self.baudrate, timeout =1)
        ser.reset_input_buffer()

        #Read currents
        for i in range(0,len(self.slots)):
            print(self.slots[i])
            ser.write((':SLOT ' + str(self.slots[i])+'\n').encode())
            slt=self.read_line(ser, ":SLOT?\n")
            print(slt)
            line=self.read_line(ser,':ILD:SET?\n')
            print(line)
            # self.currents[i] = float(line[1])*10**3 #convert to mA

        #Read powers
        for i in range(0,len(self.slots)):
            ser.write((':SLOT ' + str(self.slots[i])+'\n').encode())
            line=self.read_line(ser,':POPT:ACT?\n')
            self.powers[i] = float(line[1])*10**3 #convert to mW

        #Switch to local mode and close resource
        ser.write('&GTL\n')
        ser.close()


    #Function for ramping current between values. Assumes slot is current
    #controller slot in integer, currents in mA, and integer steps.
    #Time delay in s
    def ramp_current(self,slot, start_current, end_current, steps,time_delay):

        #Create list of currents to ramp through.
        currents = np.linspace(start_current,end_current,steps,endpoint=True, dtype = float)#Endpoint flag ensures we stop at the end point....

        #Open communcation to Pro8000. Tell it which slot
        ser = serial.Serial(self.address,self.baudrate, timeout =1)
        ser.reset_input_buffer()
        ser.write(':SLOT ' + str(slot) + '\n')

        #Write current ramps with delay between.
        for current in currents:
            ser.write(':ILD:SET ' + str(current) + 'e-3\n')
            time.sleep(time_delay)

        #Switch to local mode and close resource
        ser.write('&GTL\n')
        ser.close()

    def ramp_current_for_maxp(self,diode, start_current, end_current, steps,time_delay):
        slot=self.slots[diode]

        #Create list of currents to ramp through up and down.
        currents = np.linspace(start_current,end_current,steps,endpoint=True, dtype = float)#Endpoint flag ensures we stop at the end point....
        #currents_up = np.linspace(end_current+ramp_up,end_current, steps,endpoint=True, dtype = float)
        #Open communcation to Pro8000. Tell it which slot
        ser = serial.Serial(self.address,self.baudrate, timeout =1)
        ser.reset_input_buffer()
        ser.write(':SLOT ' + str(slot) + '\n')
        
        #Write current ramps with delay between.
        for current in currents:
            ser.write(':ILD:SET ' + str(current) + 'e-3\n')
            #read power
            line=self.read_line(ser,':POPT:ACT?\n')
            p_temp=float(line[1])*10**3
            #print(p_temp)
            #check for max
            if self.maxp_powers[diode]<p_temp:
                self.maxp_powers[diode]=p_temp
                self.maxp_currents[diode]=current
            time.sleep(time_delay)

        #Switch to local mode and close resource
        ser.write('&GTL\n')
        ser.close()

    def ramp_up_down(self, diode, end_current, ramp_up, steps,time_delay):
        time.sleep(time_delay)
        self.read_blues()
        #ramp up to some max
        self.ramp_current(self.slots[diode],self.currents[diode],end_current+ramp_up,steps,time_delay)
        #ramp down recording values 
        time.sleep(time_delay)
        self.read_blues()
        #self.ramp_current(self.slots[diode],self.currents[diode],end_current,steps,time_delay)
        self.ramp_current_for_maxp(diode,self.currents[diode],end_current,steps,time_delay)

    #Use to initialize locked values once locked
    def init_lockvals(self):

        #Open communcation to Pro8000
        ser = serial.Serial(self.address,self.baudrate, timeout =1)
        ser.reset_input_buffer()

        #Read currents
        for i in range(0,len(self.slots)):
            ser.write(':SLOT ' + str(self.slots[i])+'\n')
            line=self.read_line(ser,':ILD:SET?\n')
            self.maxp_currents[i] = float(line[1])*10**3 #convert to mA

        #Read powers
        for i in range(0,len(self.slots)):
            ser.write(':SLOT ' + str(self.slots[i])+'\n')
            line=self.read_line(ser,':POPT:ACT?\n')
            self.lockps[i] = float(line[1])*10**3 #convert to mW

        #Switch to local mode and close resource
        ser.write('&GTL\n')
        ser.close()

    def ramp_current_for_pi_curve(self,diode, start_current, end_current, steps,time_delay):
        #powers
        powers=np.array([])

        slot=self.slots[diode]

        #Create list of currents to ramp through
        currents = np.linspace(start_current,end_current,steps,endpoint=True, dtype = float)#Endpoint flag ensures we stop at the end point....
        
        #Open communcation to Pro8000. Tell it which slot
        ser = serial.Serial(self.address,self.baudrate, timeout =1)
        ser.reset_input_buffer()
        ser.write(':SLOT ' + str(slot) + '\n')
        
        #Write current ramps with delay between.
        for current in currents:
            ser.write(':ILD:SET ' + str(current) + 'e-3\n')
            #read power
            line=self.read_line(ser,':POPT:ACT?\n')
            #add to list
            #print(line)
            powers=np.append(powers,[float(line[1])*10**3])
            time.sleep(time_delay)

        #Switch to local mode and close resource
        ser.write('&GTL\n')
        ser.close()

        return currents, powers

    def curve_scan(self,diode, end_current,time_delay):
        self.read_blues()
        steps_up=int((self.limited_currents[diode]-self.currents[diode])/.01)
        #ramp up to the top
        self.ramp_current(self.slots[diode],self.currents[diode],self.limited_currents[diode],steps_up,time_delay)
        time.sleep(time_delay)

        steps_down=int((self.limited_currents[diode]-end_current)/.01)
        currents, powers= self.ramp_current_for_pi_curve(diode,self.limited_currents[diode],end_current,steps_down,time_delay)

        return currents, powers





