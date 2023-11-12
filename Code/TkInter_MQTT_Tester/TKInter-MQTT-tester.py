#--------------------------------------------------------------------------
# Code pour tester MQTT avec les raspi ...
#
# subcribe to what the events the raspi is generating
#
# create buttons to send the events to the raspi
#   # Led.on, .off, .toggle, .GetValue
#   
# create a text zone to receive the events from the raspi (topic, payload)
#--------------------------------------------------------------------------
import xml.etree.ElementTree as oXML
import paho.mqtt.client as mqtt
from tkinter import *
from tkinter import messagebox as mb
from tkinter import ttk
import json
import sys
import platform
import datetime
import clsLog
#------------------------------------------------------------------
WORKINGSTRING = "/OUT/Room1/RGB1/OFF"
#------------------------------------------------------------------
mosquitto_client = mqtt.Client(protocol=mqtt.MQTTv311)
#------------------------------------------------------------------
# utility functions
#------------------------------------------------------------------
def timestampIt():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
#------------------------------------------------------------------
def BuildTimestampDict(d):
        rightnow = d
        Y = rightnow.year
        Mo = rightnow.month
        D = rightnow.day
        H = rightnow.hour
        Mi = rightnow.minute
        S = rightnow.second
        X = rightnow.microsecond
        return {"Y":Y,"M":Mo,"D":D,"H":H,"m":Mi,"s":S,"x":X}   
#------------------------------------------------------------------
# Utility function to extract Room, Who and What from MQTT Topics
#------------------------------------------------------------------
def GetRoom(s, prefix):
    return s.split(prefix)[1].split("/")[0]
#--------------------------------------------------------
def GetWho(s, prefix):
    return s.split(prefix)[1].split("/")[1].split("/")[0]
#--------------------------------------------------------
def GetWhat(s, prefix):
    return s.split(prefix)[1].split("/")[2].split("/")[0]
#--------------------------------------------------------
#--------------------------------------------------------
# variables
#--------------------------------------------------------
qosToUse = 2
RoomToUse = "Room1"
AllValues = {}
AllEvents = {}
AllEventsDone = {}
AllIoTcpu = {}

AllButtons = {}
AllLEDs = {}
ALLDigitalInputs = {}
#--------------------------------------------------------
# Functions on_closing() and ConnectNow()
#--------------------------------------------------------
def on_closing():
    if mb.askokcancel("Quit", "Do you want to quit?"):
        root.destroy()
        sys.exit()
def ConnectNow():
    if connect_btn['text'] == "Disconnect":
        #mb.showinfo(message="got here")
        mosquitto_client.disconnect()
        mosquitto_client.loop_stop()
        root.destroy()
        sys.exit()
    else:
        #mb.showinfo(message=hostVAR.get())
        if hostVAR.get()=="":
            mb.showinfo(message="Please enter a HOST")
        else:
            if portVAR.get()=="":
                mb.showinfo(message="Please enter a PORT")
            else:
                if keepaliveVAR.get()=="":
                    mb.showinfo(message="Please enter a keep alive value")
                else:
                    mosquitto_client.connect(host = hostVAR.get(), port = int(portVAR.get()), keepalive = int(keepaliveVAR.get()))
                    mosquitto_client.loop_start()
