import xml.etree.ElementTree as oXML
#-------------------------------------------------------------
# import SourceConnectionProcessor as SCP
#    #-------------------------------------------------------------
#    xmlFilename = "./data/GPIO4MQTT.xml"
#    oXMLtree = oXML.parse(xmlFilename)
#    oXMLroot = oXMLtree.getroot()
#
#    self.logTo = oXMLroot.get('logTo')
#    self.atLevel = int(oXMLroot.get('atLevel'))
#    self.fn = clsLog.BuildFilename(self.logTo, "log")
#    self.log = clsLog.Logger(self.fn, self.atLevel)
#    #-------------------------------------------------------------
#    SCP.ExcecuteSimpleConnect(oXMLroot, self.log)
#    SCP.ExecuteMultiConnect(oXMLroot, self.log)
#    #-------------------------------------------------------------
#-------------------------------------------------------------
# ExcecuteSimpleConnect
#-------------------------------------------------------------
def ExcecuteSimpleConnect(oXMLroot, log, GPIOs):
    for ox in oXMLroot.findall('./SourceConnections/Connect'):
        target   = ox.get('target')
        function = ox.get('function')
        source   = ox.get('source')
        Params={}
        AllParams = {}
        if function == "":
            codeToRun="GPIOs[\"{}\"].widget.source= GPIOs[\"{}\"].widget".format(target, source)
        else:
            # does the function have parameters
            AllParams["{}-{}-{}".format(target, function, source)] =  Params
            oxP = ox.find('Params')
            if not oxP == None:
                attrName = [attrName for attrName, attrValue in oxP.items()]
                attrValue = [attrValue for attrName, attrValue in oxP.items()]
                AllParams["{}-{}-{}".format(target, function, source)] = dict(zip(attrName, attrValue))
                #--------------------------------------------------------------------------------------------------
                # Now build the string to execute for this target
                #--------------------------------------------------------------------------------------------------
                codeToRun="GPIOs[\"{}\"].widget.source=".format(target)
                for key in AllParams:
                    function = key.split("-")[1]
                    source = key.split("-")[2]
                    params = AllParams[key]
                    if bool(params): # the function has parameters
                        codeToRun += "{}(GPIOs[\"{}\"].widget, ".format(function, source)
                        s=""
                        for paramName in params:
                            s += "{}={}, ".format(paramName, params[paramName])
                        s = s[:-2] # to remove le last coma ...
                        codeToRun += s
                    else:
                        codeToRun += "{}(GPIOs[\"{}\"].widget".format(function, source)
                    codeToRun += ")"
                    codeToRun += ", "
                codeToRun = codeToRun[:-2] # to remove the last coma
            else: # function with no parameters
                codeToRun="GPIOs[\"{}\"].widget.source= {}(GPIOs[\"{}\"].widget)".format(target, function, source)             
        print(codeToRun)
        log.Debug("{}".format(codeToRun))
        exec(codeToRun)
#-------------------------------------------------------------
# ExecuteMultiConnect
#-------------------------------------------------------------
def ExecuteMultiConnect(oXMLroot, log, GPIOs):
    MultiValues = ["All_Values","Any_Values","Averaged","Multiplied","Summed","Zip_Values","Zip"]
    for which in MultiValues:
        for ox in oXMLroot.findall('SourceConnections/{}'.format(which)):
            codeToRun=""
            closingString=""
            target   = ox.get('target')
            AllParams = {}
            #--------------------------------------------------------------------------------------------------
            # Find Devices for the aggragator, to set target
            #--------------------------------------------------------------------------------------------------
            for oxD in ox.findall('Device'):
                function = oxD.get('function')
                source   = oxD.get('source')
                Params={}
                AllParams["{}-{}-{}".format(target, function, source)] =  Params
                oxP = oxD.find('Params')
                if not oxP == None:
                    attrName = [attrName for attrName, attrValue in oxP.items()]
                    attrValue = [attrValue for attrName, attrValue in oxP.items()]
                    AllParams["{}-{}-{}".format(target, function, source)] = dict(zip(attrName, attrValue))
            #--------------------------------------------------------------------------------------------------
            # All devices have been found
            #--------------------------------------------------------------------------------------------------
            # Now build the string to execute for this target
            #--------------------------------------------------------------------------------------------------
            codeToRun="GPIOs[\"{}\"].widget.source={}(".format(target, which)
            closingString=")"
            for key in AllParams:
                function = key.split("-")[1]
                source = key.split("-")[2]
                params = AllParams[key]
                if function == "":
                    codeToRun += "GPIOs[\"{}\"].widget".format(source)
                else:
                    if bool(params): # the function has parameters
                        codeToRun += "{}(GPIOs[\"{}\"].widget, ".format(function, source)
                        s=""
                        for paramName in params:
                            s += "{}={}, ".format(paramName, params[paramName])
                        s = s[:-2] # to remove le last coma ...
                        codeToRun += s
                    else:
                        codeToRun += "{}(GPIOs[\"{}\"].widget".format(function, source)
                    codeToRun += ")"
                codeToRun += ", "
            codeToRun = codeToRun[:-2] # to remove the last coma
            codeToRun += closingString  
            #--------------------------------------------------------------------------------------------------
            print(codeToRun)
            log.Debug("{}".format(codeToRun))
            exec(codeToRun)
            #--------------------------------------------------------------------------------------------------
            # Going for the next aggragator of the same type 
        # ALL Done for the type of aggragator   
