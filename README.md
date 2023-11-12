# gpiozero4mqtt-v0.0.1-POC

Hi there,

This is my first Python program so bare with me ;)

By using a simple XML file to define what is connected to a Raspberry PI (2,3,4,zero,400) you can connect all of the IN and OUT to a local MQTT broker.

By augmenting the gpiozero library with a MQTT layer that defines functions to listen to the MQTT broker or send information to it, we can completely automate the coding needed for the communication between the Raspberry pi and the local MQTT broker. Only configure the XML and run the framework … voila ! No coding !

The library gpiozero4mqtt.py is a Python layer added to the gpiozero library, used on many Raspberry Pi projects, to allow it to use an MQTT broker by only defining the resource and its connections in an XML file. It also allows usage of the source connection found in the gpiozero library.

The concept implemented here is that a Raspberry Pi is usually associated to a room. There can be many Raspberry Pi in a room and there can be many rooms. Each Raspberry Pi has its own XML relating to what is connected to it and what MQTT broker to send information to or listen to for commands.

It has no intelligence about what to do with those messages. That is another problem altogether, which will be part of another document soon. I will be creating an XML "language" for the management of the MQTT messages ... in different contexts. More to come ...

I didn't make a solution that is pure OO ... I lack knowledge of Python ... and MQTT ... and ... well this is my first trial at it.

The main thing for now is that it works fine ... in a local network. It would need certificates but since python 3.7 (I think) I cannot create my own certificates to have everything encrypted on my local network ... pity !

If this can help or give ideas to anyone, I would be happy !

Give me time to build a sample project that uses it and I can publish !

Oh and I'm french canadian ... it could explain some mistakes ;)

Mike.

Mar 26, 2021

Michel Trahan

p.s.: I do see it is not real OOD ... but it was a proof of concept ... it would make sense to make it more like something we register what we want to communicate through MQTT. Moving on to kubernets myself, if anyone has the energy to augment/maintain this ... I am open to discussion !