#------------------------------------------------
# for MQTT
#------------------------------------------------
def on_connect_mosquitto(client, userdata, flags, rc):
    log.Info("Result from Mosquitto connect: {}".format(mqtt.connack_string(rc)))
    # Check whether the result form connect is the CONNACK_ACCEPTED connack code
    if rc == mqtt.CONNACK_ACCEPTED:
        connect_btn.config(text="Disconnect")
        # -----> activate the notebooks 
        MainNotebook.tab(1, state='normal')
        MainNotebook.tab(2, state='normal')
        MainNotebook.select(1)
        #------------------------------------------------------------------------------------------------------------
        # -----> subscribe to 
        #------------------------------------------------------------------------------------------------------------
        # /XML/room/cpu
        # /VAL/room/GPIOs[name] ------> uses payload
        # /DONE/room/GPIOs[name]/ACTION
        # /DOING/room/ACTION/cpu
        # /IN/room/GPIOs[name]/EVENT
        #------------------------------------------------------------------------------------------------------------
        # -----> /SEND/XML/RoomToUse ... message sent by controler to get the configuration 
        # -----> /XML/RoomToUse/iotCPUname     payload = XML ... message sent by the IoT-CPUs
        # -----> /SEND/VAL/RoomToUse/who ... message sent by controler to get the state of something
        # -----> /VAL/RoomToUse/who    payload = value ... message sent by the IoT-CPUs
        # -----> /OUT/RoomToUse/who/what ... message sent by controler to have some action done
        # -----> /DONE/RoomToUse/who/what ... message sent by the IoT-CPUs
        # -----> /IN/RoomToUse/who/what   (pressed, held, released) ... message sent by IoT-CPUs
        #------------------------------------------------------------------------------------------------------------
        client.subscribe("/XML/{}/#".format(RoomToUse), qos=qosToUse)
        subscribe_logger.insert(END, "{} {} {}\n".format(timestampIt(), "/XML/{}/#".format(RoomToUse), qosToUse))
        client.subscribe("/VAL/{}/#".format(RoomToUse), qos=qosToUse)
        subscribe_logger.insert(END, "{} {} {}\n".format(timestampIt(), "/VAL/{}/#".format(RoomToUse), qosToUse))
        client.subscribe("/DONE/{}/#".format(RoomToUse), qos=qosToUse)
        subscribe_logger.insert(END, "{} {} {}\n".format(timestampIt(), "/DONE/{}/#".format(RoomToUse), qosToUse))
        client.subscribe("/DOING/#", qos=qosToUse)
        subscribe_logger.insert(END, "{} {} {}\n".format(timestampIt(), "/DOING/#", qosToUse))
        client.subscribe("/IN/{}/#".format(RoomToUse), qos=qosToUse)
        subscribe_logger.insert(END, "{} {} {}\n".format(timestampIt(), "/IN/{}/#".format(RoomToUse), qosToUse))
        #------------------------------------------------------------------------------------------------------------
        client.subscribe("/STATUS/+/{}/#".format(RoomToUse), qos=qosToUse)
        subscribe_logger.insert(END, "{} {} {}\n".format(timestampIt(), "/STATUS/+/{}/#".format(RoomToUse), qosToUse))
        client.subscribe("/SYSTATUS/+/{}/#".format(RoomToUse), qos=qosToUse)
        subscribe_logger.insert(END, "{} {} {}\n".format(timestampIt(), "/SYSTATUS/+/{}/#".format(RoomToUse), qosToUse))
        #------------------------------------------------------------------------------------------------------------
        client.subscribe("/HEART/{}/#".format(RoomToUse), qos=qosToUse)
        subscribe_logger.insert(END, "{} {} {}\n".format(timestampIt(), "/HEART/{}/#".format(RoomToUse), qosToUse))
        client.subscribe("/BEAT/{}/#".format(RoomToUse), qos=qosToUse)
        subscribe_logger.insert(END, "{} {} {}\n".format(timestampIt(), "/BEAT/{}/#".format(RoomToUse), qosToUse))
        #------------------------------------------------------------------------------------------------------------
        # -----> subscribe also to verify we are the only sender of "commands"
        #------------------------------------------------------------------------------------------------------------
        # /HALT/room/cpu
        # /REBOOT/room/cpu
        # /PROGREBOOT/room/ACTION/cpu
        # /SEND/XML/room/cpu
        # /SEND/VAL/room/GPIOs[name]
        # /OUT/room/GPIOs[name]/ACTION
        #------------------------------------------------------------------------------------------------------------
        client.subscribe("/HALT/{}/#".format(RoomToUse), qos=qosToUse)
        subscribe_logger.insert(END, "{} {} {}\n".format(timestampIt(), "/HALT/{}/#".format(RoomToUse), qosToUse))
        client.subscribe("/REBOOT/{}/#".format(RoomToUse), qos=qosToUse)
        subscribe_logger.insert(END, "{} {} {}\n".format(timestampIt(), "/REBOOT/{}/#".format(RoomToUse), qosToUse))
        client.subscribe("/PROGREBOOT/{}/#".format(RoomToUse), qos=qosToUse)
        subscribe_logger.insert(END, "{} {} {}\n".format(timestampIt(), "/PROGREBOOT/{}/#".format(RoomToUse), qosToUse))
        client.subscribe("/SEND/XML/{}/#".format(RoomToUse), qos=qosToUse)
        subscribe_logger.insert(END, "{} {} {}\n".format(timestampIt(), "/SEND/XML/{}/#".format(RoomToUse), qosToUse))
        client.subscribe("/SEND/VAL/{}/#".format(RoomToUse), qos=qosToUse)
        subscribe_logger.insert(END, "{} {} {}\n".format(timestampIt(), "/SEND/VAL/{}/#".format(RoomToUse), qosToUse))
        client.subscribe("/OUT/{}/#".format(RoomToUse), qos=qosToUse)
        subscribe_logger.insert(END, "{} {} {}\n".format(timestampIt(), "/OUT/{}/#".format(RoomToUse), qosToUse))
        #------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------
# on_subscribe_mosquitto ... 
#------------------------------------------------------------------------------------------------------------
def on_subscribe_mosquitto(client, userdata, mid, granted_qos):
    log.Info("I've subscribed with QoS: {}".format(granted_qos[0]))
    #log.Debug("Subscription results : {}{}{}".format(userdata, mid, granted_qos)) # for testing
    subscribe_logger.insert(END, "{} Mid: {}. I've subscribed with QoS: {}\n".format(timestampIt(), mid, granted_qos[0]))
    #mb.showinfo(message="userdata: {}".format(str(userdata)))
#------------------------------------------------------------------------------------------------------------------------------------
# WORKHORSE - Deals with the payloads ... if topic = XML do not unjson ...
#
# on_message_mosquitto ... 
#
#------------------------------------------------------------------------------------------------------------------------------------
def on_message_mosquitto(client, userdata, msg):
    log.Info("Message received. Topic: {}. Payload: {}".format(msg.topic, str(msg.payload)))
    subscribe_logger.insert(END, "{} Message received. Topic: {}. Payload: {}\n".format(timestampIt(), msg.topic, str(msg.payload)))
    
    
    # because of the following callbacks 
    
    # mosquitto_client.message_callback_add("/XML/#", on_XML)
    # mosquitto_client.message_callback_add("/VAL/#", on_VAL)
    # mosquitto_client.message_callback_add("/DONE/#", on_DONE)
    # mosquitto_client.message_callback_add("/DOING/#", on_DOING)
    # mosquitto_client.message_callback_add("/IN/#", on_IN)
    
    # this should never be called except on those

        # /HALT/room/cpu
        # /REBOOT/room/cpu
        # /PROGREBOOT/room/ACTION/cpu
        # /SEND/XML/room/cpu
        # /SEND/VAL/room/GPIOs[name]
        # /OUT/room/GPIOs[name]/ACTION
    




