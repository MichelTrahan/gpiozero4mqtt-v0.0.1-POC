#----------------------------------------------
# code to give gpiozero widgets access to mqtt
# Author: Michel Trahan
# Created: 2020-09-14
# Last tested: 2021-03-04
#----------------------------------------------
import paho.mqtt.client as mqtt
#----------------------------------------------
import xml.etree.ElementTree as oXML
#----------------------------------------------
from gpiozero import Button, LED, DigitalInputDevice
from gpiozero import RGBLED, PWMLED, PWMOutputDevice, Buzzer
from gpiozero import LineSensor, MotionSensor, LightSensor, DistanceSensor
from gpiozero import TonalBuzzer, Motor, PhaseEnableMotor, Servo, AngularServo
from gpiozero import DigitalOutputDevice, OutputDevice
#from gpiozero import InputDevice, GPIODevice
#----------------------------------------------
import Raspi_Info as RI
import SourceConnectionProcessor as SCP 
import clsLog
#----------------------------------------------
import pygame.mixer as pygmx # for SoundMixer
import RPi_I2C_driver        # for LCD2x16
#----------------------------------------------
import datetime
import time
import json
import os
import ast
#----------------------------------------------
# Variables
#----------------------------------------------
CURRENT_VERSION = "0.0.2"
#----------------------------------------------
SLEEPTIME = 3
#----------------------------------------------
MONO = 0
STEREO = 1
#----------------------------------------------
#-------------------------------------------------
# Conversion functions
#-------------------------------------------------
# str_to_bool   
# str_to_bool_or_None       
# isstrNone
# str_to_tuple
# IntorNone     
# FloatorNone
#---------------------------------------------------------
#-------------------------------------------------
#-------------------------------------------------
def str_to_bool(s):
    if s.upper() == 'TRUE':
         return True
    elif s.upper() == 'FALSE':
         return False
    else:
         raise ValueError # evil ValueError that doesn't tell you what the wrong value was
#-------------------------------------------------
def str_to_bool_or_None(s):
    if s == None:
         return None
    elif s.upper() == 'NONE':
         return None
    elif s.upper() == 'TRUE':
         return True
    elif s.upper() == 'FALSE':
         return False
    else:
         raise ValueError # evil ValueError that doesn't tell you what the wrong value was
#-------------------------------------------------
def isstrNone(s):
    if s.upper() == 'NONE':
        return None
    else:
        return s
#-------------------------------------------------
def str_to_tuple(s):
    return ast.literal_eval(s)
#-------------------------------------------------
def IntorNone(s):
    if s.upper() == 'NONE':
        return None
    else:
        return int(s)
#-------------------------------------------------
def FloatorNone(s):
    if s.upper() == 'NONE':
        return None
    else:
        return float(s)
#---------------------------------------------------------
#---------------------------------------------------------
#---------------------------------------------------------
# Empty function, used to deactivate some IN functions
#---------------------------------------------------------
#---------------------------------------------------------
#---------------------------------------------------------
def EmptyFunction():
    pass
#---------------------------------------------------------
#---------------------------------------------------------
#---------------------------------------------------------
# functions to reboot the system
#---------------------------------------------------------
#---------------------------------------------------------
#---------------------------------------------------------
def SystemHalt():
    os.system("shutdown -h now")
def SystemReboot():
    os.system("shutdown -r now")
#---------------------------------------------------------
def SystemProgrammedRebootInMinutes(m):
    os.system("shutdown -r +{}".format(m))
def SystemProgrammedRebootTime(t):
    os.system("shutdown -r {}".format(t))
def SystemProgrammedRebootCancel():
    os.system("shutdown -c")
