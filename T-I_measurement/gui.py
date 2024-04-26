from nicegui import ui
from nicegui.events import ValueChangeEventArguments
from datetime import datetime
import json
import pyvisa
import sys
import os
import pandas as pd
import numpy as np

# Load default parameters
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from default_settings import lasers

# clock for checking if server working
label = ui.label()
ui.timer(1.0, lambda: label.set_text(f'{datetime.now():%X}'))

# Parameter reading
columns = [
    {'name': 'name', 'label': 'Name', 'field': 'name', 'required': True, 'align': 'left'},
    {'name': 'I', 'label': 'I', 'field': 'I', },
    {'name': 'P', 'label': 'P', 'field': 'P', },
    {'name': 'T', 'label': 'T', 'field': 'T', },
]
rows = [{'name': laser["name"], 'I':None, "P":None, "T":None } for laser in lasers]
status_table = ui.table(columns=columns, rows=rows)
def read_parameters():
    rm = pyvisa.ResourceManager()
    inst = rm.open_resource('ASRL4::INSTR', open_timeout=10)        
    inst.baud_rate=19200
    
    global rows
    ii = 0
    for laser in lasers:
        rows[ii]["name"] = laser["name"]
        # Select the current controller
        inst.write(':SLOT ' + str(laser["Islot"]) + '\n')
        rows[ii]["I"] = np.round(float(inst.query(":ILD:SET?",).split(' ')[1])*1e3, decimals=3)
        rows[ii]["P"] = np.round(float(inst.query(":POPT:ACT?",).split(' ')[1])*1e3, decimals=3)
        
        inst.write(':SLOT ' + str(laser["Tslot"]) + '\n')
        rows[ii]["T"] = np.round(float(inst.query(":TEMP:ACT?",).split(' ')[1]), decimals=3)
        ii += 1
    inst.close()
    status_table.update()
    # ui.notify("Parameter updated")

read_parameters()
ui.timer(3.0, read_parameters)
# ui.button('Read parameters', on_click=read_parameters)

control_pannel = ui.row()
def change_current(ii, dI):
    global rows
    global status_table
    rm = pyvisa.ResourceManager()
    inst = rm.open_resource('ASRL4::INSTR', open_timeout=10)        
    inst.baud_rate=19200
    inst.query("*idn?")
    inst.write(':SLOT ' + str(lasers[ii]["Islot"]) + '\n')
    
    I_old = rows[ii]["I"]
    inst.write(f":ILD:SET {str(I_old*1e-3 + dI*1e-3)}")
    rows[ii]["I"] = np.round(float(inst.query(":ILD:SET?",).split(' ')[1])*1e3, decimals=3)
    rows[ii]["P"] = np.round(float(inst.query(":POPT:ACT?",).split(' ')[1])*1e3, decimals=3)
    status_table.update()
    inst.close()

dI = 0.02
with ui.row():
    ui.button(f'{lasers[0]["name"]} I', icon='arrow_upward', on_click=lambda: change_current(0, dI))
    ui.button(f'{lasers[0]["name"]} I', icon='arrow_downward', on_click=lambda: change_current(0, -dI))
with ui.row():
    ui.button(f'{lasers[1]["name"]} I', icon='arrow_upward', on_click=lambda: change_current(1, dI))
    ui.button(f'{lasers[1]["name"]} I', icon='arrow_downward', on_click=lambda: change_current(1, -dI))
with ui.row():
    ui.button(f'{lasers[2]["name"]} I', icon='arrow_upward', on_click=lambda: change_current(2, dI))
    ui.button(f'{lasers[2]["name"]} I', icon='arrow_downward', on_click=lambda: change_current(2, -dI))

def change_temperature(ii, dT):
    global rows
    global status_table
    rm = pyvisa.ResourceManager()
    inst = rm.open_resource('ASRL4::INSTR', open_timeout=10)        
    inst.baud_rate=19200
    inst.write(':SLOT ' + str(lasers[ii]["Tslot"]) + '\n')
    
    T_old = rows[ii]["T"]
    inst.write(f":TEMP:SET {str(T_old + dT)}")
    rows[ii]["T"] = np.round(float(inst.query(":TEMP:SET?",).split(' ')[1]), decimals=3)
    status_table.update()
    inst.close()

with ui.row():
    ui.button(f'{lasers[1]["name"]} T', icon='arrow_upward', on_click=lambda: change_temperature(1, 0.005))
    ui.button(f'{lasers[1]["name"]} T', icon='arrow_downward', on_click=lambda: change_temperature(1, -0.005))

# TODO: maximum value safety feature

ui.run(title="Blue laser controller")