#------------------------------------------------------------------------------------------------    
# on_VAL
#------------------------------------------------------------------------------------------------    
def on_VAL(client, userdata, msg):
    log.Debug("VAL Message received. Topic: {}. Payload: {}".format(msg.topic, str(msg.payload)))
    #-------------------------------------------------------
    # extract from the msg.topic, the room and the who
    #-------------------------------------------------------
    room = GetRoom(msg.topic, "/VAL/")
    who  = GetWho(msg.topic, "/VAL/")
    #-------------------------------------------------------
    # unjson the payload
    #-------------------------------------------------------
    jsonPayload = str(msg.payload.decode("utf-8", "ignore"))
    PayloadDict = json.loads(jsonPayload)
    #-------------------------------------------------------
    value       = PayloadDict["Payload"]["Value"]
    #-------------------------------------------------------
    # add the value to the global dictionnary
    #-------------------------------------------------------
    AllValues["{}/{}".format(room, who)] = value
    #-------------------------------------------------------
    # log the fact
    #-------------------------------------------------------
    log.Info("VAL Message received. Topic: {}. Value: {}".format(msg.topic, str(value)))
    subscribe_logger.insert(END, "{} VAL Message received. Topic: {}. Value: {}\n".format(timestampIt(), msg.topic, str(value)))
#------------------------------------------------------------------------------------------------    
# on_IN
#------------------------------------------------------------------------------------------------    
def on_IN(client, userdata, msg):
    log.Debug("IN Message received. Topic: {}. Payload: {}".format(msg.topic, str(msg.payload)))
    #-------------------------------------------------------
    # extract from the msg.topic, the room, the who, the what
    #-------------------------------------------------------
    room = GetRoom(msg.topic, "/IN/")
    who  = GetWho(msg.topic, "/IN/")
    what = GetWhat(msg.topic, "/IN/")
    #-------------------------------------------------------
    # no payload
    #---------------------------------------------------------------------
    # Add the event to the global dictionnary, should add a time stamp ...
    #---------------------------------------------------------------------
    AllEvents["{}/{}".format(room, who)] = what
    #-------------------------------------------------------
    # log the fact
    #-------------------------------------------------------
    log.Info("IN Message received. Topic: {}. Room: {} Who: {} What: {}".format(msg.topic, room, who, what))
    subscribe_logger.insert(END, "IN Message received. Topic: {}. Room: {} Who: {} What: {}\n".format(msg.topic, room, who, what))
#------------------------------------------------------------------------------------------------    
# on_DONE
#------------------------------------------------------------------------------------------------    
def on_DONE(client, userdata, msg):
    log.Debug("DONE Message received. Topic: {}. Payload: {}".format(msg.topic, str(msg.payload)))
    # extract from the msg.topic, the room, the who, the what
    room = GetRoom(msg.topic, "/DONE/")
    who  = GetWho(msg.topic, "/DONE/")
    what = GetWhat(msg.topic, "/DONE/")
    #-------------------------------------------------------
    # no payload
    #---------------------------------------------------------------------
    # Add the event to the global dictionnary, should add a time stamp ...
    #---------------------------------------------------------------------
    AllEventsDone["{}/{}".format(room, who)] = what
    #-------------------------------------------------------
    # log the fact
    #-------------------------------------------------------
    log.Info("DONE Message received. Topic: {}. Room: {} Who: {} What: {}".format(msg.topic, room, who, what))
    subscribe_logger.insert(END, "DONE Message received. Topic: {}. Room: {} Who: {} What: {}\n".format(msg.topic, room, who, what))
#------------------------------------------------------------------------------------------------    
# on_DOING
#------------------------------------------------------------------------------------------------    
def on_DOING(client, userdata, msg):
    log.Debug("DOING Message received. Topic: {}. Payload: {}".format(msg.topic, str(msg.payload)))
    # extract from the msg.topic, the room, the who, the what
    room = GetRoom(msg.topic, "/DOING/")
    who  = GetWho(msg.topic, "/DOING/")
    what = GetWhat(msg.topic, "/DOING/") # ... not right ... 





    #-------------------------------------------------------
    # no payload
    #---------------------------------------------------------------------
    # Add the event to the global dictionnary, should add a time stamp ...
    #---------------------------------------------------------------------
    AllEventsDone["{}/{}".format(room, who)] = what
    #-------------------------------------------------------
    # log the fact
    #-------------------------------------------------------
    log.Info("DONE Message received. Topic: {}. Room: {} Who: {} What: {}".format(msg.topic, room, who, what))
    subscribe_logger.insert(END, "DONE Message received. Topic: {}. Room: {} Who: {} What: {}\n".format(msg.topic, room, who, what))




   
    
    