#---------------------------------------------------------
#---------------------------------------------------------
#---------------------------------------------------------
#---------------------------------------------------------
# Main holder of all the GPIO for the IOTcpu
#---------------------------------------------------------
# in app
# xmlfilename = sys.argv[1] # usefull for testing ;)
# 
# gpioList = GPIOList(xmlfilename)
#---------------------------------------------------------
# connect and start loop
#---------------------------------------------------------
# gpioList.MQTTconnectNow()
# gpioList.MQTT_client.loop_start()
# try:
#   while True:
#       gpioList.loop_process() # for distance sensor and keypad
# 
# except KeyboardInterrupt:
#     gpioList.MQTT_client.disconnect()
#     gpioList.MQTT_client.loop_stop()
#---------------------------------------------------------
#---------------------------------------------------------
#---------------------------------------------------------
#---------------------------------------------------------------------------------
# GPIOList
#---------------------------------------------------------------------------------
class GPIOList(): 
    #----------------------------------------------------------------------------------
    # pass the xml ... 
    # this class will fetch the IN and OUT widgets defined in the XML
    # then the code that uses this class iterates on the GPIOs dictionnary
    #----------------------------------------------------------------------------------
    #-----------------------------------------------------------
    def __init__(self, xmlFilename = "./data/GPIO4MQTT.xml"):
        self.version = CURRENT_VERSION
        #--------------------------------
        self.GPIOs = {}
        #--------------------------------
        # Name, Room, logTo, atLevel
        #--------------------------------
        oXMLtree = oXML.parse(xmlFilename)
        oXMLroot = oXMLtree.getroot()
        self.sXML = oXML.tostring(oXMLroot, encoding='utf8', method='xml')
        self.IoTcpu = oXMLroot.get('name')
        self.room = oXMLroot.get('room')
        self.logTo = oXMLroot.get('logTo')
        self.atLevel = int(oXMLroot.get('atLevel'))
        self.fn = clsLog.BuildFilename(self.logTo, "log")
        self.log = clsLog.Logger(self.fn, self.atLevel)
        self.log.Info("{} in {} will log to : {}, at Level {}".format(self.IoTcpu, self.room, self.logTo, self.atLevel))
        #--------------------------------
        # MQTT informations
        #--------------------------------
        oXMLMQTT = oXMLroot.find('MQTT')
        self.MQTT_host = oXMLMQTT.get('host')
        self.MQTT_port = int(oXMLMQTT.get('port'))
        self.MQTT_keepalive = int(oXMLMQTT.get('keepalive'))
        self.MQTT_qos = int(oXMLMQTT.get('qos'))
        self.log.Info("{}:{} QoS:{} keepalive:{}".format(self.MQTT_host, self.MQTT_port, self.MQTT_qos, self.MQTT_keepalive))
        #-----------------------------------------------------------------------------------
        #-----------------------------------------------------------------------------------
        # INPUTs
        #-----------------------------------------------------------------------------------
        #-----------------------------------------------------------------------------------
        #-----------------------------------------------------------------------------------
        # MQTT_Button
        #-----------------------------------------------------------------------------------
        for ox in oXMLroot.findall('MQTT_Button'):
            name = ox.get('name')
            pin = int(ox.get('pin'))
            when_pressed    = str_to_bool(ox.get('when_pressed'))
            when_held       = str_to_bool(ox.get('when_held'))
            when_released   = str_to_bool(ox.get('when_released'))
            #-----------------------------
            oXMLStatic = ox.find('Static')
            if not oXMLStatic == None:
                pull_up         = str_to_bool_or_None(oXMLStatic.get('pull_up'))
                active_state    = str_to_bool_or_None(oXMLStatic.get('active_state'))
                pin_factory     = isstrNone(oXMLStatic.get('pin_factory'))
            else:
                pull_up         = True
                active_state    = None
                pin_factory     = None
            #-----------------------------
            oXMLTime = ox.find('Time')
            if not oXMLTime == None:
                bounce_time = FloatorNone(oXMLTime.get('bounce_time'))
                hold_time   = float(oXMLTime.get('hold_time'))
                hold_repeat = str_to_bool(oXMLTime.get('hold_repeat'))
            else:
                bounce_time = 0.05
                hold_time   = 0.25
                hold_repeat = False
            #----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            self.log.Info("MQTT_Button {} at pin: {} - {}{}{} - {}{}{} - bounce:{} hold:{} repeat:{}".format(name, pin, when_pressed, when_held, when_released, pull_up, active_state, pin_factory, bounce_time, hold_time, hold_repeat))
            #----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            # create the button while adding it to the dictionnary
            self.GPIOs[name] = mqtt_Button(self.mqttSender, self.log, name, pin, pull_up=pull_up, active_state=active_state, bounce_time=bounce_time, hold_time=hold_time, hold_repeat=hold_repeat, pin_factory=pin_factory)
            self.log.Debug("Button Created")
            if not when_pressed:
                self.GPIOs[name].widget.when_pressed = EmptyFunction
            if not when_held:
                self.GPIOs[name].widget.when_held = EmptyFunction
            if not when_released:
                self.GPIOs[name].widget.when_released = EmptyFunction
            self.log.Debug("Removed not needed button events")
        #-----------------------------------------------------------------------------------
        # MQTT_DigitalInputDevice
        #-----------------------------------------------------------------------------------
        for ox in oXMLroot.findall('MQTT_DigitalInputDevice'):
            name = ox.get('name')
            pin = int(ox.get('pin'))
            when_activated   = str_to_bool(ox.get('when_activated'))
            when_deactivated = str_to_bool(ox.get('when_deactivated'))
            bounce_time = FloatorNone(ox.get('bounce_time'))
            #-----------------------------
            oXMLStatic = ox.find('Static')
            if not oXMLStatic == None:
                pull_up         = str_to_bool_or_None(oXMLStatic.get('pull_up'))
                active_state    = str_to_bool_or_None(oXMLStatic.get('active_state'))
                pin_factory     = isstrNone(oXMLStatic.get('pin_factory'))
            else:
                pull_up         = True
                active_state    = None
                pin_factory     = None
            #----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            self.log.Info("MQTT_DigitalInputDevice {} at pin: {} - {}{} - bounce:{} pull_up:{} active:{} factory:{}".format(name, pin, when_activated, when_deactivated, bounce_time, pull_up, active_state, pin_factory))
            #----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            self.GPIOs[name] = mqtt_DigitalInputDevice(self.mqttSender, self.log, name, pin, pull_up=pull_up, active_state=active_state, bounce_time=bounce_time, pin_factory=pin_factory)
            self.log.Debug("DigitalInputDevice Created")
            if not when_activated:
                self.GPIOs[name].widget.when_activated = EmptyFunction
            if not when_deactivated:
                self.GPIOs[name].widget.when_deactivated = EmptyFunction
            self.log.Debug("Removed not needed DigitalInputDevice events")
        #-----------------------------------------------------------------------------------
        # MQTT_LineSensor
        #-----------------------------------------------------------------------------------
        for ox in oXMLroot.findall('MQTT_LineSensor'):
            name = ox.get('name')
            pin = int(ox.get('pin'))
            when_line   = str_to_bool(ox.get('when_line'))
            when_no_line = str_to_bool(ox.get('when_no_line'))
            #-----------------------------
            oXMLStatic = ox.find('Static')
            if not oXMLStatic == None:
                pull_up         = str_to_bool_or_None(oXMLStatic.get('pull_up'))
                active_state    = str_to_bool_or_None(oXMLStatic.get('active_state'))
                pin_factory     = isstrNone(oXMLStatic.get('pin_factory'))
            else:
                pull_up         = True
                active_state    = None
                pin_factory     = None
            #-----------------------------
            oXMLTime = ox.find('Queue')
            if not oXMLTime == None:
                queue_len   = int(oXMLTime.get('queue_len'))
                sample_rate   = float(oXMLTime.get('sample_rate'))
                threshold   = float(oXMLTime.get('threshold'))
                partial   = str_to_bool(oXMLTime.get('partial'))
            else:
                queue_len   = 5
                sample_rate   = float(100)
                threshold   = 0.5
                partial   = False
            #----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            self.log.Info("MQTT_LineSensor {} at pin: {} - {}{} - {}{}{} - queue_len:{} sample_rate:{} threshold:{} partial:{}".format(name, pin, when_line, when_no_line, pull_up, active_state, pin_factory, queue_len, sample_rate, threshold, partial))
            #----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            # create the LineSensor while adding it to the dictionnary
            self.GPIOs[name] = mqtt_LineSensor(self.mqttSender, self.log, name, pin, pull_up=pull_up, active_state=active_state, queue_len=queue_len, sample_rate=sample_rate, threshold=threshold, partial=partial, pin_factory=pin_factory)
            self.log.Debug("LineSensor Created")
            if not when_line:
                self.GPIOs[name].widget.when_line = EmptyFunction
            if not when_no_line:
                self.GPIOs[name].widget.when_no_line = EmptyFunction
            self.log.Debug("Removed not needed LineSensor events")
        #-----------------------------------------------------------------------------------
        # MQTT_MotionSensor
        #-----------------------------------------------------------------------------------
        for ox in oXMLroot.findall('MQTT_MotionSensor'):
            name = ox.get('name')
            pin = int(ox.get('pin'))
            when_motion   = str_to_bool(ox.get('when_motion'))
            when_no_motion = str_to_bool(ox.get('when_no_motion'))
            #-----------------------------
            oXMLStatic = ox.find('Static')
            if not oXMLStatic == None:
                pull_up         = str_to_bool_or_None(oXMLStatic.get('pull_up'))
                active_state    = str_to_bool_or_None(oXMLStatic.get('active_state'))
                pin_factory     = isstrNone(oXMLStatic.get('pin_factory'))
            else:
                pull_up         = True
                active_state    = None
                pin_factory     = None
            #-----------------------------
            oXMLTime = ox.find('Queue')
            if not oXMLTime == None:
                queue_len   = int(oXMLTime.get('queue_len'))
                sample_rate   = float(oXMLTime.get('sample_rate'))
                threshold   = float(oXMLTime.get('threshold'))
                partial   = str_to_bool(oXMLTime.get('partial'))
            else:
                queue_len   = 1
                sample_rate   = float(10)
                threshold   = 0.5
                partial   = True
            #----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            self.log.Info("MQTT_MotionSensor {} at pin: {} - {}{} - {}{}{} - queue_len:{} sample_rate:{} threshold:{} partial:{}".format(name, pin, when_motion, when_no_motion, pull_up, active_state, pin_factory, queue_len, sample_rate, threshold, partial))
            #----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            # create the MotionSensor while adding it to the dictionnary
            self.GPIOs[name] = mqtt_MotionSensor(self.mqttSender, self.log, name, pin, pull_up=pull_up, active_state=active_state, queue_len=queue_len, sample_rate=sample_rate, threshold=threshold, partial=partial, pin_factory=pin_factory)
            self.log.Debug("MotionSensor Created")
            if not when_motion:
                self.GPIOs[name].widget.when_motion = EmptyFunction
            if not when_no_motion:
                self.GPIOs[name].widget.when_no_motion = EmptyFunction
            self.log.Debug("Removed not needed MotionSensor events")
        #-----------------------------------------------------------------------------------
        # MQTT_LightSensor
        #-----------------------------------------------------------------------------------
        for ox in oXMLroot.findall('MQTT_LightSensor'):
            name = ox.get('name')
            pin = int(ox.get('pin'))
            when_light   = str_to_bool(ox.get('when_light'))
            when_dark = str_to_bool(ox.get('when_dark'))
            #-----------------------------
            oXMLStatic = ox.find('Static')
            if not oXMLStatic == None:
                pin_factory     = isstrNone(oXMLStatic.get('pin_factory'))
            else:
                pin_factory     = None
            #-----------------------------
            oXMLTime = ox.find('Queue')
            if not oXMLTime == None:
                queue_len   = int(oXMLTime.get('queue_len'))
                charge_time_limit   = float(oXMLTime.get('charge_time_limit'))
                threshold   = float(oXMLTime.get('threshold'))
                partial   = str_to_bool(oXMLTime.get('partial'))
            else:
                queue_len   = 5
                charge_time_limit   = 0.1
                threshold   = 0.5
                partial   = False
            #----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            self.log.Info("MQTT_LightSensor {} at pin: {} - {}{} -{} - queue_len:{} sample_rate:{} threshold:{} partial:{}".format(name, pin, when_light, when_dark, pin_factory, queue_len, sample_rate, threshold, partial))
            #----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            # create the LightSensor while adding it to the dictionnary
            self.GPIOs[name] = mqtt_LightSensor(self.mqttSender, self.log, name, pin, queue_len=queue_len, charge_time_limit=charge_time_limit, threshold=threshold, partial=partial, pin_factory=pin_factory)
            self.log.Debug("LightSensor Created")
            if not when_light:
                self.GPIOs[name].widget.when_light = EmptyFunction
            if not when_dark:
                self.GPIOs[name].widget.when_dark = EmptyFunction
            self.log.Debug("Removed not needed LightSensor events")
        #-----------------------------------------------------------------------------------
        # MQTT_DistanceSensor
        #-----------------------------------------------------------------------------------
        for ox in oXMLroot.findall('MQTT_DistanceSensor'):
            name = ox.get('name')
            echo = int(ox.get('echo'))
            trigger = int(ox.get('trigger'))
            when_in_range   = str_to_bool(ox.get('when_in_range'))
            when_out_of_range = str_to_bool(ox.get('when_out_of_range'))
            send_every = FloatorNone(ox.get('send_every'))
            #-----------------------------
            oXMLStatic = ox.find('Static')
            if not oXMLStatic == None:
                pin_factory     = isstrNone(oXMLStatic.get('pin_factory'))
            else:
                pin_factory     = None
            #-----------------------------
            oXMLTime = ox.find('Queue')
            if not oXMLTime == None:
                queue_len   = int(oXMLTime.get('queue_len'))
                max_distance   = float(oXMLTime.get('max_distance'))
                threshold_distance   = float(oXMLTime.get('threshold_distance'))
                partial   = str_to_bool(oXMLTime.get('partial'))
            else:
                queue_len   = 30
                max_distance   = float(1)
                threshold_distance   = 0.3
                partial   = False
            #----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            self.log.Info("MQTT_DistanceSensor {} at echo:{} trigger{} - {} - {} {} - {} - queue_len:{} max_distance:{} threshold_distance:{} partial:{}".format(name, echo, trigger, send_every, when_in_range, when_out_of_range, pin_factory, queue_len, max_distance, threshold_distance, partial))
            #----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            # create the DistanceSensor while adding it to the dictionnary
            self.GPIOs[name] = mqtt_DistanceSensor(self.mqttSender, self.log, name, echo, trigger, send_every=send_every, queue_len=queue_len, max_distance=max_distance, threshold_distance=threshold_distance, partial=partial, pin_factory=pin_factory)
            self.log.Debug("DistanceSensor Created")
            if not when_in_range:
                self.GPIOs[name].widget.when_in_range = EmptyFunction
            if not when_out_of_range:
                self.GPIOs[name].widget.when_out_of_range = EmptyFunction
            self.log.Debug("Removed not needed DistanceSensor events")
        #-----------------------------------------------------------------------------------
        #-----------------------------------------------------------------------------------
        # End of inputs ... Add custom ones here                               ****MIKEINPUT
        #-----------------------------------------------------------------------------------
        #-----------------------------------------------------------------------------------




        #-----------------------------------------------------------------------------------
        #-----------------------------------------------------------------------------------
        # OUTPUTs
        #-----------------------------------------------------------------------------------
        #-----------------------------------------------------------------------------------
        #-----------------------------------------------------------------------------------
        # MQTT_LED
        #-----------------------------------------------------------------------------------
        for ox in oXMLroot.findall('MQTT_LED'):
            name = ox.get('name')
            pin = int(ox.get('pin'))
            #-----------------------------
            oXMLStatic = ox.find('Static')
            if not oXMLStatic == None:
                active_high     = str_to_bool(oXMLStatic.get('active_high'))
                initial_value   = str_to_bool_or_None(oXMLStatic.get('initial_value'))
                pin_factory     = isstrNone(oXMLStatic.get('pin_factory'))
            else:
                active_high     = True
                initial_value   = False
                pin_factory     = None
            #----------------------------------------------------------------------------------------------------------------------------------------------------
            self.log.Info("MQTT_LED {} at pin: {} - {}{}{}".format(name, pin, active_high, initial_value, pin_factory))
            #----------------------------------------------------------------------------------------------------------------------------------------------------
            self.GPIOs[name] = mqtt_LED(self.mqttSender, self.log, name, pin, active_high=active_high, initial_value=initial_value, pin_factory=pin_factory)
            self.log.Debug("LED Created")
        #-----------------------------------------------------------------------------------
        # MQTT_RGBLED
        #-----------------------------------------------------------------------------------
        for ox in oXMLroot.findall('MQTT_RGBLED'):
            name = ox.get('name')
            r = int(ox.get('r'))
            g = int(ox.get('g'))
            b = int(ox.get('b'))
            #-----------------------------
            oXMLStatic = ox.find('Static')
            if not oXMLStatic == None:
                active_high     = str_to_bool(oXMLStatic.get('active_high'))
                initial_value   = str_to_tuple(oXMLStatic.get('initial_value'))
                pwm             = str_to_bool(oXMLStatic.get('pwm'))
                pin_factory     = isstrNone(oXMLStatic.get('pin_factory'))
            else:
                active_high     = True
                initial_value   = (0, 0, 0)
                pwm             = True
                pin_factory     = None
            #----------------------------------------------------------------------------------------------------------------------------------------------------
            self.log.Info("MQTT_RGBLED {} at pin: r{} g{} b{} - {} {} {} {}".format(name, r, g, b, active_high, initial_value, pwm, pin_factory))
            #----------------------------------------------------------------------------------------------------------------------------------------------------
            self.GPIOs[name] = mqtt_RGBLED(self.mqttSender, self.log, name, r, g, b, active_high=active_high, initial_value=initial_value, pwm=pwm, pin_factory=pin_factory)
            self.log.Debug("RGBLED Created")
        #-----------------------------------------------------------------------------------
        # MQTT_PWMLED
        #-----------------------------------------------------------------------------------
        for ox in oXMLroot.findall('MQTT_PWMLED'):
            name = ox.get('name')
            pin = int(ox.get('pin'))
            #-----------------------------
            oXMLStatic = ox.find('Static')
            if not oXMLStatic == None:
                active_high     = str_to_bool(oXMLStatic.get('active_high'))
                initial_value   = float(oXMLStatic.get('initial_value'))
                frequency       = float(oXMLStatic.get('frequency'))
                pin_factory     = isstrNone(oXMLStatic.get('pin_factory'))
            else:
                active_high     = True
                initial_value   = 0
                frequency       = float(100)
                pin_factory     = None
            #----------------------------------------------------------------------------------------------------------------------------------------------------
            self.log.Info("MQTT_PWMLED {} at pin: {} - {}{}{}{}".format(name, pin, active_high, initial_value, frequency, pin_factory))
            #----------------------------------------------------------------------------------------------------------------------------------------------------
            self.GPIOs[name] = mqtt_PWMLED(self.mqttSender, self.log, name, pin, active_high=active_high, initial_value=initial_value, frequency=frequency, pin_factory=pin_factory)
            self.log.Debug("PWMLED Created")
        #-----------------------------------------------------------------------------------
        # MQTT_PWMOutputDevice
        #-----------------------------------------------------------------------------------
        for ox in oXMLroot.findall('MQTT_PWMOutputDevice'):
            name = ox.get('name')
            pin = int(ox.get('pin'))
            #-----------------------------
            oXMLStatic = ox.find('Static')
            if not oXMLStatic == None:
                active_high     = str_to_bool(oXMLStatic.get('active_high'))
                initial_value   = float(oXMLStatic.get('initial_value'))
                frequency       = float(oXMLStatic.get('frequency'))
                pin_factory     = isstrNone(oXMLStatic.get('pin_factory'))
            else:
                active_high     = True
                initial_value   = 0
                frequency       = float(100)
                pin_factory     = None
            #----------------------------------------------------------------------------------------------------------------------------------------------------
            self.log.Info("MQTT_PWMOutputDevice {} at pin: {} - {}{}{}{}".format(name, pin, active_high, initial_value, frequency, pin_factory))
            #----------------------------------------------------------------------------------------------------------------------------------------------------
            self.GPIOs[name] = mqtt_PWMOutputDevice(self.mqttSender, self.log, name, pin, active_high=active_high, initial_value=initial_value, frequency=frequency, pin_factory=pin_factory)
            self.log.Debug("PWMOutputDevice Created")
        #-----------------------------------------------------------------------------------
        # MQTT_Buzzer
        #-----------------------------------------------------------------------------------
        for ox in oXMLroot.findall('MQTT_Buzzer'):
            name = ox.get('name')
            pin = int(ox.get('pin'))
            #-----------------------------
            oXMLStatic = ox.find('Static')
            if not oXMLStatic == None:
                active_high     = str_to_bool(oXMLStatic.get('active_high'))
                initial_value   = str_to_bool(oXMLStatic.get('initial_value'))
                pin_factory     = isstrNone(oXMLStatic.get('pin_factory'))
            else:
                active_high     = True
                initial_value   = False
                pin_factory     = None
            #----------------------------------------------------------------------------------------------------------------------------------------------------
            self.log.Info("MQTT_Buzzer {} at pin: {} - {}{}{}".format(name, pin, active_high, initial_value, pin_factory))
            #----------------------------------------------------------------------------------------------------------------------------------------------------
            self.GPIOs[name] = mqtt_Buzzer(self.mqttSender, self.log, name, pin, active_high=active_high, initial_value=initial_value, pin_factory=pin_factory)
            self.log.Debug("MQTT_Buzzer Created")
        #-----------------------------------------------------------------------------------
        # MQTT_TonalBuzzer
        #-----------------------------------------------------------------------------------
        for ox in oXMLroot.findall('MQTT_TonalBuzzer'):
            name = ox.get('name')
            pin = int(ox.get('pin'))
            #-----------------------------
            oXMLStatic = ox.find('Static')
            if not oXMLStatic == None:
                pin_factory     = isstrNone(oXMLStatic.get('pin_factory'))
            else:
                pin_factory     = None
            #-----------------------------
            oXMLStatic = ox.find('ToneSpec')
            if not oXMLStatic == None:
                initial_value   = isstrNone(oXMLStatic.get('initial_value'))
                mid_tone        = oXMLStatic.get('mid_tone')
                octaves         = int(oXMLStatic.get('octaves'))
            else:
                initial_value   = None
                mid_tone = "A4"
                octaves = 1
            #----------------------------------------------------------------------------------------------------------------------------------------------------
            self.log.Info("MQTT_TonalBuzzer {} at pin: {} - {}{} mid_tone:{} octaves{}".format(name, pin, initial_value, pin_factory, mid_tone, octaves))
            #----------------------------------------------------------------------------------------------------------------------------------------------------
            self.GPIOs[name] = mqtt_TonalBuzzer(self.mqttSender, self.log, name, pin, initial_value=initial_value, mid_tone=mid_tone, octaves=octaves, pin_factory=pin_factory)
            self.log.Debug("MQTT_TonalBuzzer Created")
        #-----------------------------------------------------------------------------------
        # MQTT_Motor
        #-----------------------------------------------------------------------------------
        for ox in oXMLroot.findall('MQTT_Motor'):
            name = ox.get('name')
            forward = int(ox.get('forward'))
            backward = int(ox.get('backward'))
            enable = IntorNone(ox.get('enable'))
            pwm = str_to_bool(ox.get('pwm'))
            #-----------------------------
            oXMLStatic = ox.find('Static')
            if not oXMLStatic == None:
                pin_factory     = isstrNone(oXMLStatic.get('pin_factory'))
            else:
                pin_factory     = None
            #----------------------------------------------------------------------------------------------------------------------------------------------------
            self.log.Info("MQTT_Motor {} at pin: {}{}{} - {}{}".format(name, forward, backward, enable, pin_factory, pwm))
            #----------------------------------------------------------------------------------------------------------------------------------------------------
            self.GPIOs[name] = mqtt_Motor(self.mqttSender, self.log, name, forward, backward, enable, pwm=pwm, pin_factory=pin_factory)
            self.log.Debug("MQTT_Motor Created")
        
        #-----------------------------------------------------------------------------------
        # MQTT_Rover
        #-----------------------------------------------------------------------------------
        for ox in oXMLroot.findall('MQTT_Rover'):
            pass


        
        
        
        #-----------------------------------------------------------------------------------
        # MQTT_PhaseEnableMotor
        #-----------------------------------------------------------------------------------
        for ox in oXMLroot.findall('MQTT_PhaseEnableMotor'):
            name = ox.get('name')
            phase = int(ox.get('phase'))
            enable = int(ox.get('enable'))
            pwm = str_to_bool(ox.get('pwm'))
            #-----------------------------
            oXMLStatic = ox.find('Static')
            if not oXMLStatic == None:
                active_high     = str_to_bool(oXMLStatic.get('active_high'))
                pin_factory     = isstrNone(oXMLStatic.get('pin_factory'))
            else:
                active_high     = True
                pin_factory     = None
            #----------------------------------------------------------------------------------------------------------------------------------------------------
            self.log.Info("MQTT_PhaseEnableMotor {} at pin: {}{} - {}{}{}".format(name, phase, enable, active_high, pin_factory, pwm))
            #----------------------------------------------------------------------------------------------------------------------------------------------------
            self.GPIOs[name] = mqtt_PhaseEnableMotor(self.mqttSender, self.log, name, phase, enable, pwm=pwm, active_high=active_high, pin_factory=pin_factory)
            self.log.Debug("MQTT_PhaseEnableMotor Created")
        #-----------------------------------------------------------------------------------
        # MQTT_Servo
        #-----------------------------------------------------------------------------------
        for ox in oXMLroot.findall('MQTT_Servo'):
            name = ox.get('name')
            pin = int(ox.get('pin'))
            initial_value = float(ox.get('initial_value'))
            min_pulse_width = float(ox.get('min_pulse_width'))
            max_pulse_width = float(ox.get('max_pulse_width'))
            frame_width = float(ox.get('frame_width'))
            #-----------------------------
            oXMLStatic = ox.find('Static')
            if not oXMLStatic == None:
                active_high     = str_to_bool(oXMLStatic.get('active_high'))
                pin_factory     = isstrNone(oXMLStatic.get('pin_factory'))
            else:
                active_high     = True
                pin_factory     = None
            #----------------------------------------------------------------------------------------------------------------------------------------------------
            self.log.Info("MQTT_Servo {} at pin:{} {}{}{}{}{}{}".format(name, pin, initial_value, min_pulse_width, max_pulse_width, frame_width, active_high, pin_factory))
            #----------------------------------------------------------------------------------------------------------------------------------------------------
            self.GPIOs[name] = mqtt_Servo(self.mqttSender, self.log, name, pin, initial_value, min_pulse_width, max_pulse_width, frame_width, active_high=active_high, pin_factory=pin_factory)
            self.log.Debug("MQTT_Servo Created")
        #-----------------------------------------------------------------------------------
        # MQTT_AngularServo
        #-----------------------------------------------------------------------------------
        for ox in oXMLroot.findall('MQTT_AngularServo'):
            name = ox.get('name')
            pin = int(ox.get('pin'))
            initial_angle = float(ox.get('initial_angle'))
            min_angle = float(ox.get('min_angle'))
            max_angle = float(ox.get('max_angle'))
            min_pulse_width = float(ox.get('min_pulse_width'))
            max_pulse_width = float(ox.get('max_pulse_width'))
            frame_width = float(ox.get('frame_width'))
            #-----------------------------
            oXMLStatic = ox.find('Static')
            if not oXMLStatic == None:
                active_high     = str_to_bool(oXMLStatic.get('active_high'))
                pin_factory     = isstrNone(oXMLStatic.get('pin_factory'))
            else:
                active_high     = True
                pin_factory     = None
            #----------------------------------------------------------------------------------------------------------------------------------------------------
            self.log.Info("MQTT_AngularServo {} at pin:{} {}{}{}- {}{}{} - {}{}".format(name, pin, initial_angle, min_angle, max_angle, min_pulse_width, max_pulse_width, frame_width, active_high, pin_factory))
            #----------------------------------------------------------------------------------------------------------------------------------------------------
            self.GPIOs[name] = mqtt_AngularServo(self.mqttSender, self.log, name, pin, initial_angle, min_angle, max_angle, min_pulse_width, max_pulse_width, frame_width, active_high=active_high, pin_factory=pin_factory)
            self.log.Debug("MQTT_AngularServo Created")
        #-----------------------------------------------------------------------------------
        # MQTT_DigitalOutputDevice
        #-----------------------------------------------------------------------------------
        for ox in oXMLroot.findall('MQTT_DigitalOutputDevice'):
            name = ox.get('name')
            pin = int(ox.get('pin'))
            #-----------------------------
            oXMLStatic = ox.find('Static')
            if not oXMLStatic == None:
                active_high     = str_to_bool(oXMLStatic.get('active_high'))
                initial_value   = str_to_bool_or_None(oXMLStatic.get('initial_value'))
                pin_factory     = isstrNone(oXMLStatic.get('pin_factory'))
            else:
                active_high     = True
                initial_value   = False
                pin_factory     = None
            #----------------------------------------------------------------------------------------------------------------------------------------------------
            self.log.Info("MQTT_DigitalOutputDevice {} at pin: {} - {}{}{}".format(name, pin, active_high, initial_value, pin_factory))
            #----------------------------------------------------------------------------------------------------------------------------------------------------
            self.GPIOs[name] = mqtt_DigitalOutputDevice(self.mqttSender, self.log, name, pin, active_high=active_high, initial_value=initial_value, pin_factory=pin_factory)
            self.log.Debug("MQTT_DigitalOutputDevice Created")
        #-----------------------------------------------------------------------------------
        # MQTT_OutputDevice
        #-----------------------------------------------------------------------------------
        for ox in oXMLroot.findall('MQTT_OutputDevice'):
            name = ox.get('name')
            pin = int(ox.get('pin'))
            #-----------------------------
            oXMLStatic = ox.find('Static')
            if not oXMLStatic == None:
                active_high     = str_to_bool(oXMLStatic.get('active_high'))
                initial_value   = str_to_bool_or_None(oXMLStatic.get('initial_value'))
                pin_factory     = isstrNone(oXMLStatic.get('pin_factory'))
            else:
                active_high     = True
                initial_value   = False
                pin_factory     = None
            #----------------------------------------------------------------------------------------------------------------------------------------------------
            self.log.Info("MQTT_OutputDevice {} at pin: {} - {}{}{}".format(name, pin, active_high, initial_value, pin_factory))
            #----------------------------------------------------------------------------------------------------------------------------------------------------
            self.GPIOs[name] = mqtt_OutputDevice(self.mqttSender, self.log, name, pin, active_high=active_high, initial_value=initial_value, pin_factory=pin_factory)
            self.log.Debug("MQTT_OutputDevice Created")
        #-----------------------------------------------------------------------------------
        # MQTT_SoundMixer
        #-----------------------------------------------------------------------------------
        for ox in oXMLroot.findall('MQTT_SoundMixer'):
            name = ox.get('name')
            #-----------------------------
            oXMLStatic = ox.find('Static')
            if not oXMLStatic == None:
                nbr_of_channels = int(oXMLStatic.get('nbr_of_channels'))
                frequency       = int(oXMLStatic.get('frequency'))
                size            = int(oXMLStatic.get('size'))
                mono_or_stereo  = int(oXMLStatic.get('mono_or_stereo'))     # stereo:1, mono:0
                buffer_size     = int(oXMLStatic.get('buffer_size'))
            else:
                nbr_of_channels = 6
                frequency       = 48000
                size            = -16
                mono_or_stereo  = 1     # stereo:1, mono:0
                buffer_size     = 1024
            #----------------------------------------------------------------------------------------------------------------------------------------------------
            self.log.Info("MQTT_SoundMixer {} nbrCH:{}, Freq:{}, size:{}, stereo:{}, buffersize:{}".format(name, nbr_of_channels, frequency, size, mono_or_stereo, buffer_size))
            #----------------------------------------------------------------------------------------------------------------------------------------------------
            self.GPIOs[name] = mqtt_SoundMixer(self.mqttSender, self.log, name, nbr_of_channels, frequency, size, mono_or_stereo, buffer_size)
            self.log.Debug("MQTT_SoundMixer Created")
        #-----------------------------------------------------------------------------------
        # MQTT_2x16_lcd_I2C
        #-----------------------------------------------------------------------------------
        for ox in oXMLroot.findall('MQTT_2x16_lcd_I2C'):
            name = ox.get('name')
            address = int(ox.get('address'),16)
            #----------------------------------------------------------------------------------------------------------------------------------------------------
            self.log.Info("MQTT_2x16_lcd_I2C {} at address {}".format(name, address))
            #----------------------------------------------------------------------------------------------------------------------------------------------------
            self.GPIOs[name] = mqtt_2x16_lcd_I2C(self.mqttSender, self.log, name, address)
            self.log.Debug("MQTT_2x16_lcd_I2C Created")
        #-----------------------------------------------------------------------------------
        #-----------------------------------------------------------------------------------
        # End of outputs ... Add custom ones here                             ****MIKEOUTPUT
        #-----------------------------------------------------------------------------------
        #-----------------------------------------------------------------------------------




        #-----------------------------------------------------------------------------------
        # Now that ALL Inputs and Outputs are defined ... we can connect their source    DOES NOT SEEMS TO WORK ... caliss
        #-----------------------------------------------------------------------------------
        SCP.ExcecuteSimpleConnect(oXMLroot, self.log, self.GPIOs)
        SCP.ExecuteMultiConnect(oXMLroot, self.log, self.GPIOs)
        #-----------------------------------------------------------------------------------






        #-----------------------------------------------------------------------------------
        #-----------------------------------------------------------------------------------
        #-----------------------------------------------------------------------------------
        # XML file done, now deal with MQTT CALLBACKs
        #-----------------------------------------------------------------------------------
        #-----------------------------------------------------------------------------------
        #-----------------------------------------------------------------------------------
        self.log.Info("Creating the MQTT client and associate the callbacks ...")
        #----------------------------------------------------------------------------------
        # Create the MQTT client using version 3.1.1 and associate its callbacks
        #----------------------------------------------------------------------------------
        self.MQTT_client = mqtt.Client(protocol=mqtt.MQTTv311)
        self.MQTT_client.on_connect = self.on_connect_MQTT
        self.MQTT_client.on_subscribe = self.on_subscribe_MQTT
        #----------------------------------------------------------------------------------------------------------------------------
        # for the IoTcpu ... /HEART, /HALT, /REBOOT, /PROGREBOOT, 
        #                   /SEND/XML, 
        #                   /SEND/SYSINFO, /SEND/TEMPERATURE, /SEND/DISKINFO, /SEND/MEMINFO
        #----------------------------------------------------------------------------------------------------------------------------
        self.MQTT_client.message_callback_add("/HEART/{}/{}".format(self.room, self.IoTcpu),                self.on_heartbeat)
        self.log.Debug("added callback for /HEART/{}/{}".format(self.room, self.IoTcpu))
        #----------------------------------------------------------------------------------------------------------------------------
        self.MQTT_client.message_callback_add("/HALT/{}/ALL".format(self.room),                             self.on_halt_all)
        self.log.Debug("added callback for /HALT/{}/ALL".format(self.room))
        self.MQTT_client.message_callback_add("/HALT/{}/{}".format(self.room, self.IoTcpu),                 self.on_halt_me)
        self.log.Debug("added callback for /HALT/{}/{}".format(self.room, self.IoTcpu))
        #----------------------------------------------------------------------------------------------------------------------------
        self.MQTT_client.message_callback_add("/REBOOT/{}/ALL".format(self.room),                           self.on_reboot_all)
        self.log.Debug("added callback for /REBOOT/{}/ALL".format(self.room))
        self.MQTT_client.message_callback_add("/REBOOT/{}/{}".format(self.room, self.IoTcpu),               self.on_reboot_me)
        self.log.Debug("added callback for /REBOOT/{}/{}".format(self.room, self.IoTcpu))
        #----------------------------------------------------------------------------------------------------------------------------
        self.MQTT_client.message_callback_add("/PROGREBOOT/ACTIVATEM/{}/{}".format(self.room, self.IoTcpu), self.on_progreboot_M)
        self.log.Debug("added callback for /PROGREBOOT/ACTIVATEM/{}/{}".format(self.room, self.IoTcpu))
        #----------------------------------------------------------------------------------------------------------------------------
        self.MQTT_client.message_callback_add("/PROGREBOOT/ACTIVATET/{}/{}".format(self.room, self.IoTcpu), self.on_progreboot_T)
        self.log.Debug("added callback for /PROGREBOOT/ACTIVATET/{}/{}".format(self.room, self.IoTcpu))
        #----------------------------------------------------------------------------------------------------------------------------
        self.MQTT_client.message_callback_add("/PROGREBOOT/CANCEL/{}/{}".format(self.room, self.IoTcpu),    self.on_progreboot_cancel)
        self.log.Debug("added callback for /PROGREBOOT/CANCEL/{}/{}".format(self.room, self.IoTcpu))
        #----------------------------------------------------------------------------------------------------------------------------
        self.MQTT_client.message_callback_add("/SEND/XML/{}/ALL".format(self.room),                         self.on_send_xml_all)
        self.log.Debug("added callback for /SEND/XML/{}/ALL".format(self.room))
        self.MQTT_client.message_callback_add("/SEND/XML/{}/{}".format(self.room, self.IoTcpu),             self.on_send_xml_me)
        self.log.Debug("added callback for /SEND/XML/{}/{}".format(self.room, self.IoTcpu))
        #----------------------------------------------------------------------------------------------------------------------------
        self.MQTT_client.message_callback_add("/SEND/SYSINFO/{}/{}".format(self.room, self.IoTcpu),         self.on_SYSINFO)
        self.log.Debug("added callback for /SEND/SYSINFO/{}/{}".format(self.room, self.IoTcpu))
        #----------------------------------------------------------------------------------------------------------------------------
        self.MQTT_client.message_callback_add("/SEND/TEMPERATURE/{}/{}".format(self.room, self.IoTcpu),     self.on_TEMPERATURE)
        self.log.Debug("added callback for /SEND/TEMPERATURE/{}/{}".format(self.room, self.IoTcpu))
        #----------------------------------------------------------------------------------------------------------------------------
        self.MQTT_client.message_callback_add("/SEND/DISKINFO/{}/{}".format(self.room, self.IoTcpu),        self.on_DISKINFO)
        self.log.Debug("added callback for /SEND/DISKINFO/{}/{}".format(self.room, self.IoTcpu))
        #----------------------------------------------------------------------------------------------------------------------------
        self.MQTT_client.message_callback_add("/SEND/MEMINFO/{}/{}".format(self.room, self.IoTcpu),         self.on_MEMINFO)
        self.log.Debug("added callback for /SEND/MEMINFO/{}/{}".format(self.room, self.IoTcpu))
        #----------------------------------------------------------------------------------------------------------------------------
        #----------------------------------------------------------------------------------------------------------------------------
        #----------------------------------------------------------------------------------------------------------------------------
        #----------------------------------------------------------------------------------------------------------------------------
        #----------------------------------------------------------------------------------------------------------------------------
        # loop on the dictionnary items to add the callbacks 1- SEND/VAL/ and all OUT widgets
        #----------------------------------------------------------------------------------------------------------------------------
        #----------------------------------------------------------------------------------------------------------------------------
        #----------------------------------------------------------------------------------------------------------------------------
        #----------------------------------------------------------------------------------------------------------------------------
        #----------------------------------------------------------------------------------------------------------------------------
        for name in self.GPIOs:
            #----------------------------------------------------------------------------------------------------------------------------
            # for all widgets, add a callback to listen to SEND/VAL specific to itself
            #----------------------------------------------------------------------------------------------------------------------------
            self.MQTT_client.message_callback_add("/SEND/VAL/{}/{}".format(self.room, name),                self.GPIOs[name].on_GetValue)
            self.log.Debug("added callback for /SEND/VAL/{}/{}".format(self.room, name))
            #----------------------------------------------------------------------------------------------------------------------------
            #----------------------------------------------------------------------------------------------------------------------------
            # For the INPUTs and OUTPUTs, query functions on their status beside its value
            #----------------------------------------------------------------------------------------------------------------------------
            #----------------------------------------------------------------------------------------------------------------------------
            if self.GPIOs[name].type == "MQTT_Button":
                self.MQTT_client.message_callback_add("/SEND/HELDTIME/{}/{}".format(self.room, name),       self.GPIOs[name].on_Held_Time)
                self.log.Debug("added callback for /SEND/HELDTIME/{}/{}".format(self.room, name))
                self.MQTT_client.message_callback_add("/SEND/ISHELD/{}/{}".format(self.room, name),         self.GPIOs[name].on_Is_Held)
                self.log.Debug("added callback for /SEND/ISHELD/{}/{}".format(self.room, name))
                self.MQTT_client.message_callback_add("/SEND/ISPRESSED/{}/{}".format(self.room, name),      self.GPIOs[name].on_Is_Pressed)
                self.log.Debug("added callback for /SEND/ISPRESSED/{}/{}".format(self.room, name))
            #----------------------------------------------------------------------------------------------------------------------------
            if self.GPIOs[name].type == "MQTT_DigitalInputDevice":
                self.MQTT_client.message_callback_add("/SEND/ACTIVETIME/{}/{}".format(self.room, name),     self.GPIOs[name].on_Active_Time)
                self.log.Debug("added callback for /SEND/ACTIVETIME/{}/{}".format(self.room, name))
                self.MQTT_client.message_callback_add("/SEND/INACTIVETIME/{}/{}".format(self.room, name),   self.GPIOs[name].on_Inactive_Time)
                self.log.Debug("added callback for /SEND/INACTIVETIME/{}/{}".format(self.room, name))
            #----------------------------------------------------------------------------------------------------------------------------
            if self.GPIOs[name].type == "MQTT_LightSensor":
                self.MQTT_client.message_callback_add("/SEND/LIGHTDETECTED/{}/{}".format(self.room, name),   self.GPIOs[name].on_Light_Detected)
                self.log.Debug("added callback for /SEND/LIGHTDETECTED/{}/{}".format(self.room, name))
            #----------------------------------------------------------------------------------------------------------------------------
            if self.GPIOs[name].type == "MQTT_MotionSensor":
                self.MQTT_client.message_callback_add("/SEND/MOTIONDETECTED/{}/{}".format(self.room, name),   self.GPIOs[name].on_Motion_Detected)
                self.log.Debug("added callback for /SEND/MOTIONDETECTED/{}/{}".format(self.room, name))
            #----------------------------------------------------------------------------------------------------------------------------
            if self.GPIOs[name].type == "MQTT_DistanceSensor":
                self.MQTT_client.message_callback_add("/SEND/DISTANCE/{}/{}".format(self.room, name),   self.GPIOs[name].on_Distance)
                self.log.Debug("added callback for /SEND/DISTANCE/{}/{}".format(self.room, name))
            #----------------------------------------------------------------------------------------------------------------------------
            Implemented_1_function = ["MQTT_LED", "MQTT_RGBLED", "MQTT_PWMLED"]
            if self.GPIOs[name].type in Implemented_1_function:
                self.MQTT_client.message_callback_add("/{}/{}/{}".format("SEND/ISLIT", self.room, name),     self.GPIOs[name].on_Is_Lit)
                self.log.Debug("added callback for /{}/{}/{}".format("SEND/ISLIT", self.room, name))
            #----------------------------------------------------------------------------------------------------------------------------
            Implemented_1_function = ["MQTT_Buzzer", "MQTT_TonalBuzzer", "MQTT_Motor", "MQTT_PhaseEnableMotor", "MQTT_Servo", "MQTT_AngularServo", "MQTT_PWMOutputDevice"]
            if self.GPIOs[name].type in Implemented_1_function:
                self.MQTT_client.message_callback_add("/{}/{}/{}".format("SEND/ISACTIVE", self.room, name),     self.GPIOs[name].on_Is_Active)
                self.log.Debug("added callback for /{}/{}/{}".format("SEND/ISACTIVE", self.room, name))
            #----------------------------------------------------------------------------------------------------------------------------
            if self.GPIOs[name].type == "MQTT_PWMOutputDevice":
                self.MQTT_client.message_callback_add("/{}/{}/{}".format("SEND/FREQUENCY", self.room, name),     self.GPIOs[name].on_Frequency)
                self.log.Debug("added callback for /{}/{}/{}".format("SEND/FREQUENCY", self.room, name))
            #----------------------------------------------------------------------------------------------------------------------------
            #----------------------------------------------------------------------------------------------------------------------------
            # Now for all OUTPUT widget types defined ... Add their ACTIONS ...
            #----------------------------------------------------------------------------------------------------------------------------
            #----------------------------------------------------------------------------------------------------------------------------
            #----------------------------------------------------------------------------------------------------------------------------
            # MQTT_LED : ON, OFF, TOGGLE, BLINK
            #----------------------------------------------------------------------------------------------------------------------------
            if self.GPIOs[name].type == "MQTT_LED":
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "ON"),        self.GPIOs[name].on_ON)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "ON"))
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "OFF"),       self.GPIOs[name].on_OFF)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "OFF"))
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "TOGGLE"),    self.GPIOs[name].on_TOGGLE)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "TOGGLE"))
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "BLINK"),     self.GPIOs[name].on_BLINK)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "BLINK"))
            #----------------------------------------------------------------------------------------------------------------------------
            # MQTT_RGBLED, MQTT_PWMLED, PWMOutputDevice : ON, OFF, TOGGLE, BLINK, PULSE
            #----------------------------------------------------------------------------------------------------------------------------
            Implemented_5_functions = ["MQTT_RGBLED","MQTT_PWMLED","PWMOutputDevice"]
            if self.GPIOs[name].type in Implemented_5_functions:
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "ON"),        self.GPIOs[name].on_ON)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "ON"))
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "OFF"),       self.GPIOs[name].on_OFF)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "OFF"))
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "TOGGLE"),    self.GPIOs[name].on_TOGGLE)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "TOGGLE"))
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "BLINK"),     self.GPIOs[name].on_BLINK)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "BLINK"))
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "PULSE"),     self.GPIOs[name].on_PULSE)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "PULSE"))
            if self.GPIOs[name].type == "MQTT_RGBLED":
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "COLOR"),        self.GPIOs[name].on_COLOR)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "COLOR"))
            #----------------------------------------------------------------------------------------------------------------------------
            # MQTT_Buzzer : ON, OFF, TOGGLE, BEEP
            #----------------------------------------------------------------------------------------------------------------------------
            if self.GPIOs[name].type == "MQTT_Buzzer":
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "ON"),        self.GPIOs[name].on_ON)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "ON"))
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "OFF"),       self.GPIOs[name].on_OFF)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "OFF"))
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "TOGGLE"),    self.GPIOs[name].on_TOGGLE)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "TOGGLE"))
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "BEEP"),      self.GPIOs[name].on_BEEP)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "BEEP"))
            #----------------------------------------------------------------------------------------------------------------------------
            # MQTT_TonalBuzzer : PLAY(tone), STOP
            #----------------------------------------------------------------------------------------------------------------------------
            if self.GPIOs[name].type == "MQTT_TonalBuzzer":
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "PLAY"),      self.GPIOs[name].on_PLAY)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "PLAY"))
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "STOP"),      self.GPIOs[name].on_STOP)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "STOP"))
            #----------------------------------------------------------------------------------------------------------------------------
            # MQTT_Motor, MQTT_PhaseEnableMotor : FORWARD, BACKWARD, REVERSE, STOP 
            #----------------------------------------------------------------------------------------------------------------------------
            Implemented_4_functions = ["MQTT_Motor","MQTT_PhaseEnableMotor"]
            if self.GPIOs[name].type in Implemented_4_functions:
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "FORWARD"),   self.GPIOs[name].on_FORWARD)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "FORWARD"))
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "BACKWARD"),  self.GPIOs[name].on_BACKWARD)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "BACKWARD"))
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "REVERSE"),   self.GPIOs[name].on_REVERSE)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "REVERSE"))
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "STOP"),      self.GPIOs[name].on_STOP)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "STOP"))



            #----------------------------------------------------------------------------------------------------------------------------
            # MQTT_Rover : Move_Straight, Move_Sideways, Move_U_Turn, Move_Diagonal, Move_TurnOfRearAxis, Move_Concerning, Stop
            #----------------------------------------------------------------------------------------------------------------------------
            # ~ Move_Straight("Forward", 0.5)
            # ~ Move_Sideways("Right", 0.5)
            # ~ Move_U_Turn("Clockwise", 0.5)
            # ~ Move_Diagonal("Forward", "Right", 0.5)
            # ~ Move_TurnOfRearAxis("Bottom", "Clockwise", 0.5)
            # ~ Move_Concerning("Right", "Forward", 0.5)
            # ~ Stop()



            #----------------------------------------------------------------------------------------------------------------------------
            # MQTT_Servo : DETACH, MIN, MID, MAX
            #----------------------------------------------------------------------------------------------------------------------------
            if self.GPIOs[name].type == "MQTT_Servo":
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name,"DETACH"), self.GPIOs[name].on_DETACH)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "DETACH"))
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "MIN"),   self.GPIOs[name].on_MIN)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "MIN"))
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "MID"),   self.GPIOs[name].on_MID)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "MID"))
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "MAX"),   self.GPIOs[name].on_MAX)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "MAX"))
                #--------------------------------------------------------------------------------------------------------------------
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "SETVALUE"),   self.GPIOs[name].on_SetValue)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "SETVALUE"))
                #--------------------------------------------------------------------------------------------------------------------
            #----------------------------------------------------------------------------------------------------------------------------
            # MQTT_AngularServo : ANGLE, MIN, MID, MAX
            #----------------------------------------------------------------------------------------------------------------------------
            if self.GPIOs[name].type == "MQTT_AngularServo":
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "MIN"),   self.GPIOs[name].on_MIN)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "MIN"))
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "MID"),   self.GPIOs[name].on_MID)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "MID"))
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "MAX"),   self.GPIOs[name].on_MAX)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "MAX"))
                #--------------------------------------------------------------------------------------------------------------------
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "ANGLE"),   self.GPIOs[name].on_ANGLE)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "ANGLE"))
                #--------------------------------------------------------------------------------------------------------------------
            #----------------------------------------------------------------------------------------------------------------------------
            # MQTT_DigitalOutputDevice : ON, OFF, BLINK
            #----------------------------------------------------------------------------------------------------------------------------
            if self.GPIOs[name].type == "MQTT_DigitalOutputDevice":
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "ON"),        self.GPIOs[name].on_ON)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "ON"))
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "OFF"),       self.GPIOs[name].on_OFF)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "OFF"))
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "BLINK"),     self.GPIOs[name].on_BLINK)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "BLINK"))
            #----------------------------------------------------------------------------------------------------------------------------
            # MQTT_OutputDevice : ON, OFF, TOGGLE
            #----------------------------------------------------------------------------------------------------------------------------
            if self.GPIOs[name].type == "MQTT_OutputDevice":
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "ON"),        self.GPIOs[name].on_ON)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "ON"))
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "OFF"),       self.GPIOs[name].on_OFF)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "OFF"))
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "TOGGLE"),    self.GPIOs[name].on_TOGGLE)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "TOGGLE"))
            #----------------------------------------------------------------------------------------------------------------------------
            # MQTT_SoundMixer : PLAY, PAUSE, UNPAUSE, STOP
            #----------------------------------------------------------------------------------------------------------------------------
            if self.GPIOs[name].type == "MQTT_SoundMixer":
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "PLAY"),      self.GPIOs[name].on_PLAY)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "PLAY"))
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "PAUSE"),     self.GPIOs[name].on_PAUSE)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "PAUSE"))
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "UNPAUSE"),   self.GPIOs[name].on_UNPAUSE)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "UNPAUSE"))
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "STOP"),      self.GPIOs[name].on_STOP)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "STOP"))
            #----------------------------------------------------------------------------------------------------------------------------
            # MQTT_2x16_lcd_I2C : CLEAR, BACKLIT, DISPLAYATLINE, DISPLAYATLINECOL, LOADCUSTOMCHAR
            #----------------------------------------------------------------------------------------------------------------------------
            if self.GPIOs[name].type == "MQTT_2x16_lcd_I2C":
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "CLEAR"),             self.GPIOs[name].on_CLEAR)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "CLEAR"))
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "BACKLIT"),           self.GPIOs[name].on_BACKLIT)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "BACKLIT"))
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "DISPLAYATLINE"),     self.GPIOs[name].on_DISPLAYTHISATTHATLINE)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "DISPLAYATLINE"))
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "DISPLAYATLINECOL"),  self.GPIOs[name].on_DISPLAYTHISATTHATPOSITION)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "DISPLAYATLINECOL"))
                self.MQTT_client.message_callback_add("/OUT/{}/{}/{}".format(self.room, name, "LOADCUSTOMCHAR"),    self.GPIOs[name].on_LCDLOADCUSTOMCHARS)
                self.log.Debug("added callback for /OUT/{}/{}/{}".format(self.room, name, "LOADCUSTOMCHAR"))
            #----------------------------------------------------------------------------------------------------------------------------
            #----------------------------------------------------------------------------------------------------------------------------
            # END of Output listening callbacks, add customs one here                                                      ****MIKEOUTPUT
            #----------------------------------------------------------------------------------------------------------------------------
            #----------------------------------------------------------------------------------------------------------------------------


            #----------------------------------------------------------------------------------------------------------------------------
            #----------------------------------------------------------------------------------------------------------------------------
            #----------------------------------------------------------------------------------------------------------------------------
        #---------------------------------------------
        self.log.Info("Ready to call MQTTconnectNow")
        #---------------------------------------------
    #---------------------------------------------------------------------------------------------------
    # INTERNAL CLASS FUNCTIONS 
    #---------------------------------------------------------------------------------------------------
    #   _BuildTimestampDict
    #   BuildJSONPayload
    #   mqttSender
    #---------------------------------------------------------------------------------------------------
        # on_send_xml_all
        # on_send_xml_me
        # on_halt_all
        # on_halt_me
        # on_reboot_all
        # on_reboot_me
        # on_progreboot_cancel
        # on_progreboot_M
        # on_progreboot_T
    #---------------------------------------------------------------------------------------------------
        # on_SYSINFO
        # on_TEMPERATURE
        # on_DISKINFO
        # on_MEMINFO
    #---------------------------------------------------------------------------------------------------
        # on_connect_MQTT
        # on_subscribe_MQTT
        # MQTTconnectNow
    #---------------------------------------------------------------------------------------------------
    #---------------------------------------------------------------------------------------------------
    # MQTT Payload Timestamp function _BuildTimestampDict for sending using json ...
    #---------------------------------------------------------------------------------------------------
    #---------------------------------------------------------------------------------------------------
    def _BuildTimestampDict(self, d):
        rightnow = d
        Y = rightnow.year
        Mo = rightnow.month
        D = rightnow.day
        H = rightnow.hour
        Mi = rightnow.minute
        S = rightnow.second
        X = rightnow.microsecond
        return {"Y":Y,"M":Mo,"D":D,"H":H,"m":Mi,"s":S,"x":X}
    #---------------------------------------------------------------------------------------------------
    # Build JSON Payload ...
    #---------------------------------------------------------------------------------------------------
    def BuildJSONPayload(self, payloadtouse=""):
        d = datetime.datetime.now()
        dDict = self._BuildTimestampDict(d)                          # Build the timestamp dictionnary 
        PayloadDict = {"Timestamp": dDict, "Payload": payloadtouse} # Build the payload dictionnary
        return json.dumps(PayloadDict)                            # json it and return it
    #---------------------------------------------------------------------------------------------------
    #---------------------------------------------------------------------------------------------------
    # Workhorse : mqttSender (IN/OUT/DONE/VAL, who, what, payload)
    #---------------------------------------------------------------------------------------------------
    #---------------------------------------------------------------------------------------------------
    def mqttSender(self, Direction, who, what="", payloadtouse=""):
        jsonPayload = self.BuildJSONPayload(payloadtouse)
        self.MQTT_client.publish(topic="/{}/{}/{}/{}".format(Direction, self.room, who, what), payload=jsonPayload, qos=self.MQTT_qos, retain=False)
        self.log.Info("Published /{}/{}/{}/{} - {}".format(Direction, self.room, who, what, jsonPayload))
    #---------------------------------------------------------------------
    #---------------------------------------------------------------------
    # Global Topics functions : SEND/XML, HEART, HALT, REBOOT, PROGREBOOT
    #---------------------------------------------------------------------
    #---------------------------------------------------------------------
    #------------------------------------------------------
    # on /SEND/XML
    #------------------------------------------------------
    def on_send_xml_all(self, client, userdata, msg):
        self.log.Info("Sending XML, responding to /SEND/XML/{}/ALL".format(self.room))
        self.MQTT_client.publish(topic="/XML/{}/{}".format(self.room, self.IoTcpu), payload=self.sXML, qos=self.MQTT_qos, retain=False)
    def on_send_xml_me(self, client, userdata, msg):
        self.log.Info("Sending XML, responding to /SEND/XML/{}/{}".format(self.room, self.IoTcpu))
        self.MQTT_client.publish(topic="/XML/{}/{}".format(self.room, self.IoTcpu), payload=self.sXML, qos=self.MQTT_qos, retain=False)
    #------------------------------------------------------
    # on /HEART, send /BEAT
    #------------------------------------------------------
    def on_heartbeat(self, client, userdata, msg):
        self.log.Info("Sending BEAT, responding to /HEART/{}/{}".format(self.room, self.IoTcpu))
        jsonPayload = self.BuildJSONPayload("")
        self.MQTT_client.publish(topic="/BEAT/{}/{}".format(self.room, self.IoTcpu), payload=jsonPayload, qos=self.MQTT_qos, retain=False)
    #------------------------------------------------------
    # on HALT
    #------------------------------------------------------
    def on_halt_all(self, client, userdata, msg):
        self.mqttSender("DOING/HALT", self.IoTcpu, "", "")
        time.sleep(SLEEPTIME)
        SystemHalt()
    def on_halt_me(self, client, userdata, msg):
        self.mqttSender("DOING/HALT", self.IoTcpu, "", "")
        time.sleep(SLEEPTIME)
        SystemHalt()
    #------------------------------------------------------
    # on REBOOT
    #------------------------------------------------------
    def on_reboot_all(self, client, userdata, msg):
        self.mqttSender("DOING/REBOOT", self.IoTcpu, "", "")
        time.sleep(SLEEPTIME)
        SystemReboot()
    def on_reboot_me(self, client, userdata, msg):
        self.mqttSender("DOING/REBOOT", self.IoTcpu, "", "")
        time.sleep(SLEEPTIME)
        SystemReboot()
    #------------------------------------------------------
    # on PROGREBOOT
    #------------------------------------------------------
    def on_progreboot_cancel(self, client, userdata, msg):
        self.mqttSender("DOING/PROGREBOOT/CANCEL", self.IoTcpu, "", "")
        time.sleep(SLEEPTIME)
        SystemProgrammedRebootCancel()
    def on_progreboot_M(self, client, userdata, msg):
        # unjson the payload part, get the minutes parameter
        jsonPayload = str(msg.payload.decode("utf-8", "ignore"))
        PayloadDict = json.loads(jsonPayload)
        minutes     = PayloadDict["Payload"]["minutes"]
        self.mqttSender("DOING/PROGREBOOT/MINUTES", self.IoTcpu, "", "")
        time.sleep(SLEEPTIME)
        SystemProgrammedRebootInMinutes(minutes)
    def on_progreboot_T(self, client, userdata, msg):
        # unjson the payload part, get the time parameter
        jsonPayload = str(msg.payload.decode("utf-8", "ignore"))
        PayloadDict = json.loads(jsonPayload)
        timetouse     = PayloadDict["Payload"]["timetouse"]
        self.mqttSender("DOING/PROGREBOOT/TIME", self.IoTcpu, "", "")
        time.sleep(SLEEPTIME)
        SystemProgrammedRebootTime(timetouse)
    #-----------------------------------------------------------------    
    #-----------------------------------------------------------------    
    #-----------------------------------------------------------------    
    # Global System Status functions : Disk, Memory, System, Temp
    #-----------------------------------------------------------------    
    # /SEND/SYSINFO
    # /SEND/TEMPERATURE
    # /SEND/DISKINFO
    # /SEND/MEMINFO
    #-----------------------------------------------------------------    
    #-----------------------------------------------------------------    
    #-----------------------------------------------------------------    
    # on /SEND/SYSINFO ... almost full blown info 
    #-----------------------------------------------------------------    
    def on_SYSINFO(self, client, userdata, msg):
        aDict = RI.getSystemInfoDict()
        jsonPayload = self.BuildJSONPayload(aDict)
        self.MQTT_client.publish(topic="/SYSTATUS/SYSINFO/{}/{}".format(self.room, self.IoTcpu), payload=jsonPayload, qos=self.MQTT_qos, retain=False)
        self.log.Info("responding to /SEND/SYSINFO/{}/{} ---> {}".format(self.room, self.IoTcpu, aDict))
    #-----------------------------------------------------------------    
    # on /SEND/TEMPERATURE
    #-----------------------------------------------------------------    
    def on_TEMPERATURE(self, client, userdata, msg):
        aDict = RI.getTempDict()
        jsonPayload = self.BuildJSONPayload(aDict)
        self.MQTT_client.publish(topic="/SYSTATUS/TEMPERATURE/{}/{}".format(self.room, self.IoTcpu), payload=jsonPayload, qos=self.MQTT_qos, retain=False)
        self.log.Info("responding to /SEND/TEMPERATURE/{}/{} ---> {}".format(self.room, self.IoTcpu, aDict))
    #-----------------------------------------------------------------    
    # on /SEND/DISKINFO ... for / and /boot
    #-----------------------------------------------------------------    
    def on_DISKINFO(self, client, userdata, msg):
        aDict = RI.getDiskDict()
        jsonPayload = self.BuildJSONPayload(aDict)
        self.MQTT_client.publish(topic="/SYSTATUS/DISKINFO/{}/{}".format(self.room, self.IoTcpu), payload=jsonPayload, qos=self.MQTT_qos, retain=False)
        self.log.Info("responding to /SEND/DISKINFO/{}/{} ---> {}".format(self.room, self.IoTcpu, aDict))
    #-----------------------------------------------------------------    
    # on /SEND/MEMINFO ... main and SWAP
    #-----------------------------------------------------------------    
    def on_MEMINFO(self, client, userdata, msg):
        MemDict = RI.getMemDict()
        SWAPDict = RI.getSWAPDict()
        aDict = {"Memory": MemDict, "SWAP": SWAPDict}
        jsonPayload = self.BuildJSONPayload(aDict)
        self.MQTT_client.publish(topic="/SYSTATUS/MEMINFO/{}/{}".format(self.room, self.IoTcpu), payload=jsonPayload, qos=self.MQTT_qos, retain=False)
        self.log.Info("responding to /SEND/MEMINFO/{}/{} ---> {}".format(self.room, self.IoTcpu, aDict))
    #----------------------------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------------
    # on_connect_MQTT callback
    #----------------------------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------------
    def on_connect_MQTT(self, client, userdata, flags, rc):
        self.log.Info("MQTT Connection results : {}".format(mqtt.connack_string(rc)))
        # Check whether the result from connect is the CONNACK_ACCEPTED connack code
        if rc == mqtt.CONNACK_ACCEPTED:
            #----------------------------------------------------------------------
            # Subscribe to a topics related to VAL or CPU (HALT, REBOOT, XML, ...)
            #----------------------------------------------------------------------
            self.log.Info("Subscibing to Global topics")
            #----------------------------------------------------------------------
            client.subscribe("/SEND/+/{}/+".format(self.room, self.IoTcpu), qos=self.MQTT_qos)    
            self.log.Debug("subscribed to /SEND/+/{}/+".format(self.room, self.IoTcpu))
           #----------------------------------------------------------------------
            client.subscribe("/HEART/{}/+".format(self.room, self.IoTcpu), qos=self.MQTT_qos)    
            self.log.Debug("subscribed to /HEART/{}/{}".format(self.room, self.IoTcpu))
           #----------------------------------------------------------------------
            client.subscribe("/HALT/{}/+".format(self.room), qos=self.MQTT_qos)    
            self.log.Debug("subscribed to /HALT/{}/+".format(self.room))
           #----------------------------------------------------------------------
            client.subscribe("/REBOOT/{}/+".format(self.room), qos=self.MQTT_qos)    
            self.log.Debug("subscribed to /REBOOT/{}/+".format(self.room))
            #----------------------------------------------------------------------
            client.subscribe("/PROGREBOOT/ACTIVATEM/{}/{}".format(self.room, self.IoTcpu), qos=self.MQTT_qos)    
            self.log.Debug("subscribed to /PROGREBOOT/ACTIVATEM/{}/{}".format(self.room, self.IoTcpu))
            client.subscribe("/PROGREBOOT/ACTIVATET/{}/{}".format(self.room, self.IoTcpu), qos=self.MQTT_qos)    
            self.log.Debug("subscribed to /PROGREBOOT/ACTIVATET/{}/{}".format(self.room, self.IoTcpu))
            client.subscribe("/PROGREBOOT/CANCEL/{}/{}".format(self.room, self.IoTcpu), qos=self.MQTT_qos)    
            self.log.Debug("subscribed to /PROGREBOOT/CANCEL/{}/{}".format(self.room, self.IoTcpu))
            #--------------------------------------------------------------------------------------------
            #--------------------------------------------------------------------------------------------
            #--------------------------------------------------------------------------------------------
            self.log.Info("Subscibing to OUT topics")
            Implemented_OUTs = [
                "MQTT_LED","MQTT_RGBLED","MQTT_PWMLED", "MQTT_PWMOutputDevice",
                "MQTT_Buzzer", "MQTT_TonalBuzzer", "MQTT_Motor", "MQTT_Rover", "MQTT_PhaseEnableMotor",
                "MQTT_Servo", "MQTT_AngularServo", "MQTT_DigitalOutputDevice", "MQTT_OutputDevice",
                "MQTT_SoundMixer", "MQTT_2x16_lcd_I2C"
            ]
            #--------------------------------------------------------------------------------------------
            # add the output classes name in the list above                              *****MIKEOUTPUT
            #--------------------------------------------------------------------------------------------
            for name in self.GPIOs:
                if self.GPIOs[name].type in Implemented_OUTs:
                    client.subscribe("/OUT/{}/{}/+".format(self.room, name), qos=self.MQTT_qos)
                    self.log.Debug("subscribed to /OUT/{}/{}/+".format(self.room, name))
            #--------------------------------------------------------------------------------------------
            #--------------------------------------------------------------------------------------------
            #--------------------------------------------------------------------------------------------
            #--------------------------------------------------------------------------------------------
            self.log.Info("on_connect_MQTT done")
    #----------------------------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------------
    # on_subscribe_MQTT callback
    #----------------------------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------------
    def on_subscribe_MQTT(self, client, userdata, mid, granted_qos):
        self.log.Info("Subscription results : {}".format(granted_qos[0]))
        #self.log.Debug("Subscription results : {}{}{}".format(userdata, mid, granted_qos)) # for testing
    #----------------------------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------------
    # MQTTConnectNow()
    #----------------------------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------------
    def MQTTconnectNow(self):
        self.log.Info("Connecting now to {}:{} keepalive:{}".format(self.MQTT_host, self.MQTT_port, self.MQTT_keepalive))
        self.MQTT_client.connect(host=self.MQTT_host, port=self.MQTT_port, keepalive=self.MQTT_keepalive)
    #----------------------------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------------
    # loop_process()
    #----------------------------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------------
    #----------------------------------------------------------------------------------------------------
    def loop_process(self):
        # this is called by an external program in an action loop. It provides access to automaticaly 
        # - send distance information from HC-SR04 (per time set in the XML)
        # - check if some keypad has been pressed
        #---------------------------------------------------------------
        # For each GPIOs of type MQTT_DistanceSensor or MQTT_4x4Keypad
        #---------------------------------------------------------------
        for name in self.GPIOs:
            #-------------------------------------------------------
            # for each MQTT_DistanceSensor
            #-------------------------------------------------------
            if self.GPIOs[name].type == "MQTT_DistanceSensor":
                #   check if actual time - start_time >= send_every
                #       send distance
                d = time.time()
                elapsed = d - self.GPIOs[name].start_time
                if self.GPIOs[name].send_every is not None:
                    if elapsed >= self.GPIOs[name].send_every:
                        self.GPIOs[name].Send_Distance()
                        self.GPIOs[name].start_time = d
            #---------------------------------------------
            # for each MQTT_4x4Keypad
            #---------------------------------------------
            if self.GPIOs[name].type == "MQTT_4x4Keypad":
                key = self.GPIOs[name].getKey()
                if(key != self.GPIOs[name].NULL):
                    self.GPIOs[name].SendKey()



        
        
        
