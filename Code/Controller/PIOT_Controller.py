import sys
import gpiozero4mqtt
if __name__ == "__main__":
    if len(sys.argv) > 1:
        gpioList = gpiozero4mqtt.GPIOList(xmlFilename=sys.argv[1])
    else:
        gpioList = gpiozero4mqtt.GPIOList()
    gpioList.MQTTconnectNow()
    gpioList.MQTT_client.loop_start()
    try:
        while True:
            gpioList.loop_process()
    except KeyboardInterrupt:
        gpioList.MQTT_client.disconnect()
        gpioList.MQTT_client.loop_stop()