#------------------------------------------------------------------------------------------------    
# on_XML
#------------------------------------------------------------------------------------------------    
def on_XML(client, userdata, msg):
    log.Debug("XML Message received. Topic: {}. Payload: {}".format(msg.topic, str(msg.payload)))
    #-------------------------------------------------------
    # extract from the msg.topic, the room, the who
    #-------------------------------------------------------
    room = GetRoom(msg.topic, "/XML/")
    who  = GetWho(msg.topic, "/XML/")
    #-------------------------------------------------------
    # extract the XML from the payload
    #-------------------------------------------------------
    xmlPayload = str(msg.payload.decode("utf-8", "ignore"))
    #-------------------------------------------------------
    # save the XML to disk with name of IoTcpu
    #-------------------------------------------------------
    cpu_f = "{}_{}.xml".format(room, who)
    f = open("./XML/{}".format(cpu_f),"w+")
    f.write("{}".format(xmlPayload))
    f.flush()
    f.close()
    #-------------------------------------------------------
    # add IoTcpu to combobox and set current
    # add XML to XMLviewer textbox (similar to subscribe_logger and publish_logger)
    # from XML, build item dictionary ... inputs msg to expect and possible actions to send
    #-------------------------------------------------------
    oXMLroot = oXML.fromstring(xmlPayload)
    #-------------------------------------------------------
    room = oXMLroot.get('room')
    if room not in PublishRooms:
        PublishRooms.append(room)
    #-------------------------------------------------------
    IoTcpu = oXMLroot.get('name')
    if IoTcpu not in PublishCPUs:
        PublishCPUs.append(IoTcpu)
    #-------------------------------------------------------
    for ox in oXMLroot.findall('MQTT_Button'):
        name = ox.get('name')
        pin = int(ox.get('pin'))
        AllButtons[name] = pin
        if name not in PublishWHOs:
            PublishWHOs.append(name)
    for ox in oXMLroot.findall('MQTT_LED'):
        name = ox.get('name')
        pin = int(ox.get('pin'))
        AllLEDs[name] = pin
        if name not in PublishWHOs:
            PublishWHOs.append(name)
    for ox in oXMLroot.findall('MQTT_DigitalInputDevice'):
        name = ox.get('name')
        pin = int(ox.get('pin'))
        ALLDigitalInputs[name] = pin
        if name not in PublishWHOs:
            PublishWHOs.append(name)
    #-------------------------------------------------------







    #---------------------------------------------------------------------
    # Add the cpu to the global dictionnary, should add a time stamp ...
    #---------------------------------------------------------------------
    AllIoTcpu["{}/{}".format(room, who)] = "XML received"
    #-------------------------------------------------------
    # log the fact
    #-------------------------------------------------------
    log.Info("XML Message received. Topic: {}. Payload: {}".format(msg.topic, "XML"))
    subscribe_logger.insert(END, "{} VAL Message received. Topic: {}. Payload: {}\n".format(timestampIt(), msg.topic, "XML"))
#------------------------------------------------------------------------------------------------
# SubscribeNow      and    PublishNow       Buttons
#------------------------------------------------------------------------------------------------
def SubscribeNow():
    if SubscribeTopicVAR.get() == "":
        mb.showinfo(message="Please enter a topic")
    else:
        mosquitto_client.subscribe(SubscribeTopicVAR.get(), qos=int(SubscribeQoSVAR.get()))
        subscribe_logger.insert(END, "{} Subscribed to Topic: {} QoS: {}\n".format(timestampIt(), SubscribeTopicVAR.get(), SubscribeQoSVAR.get()))
#-------------------------------------------------------------------------------------------------
def ClearALLNow():
    PublishTopicVAR.set(WORKINGSTRING)
    Publish_qos_cb.current(2)
    PublishPayloadName_1_VAR.set("")
    PublishPayloadName_2_VAR.set("")
    PublishPayloadName_3_VAR.set("")
    PublishPayloadName_4_VAR.set("")
    PublishPayloadName_5_VAR.set("")
    PublishPayloadName_6_VAR.set("")
    PublishPayloadName_7_VAR.set("")
    PublishPayloadName_8_VAR.set("")
    PublishPayloadValue_1_VAR.set("")
    PublishPayloadValue_2_VAR.set("")
    PublishPayloadValue_3_VAR.set("")
    PublishPayloadValue_4_VAR.set("")
    PublishPayloadValue_5_VAR.set("")
    PublishPayloadValue_6_VAR.set("")
    PublishPayloadValue_7_VAR.set("")
    PublishPayloadValue_8_VAR.set("")
def ClearNow():
    Publish_qos_cb.current(2)
    PublishPayloadName_1_VAR.set("")
    PublishPayloadName_2_VAR.set("")
    PublishPayloadName_3_VAR.set("")
    PublishPayloadName_4_VAR.set("")
    PublishPayloadName_5_VAR.set("")
    PublishPayloadName_6_VAR.set("")
    PublishPayloadName_7_VAR.set("")
    PublishPayloadName_8_VAR.set("")
    PublishPayloadValue_1_VAR.set("")
    PublishPayloadValue_2_VAR.set("")
    PublishPayloadValue_3_VAR.set("")
    PublishPayloadValue_4_VAR.set("")
    PublishPayloadValue_5_VAR.set("")
    PublishPayloadValue_6_VAR.set("")
    PublishPayloadValue_7_VAR.set("")
    PublishPayloadValue_8_VAR.set("")