#****************************************************************************************************************
#****************************************************************************************************************
#****************************************************************************************************************
#                       mqtt_ classes for the gpiozero and home brewed ...
#****************************************************************************************************************
#****************************************************************************************************************
#****************************************************************************************************************
#---------------------------------------------------------
# Basic Input and Output widgets ... Button and LED
#---------------------------------------------------------
#****************************************************************************************************************
#****************************************************************************************************************
#****************************************************************************************************************
# INPUTs
#****************************************************************************************************************
#****************************************************************************************************************
#****************************************************************************************************************
# mqtt_Button
#****************************************************************************************************************
class mqtt_Button():
    def __init__(self, mqttSender, log, name, pin, pull_up=True, active_state=None, bounce_time=None, hold_time=1, hold_repeat=False, pin_factory=None):
        self.mqttSender = mqttSender
        self.name = name
        self.type = "MQTT_Button"
        self.widget = Button(pin=pin, pull_up=pull_up, active_state=active_state, bounce_time=bounce_time, hold_time=hold_time, hold_repeat=hold_repeat, pin_factory=pin_factory)
        self.widget.when_released = self.when_released
        self.widget.when_pressed = self.when_pressed
        self.widget.when_held = self.when_held
        self.log = log
        self.log.Debug("mqtt_Button {} created with gpiozero callbacks".format(self.name))
    #------------------------------------------------------
    def on_GetValue(self, client, userdata, msg):
        PayloadDict = {"Value": self.widget.value}
        self.mqttSender("VAL", self.name, "", PayloadDict)
    #------------------------------------------------------
    def on_Held_Time(self, client, userdata, msg):
        PayloadDict = {"held_time": self.widget.held_time}
        self.mqttSender("STATUS/HELDTIME", self.name, "", PayloadDict)
    #------------------------------------------------------
    def on_Is_Held(self, client, userdata, msg):
        PayloadDict = {"is_held": self.widget.is_held}
        self.mqttSender("STATUS/ISHELD", self.name, "", PayloadDict)
    #------------------------------------------------------
    def on_Is_Pressed(self, client, userdata, msg):
        PayloadDict = {"is_pressed": self.widget.is_pressed}
        self.mqttSender("STATUS/ISPRESSED", self.name, "", PayloadDict)
    #------------------------------------------------------
    def when_pressed(self):
        self.mqttSender("IN", self.name, "PRESSED")
    def when_held(self):
        self.mqttSender("IN", self.name, "HELD")
    def when_released(self):
        self.mqttSender("IN", self.name, "RELEASED")
