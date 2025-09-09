from nicegui import ui, app
from nicegui.events import ValueChangeEventArguments
from datetime import datetime
import json
import pyvisa
import sys
import os
import pandas as pd
import numpy as np
from default_settings import lasers

THORLABS_CONTROLLER = 'ASRL3::INSTR'
servo_switches = {}
dI = 0.05
columns = [
    {'name': 'name', 'label': 'Name', 'field': 'name', 'required': True, 'align': 'left'},
    {'name': 'I', 'label': 'I', 'field': 'I', },
    {'name': 'P', 'label': 'P', 'field': 'P', },
    {'name': 'T', 'label': 'T', 'field': 'T', },
]
rows = [{'name': laser["name"], 'I':None, "P":None, "T":None } for laser in lasers]
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

def read_parameters():
    rm = pyvisa.ResourceManager()
    inst = rm.open_resource(THORLABS_CONTROLLER, open_timeout=10)        
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

class ServoParams:
    # slot numbers for current controllers
    laser_slots = {'2DMOT': 4,
              'MOT': 5,
              'ZS': 6}
    
    def __init__(self, laser_name, invert=False, lock_deriv=True, step_size=0.03, lock_point=0):
        self.laser_name = laser_name
        self.slot = self.laser_slots[laser_name]
        self.step_size = step_size # mA
        self.lock_point = lock_point # %/mA
        self.invert = invert
        self.current = self.read_current()  # mA
        self.ilim_low = self.current - 2 # mA. Assumes operation range is always within +-2 mA
        self.ilim_high = min(self.current + 2, self.read_current_limit()) # mA
        self.deriv = 0
        self.power = 0
        self.lock_deriv = lock_deriv

    def is_safe(self):
        step_size_check = self.step_size < 0.1 and self.step_size > 0
        curr_limit_check = self.current + self.step_size < self.ilim_high
        return step_size_check and curr_limit_check
        
    def read_current(self):
        rm = pyvisa.ResourceManager()
        inst = rm.open_resource(THORLABS_CONTROLLER, open_timeout=10)        
        inst.baud_rate=19200
        inst.write(':SLOT ' + str(self.slot) + '\n')
        current = float(inst.query(":ILD:SET?",).split(' ')[1])*1e3
        inst.close()
        self.current = current
        return current
    
    def reset_limits(self):
        self.ilim_low = self.current - 2
        self.ilim_high = min(self.current + 2, self.read_current_limit()) # mA
    
    def read_current_limit(self):
        rm = pyvisa.ResourceManager()
        inst = rm.open_resource(THORLABS_CONTROLLER, open_timeout=10)        
        inst.baud_rate=19200
        inst.write(':SLOT ' + str(self.slot) + '\n')
        ilim_high = float(inst.query(':LIMC:SET?').split()[-1])*1e3
        inst.close()
        return ilim_high
    
    def read_power(self):
        """
        Read power in mW units
        """
        rm = pyvisa.ResourceManager()
        inst = rm.open_resource(THORLABS_CONTROLLER, open_timeout=10)        
        inst.baud_rate=19200
        inst.write(':SLOT ' + str(self.slot) + '\n')
        power = float(inst.query(":POPT:ACT?",).split(' ')[1])*1e3
        inst.close()
        self.power = power
        return power
    
    def set_current(self, current):
        """
        current is passed as mA to this function
        remember to give A units to the controller, not mA units
        """
        if current < self.ilim_high:
            rm = pyvisa.ResourceManager()
            inst = rm.open_resource(THORLABS_CONTROLLER, open_timeout=10)        
            inst.baud_rate=19200
            inst.write(':SLOT ' + str(self.slot) + '\n')
            inst.write(f":ILD:SET {current*1e-3}")
            inst.close()

        self.current = self.read_current()

    def get_derivative(self):
        """get (dP/P)/dI in units of %/mA"""
        i_before = self.current
        i_after = i_before + self.step_size
        p_before = self.read_power()
        self.set_current(i_after)
        p_after = self.read_power()
        self.set_current(i_before)
        return 100*(p_after-p_before)/p_before/self.step_size
    
    def update_current(self):
        """Really basic servo with a fixed step size"""
        self.current = self.read_current()
        if self.lock_deriv:
            self.deriv = self.get_derivative()
            error = self.lock_point - self.deriv
        else:
            self.power = self.read_power()
            error = self.lock_point - self.power
        if self.invert:
            error *= -1
        if error > 0:
            next_step = min(self.current + self.step_size, self.ilim_high)
        else:
            next_step = max(self.current - self.step_size, self.ilim_low)
        self.set_current(next_step)

def change_current(ii, dI):
    global rows
    global status_table
    rm = pyvisa.ResourceManager()
    inst = rm.open_resource(THORLABS_CONTROLLER, open_timeout=10)        
    inst.baud_rate=19200
    inst.query("*idn?")
    inst.write(':SLOT ' + str(lasers[ii]["Islot"]) + '\n')
    
    I_old = rows[ii]["I"]
    inst.write(f":ILD:SET {str(I_old*1e-3 + dI*1e-3)}")
    rows[ii]["I"] = np.round(float(inst.query(":ILD:SET?",).split(' ')[1])*1e3, decimals=3)
    rows[ii]["P"] = np.round(float(inst.query(":POPT:ACT?",).split(' ')[1])*1e3, decimals=3)
    status_table.update()
    inst.close()