#-------------------------------------------------------------------------------------------------
def PublishNow():
    if PublishTopicVAR.get() == "":
        mb.showinfo(message="Please enter a topic")
    else:
        #------------------------------------------------------------------------------------------
        # when publishing, things depends on the type of topic, payload or none ?
        #
        # /SEND/XML/room/ALL
        # /SEND/XML/room/cpu
        #   /XML/room/cpu -------------> XML in payload
        #
        # /HALT/room/ALL
        # /HALT/room/cpu
        # /REBOOT/room/ALL
        # /REBOOT/room/cpu
        # /PROGREBOOT/ACTIVATEM/room/cpu  -----> minutes in payload
        # /PROGREBOOT/ACTIVATET/room/cpu  -----> Time in payload
        # /PROGREBOOT/CANCEL/room/cpu
        #
        #   /DOING/.../room/cpu where ... = HALT, REBOOT, PROGREBOOT/MINUTES, PROGREBOOT/TIME, PROGREBOOT/CANCEL
        #
        # /SEND/VAL/room/who
        #   /VAL/room/who ---------------> value in payload
        
        # /OUT/room/who/what
        #   /DONE/room/who/what
        #
        # /IN/room/who/what
        #
        #------------------------------------------------------------------------------------------
        Topic = PublishTopicVAR.get()
        QoS = int(PublishQoSVAR.get())
        # Build Payload from the fields ... Payload = {"Timestamp": dDict, "Payload": PayloadToUse}
        dDict = BuildTimestampDict(datetime.datetime.now())
        CurrentPayload = {}
        if PublishPayloadName_1_VAR.get() == "":
            pass
        else:
            # check if more than one ...
            CurrentPayload[PublishPayloadName_1_VAR.get()] = PublishPayloadValue_1_VAR.get()
            if PublishPayloadName_2_VAR.get() != "":
                CurrentPayload[PublishPayloadName_2_VAR.get()] = PublishPayloadValue_2_VAR.get()
            if PublishPayloadName_3_VAR.get() != "":
                CurrentPayload[PublishPayloadName_3_VAR.get()] = PublishPayloadValue_3_VAR.get()
            if PublishPayloadName_4_VAR.get() != "":
                CurrentPayload[PublishPayloadName_4_VAR.get()] = PublishPayloadValue_4_VAR.get()
            if PublishPayloadName_5_VAR.get() != "":
                CurrentPayload[PublishPayloadName_5_VAR.get()] = PublishPayloadValue_5_VAR.get()
            if PublishPayloadName_6_VAR.get() != "":
                CurrentPayload[PublishPayloadName_6_VAR.get()] = PublishPayloadValue_6_VAR.get()
            if PublishPayloadName_7_VAR.get() != "":
                CurrentPayload[PublishPayloadName_7_VAR.get()] = PublishPayloadValue_7_VAR.get()
            if PublishPayloadName_8_VAR.get() != "":
                CurrentPayload[PublishPayloadName_8_VAR.get()] = PublishPayloadValue_8_VAR.get()
        #------------------------------------------------------------------------------------------
        #json the payload ...
        PayloadToUse = {"Timestamp": dDict, "Payload": CurrentPayload}
        jsonPayload = json.dumps(PayloadToUse)
        #------------------------------------------------------------------------------------------
        mosquitto_client.publish(topic=Topic, payload=jsonPayload, qos=QoS, retain=False)
        Publish_logger.insert(END, "{} Published Topic: {} with Payload: {} QoS: {}\n".format(timestampIt(), Topic, jsonPayload, PublishQoSVAR.get()))