#****************************************************************************************************************
# mqtt_DigitalInputDevice`
#****************************************************************************************************************
class mqtt_DigitalInputDevice():
    active_instance = None
    def __init__(self, mqttSender, log, name, pin, pull_up=True, active_state=None, bounce_time=None, hold_time=1, hold_repeat=False, pin_factory=None):
        self.mqttSender = mqttSender
        self.name = name
        self.type = "MQTT_DigitalInputDevice"
        self.widget = DigitalInputDevice(pin=pin, pull_up=pull_up, active_state=active_state, bounce_time=bounce_time, pin_factory=pin_factory)
        self.widget.when_activated = self.when_activated
        self.widget.when_deactivated = self.when_deactivated
        self.log = log
        self.log.Debug("mqtt_DigitalInputDevice {} created with gpiozero callbacks".format(self.name))
    #------------------------------------------------------
    def on_GetValue(self, client, userdata, msg):
        PayloadDict = {"Value": self.widget.value}
        self.mqttSender("VAL", self.name, "", PayloadDict)
    #------------------------------------------------------
    def on_Active_Time(self, client, userdata, msg):
        PayloadDict = {"active_time": self.widget.active_time}
        self.mqttSender("STATUS/ACTIVETIME", self.name, "", PayloadDict)
    #------------------------------------------------------
    def on_Inactive_Time(self, client, userdata, msg):
        PayloadDict = {"inactive_time": self.widget.inactive_time}
        self.mqttSender("STATUS/INACTIVETIME", self.name, "", PayloadDict)
    #------------------------------------------------------
    def when_activated(self):
        self.mqttSender("IN", self.name, "ACTIVATED")
    def when_deactivated(self):
        self.mqttSender("IN", self.name, "DEACTIVATED")
