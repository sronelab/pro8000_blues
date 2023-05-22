#GUI 

from operator import truediv
import sys
import time
#from gmpy2 import *
from PyQt4 import QtGui, QtCore
from blue_lasers import blue_lasers
import numpy as np

#Class for blue laser gui
class blue_GUI(QtGui.QWidget):

    def __init__(self):
            super(blue_GUI, self).__init__()
            self.initUI()
            
            
    def initUI(self):
    
        #Lock currents for 4, 5, 6
        self.rampups=[1.1,1.1,1.2]
        self.lock_currents = [153.78,152.08,155.03]
        
        #self.locked_powers=[0,0,0]
        
        self.step_size=.01 
        self.time_delay=.01
        self.quit=0
        self.timer_length=15  #s
        
        #Call blue class functions for slaves
        self.blues = blue_lasers()
        
        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        
        #a timer to handle the monitering
        self.timer=QtCore.QTimer()
        self.timer.timeout.connect(self.lock)

        #handle logging file names
        self.file_time_str=''

        #Declaring and propagating buttons/labels/etc        
        #Row 0 is all labels
        labels_row_0 = ['Laser','Current (mA)', 'Power (mW)', 'Set current to specific value (mA)', 'Press to set', 'ramp current a specific amount (mA) above and back down to specific value', "Press to ramp up then down", 'set time delay between .01 mA steps in ramp', 'max recorded power in ramp down', 'Associated Current']
        for i in range(0,len(labels_row_0)):
            label = QtGui.QLabel(labels_row_0[i])
            grid.addWidget(label,0,i)

        #Column for Laser Labels
        labels_lasers = ['MOT', 'TC', 'ZS']
        for i in range(0,len(labels_lasers)):
            label = QtGui.QLabel(labels_lasers[i])
            grid.addWidget(label,1+i,0) 
            
        
        #Columns for powers and currentsa, and setcurrents. Store labels in lists for ease of calling.
        self.labels_powers = [QtGui.QLabel("Null"), QtGui.QLabel("Null"), QtGui.QLabel("Null")]
        self.labels_currents = [QtGui.QLabel("Null"), QtGui.QLabel("Null"), QtGui.QLabel("Null")]
        self.line_edits_lock_currents = [QtGui.QLineEdit(str(self.lock_currents[0])),QtGui.QLineEdit(str(self.lock_currents[1])),QtGui.QLineEdit(str(self.lock_currents[2]))]
        for i in range(0,len(self.labels_powers)):
            grid.addWidget(self.labels_currents[i],1+i,1)
            grid.addWidget(self.labels_powers[i],1+i,2)
            grid.addWidget(self.line_edits_lock_currents[i],1+i,3)
            

        #Buttons to set currents

        #Set MOT Current Button    
        button_set_MOT = QtGui.QPushButton("Set MOT")
        grid.addWidget(button_set_MOT,1,4)
        button_set_MOT.clicked.connect(self.handle_button_set_MOT)
        #Set TC Current Button
        button_set_TC = QtGui.QPushButton("Set TC")
        grid.addWidget(button_set_TC,2,4)
        button_set_TC.clicked.connect(self.handle_button_set_TC)
        #Set ZS Current button
        button_set_ZS = QtGui.QPushButton("Set ZS")
        grid.addWidget(button_set_ZS,3,4)
        button_set_ZS.clicked.connect(self.handle_button_set_ZS)

        self.line_edits_rampups = [QtGui.QLineEdit(str(self.rampups[0])),QtGui.QLineEdit(str(self.rampups[1])),QtGui.QLineEdit(str(self.rampups[2]))]
        for i in range(0,len(self.labels_powers)):
            grid.addWidget(self.line_edits_rampups[i],1+i,5)

        #ramp up above then down down to set value
        button_updown_MOT = QtGui.QPushButton("ramp MOT")
        grid.addWidget(button_updown_MOT,1,6)
        button_updown_MOT.clicked.connect(self.handle_button_updown_MOT)
        #Set TC Current Button
        button_updown_TC = QtGui.QPushButton("ramp TC")
        grid.addWidget(button_updown_TC,2,6)
        button_updown_TC.clicked.connect(self.handle_button_updown_TC)
        #Set ZS Current button
        button_updown_ZS = QtGui.QPushButton("ramp ZS")
        grid.addWidget(button_updown_ZS,3,6)
        button_updown_ZS.clicked.connect(self.handle_button_updown_ZS)

        #set ramp speed
        self.line_edit_time_delay = QtGui.QLineEdit(str(self.time_delay))
        grid.addWidget(self.line_edit_time_delay,1,7)

        #display max power/current
        self.labels_maxp_powers = [QtGui.QLabel("Null"), QtGui.QLabel("Null"), QtGui.QLabel("Null")]
        self.labels_maxp_currents = [QtGui.QLabel("Null"), QtGui.QLabel("Null"), QtGui.QLabel("Null")]
        for i in range(0,len(self.labels_powers)):
            grid.addWidget(self.labels_maxp_currents[i],1+i,9)
            grid.addWidget(self.labels_maxp_powers[i],1+i,8)


        #Row 5 buttons for reading current/power, 
        button_read_blues = QtGui.QPushButton('Read blues')
        grid.addWidget(button_read_blues,5,0)
        button_read_blues.clicked.connect(self.handle_button_read_blues)

        self.button_monitor = QtGui.QPushButton('monitor (no inputs just assumes already locked)')
        grid.addWidget(self.button_monitor,6,0)
        self.button_monitor.clicked.connect(self.handle_button_monitor)

        self.button_stop_monitor = QtGui.QPushButton('stop monitor')
        grid.addWidget(self.button_stop_monitor,6,1)
        self.button_stop_monitor.clicked.connect(self.handle_button_stop_monitor)

        self.timing_label=QtGui.QLabel("time (s) between monitoring diodes")
        grid.addWidget(self.timing_label,6,2)
        self.line_edit_timer_length = QtGui.QLineEdit(str(self.timer_length))
        grid.addWidget(self.line_edit_timer_length,6,3)

        #Moves the window to this screen position.
        self.resize(400,200)
        self.move(300, 300)

        self.setWindowTitle('Blue Laser Control GUI')
        self.show()

    #Read powers and currents
    def handle_button_read_blues(self):
        #Get powers and currents updated
        self.blues.read_blues()
        #print(self.blues.powers)
        #Update the powers/currents. 3 Controllers!
        for i in range(0,3):
            self.labels_currents[i].setText(str(self.blues.currents[i]))
            self.labels_powers[i].setText(str(self.blues.powers[i]))
            
        #Add a delay for people rage clicking
        time.sleep(.05)

        #[self.label_MOT_current,self.label_TC_current,self.label_ZS_current] = self.blues.currents
        #[self.label_MOT_power,self.label_TC_power,self.label_ZS_power] = self.blues.powers

    def handle_button_set_MOT(self):
        diode=0
        self.blues.read_blues()
        set_current=float(self.line_edits_lock_currents[diode].text())
        steps=int(abs(set_current-self.blues.currents[diode])/.01)
        #assumes currents in mA
        self.blues.ramp_current(self.blues.slots[diode],self.blues.currents[diode],set_current,steps,self.time_delay)
        self.handle_button_read_blues()
        #units

    def handle_button_set_TC(self):
        diode=1
        self.blues.read_blues()
        set_current=float(self.line_edits_lock_currents[diode].text())
        steps=int(abs(set_current-self.blues.currents[diode])/.01)
        #assumes currents in mA
        self.blues.ramp_current(self.blues.slots[diode],self.blues.currents[diode],set_current,steps,self.time_delay)
        self.handle_button_read_blues()
        #units

    def handle_button_set_ZS(self):
        diode=2
        self.blues.read_blues()
        set_current=float(self.line_edits_lock_currents[diode].text())
        steps=int(abs(set_current-self.blues.currents[diode])/.01)
        #assumes currents in mA
        self.blues.ramp_current(self.blues.slots[diode],self.blues.currents[diode],set_current,steps,self.time_delay)
        self.handle_button_read_blues()
        #units

    def handle_button_updown_MOT(self):
        diode=0
        self.blues.read_blues()
        set_current=float(self.line_edits_lock_currents[diode].text())
        ramp_up=float(self.line_edits_rampups[diode].text())
        time_delay=float(self.line_edit_time_delay.text())
        steps=int(abs(set_current+ramp_up-self.blues.currents[diode])/.01)
        #assumes currents in mA
        self.blues.ramp_up_down(diode,set_current,ramp_up,steps,time_delay)
        self.handle_button_read_blues()
        self.labels_maxp_currents[diode].setText(str(self.blues.maxp_currents[diode]))
        self.labels_maxp_powers[diode].setText(str(self.blues.maxp_powers[diode]))
        #reset the power so the next sweep can check if the new lock point drifted AND had a lower power than some previous max?
        self.blues.maxp_powers[diode]=0

    def handle_button_updown_TC(self):
        diode=1
        self.blues.read_blues()
        set_current=float(self.line_edits_lock_currents[diode].text())
        ramp_up=float(self.line_edits_rampups[diode].text())
        time_delay=float(self.line_edit_time_delay.text())
        steps=int(abs(set_current+ramp_up-self.blues.currents[diode])/.01)
        #assumes currents in mA
        self.blues.ramp_up_down(diode,set_current,ramp_up,steps,time_delay)
        self.handle_button_read_blues()
        self.labels_maxp_currents[diode].setText(str(self.blues.maxp_currents[diode]))
        self.labels_maxp_powers[diode].setText(str(self.blues.maxp_powers[diode]))
        #reset the power so the next sweep can check if the new lock point drifted AND had a lower power than some previous max?
        self.blues.maxp_powers[diode]=0

    def handle_button_updown_ZS(self):
        diode=2
        self.blues.read_blues()
        set_current=float(self.line_edits_lock_currents[diode].text())
        ramp_up=float(self.line_edits_rampups[diode].text())
        time_delay=float(self.line_edit_time_delay.text())
        steps=int(abs(set_current+ramp_up-self.blues.currents[diode])/.01)
        #assumes currents in mA
        self.blues.ramp_up_down(diode,set_current,ramp_up,steps,time_delay)
        self.handle_button_read_blues()
        self.labels_maxp_currents[diode].setText(str(self.blues.maxp_currents[diode]))
        self.labels_maxp_powers[diode].setText(str(self.blues.maxp_powers[diode]))
        #reset the power so the next sweep can check if the new lock point drifted AND had a lower power than some previous max?
        self.blues.maxp_powers[diode]=0

    #monitor button
    def handle_button_monitor(self):
        #assume locked, initialize currents, powers
        self.handle_button_read_blues()
        self.blues.init_lockvals()
        #begin log file:
        time=QtCore.QDateTime.currentDateTime()
        self.file_time_str=time.toString('yyyy-MM-dd hh-mm-ss dddd')
        with open('Blues Monitoring '+str(self.file_time_str)+'.txt','w') as f:
            f.write('Monitoring')
            f.write('\n')
            f.close()
        self.timer_length=int(self.line_edit_timer_length.text())*10**3 #convert s to ms
        self.timer.start(self.timer_length) #time in ms
        self.button_monitor.setEnabled(False)
        self.button_stop_monitor.setEnabled(True)

    def handle_button_stop_monitor(self):
        self.timer.stop()
        self.button_stop_monitor.setEnabled(False)
        self.button_monitor.setEnabled(True)

    #DOES NOT HANDLE a case in which the power doesnt increase as you decrease the current from the max
    #WILL STOP if unable to lock a diode
    def lock(self):
        #assumes everything is locked
        thresh=.2 #how much a power has todrop to be "unlocked"
        lockedps=self.blues.lockps
        self.handle_button_read_blues()
        #write powers to text file with time stamp
        time=QtCore.QDateTime.currentDateTime()
        timeDisplay=time.toString('yyyy-MM-dd hh:mm:ss dddd')
        with open('Blues Monitoring '+ str(self.file_time_str)+'.txt','a') as f:
            f.write(timeDisplay)
            f.write('\n')
            f.write(str(self.blues.powers))
            f.write('\n')
            f.close()
        for i in range(len(lockedps)):
            diode=i
            #check powers to see if locked
            if self.blues.powers[i]<lockedps[i]-thresh:
                #self.timer.stop() #stop timer in case this takes a while
                #if not, relock, may have to try a couple of times if lock point drifts
                #initial relock info that won't update if lock fails
                print("relock")
                print(diode)
                with open('Blues Monitoring '+str(self.file_time_str)+'.txt','a') as f:
                    f.write('relock '+str(diode))
                    f.write('\n')
                    f.close()
                top_current=self.blues.limited_currents[diode]
                time_delay=float(self.line_edit_time_delay.text())
                for j in range(4):
                    set_current=self.blues.maxp_currents[diode] #return to the previous max current
                    print(set_current)
                    ramp_up=top_current-set_current
                    steps=int(abs(top_current-self.blues.currents[diode])/.01)
                    #mA
                    #print(j)
                    self.blues.ramp_up_down(diode,set_current,ramp_up,steps,time_delay)
                    self.handle_button_read_blues()
                    #display the max from the sweep
                    self.labels_maxp_currents[diode].setText(str(self.blues.maxp_currents[diode]))
                    self.labels_maxp_powers[diode].setText(str(self.blues.maxp_powers[diode]))
                    #reset the power so the next sweep can check if the new lock point drifted AND had a lower power than some previous max?
                    self.blues.maxp_powers[diode]=0
                    #check to see if we relocked
                    if self.blues.powers[diode]>lockedps[diode]-thresh:
                        #update locked power
                        #self.blues.init_lockvals()
                        self.timer.start(self.timer_length)
                        break
                    #if not go again to the new lock point which was recorded by looping again...
            #make small adjustments to keep the power level constant
            if round(self.blues.powers[i],2)!=round(lockedps[i],2):
                increment=.01 #this may need to change for each diode
                ramp_val= np.sign(self.blues.powers[i]-lockedps[i])*increment
                set_current=self.blues.currents[diode]+ramp_val
                print("adjusting")
                print(set_current)
                self.blues.ramp_current(self.blues.slots[diode],self.blues.currents[diode],set_current,2,self.time_delay)


            



        

#Defines main to be called to execute the program

def main():

    app = QtGui.QApplication(sys.argv)
    ex = blue_GUI()
    sys.exit(app.exec_())


#Exectutes gui
if __name__ == '__main__':
    main()