def change_temperature(ii, dT):
    global rows
    global status_table
    rm = pyvisa.ResourceManager()
    inst = rm.open_resource(THORLABS_CONTROLLER, open_timeout=10)        
    inst.baud_rate=19200
    inst.write(':SLOT ' + str(lasers[ii]["Tslot"]) + '\n')
    
    T_old = rows[ii]["T"]
    inst.write(f":TEMP:SET {str(T_old + dT)}")
    rows[ii]["T"] = np.round(float(inst.query(":TEMP:SET?",).split(' ')[1]), decimals=3)
    status_table.update()
    inst.close()

def injection_lock_servo_notification(event: ValueChangeEventArguments, servo_params):
    servo_on = event.value
    if servo_on:
        message = 'stabilization on'
        servo_params.reset_limits()
    else:
        message = 'stabilization off'
    ui.notify(message)

def update_servo(servo_switch, servo_params):
    def update_params():
        if servo_switch.value and servo_params.is_safe():
            servo_params.update_current()
    return update_params

def make_current_controls(laser_index, dI):
    with ui.button_group():
        ui.button(f'{lasers[laser_index]["name"]}',
                  icon='arrow_upward',
                  on_click=lambda: change_current(laser_index, dI))
        ui.button(f'{lasers[laser_index]["name"]}',
                  icon='arrow_downward',
                  on_click=lambda: change_current(laser_index, -dI))

def make_servo_controls(laser_index, servo_params, image_path):
    with ui.row():
        servo_switch = ui.switch('injection lock servo ',
                                 on_change=lambda event: injection_lock_servo_notification(event, servo_params))
        servo_switches[servo_params.laser_name] = servo_switch

        v = ui.checkbox('show parameters', value=False)

        with ui.column().bind_visibility_from(v, 'value'):
            ui.number('step size (mA)',
                    format='%.2f',
                    max=0.1,
                    min=0,
                    step=0.01,
                    validation={'too high': lambda value: value < 0.1,
                                '>0': lambda value: value > 0}).bind_value(servo_params, 'step_size').classes('w-64')
            ui.number('lock point (%/mA or mW)',
                    format='%.2f',
                    step=0.1).bind_value(servo_params, 'lock_point').classes('w-64')
            
            ui.label().bind_text_from(servo_params, 'current', backward=lambda x: f'Current = {x:.2f} mA')
            ui.label().bind_text_from(servo_params, 'deriv', backward=lambda x: f'Derivative = {x:.2f} %/mA')
            ui.label().bind_text_from(servo_params, 'power', backward=lambda x: f'Power = {x:.2f} mW')
            
            current_dir = os.path.dirname(os.path.abspath(__file__))
            image_folder = os.path.join(current_dir, 'images')
            app.add_static_files('/image', image_folder)
            ui.image(image_path).classes('w-96')

# clock for checking if server working
label = ui.label()
ui.timer(1.0, lambda: label.set_text(f'{datetime.now():%X}'))
status_table = ui.table(columns=columns, rows=rows)
read_parameters()
ui.timer(3.0, read_parameters)
control_pannel = ui.row()

twodmotservo_params = ServoParams('2DMOT', invert=True, lock_deriv=False, step_size=0.01, lock_point=39.67)
motservo_params = ServoParams('MOT', invert=True, step_size=0.01, lock_point=1.5)
zsservo_params = ServoParams('ZS', invert=True, lock_point=-3)

make_current_controls(0, dI)
make_servo_controls(0, twodmotservo_params, 'image/output power lock.png')
make_current_controls(1, dI)
make_servo_controls(1, motservo_params, 'image/20250826_mot_deriv.png')
make_current_controls(2, dI)
make_servo_controls(2, zsservo_params, 'image/20250826_ZS_deriv.png')

# with ui.button_group():
#     ui.button(f'{lasers[0]["name"]} T', icon='arrow_upward', on_click=lambda: change_temperature(0, 0.01))
#     ui.button(f'{lasers[0]["name"]} T', icon='arrow_downward', on_click=lambda: change_temperature(0, -0.01))
# with ui.button_group():
#     ui.button(f'{lasers[1]["name"]} T', icon='arrow_upward', on_click=lambda: change_temperature(1, 0.01))
#     ui.button(f'{lasers[1]["name"]} T', icon='arrow_downward', on_click=lambda: change_temperature(1, -0.01))
# with ui.button_group():
#     ui.button(f'{lasers[2]["name"]} T', icon='arrow_upward', on_click=lambda: change_temperature(2, 0.01))
#     ui.button(f'{lasers[2]["name"]} T', icon='arrow_downward', on_click=lambda: change_temperature(2, -0.01))

ui.timer(15.0, update_servo(servo_switches['2DMOT'], twodmotservo_params))
ui.timer(15.0, update_servo(servo_switches['MOT'], motservo_params))
ui.timer(15.0, update_servo(servo_switches['ZS'], zsservo_params))

ui.run(title="Blue laser controller")