#****************************************************************************************************************
# mqtt_LineSensor
#****************************************************************************************************************
class mqtt_LineSensor():
    def __init__(self, mqttSender, log, name, pin, pull_up=True, active_state=None, queue_len=5, sample_rate=100, threshold=0.5, partial=False, pin_factory=None):
        self.mqttSender = mqttSender
        self.name = name
        self.type = "MQTT_LineSensor"
        self.widget = LineSensor(pin=pin, pull_up=pull_up, active_state=active_state, queue_len=queue_len, sample_rate=sample_rate, threshold=threshold, partial=partial, pin_factory=pin_factory)
        self.widget.when_line = self.when_line
        self.widget.when_no_line = self.when_no_line
        self.log = log
        self.log.Debug("MQTT_LineSensor {} created with gpiozero callbacks".format(self.name))
    #------------------------------------------------------
    def on_GetValue(self, client, userdata, msg):
        PayloadDict = {"Value": self.widget.value}          # returns a float between 0 (black) and 1 (white))
        self.mqttSender("VAL", self.name, "", PayloadDict)
    #------------------------------------------------------
    def when_line(self):
        self.mqttSender("IN", self.name, "LINE")
    def when_no_line(self):
        self.mqttSender("IN", self.name, "NO_LINE")
#****************************************************************************************************************
# mqtt_MotionSensor
#****************************************************************************************************************
class mqtt_MotionSensor():
    def __init__(self, mqttSender, log, name, pin, pull_up=True, active_state=None, queue_len=1, sample_rate=10, threshold=0.5, partial=True, pin_factory=None):
        self.mqttSender = mqttSender
        self.name = name
        self.type = "MQTT_MotionSensor"
        self.widget = MotionSensor(pin=pin, pull_up=pull_up, active_state=active_state, queue_len=queue_len, sample_rate=sample_rate, threshold=threshold, partial=partial, pin_factory=pin_factory)
        self.widget.when_motion = self.when_motion
        self.widget.when_no_motion = self.when_no_motion
        self.log = log
        self.log.Debug("MQTT_MotionSensor {} created with gpiozero callbacks".format(self.name))
    #------------------------------------------------------
    def on_GetValue(self, client, userdata, msg):
        PayloadDict = {"Value": self.widget.value}          # returns a float between 0 (black) and 1 (white) if queue_len > 1
        self.mqttSender("VAL", self.name, "", PayloadDict)
    #------------------------------------------------------
    def on_Motion_Detected(self, client, userdata, msg):
        PayloadDict = {"motion_detected": self.widget.motion_detected}
        self.mqttSender("STATUS/MOTIONDETECTED", self.name, "", PayloadDict)
    #------------------------------------------------------
    def when_motion(self):
        self.mqttSender("IN", self.name, "MOTION")
    def when_no_motion(self):
        self.mqttSender("IN", self.name, "NO_MOTION")