#------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------
# Start the main 
#------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    #--------------------------------------------------------------------------------------------
    # Build the Tk interface
    #--------------------------------------------------------------------------------------------
    fn = clsLog.BuildFilename("./log/TKInter_MQTT_Tester", "log")
    log = clsLog.Logger(fn, 10)
    root = Tk()
    root.resizable(True, True) 
    root.title(" Python-IoT.com  -  MQTT Tester")
    root.protocol("WM_DELETE_WINDOW", on_closing)
    #-------------------------------
    # Create the screen variables
    #-------------------------------
    hostVAR = StringVar()
    portVAR = StringVar()
    keepaliveVAR = StringVar()
    keepaliveVAR.set('60')
    SubscribeTopicVAR = StringVar()
    SubscribeQoSVAR = StringVar()
    PublishTopicVAR = StringVar()
    PublishQoSVAR = StringVar()
    PublishRooms = []
    PublishCPUs = []
    PublishWHOs = []
    PublishPayloadName_1_VAR = StringVar() # this should be a list ...
    PublishPayloadName_2_VAR = StringVar()
    PublishPayloadName_3_VAR = StringVar()
    PublishPayloadName_4_VAR = StringVar()
    PublishPayloadName_5_VAR = StringVar()
    PublishPayloadName_6_VAR = StringVar()
    PublishPayloadName_7_VAR = StringVar()
    PublishPayloadName_8_VAR = StringVar()
    PublishPayloadValue_1_VAR = StringVar()
    PublishPayloadValue_2_VAR = StringVar()
    PublishPayloadValue_3_VAR = StringVar()
    PublishPayloadValue_4_VAR = StringVar()
    PublishPayloadValue_5_VAR = StringVar()
    PublishPayloadValue_6_VAR = StringVar()
    PublishPayloadValue_7_VAR = StringVar()
    PublishPayloadValue_8_VAR = StringVar()
    #PublishPayloadVAR = StringVar()
    #-------------------------------
    # MainFrame and MainNotebook
    #-------------------------------
    MainFrame = ttk.Labelframe(root, text=' v 0.1.2')
    MainNotebook = ttk.Notebook(MainFrame)
    #----------------------------------------------------------------------------------------------
    # the individual internal frames of each notebook tabs
    #----------------------------------------------------------------------------------------------
    ConnectFrame = ttk.Frame(MainNotebook, padding=(5,5,5,5), relief = 'sunken', borderwidth = 2)
    SubscribeFrame = ttk.Frame(MainNotebook, padding=(5,5,5,5), relief = 'sunken', borderwidth = 2)
    PublishFrame = ttk.Frame(MainNotebook, padding=(5,5,5,5), relief = 'sunken', borderwidth = 2)
    XMLFrame = ttk.Frame(MainNotebook, padding=(5,5,5,5), relief = 'sunken', borderwidth = 2)
    #----------------------------------------------------------------------------------------------
    # the first tab : ConnectFrame
    #----------------------------------------------------------------------------------------------
    hostLabel = ttk.Label(ConnectFrame, text='Host')
    portLabel = ttk.Label(ConnectFrame, text='Port')
    keepaliveLabel = ttk.Label(ConnectFrame, text='Keep alive')
    host_cb = ttk.Combobox(ConnectFrame, textvariable = hostVAR)
    host_cb['values'] = ('10.0.0.245','10.148.82.21')
    port_cb = ttk.Combobox(ConnectFrame, textvariable = portVAR)
    port_cb['values'] = ('1883','8883')
    keepalive_txt = ttk.Entry(ConnectFrame, textvariable = keepaliveVAR)
    connect_btn = ttk.Button(ConnectFrame, text = 'Connect', command = ConnectNow)
    if (platform.system() == "Linux"):
        host_cb.current(1)
    elif (platform.system() == "Darwin"):
        pass
    elif (platform.system() == "Windows"):
        host_cb.current(0)
    port_cb.current(0)
    #----------------------------------------------------------------------------------------------
    # the second tab : SubscribeFrame
    #----------------------------------------------------------------------------------------------
    SubscribeTopicLabel = ttk.Label(SubscribeFrame, text='Topic')
    SubscribeQoSLabel = ttk.Label(SubscribeFrame, text='QoS')
    SubscribeTopicEntry = ttk.Entry(SubscribeFrame, textvariable = SubscribeTopicVAR, width=80)
    Subscribe_qos_cb = ttk.Combobox(SubscribeFrame, textvariable = SubscribeQoSVAR, width=5)
    Subscribe_qos_cb['values'] = (0,1,2)
    Subscribe_qos_cb.current(2)
    subscribe_btn = ttk.Button(SubscribeFrame, text = 'Subscribe', command = SubscribeNow)
    subscribe_logger = Text(SubscribeFrame, height=30, width=120, wrap="none")
    SubscribeVScroll = ttk.Scrollbar(SubscribeFrame, orient=VERTICAL, command=subscribe_logger.yview)
    SubscribeHScroll = ttk.Scrollbar(SubscribeFrame, orient=HORIZONTAL, command=subscribe_logger.xview)
    subscribe_logger.config(yscrollcommand=SubscribeVScroll.set)
    subscribe_logger.config(xscrollcommand=SubscribeHScroll.set)
    #----------------------------------------------------------------------------------------------
    # the third tab : PublishFrame
    #----------------------------------------------------------------------------------------------
    PublishTopicLabel = ttk.Label(PublishFrame, text='Topic')
    PublishQoSLabel = ttk.Label(PublishFrame, text='QoS')
    #PublishPayloadLabel = ttk.Label(PublishFrame, text='Payload')
    PublishPayloadNameLabel  = ttk.Label(PublishFrame, text='Name')
    PublishPayloadValueLabel = ttk.Label(PublishFrame, text='Value')
    PublishTopicEntry = ttk.Entry(PublishFrame, textvariable = PublishTopicVAR, width=80)
    PublishPayloadName_1 = ttk.Entry(PublishFrame, textvariable = PublishPayloadName_1_VAR, width=20)
    PublishPayloadName_2 = ttk.Entry(PublishFrame, textvariable = PublishPayloadName_2_VAR, width=20)
    PublishPayloadName_3 = ttk.Entry(PublishFrame, textvariable = PublishPayloadName_3_VAR, width=20)
    PublishPayloadName_4 = ttk.Entry(PublishFrame, textvariable = PublishPayloadName_4_VAR, width=20)
    PublishPayloadName_5 = ttk.Entry(PublishFrame, textvariable = PublishPayloadName_5_VAR, width=20)
    PublishPayloadName_6 = ttk.Entry(PublishFrame, textvariable = PublishPayloadName_6_VAR, width=20)
    PublishPayloadName_7 = ttk.Entry(PublishFrame, textvariable = PublishPayloadName_7_VAR, width=20)
    PublishPayloadName_8 = ttk.Entry(PublishFrame, textvariable = PublishPayloadName_8_VAR, width=20)
    PublishPayloadValue_1 = ttk.Entry(PublishFrame, textvariable = PublishPayloadValue_1_VAR, width=20)
    PublishPayloadValue_2 = ttk.Entry(PublishFrame, textvariable = PublishPayloadValue_2_VAR, width=20)
    PublishPayloadValue_3 = ttk.Entry(PublishFrame, textvariable = PublishPayloadValue_3_VAR, width=20)
    PublishPayloadValue_4 = ttk.Entry(PublishFrame, textvariable = PublishPayloadValue_4_VAR, width=20)
    PublishPayloadValue_5 = ttk.Entry(PublishFrame, textvariable = PublishPayloadValue_5_VAR, width=20)
    PublishPayloadValue_6 = ttk.Entry(PublishFrame, textvariable = PublishPayloadValue_6_VAR, width=20)
    PublishPayloadValue_7 = ttk.Entry(PublishFrame, textvariable = PublishPayloadValue_7_VAR, width=20)
    PublishPayloadValue_8 = ttk.Entry(PublishFrame, textvariable = PublishPayloadValue_8_VAR, width=20)
    #PublishPayloadEntry = ttk.Entry(PublishFrame, textvariable = PublishPayloadVAR, width=80)
    Publish_qos_cb = ttk.Combobox(PublishFrame, textvariable = PublishQoSVAR, width=5)
    Publish_qos_cb['values'] = (0,1,2)
    Publish_qos_cb.current(2)
    Publish_Rooms_cb = ttk.Combobox(PublishFrame, values=PublishRooms, postcommand=lambda: Publish_Rooms_cb.configure(values=PublishRooms), width=20)
    Publish_CPUs_cb = ttk.Combobox(PublishFrame, values=PublishCPUs, postcommand=lambda: Publish_CPUs_cb.configure(values=PublishCPUs), width=20)
    Publish_Who_cb = ttk.Combobox(PublishFrame, values=PublishWHOs, postcommand=lambda: Publish_Who_cb.configure(values=PublishWHOs), width=20)
    Publish_btn = ttk.Button(PublishFrame, text = 'Publish', command = PublishNow)
    Publish_CLEAR_btn = ttk.Button(PublishFrame, text = 'Clear ALL fields', command = ClearALLNow)
    Publish_CLEAR_FIELDS_btn = ttk.Button(PublishFrame, text = 'Clear fields', command = ClearNow)
    Publish_logger = Text(PublishFrame, height=30, width=120, wrap="none")
    PublishVScroll = ttk.Scrollbar(PublishFrame, orient=VERTICAL, command=Publish_logger.yview)
    PublishHScroll = ttk.Scrollbar(PublishFrame, orient=HORIZONTAL, command=Publish_logger.xview)
    Publish_logger.config(yscrollcommand=PublishVScroll.set)
    Publish_logger.config(xscrollcommand=PublishHScroll.set)
    #----------------------------------------------------------------------------------------------
    # the fourth tab : XMLFrame
    #----------------------------------------------------------------------------------------------








    #------------------------------------------------
    # Add the tabs to the notebook
    #------------------------------------------------
    MainNotebook.add(ConnectFrame, text = 'Connect')
    MainNotebook.add(SubscribeFrame, text = 'Subscribe', state = 'disabled')
    MainNotebook.add(PublishFrame, text = 'Publish', state = 'disabled')
    MainNotebook.add(XMLFrame, text = 'XML', state = 'disabled')
    #------------------------------------------------
    # now grid everything 
    #------------------------------------------------
    MainFrame.grid(column=0,row=0, sticky=(N,S,E,W))
    MainNotebook.grid(column=0,row=0, sticky=(N,S,E,W))
    #ConnectFrame.grid(column=0,row=0, sticky=(N,S,E,W))
    #-----------------------------------------------------
    # Grid Connect Tab
    #-----------------------------------------------------
    hostLabel.grid(column=0,row=0, sticky=(N,S,W))
    portLabel.grid(column=0,row=1, sticky=(N,S,W))
    keepaliveLabel.grid(column=0,row=2, sticky=(N,S,W))
    host_cb.grid(column=1,row=0, sticky=(N,S,E))
    port_cb.grid(column=1,row=1, sticky=(N,S,E))
    keepalive_txt.grid(column=1,row=2, sticky=(N,S,E))
    connect_btn.grid(column=0,row=3, sticky=(N,S,E,W))
    #-----------------------------------------------------
    # Grid Subscribe Tab
    #-----------------------------------------------------
    SubscribeTopicLabel.grid(column=0,row=0, sticky=(N,S,W))
    SubscribeQoSLabel.grid(column=0,row=1, sticky=(N,S,W))
    SubscribeTopicEntry.grid(column=1,row=0, sticky=(N,S,W))
    Subscribe_qos_cb.grid(column=1,row=1, sticky=(N,S,W))
    subscribe_btn.grid(column=2,row=0, rowspan=2, sticky=(N,S,E,W))
    subscribe_logger.grid(column=0,row=2, columnspan=3, sticky=(N,S,E,W))
    SubscribeVScroll.grid(column=4,row=2, sticky=(N,S,W))
    SubscribeHScroll.grid(column=0,row=3, columnspan=3, sticky=(N,E,W))
    #-----------------------------------------------------
    # Grid Publish Tab
    #-----------------------------------------------------
    PublishTopicLabel.grid(column=0,row=0, sticky=(N,S,W))
    PublishQoSLabel.grid(column=0,row=1, sticky=(N,S,W))
    #PublishPayloadLabel.grid(column=0,row=2, sticky=(N,S,W))
    PublishTopicEntry.grid(column=1,row=0, columnspan=4, sticky=(N,S,W))
    Publish_qos_cb.grid(column=1,row=1, sticky=(N,S,W))
    Publish_Rooms_cb.grid(column=2,row=1, sticky=(N,S))
    Publish_CPUs_cb.grid(column=3,row=1, sticky=(N,S))
    Publish_Who_cb.grid(column=4,row=1, sticky=(N,S))
    Publish_CLEAR_btn.grid(column=1,row=2, rowspan=3, sticky=(N,S,W))
    Publish_CLEAR_FIELDS_btn.grid(column=4,row=2, rowspan=3, sticky=(N,S,E))
    PublishPayloadNameLabel.grid(column=5,row=0, sticky=(N,S,W))
    PublishPayloadName_1.grid(column=5,row=1, sticky=(N,S,W))
    PublishPayloadName_2.grid(column=5,row=2, sticky=(N,S,W))
    PublishPayloadName_3.grid(column=5,row=3, sticky=(N,S,W))
    PublishPayloadName_4.grid(column=5,row=4, sticky=(N,S,W))
    PublishPayloadName_5.grid(column=5,row=5, sticky=(N,S,W))
    PublishPayloadName_6.grid(column=5,row=6, sticky=(N,S,W))
    PublishPayloadName_7.grid(column=5,row=7, sticky=(N,S,W))
    PublishPayloadName_8.grid(column=5,row=8, sticky=(N,S,W))
    PublishPayloadValueLabel.grid(column=6,row=0, sticky=(N,S,W))
    PublishPayloadValue_1.grid(column=6,row=1, sticky=(N,S,W))
    PublishPayloadValue_2.grid(column=6,row=2, sticky=(N,S,W))
    PublishPayloadValue_3.grid(column=6,row=3, sticky=(N,S,W))
    PublishPayloadValue_4.grid(column=6,row=4, sticky=(N,S,W))
    PublishPayloadValue_5.grid(column=6,row=5, sticky=(N,S,W))
    PublishPayloadValue_6.grid(column=6,row=6, sticky=(N,S,W))
    PublishPayloadValue_7.grid(column=6,row=7, sticky=(N,S,W))
    PublishPayloadValue_8.grid(column=6,row=8, sticky=(N,S,W))
    #PublishPayloadEntry.grid(column=1,row=2, sticky=(N,S,W))
    Publish_btn.grid(column=7,row=0, rowspan=3, sticky=(N,S,E,W))
    Publish_logger.grid(column=0,row=9, columnspan=8, sticky=(N,S,E,W))
    PublishVScroll.grid(column=8,row=9, sticky=(N,S,W))
    PublishHScroll.grid(column=0,row=10, columnspan=8, sticky=(N,E,W))
    PublishTopicVAR.set(WORKINGSTRING)
    #-----------------------------------------------------
    # Grid XML Tab
    #-----------------------------------------------------







    #-----------------------------------------------------
    # column configure
    #-----------------------------------------------------
    MainNotebook.columnconfigure(0, weight=1)
    #ConnectFrame.columnconfigure(0, weight=1)
    SubscribeFrame.columnconfigure(1, weight=1)
    SubscribeFrame.rowconfigure(2, weight=1)
    PublishFrame.columnconfigure(1, weight=1)
    XMLFrame.columnconfigure(0, weight=1)
    XMLFrame.rowconfigure(0, weight=1)
    #---------------------------------------------------------------------------------
    # Config the mosquitto MQTT client
    #---------------------------------------------------------------------------------
    #mosquitto_client = mqtt.Client(protocol=mqtt.MQTTv311)
    mosquitto_client.on_connect = on_connect_mosquitto
    mosquitto_client.on_subscribe = on_subscribe_mosquitto
    mosquitto_client.on_message = on_message_mosquitto
    #------------------------------------------------------------
    mosquitto_client.message_callback_add("/XML/#", on_XML)
    log.Debug("added callback for /XML/#")
    #------------------------------------------------------------
    mosquitto_client.message_callback_add("/VAL/#", on_VAL)
    log.Debug("added callback for /VAL/#")
    #------------------------------------------------------------
    mosquitto_client.message_callback_add("/DONE/#", on_DONE)
    log.Debug("added callback for /DONE/#")
    #------------------------------------------------------------
    mosquitto_client.message_callback_add("/DOING/#", on_DOING)
    log.Debug("added callback for /DOING/#")
    #------------------------------------------------------------
    mosquitto_client.message_callback_add("/IN/#", on_IN)
    log.Debug("added callback for /IN/#")
    #---------------------------------------------------------------------------------
    # connect and start loop
    #---------------------------------------------------------------------------------
    #mosquitto_client.connect(host = "10.148.82.21", port = 1883, keepalive = 60)
    #mosquitto_client.connect(host = "10.0.0.245", port = 1883, keepalive = 60)
    #mosquitto_client.loop_start()
    try:
        while True:
            root.mainloop()
            #pause()
    except KeyboardInterrupt:
        mosquitto_client.disconnect()
        mosquitto_client.loop_stop()
