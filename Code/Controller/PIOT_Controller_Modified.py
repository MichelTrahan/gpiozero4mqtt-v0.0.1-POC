import sys
import gpiozero4mqtt
import time

#-------------------------------------------------------------------------------------------------------------
# HARD CODED for show
#-------------------------------------------------------------------------------------------------------------
def OnBigButtonPressed(client, userdata, msg):
    gpioList.GPIOs['Green1'].widget.on()
    client.publish(topic="/DONE/{}/Green1/ON".format(gpioList.room), payload=gpioList.BuildJSONPayload(), qos=gpioList.MQTT_qos, retain=False)
def OnBigButtonHeld(client, userdata, msg):
    gpioList.GPIOs['Green1'].widget.off()
    gpioList.GPIOs['Yellow1'].widget.on()
def OnBigButtonReleased(client, userdata, msg):
    gpioList.GPIOs['Yellow1'].widget.off()
    gpioList.GPIOs['Red1'].widget.on()
    time.sleep(0.1)
    gpioList.GPIOs['Red1'].widget.off()
#-------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    
    if len(sys.argv) > 1:
        gpioList = gpiozero4mqtt.GPIOList(sys.argv[1])
    else:
        gpioList = gpiozero4mqtt.GPIOList()
    #-------------------------------------------------------------------------------------------------------------
    # HARD CODED for show
    #-------------------------------------------------------------------------------------------------------------
    gpioList.MQTT_client.message_callback_add("/IN/{}/BigButton1/PRESSED".format(gpioList.room), OnBigButtonPressed)
    gpioList.MQTT_client.message_callback_add("/IN/{}/BigButton1/HELD".format(gpioList.room), OnBigButtonHeld)
    gpioList.MQTT_client.message_callback_add("/IN/{}/BigButton1/RELEASED".format(gpioList.room), OnBigButtonReleased)
    #-------------------------------------------------------------------------------------------------------------

    gpioList.MQTTconnectNow()
    gpioList.MQTT_client.subscribe("/IN/{}/BigButton1/+".format(gpioList.room), gpioList.MQTT_qos)
    
    gpioList.MQTT_client.loop_start()
    try:
        while True:
            gpioList.loop_process()
    except KeyboardInterrupt:
        gpioList.MQTT_client.disconnect()
        gpioList.MQTT_client.loop_stop()