#****************************************************************************************************************
# mqtt_LightSensor
#****************************************************************************************************************
class mqtt_LightSensor():
    def __init__(self, mqttSender, log, name, pin, queue_len=5, charge_time_limit=0.01, threshold=0.1, partial=False, pin_factory=None):
        self.mqttSender = mqttSender
        self.name = name
        self.type = "MQTT_LightSensor"
        self.widget = LightSensor(pin=pin, queue_len=queue_len, charge_time_limit=charge_time_limit, threshold=threshold, partial=partial, pin_factory=pin_factory)
        self.widget.when_light = self.when_light
        self.widget.when_dark = self.when_dark
        self.log = log
        self.log.Debug("MQTT_LightSensor {} created with gpiozero callbacks".format(self.name))
    #------------------------------------------------------
    def on_GetValue(self, client, userdata, msg):
        PayloadDict = {"Value": self.widget.value}          # returns a float between 0 (black) and 1 (white) if queue_len > 1
        self.mqttSender("VAL", self.name, "", PayloadDict)
    #------------------------------------------------------
    def on_Light_Detected(self, client, userdata, msg):
        PayloadDict = {"light_detected": self.widget.light_detected}
        self.mqttSender("STATUS/LIGHTDETECTED", self.name, "", PayloadDict)
    #------------------------------------------------------
    def when_light(self):
        self.mqttSender("IN", self.name, "LIGHT")
    def when_dark(self):
        self.mqttSender("IN", self.name, "DARK")
#****************************************************************************************************************
# mqtt_DistanceSensor
#****************************************************************************************************************
class mqtt_DistanceSensor():
    def __init__(self, mqttSender, log, name, echo, trigger, send_every=None, queue_len=30, max_distance=1, threshold_distance=0.3, partial=False, pin_factory=None):
        self.mqttSender = mqttSender
        self.name = name
        self.type = "MQTT_DistanceSensor"
        #------------------------------------------------
        self.send_every = send_every
        self.original_start_time = time.time()
        self.start_time = self.original_start_time
        #------------------------------------------------
        self.widget = DistanceSensor(echo=echo, trigger=trigger, queue_len=queue_len, max_distance=max_distance, threshold_distance=threshold_distance, partial=partial, pin_factory=pin_factory)
        self.widget.when_in_range = self.when_in_range
        self.widget.when_out_of_range = self.when_out_of_range
        self.log = log
        self.log.Debug("MQTT_DistanceSensor {} created with gpiozero callbacks".format(self.name))
    #------------------------------------------------------
    def on_GetValue(self, client, userdata, msg):
        PayloadDict = {"Value": self.widget.value}          # returns a float between 0 (black) and 1 (white) if queue_len > 1
        self.mqttSender("VAL", self.name, "", PayloadDict)
    #------------------------------------------------------
    def Send_Distance(self):
        PayloadDict = {"distance": self.widget.distance}
        self.mqttSender("STATUS/DISTANCE", self.name, "", PayloadDict)
    #------------------------------------------------------
    def on_Distance(self, client, userdata, msg):
        PayloadDict = {"distance": self.widget.distance}
        self.mqttSender("STATUS/DISTANCE", self.name, "", PayloadDict)
    #------------------------------------------------------
    def when_in_range(self):
        self.mqttSender("IN", self.name, "IN_RANGE")
    def when_out_of_range(self):
        self.mqttSender("IN", self.name, "OUT_OF_RANGE")
#****************************************************************************************************************
#****************************************************************************************************************
#****************************************************************************************************************
##---------------------------------------------------------
## Higher level class ... for selectors ... NOT IMPLEMENTED
##---------------------------------------------------------
## Inputs
#class mqtt_InputDevice(InputDevice):
#class mqtt_GPIODevice(GPIODevice):
#****************************************************************************************************************
#****************************************************************************************************************
#****************************************************************************************************************
# END of gpiozero INPUT classes
#****************************************************************************************************************
#****************************************************************************************************************
#****************************************************************************************************************
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
# Keypad
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
# RFID
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
# USB_GPS
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
# MCP3008
# PressurePlate













#****************************************************************************************************************
#****************************************************************************************************************
#****************************************************************************************************************
# OUTPUTs
#****************************************************************************************************************
#****************************************************************************************************************
#****************************************************************************************************************
# mqtt_LED
#****************************************************************************************************************
class mqtt_LED():
    def __init__(self, mqttSender, log, name, pin, active_high=False, initial_value=0, pin_factory=None):
        self.mqttSender = mqttSender
        self.name = name
        self.type = "MQTT_LED"
        self.widget = LED(pin=pin, active_high=active_high, initial_value=initial_value, pin_factory=pin_factory)
        self.log = log
        self.log.Debug("mqtt_LED {} created with gpiozero callbacks".format(self.name))
    #------------------------------------------------------
    def on_GetValue(self, client, userdata, msg):
        PayloadDict = {"Value": self.widget.value}
        self.mqttSender("VAL", self.name, "", PayloadDict)
    #------------------------------------------------------
    def on_Is_Lit(self, client, userdata, msg):
        PayloadDict = {"is_lit": self.widget.is_lit}
        self.mqttSender("STATUS/ISLIT", self.name, "", PayloadDict)
    #------------------------------------------------------
    def on_ON(self, client, userdata, msg):
        self.widget.on()
        self.mqttSender("DONE", self.name, "ON")
    def on_OFF(self, client, userdata, msg):
        self.widget.off()
        self.mqttSender("DONE", self.name, "OFF")
    def on_TOGGLE(self, client, userdata, msg):
        self.widget.toggle()
        self.mqttSender("DONE", self.name, "TOGGLE")
    def on_BLINK(self, client, userdata, msg):
        # blink(on_time=1, off_time=1, n=None, background=True)
        jsonPayload = str(msg.payload.decode("utf-8", "ignore"))
        PayloadDict = json.loads(jsonPayload)
        on_time     = float(PayloadDict["Payload"]["on_time"])
        off_time    = float(PayloadDict["Payload"]["off_time"])
        n           = IntorNone(PayloadDict["Payload"]["n"])
        background  = str_to_bool(PayloadDict["Payload"]["background"])
        self.widget.blink(on_time=on_time, off_time=off_time, n=n, background=background)
        self.mqttSender("DONE", self.name, "BLINK")
#****************************************************************************************************************
# mqtt_RGBLED
#****************************************************************************************************************
class mqtt_RGBLED():
    def __init__(self, mqttSender, log, name, r, g, b, active_high=True, initial_value=(0,0,0), pwm=True, pin_factory=None):
        self.mqttSender = mqttSender
        self.name = name
        self.type = "MQTT_RGBLED"
        self.widget = RGBLED(red=r, green=g, blue=b, active_high=active_high, initial_value=initial_value, pwm=pwm, pin_factory=pin_factory)
        self.log = log
        self.log.Debug("MQTT_RGBLED {} created with gpiozero callbacks".format(self.name))
    #------------------------------------------------------
    def on_GetValue(self, client, userdata, msg):
        PayloadDict = {"Value": self.widget.value}          # sends a list for the color [0.0, 0.0, 0.0]
        self.mqttSender("VAL", self.name, "", PayloadDict)
    #------------------------------------------------------
    def on_Is_Lit(self, client, userdata, msg):
        PayloadDict = {"is_lit": self.widget.is_lit}
        self.mqttSender("STATUS/ISLIT", self.name, "", PayloadDict)
    #------------------------------------------------------
    def on_ON(self, client, userdata, msg):
        self.widget.on()
        self.mqttSender("DONE", self.name, "ON")
    def on_OFF(self, client, userdata, msg):
        self.widget.off()
        self.mqttSender("DONE", self.name, "OFF")
    def on_TOGGLE(self, client, userdata, msg):
        self.widget.toggle()
        self.mqttSender("DONE", self.name, "TOGGLE")
    def on_COLOR(self, client, userdata, msg):
        jsonPayload = str(msg.payload.decode("utf-8", "ignore"))
        PayloadDict = json.loads(jsonPayload)
        Color     = str_to_tuple(PayloadDict["Payload"]["color"])
        self.widget.color = Color
        self.mqttSender("DONE", self.name, "COLOR")
    def on_BLINK(self, client, userdata, msg):
        # blink(on_time=1, off_time=1, fade_in_time=1, fade_out_time=1, on_color=(1,1,1), off_color=(0,0,0), n=None, background=True)
        jsonPayload = str(msg.payload.decode("utf-8", "ignore"))
        PayloadDict = json.loads(jsonPayload)
        on_time     = float(PayloadDict["Payload"]["on_time"])
        off_time    = float(PayloadDict["Payload"]["off_time"])
        fade_in_time    = float(PayloadDict["Payload"]["fade_in_time"])
        fade_out_time   = float(PayloadDict["Payload"]["fade_out_time"])
        on_color        = str_to_tuple(PayloadDict["Payload"]["on_color"])
        off_color       = str_to_tuple(PayloadDict["Payload"]["off_color"])
        n           = IntorNone(PayloadDict["Payload"]["n"])
        background  = str_to_bool(PayloadDict["Payload"]["background"])
        self.widget.blink(on_time=on_time, off_time=off_time, fade_in_time=fade_in_time, fade_out_time=fade_out_time, on_color=on_color, off_color=off_color, n=n, background=background)
        self.mqttSender("DONE", self.name, "BLINK")
    def on_PULSE(self, client, userdata, msg):
        # pulse(fade_in_time=1, fade_out_time=1, on_color=(1,1,1), off_color=(0,0,0), n=None, background=True)
        jsonPayload     = str(msg.payload.decode("utf-8", "ignore"))
        PayloadDict     = json.loads(jsonPayload)
        fade_in_time    = float(PayloadDict["Payload"]["fade_in_time"])
        fade_out_time   = float(PayloadDict["Payload"]["fade_out_time"])
        on_color        = str_to_tuple(PayloadDict["Payload"]["on_color"])
        off_color       = str_to_tuple(PayloadDict["Payload"]["off_color"])
        n               = IntorNone(PayloadDict["Payload"]["n"])
        background      = str_to_bool(PayloadDict["Payload"]["background"])
        self.widget.pulse(fade_in_time=fade_in_time, fade_out_time=fade_out_time, on_color=on_color, off_color=off_color, n=n, background=background)
        self.mqttSender("DONE", self.name, "PULSE")
#****************************************************************************************************************
# mqtt_PWMLED
#****************************************************************************************************************
class mqtt_PWMLED():
    def __init__(self, mqttSender, log, name, pin, active_high=True, initial_value=0, frequency=100, pin_factory=None):
        self.mqttSender = mqttSender
        self.name = name
        self.type = "MQTT_PWMLED"
        self.widget = PWMLED(pin=pin, active_high=active_high, initial_value=initial_value, frequency=frequency, pin_factory=pin_factory)
        self.log = log
        self.log.Debug("MQTT_PWMLED {} created with gpiozero callbacks".format(self.name))
    #------------------------------------------------------
    def on_GetValue(self, client, userdata, msg):
        PayloadDict = {"Value": self.widget.value}          # sends a float between 0 and 1
        self.mqttSender("VAL", self.name, "", PayloadDict)
    #------------------------------------------------------
    def on_Is_Lit(self, client, userdata, msg):
        PayloadDict = {"is_lit": self.widget.is_lit}
        self.mqttSender("STATUS/ISLIT", self.name, "", PayloadDict)
    #------------------------------------------------------
    def on_ON(self, client, userdata, msg):
        self.widget.on()
        self.mqttSender("DONE", self.name, "ON")
    def on_OFF(self, client, userdata, msg):
        self.widget.off()
        self.mqttSender("DONE", self.name, "OFF")
    def on_TOGGLE(self, client, userdata, msg):
        self.widget.toggle()
        self.mqttSender("DONE", self.name, "TOGGLE")
    def on_BLINK(self, client, userdata, msg):
        # blink(on_time=1, off_time=1, fade_in_time=1, fade_out_time=1, n=None, background=True)
        jsonPayload = str(msg.payload.decode("utf-8", "ignore"))
        PayloadDict = json.loads(jsonPayload)
        on_time     = float(PayloadDict["Payload"]["on_time"])
        off_time    = float(PayloadDict["Payload"]["off_time"])
        fade_in_time    = float(PayloadDict["Payload"]["fade_in_time"])
        fade_out_time   = float(PayloadDict["Payload"]["fade_out_time"])
        n           = IntorNone(PayloadDict["Payload"]["n"])
        background  = str_to_bool(PayloadDict["Payload"]["background"])
        self.widget.blink(on_time=on_time, off_time=off_time, fade_in_time=fade_in_time, fade_out_time=fade_out_time, n=n, background=background)
        self.mqttSender("DONE", self.name, "BLINK")
    def on_PULSE(self, client, userdata, msg):
        # pulse(fade_in_time=1, fade_out_time=1, n=None, background=True)
        jsonPayload     = str(msg.payload.decode("utf-8", "ignore"))
        PayloadDict     = json.loads(jsonPayload)
        fade_in_time    = float(PayloadDict["Payload"]["fade_in_time"])
        fade_out_time   = float(PayloadDict["Payload"]["fade_out_time"])
        n               = IntorNone(PayloadDict["Payload"]["n"])
        background      = str_to_bool(PayloadDict["Payload"]["background"])
        self.widget.pulse(fade_in_time=fade_in_time, fade_out_time=fade_out_time, n=n, background=background)
        self.mqttSender("DONE", self.name, "PULSE")
#****************************************************************************************************************
# mqtt_PWMOutputDevice
#****************************************************************************************************************
class mqtt_PWMOutputDevice():
    def __init__(self, mqttSender, log, name, pin, active_high=True, initial_value=0, frequency=100, pin_factory=None):
        self.mqttSender = mqttSender
        self.name = name
        self.type = "MQTT_PWMOutputDevice"
        self.widget = PWMOutputDevice(pin=pin, active_high=active_high, initial_value=initial_value, frequency=frequency, pin_factory=pin_factory)
        self.log = log
        self.log.Debug("PWMOutputDevice {} created with gpiozero callbacks".format(self.name))
    #------------------------------------------------------
    def on_GetValue(self, client, userdata, msg):
        PayloadDict = {"Value": self.widget.value}          # sends a float between 0 and 1
        self.mqttSender("VAL", self.name, "", PayloadDict)
    #------------------------------------------------------
    def on_Is_Active(self, client, userdata, msg):
        PayloadDict = {"is_active": self.widget.is_active}
        self.mqttSender("STATUS/ISACTIVE", self.name, "", PayloadDict)
    #------------------------------------------------------
    def on_Frequency(self, client, userdata, msg):
        PayloadDict = {"frequency": self.widget.frequency}
        self.mqttSender("STATUS/FREQUENCY", self.name, "", PayloadDict)
    #------------------------------------------------------
    def on_ON(self, client, userdata, msg):
        self.widget.on()
        self.mqttSender("DONE", self.name, "ON")
    def on_OFF(self, client, userdata, msg):
        self.widget.off()
        self.mqttSender("DONE", self.name, "OFF")
    def on_TOGGLE(self, client, userdata, msg):
        self.widget.toggle()
        self.mqttSender("DONE", self.name, "TOGGLE")
    def on_BLINK(self, client, userdata, msg):
        # blink(on_time=1, off_time=1, fade_in_time=1, fade_out_time=1, n=None, background=True)
        jsonPayload = str(msg.payload.decode("utf-8", "ignore"))
        PayloadDict = json.loads(jsonPayload)
        on_time     = float(PayloadDict["Payload"]["on_time"])
        off_time    = float(PayloadDict["Payload"]["off_time"])
        fade_in_time    = float(PayloadDict["Payload"]["fade_in_time"])
        fade_out_time   = float(PayloadDict["Payload"]["fade_out_time"])
        n           = IntorNone(PayloadDict["Payload"]["n"])
        background  = str_to_bool(PayloadDict["Payload"]["background"])
        self.widget.blink(on_time=on_time, off_time=off_time, fade_in_time=fade_in_time, fade_out_time=fade_out_time, n=n, background=background)
        self.mqttSender("DONE", self.name, "BLINK")
    def on_PULSE(self, client, userdata, msg):
        # pulse(fade_in_time=1, fade_out_time=1, on_color=(1,1,1), off_color=(0,0,0), n=None, background=True)
        jsonPayload     = str(msg.payload.decode("utf-8", "ignore"))
        PayloadDict     = json.loads(jsonPayload)
        fade_in_time    = float(PayloadDict["Payload"]["fade_in_time"])
        fade_out_time   = float(PayloadDict["Payload"]["fade_out_time"])
        n               = IntorNone(PayloadDict["Payload"]["n"])
        background      = str_to_bool(PayloadDict["Payload"]["background"])
        self.widget.pulse(fade_in_time=fade_in_time, fade_out_time=fade_out_time, n=n, background=background)
        self.mqttSender("DONE", self.name, "PULSE")
#****************************************************************************************************************
# mqtt_Buzzer
#****************************************************************************************************************
class mqtt_Buzzer():
    def __init__(self, mqttSender, log, name, pin, active_high=True, initial_value=False, pin_factory=None):
        self.mqttSender = mqttSender
        self.name = name
        self.type = "MQTT_Buzzer"
        self.widget = Buzzer(pin=pin, active_high=active_high, initial_value=initial_value, pin_factory=pin_factory)
        self.log = log
        self.log.Debug("Buzzer {} created with gpiozero callbacks".format(self.name))
    #------------------------------------------------------
    def on_GetValue(self, client, userdata, msg):
        PayloadDict = {"Value": self.widget.value}          # sends a int 0 or 1 if active
        self.mqttSender("VAL", self.name, "", PayloadDict)
    #------------------------------------------------------
    def on_Is_Active(self, client, userdata, msg):
        PayloadDict = {"is_active": self.widget.is_active}
        self.mqttSender("STATUS/ISACTIVE", self.name, "", PayloadDict)
    #------------------------------------------------------
    def on_ON(self, client, userdata, msg):
        self.widget.on()
        self.mqttSender("DONE", self.name, "ON")
    def on_OFF(self, client, userdata, msg):
        self.widget.off()
        self.mqttSender("DONE", self.name, "OFF")
    def on_TOGGLE(self, client, userdata, msg):
        self.widget.toggle()
        self.mqttSender("DONE", self.name, "TOGGLE")
    def on_BEEP(self, client, userdata, msg):
        # beep(on_time=1, off_time=1, n=None, background=True)
        jsonPayload = str(msg.payload.decode("utf-8", "ignore"))
        PayloadDict = json.loads(jsonPayload)
        on_time     = float(PayloadDict["Payload"]["on_time"])
        off_time    = float(PayloadDict["Payload"]["off_time"])
        n           = IntorNone(PayloadDict["Payload"]["n"])
        background  = str_to_bool(PayloadDict["Payload"]["background"])
        self.widget.beep(on_time=on_time, off_time=off_time, n=n, background=background)
        self.mqttSender("DONE", self.name, "BEEP")
#****************************************************************************************************************
# mqtt_TonalBuzzer
#****************************************************************************************************************
class mqtt_TonalBuzzer():
    def __init__(self, mqttSender, log, name, pin, initial_value=None, mid_tone="A4", octaves=1, pin_factory=None):
        self.mqttSender = mqttSender
        self.name = name
        self.type = "MQTT_TonalBuzzer"
        self.widget = TonalBuzzer(pin=pin, initial_value=initial_value, mid_tone=mid_tone, octaves=octaves, pin_factory=pin_factory)
        self.log = log
        self.log.Debug("TonalBuzzer {} created with gpiozero callbacks".format(self.name))
    #------------------------------------------------------
    def on_GetValue(self, client, userdata, msg):
        PayloadDict = {"Value": self.widget.value}          # sends a float between -1 to 1 or None
        self.mqttSender("VAL", self.name, "", PayloadDict)
    #------------------------------------------------------
    def on_Is_Active(self, client, userdata, msg):
        PayloadDict = {"is_active": self.widget.is_active}
        self.mqttSender("STATUS/ISACTIVE", self.name, "", PayloadDict)
    #------------------------------------------------------
    def on_PLAY(self, client, userdata, msg):
        # play(tone)
        jsonPayload = str(msg.payload.decode("utf-8", "ignore"))
        PayloadDict = json.loads(jsonPayload)
        tone = PayloadDict["Payload"]["tone"]
        self.widget.play(tone)
        self.mqttSender("DONE", self.name, "PLAY({})".format(tone))
    def on_STOP(self, client, userdata, msg):
        self.widget.stop()
        self.mqttSender("DONE", self.name, "STOP")
#****************************************************************************************************************
# mqtt_Motor
#****************************************************************************************************************
class mqtt_Motor():
    def __init__(self, mqttSender, log, name, forward, backward, enable=None, pwm=True, pin_factory=None):
        self.mqttSender = mqttSender
        self.name = name
        self.type = "MQTT_Motor"
        self.widget = Motor(forward=forward, backward=backward, enable=enable, pwm=pwm, pin_factory=pin_factory)
        self.log = log
        self.log.Debug("Motor {} created with gpiozero callbacks".format(self.name))
    #------------------------------------------------------
    def on_GetValue(self, client, userdata, msg):
        PayloadDict = {"Value": self.widget.value}          # sends a float between -1 to 1 or None
        self.mqttSender("VAL", self.name, "", PayloadDict)
    #------------------------------------------------------
    def on_Is_Active(self, client, userdata, msg):
        PayloadDict = {"is_active": self.widget.is_active}
        self.mqttSender("STATUS/ISACTIVE", self.name, "", PayloadDict)
    #------------------------------------------------------
    def on_FORWARD(self, client, userdata, msg):
        # forward(speed)
        jsonPayload = str(msg.payload.decode("utf-8", "ignore"))
        PayloadDict = json.loads(jsonPayload)
        speed = float(PayloadDict["Payload"]["speed"])
        self.widget.forward(speed=speed)
        self.mqttSender("DONE", self.name, "FORWARD({})".format(speed))
    def on_BACKWARD(self, client, userdata, msg):
        # backward(speed)
        jsonPayload = str(msg.payload.decode("utf-8", "ignore"))
        PayloadDict = json.loads(jsonPayload)
        speed = float(PayloadDict["Payload"]["speed"])
        self.widget.backward(speed=speed)
        self.mqttSender("DONE", self.name, "BACKWARD({})".format(speed))
    def on_REVERSE(self, client, userdata, msg):
        self.widget.reverse()
        self.mqttSender("DONE", self.name, "REVERSE")
    def on_STOP(self, client, userdata, msg):
        self.widget.stop()
        self.mqttSender("DONE", self.name, "STOP")
        
        
        
#****************************************************************************************************************
# mqtt_Rover
#****************************************************************************************************************
        
        
        
        
        
        
        
        
        
        
        
        
#****************************************************************************************************************
# mqtt_PhaseEnableMotor
#****************************************************************************************************************
class mqtt_PhaseEnableMotor():
    def __init__(self, mqttSender, log, name, phase, enable, pwm=True, active_high=True, pin_factory=None):
        self.mqttSender = mqttSender
        self.name = name
        self.type = "MQTT_PhaseEnableMotor"
        self.widget = PhaseEnableMotor(forward=forward, backward=backward, enable=enable, pwm=pwm, active_high=active_high, pin_factory=pin_factory)
        self.log = log
        self.log.Debug("PhaseEnableMotor {} created with gpiozero callbacks".format(self.name))
    #------------------------------------------------------
    def on_GetValue(self, client, userdata, msg):
        PayloadDict = {"Value": self.widget.value}          # sends a float between -1 to 1 or None
        self.mqttSender("VAL", self.name, "", PayloadDict)
    #------------------------------------------------------
    def on_Is_Active(self, client, userdata, msg):
        PayloadDict = {"is_active": self.widget.is_active}
        self.mqttSender("STATUS/ISACTIVE", self.name, "", PayloadDict)
    #------------------------------------------------------
    def on_FORWARD(self, client, userdata, msg):
        # forward(speed)
        jsonPayload = str(msg.payload.decode("utf-8", "ignore"))
        PayloadDict = json.loads(jsonPayload)
        speed = float(PayloadDict["Payload"]["speed"])
        self.widget.forward(speed=speed)
        self.mqttSender("DONE", self.name, "FORWARD({})".format(speed))
    def on_BACKWARD(self, client, userdata, msg):
        # backward(speed)
        jsonPayload = str(msg.payload.decode("utf-8", "ignore"))
        PayloadDict = json.loads(jsonPayload)
        speed = float(PayloadDict["Payload"]["speed"])
        self.widget.backward(speed=speed)
        self.mqttSender("DONE", self.name, "BACKWARD({})".format(speed))
    def on_REVERSE(self, client, userdata, msg):
        self.widget.reverse()
        self.mqttSender("DONE", self.name, "REVERSE")
    def on_STOP(self, client, userdata, msg):
        self.widget.stop()
        self.mqttSender("DONE", self.name, "STOP")
#****************************************************************************************************************
# mqtt_Servo
#****************************************************************************************************************
class mqtt_Servo():
    def __init__(self, mqttSender, log, name, pin, initial_value=float(0), min_pulse_width=1/1000, max_pulse_width=2/1000, frame_width=20/1000, active_high=True, pin_factory=None):
        self.mqttSender = mqttSender
        self.name = name
        self.type = "MQTT_Servo"
        self.widget = Servo(pin=pin, initial_value=initial_value, min_pulse_width=min_pulse_width, max_pulse_width=max_pulse_width, frame_width=frame_width, active_high=active_high, pin_factory=pin_factory)
        self.log = log
        self.log.Debug("Servo {} created with gpiozero callbacks".format(self.name))
    #------------------------------------------------------
    def on_GetValue(self, client, userdata, msg):
        PayloadDict = {"Value": self.widget.value}          # sends a float between -1 to 1 or None
        self.mqttSender("VAL", self.name, "", PayloadDict)
    #------------------------------------------------------
    def on_Is_Active(self, client, userdata, msg):
        PayloadDict = {"is_active": self.widget.is_active}
        self.mqttSender("STATUS/ISACTIVE", self.name, "", PayloadDict)
    #------------------------------------------------------
    def on_SetValue(self, client, userdata, msg):
        jsonPayload = str(msg.payload.decode("utf-8", "ignore"))
        PayloadDict = json.loads(jsonPayload)
        value = float(PayloadDict["Payload"]["value"])
        self.widget.value = value
        self.mqttSender("DONE", self.name, "SETVALUE={}".format(value))
    #------------------------------------------------------
    def on_DETACH(self, client, userdata, msg):
        self.widget.detach()
        self.mqttSender("DONE", self.name, "DETACH")
    def on_MIN(self, client, userdata, msg):
        self.widget.min()
        self.mqttSender("DONE", self.name, "MIN")
    def on_MID(self, client, userdata, msg):
        self.widget.mid()
        self.mqttSender("DONE", self.name, "MID")
    def on_MAX(self, client, userdata, msg):
        self.widget.max()
        self.mqttSender("DONE", self.name, "MAX")
#****************************************************************************************************************
# mqtt_AngularServo
#****************************************************************************************************************
class mqtt_AngularServo():
    def __init__(self, mqttSender, log, name, pin, initial_angle=float(0), min_angle=float(0), max_angle=float(0), min_pulse_width=1/1000, max_pulse_width=2/1000, frame_width=20/1000, active_high=True, pin_factory=None):
        self.mqttSender = mqttSender
        self.name = name
        self.type = "MQTT_AngularServo"
        self.widget = AngularServo(pin=pin, initial_angle=initial_angle, min_angle=min_angle, max_angle=max_angle, min_pulse_width=min_pulse_width, max_pulse_width=max_pulse_width, frame_width=frame_width, active_high=active_high, pin_factory=pin_factory)
        self.log = log
        self.log.Debug("AngularServo {} created with gpiozero callbacks".format(self.name))
    #------------------------------------------------------
    def on_GetValue(self, client, userdata, msg):
        PayloadDict = {"Value": self.widget.value}          # sends a float between -1 to 1 or None
        self.mqttSender("VAL", self.name, "", PayloadDict)
    #------------------------------------------------------
    def on_Is_Active(self, client, userdata, msg):
        PayloadDict = {"is_active": self.widget.is_active}
        self.mqttSender("STATUS/ISACTIVE", self.name, "", PayloadDict)
    #------------------------------------------------------
    def on_ANGLE(self, client, userdata, msg):
        jsonPayload = str(msg.payload.decode("utf-8", "ignore"))
        PayloadDict = json.loads(jsonPayload)
        value = float(PayloadDict["Payload"]["value"])
        self.widget.angle = value
        self.mqttSender("DONE", self.name, "ANGLE={}".format(value))
    #------------------------------------------------------
    def on_MIN(self, client, userdata, msg):
        self.widget.min()
        self.mqttSender("DONE", self.name, "MIN")
    def on_MID(self, client, userdata, msg):
        self.widget.mid()
        self.mqttSender("DONE", self.name, "MID")
    def on_MAX(self, client, userdata, msg):
        self.widget.max()
        self.mqttSender("DONE", self.name, "MAX")
#****************************************************************************************************************
# mqtt_DigitalOutputDevice
#****************************************************************************************************************
class mqtt_DigitalOutputDevice():
    def __init__(self, mqttSender, log, name, pin, active_high=True, initial_value=False, pin_factory=None):
        self.mqttSender = mqttSender
        self.name = name
        self.type = "MQTT_DigitalOutputDevice"
        self.widget = DigitalOutputDevice(pin=pin, active_high=active_high, initial_value=initial_value, frequency=frequency, pin_factory=pin_factory)
        self.log = log
        self.log.Debug("DigitalOutputDevice {} created with gpiozero callbacks".format(self.name))
    #------------------------------------------------------
    def on_GetValue(self, client, userdata, msg):
        PayloadDict = {"Value": self.widget.value}          # sends a int 0 or 1 if active
        self.mqttSender("VAL", self.name, "", PayloadDict)
    #------------------------------------------------------
    def on_ON(self, client, userdata, msg):
        self.widget.on()
        self.mqttSender("DONE", self.name, "ON")
    def on_OFF(self, client, userdata, msg):
        self.widget.off()
        self.mqttSender("DONE", self.name, "OFF")
    def on_BLINK(self, client, userdata, msg):
        # blink(on_time=1, off_time=1, n=None, background=True)
        jsonPayload = str(msg.payload.decode("utf-8", "ignore"))
        PayloadDict = json.loads(jsonPayload)
        on_time     = float(PayloadDict["Payload"]["on_time"])
        off_time    = float(PayloadDict["Payload"]["off_time"])
        n           = int(PayloadDict["Payload"]["n"])
        background  = str_to_bool(PayloadDict["Payload"]["background"])
        self.widget.blink(on_time=on_time, off_time=off_time, n=n, background=background)
        self.mqttSender("DONE", self.name, "BLINK")
#****************************************************************************************************************
# mqtt_OutputDevice
#****************************************************************************************************************
class mqtt_OutputDevice():
    def __init__(self, mqttSender, log, name, pin, active_high=False, initial_value=False, pin_factory=None):
        self.mqttSender = mqttSender
        self.name = name
        self.type = "MQTT_OutputDevice"
        self.widget = OutputDevice(pin=pin, active_high=active_high, initial_value=initial_value, pin_factory=pin_factory)
        self.log = log
        self.log.Debug("MQTT_OutputDevice {} created with gpiozero callbacks".format(self.name))
    #------------------------------------------------------
    def on_GetValue(self, client, userdata, msg):
        PayloadDict = {"Value": self.widget.value}
        self.mqttSender("VAL", self.name, "", PayloadDict)
    #------------------------------------------------------
    def on_ON(self, client, userdata, msg):
        self.widget.on()
        self.mqttSender("DONE", self.name, "ON")
    def on_OFF(self, client, userdata, msg):
        self.widget.off()
        self.mqttSender("DONE", self.name, "OFF")
    def on_TOGGLE(self, client, userdata, msg):
        self.widget.toggle()
        self.mqttSender("DONE", self.name, "TOGGLE")
#****************************************************************************************************************
#****************************************************************************************************************
#****************************************************************************************************************
# END of gpiozero OUTPUT classes
#****************************************************************************************************************
#****************************************************************************************************************

#****************************************************************************************************************
# /OUT/Room1/SoundMixer1/PLAY     directory and filename in payload relative to ./SOUND/ subdirectory
# /OUT/Room1/SoundMixer1/PAUSE
# /OUT/Room1/SoundMixer1/UNPAUSE
# /OUT/Room1/SoundMixer1/STOP
# /SEND/VAL/Room1/SoundMixer1
#****************************************************************************************************************
#  mqtt_SoundMixer
#****************************************************************************************************************
class mqtt_SoundMixer():
    def __init__(self, mqttSender, log, name, nbr_of_channels=6, frequency=48000, size=-16, mono_or_stereo=STEREO, buffer_size=1024):
        #------------------------------------------------------
        self.type               = "MQTT_SoundMixer"
        self.mqttSender         = mqttSender
        self.name               = name
        self.frequency          = frequency
        self.size               = size
        self.mono_or_stereo     = mono_or_stereo + 1
        self.buffer_size        = buffer_size
        self.nbr_of_channels    = nbr_of_channels
        #----------------------------------------------------------------------------------
        self.widget = pygmx
        self.widget.quit()
        self.widget.init(frequency=self.frequency, size=self.size, channels=self.mono_or_stereo, buffer=self.buffer_size)
        self.widget.set_num_channels(self.nbr_of_channels)
        self.log = log
        self.log.Debug("MQTT_SoundMixer {} created".format(self.name))
        #----------------------------------------------------------------------------------
        self.currentlyplaying = ""
    #------------------------------------------------------
    def on_GetValue(client, userdata, msg):
        PayloadDict = {"Value": self.currentlyplaying}
        self.mqttSender("VAL", self.name, "", PayloadDict)
    #------------------------------------------------------
    def on_PLAY(self, client, userdata, msg):
        #---------------------------------------------------
        jsonPayload = str(msg.payload.decode("utf-8", "ignore"))
        PayloadDict = json.loads(jsonPayload)
        # receiving in the payload the following dict
        # PayloadDict = {"Timestamp": "", "Payload": {"filename": "filenametouse.wav"}}
        filename = PayloadDict["Payload"]["filename"]
        sound_obj = self.widget.Sound("./SOUND/{}".format(filename))
        #---------------------------------------------------------------------------------------
        nextAvailableChannel = self.widget.find_channel(True) # get next available sound channel
        # True arg override returns longest running sound channel when none are available
        if nextAvailableChannel != None and nextAvailableChannel.get_busy() == False:
            nextAvailableChannel.play(sound_obj)
            self.mqttSender("DONE", self.name, "PLAY")  
    #------------------------------------------------------
    def on_STOP(): # slowly stop the pygame operations
        time.sleep(1)
        self.widget.stop()
        time.sleep(5)
        self.widget.quit()
        time.sleep(1)
        self.mqttSender("DONE", self.name, "STOP")
    #------------------------------------------------------
    def on_PAUSE(): # pause the pygame operations
        self.widget.pause()
        self.mqttSender("DONE", self.name, "PAUSE")        
    #------------------------------------------------------
    def on_UNPAUSE(): # unpause the pygame operations
        self.widget.unpause()
        self.mqttSender("DONE", self.name, "UNPAUSE")        

#****************************************************************************************************************
#****************************************************************************************************************
# /OUT/Room1/LCD1/PRINTATLINE
# /OUT/Room1/LCD1/PRINTATLINECOL
# /OUT/Room1/LCD1/CLEAR
# /OUT/Room1/LCD1/BACKLIT         value in payload
# /SEND/VAL/Room1/LCD1    ------- NOT IMPLEMENTED
#****************************************************************************************************************
#class mqtt_2x16_lcd_I2C():
#****************************************************************************************************************
class mqtt_2x16_lcd_I2C():
    def __init__(self, mqttSender, name, address=0x27):
        #----------------------------------------
        self.type       = "MQTT_2x16_lcd_I2C"
        self.mqttSender = mqttSender
        self.name       = name
        self.address    = address
        self.value      = "Not Implemented"
        #----------------------------------------
        self.widget = RPi_I2C_driver.lcd(self.address)
        print("2x16 LCD I2C Created")
    #------------------------------------------------------
    def on_GetValue(client, userdata, msg):
        PayloadDict = {"Value": "Not Implemented"}
        self.mqttSender("VAL", self.name, "", PayloadDict)
    #------------------------------------------------------
    def on_CLEAR(self, client, userdata, msg):
        self.widget.lcd_clear()
        self.mqttSender("DONE", self.name, "")
    #------------------------------------------------------
    def on_BACKLIT(self, client, userdata, msg):
        jsonPayload = str(msg.payload.decode("utf-8", "ignore"))
        PayloadDict = json.loads(jsonPayload)
        # receiving in the payload the following dict
        # PayloadDict = {"Timestamp": "", "Payload": {"backlit": 1}}    0 or 1
        backlit = PayloadDict["Payload"]["backlit"]
        self.widget.backlight(backlit)
        self.mqttSender("DONE", self.name, "")
    #------------------------------------------------------
    def on_DISPLAYTHISATTHATLINE(self, client, userdata, msg):
        jsonPayload = str(msg.payload.decode("utf-8", "ignore"))
        PayloadDict = json.loads(jsonPayload)
        # receiving in the payload the following dict
        # PayloadDict = {"Timestamp": "", "Payload": {"text": "text to display", "line": 1}}
        whattodisplay = PayloadDict["Payload"]["text"]
        whatline = PayloadDict["Payload"]["line"]
        self.widget.lcd_display_string(whattodisplay, whatline)
        self.mqttSender("DONE", self.name, "")
    #------------------------------------------------------
    def on_DISPLAYTHISATTHATPOSITION(self, client, userdata, msg):
        jsonPayload = str(msg.payload.decode("utf-8", "ignore"))
        PayloadDict = json.loads(jsonPayload)
        # receiving in the payload the following dict
        # PayloadDict = {"Timestamp": "", "Payload": {"text": "text to display", "line": 1, "column": 5}}
        whattodisplay = PayloadDict["Payload"]["text"]
        whatline = PayloadDict["Payload"]["line"]
        whatcol = PayloadDict["Payload"]["column"]
        self.widget.lcd_display_string_pos(whattodisplay, whatline, whatcol)
        self.mqttSender("DONE", self.name, "")
    #------------------------------------------------------
    def on_LCDLOADCUSTOMCHARS(self, client, userdata, msg):
        jsonPayload = str(msg.payload.decode("utf-8", "ignore"))
        PayloadDict = json.loads(jsonPayload)
        # receiving in the payload the following dict
        # PayloadDict = {"Timestamp": "", "Payload": {"FontData": [[char1],[char2],[char3],...]}}
        FontData = PayloadDict["Payload"]["FontData"]
        self.widget.lcd_load_custom_chars(FontData)
        self.mqttSender("DONE", self.name, "")
#****************************************************************************************************************
#****************************************************************************************************************
#****************************************************************************************************************
#****************************************************************************************************************
# ShiftRegister
# 7SegmentDisplay

