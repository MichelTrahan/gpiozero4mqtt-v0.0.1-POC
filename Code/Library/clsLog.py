import datetime
class Logger():
    def __init__(self, logTo="./log/Logger.log", atLevel=10):
        self.logTo = logTo
        self.atLevel = atLevel
        self.f = open(self.logTo, "a+")
        self.f.write("------------- Creating a Logger at level {} ------------\n".format(self.atLevel))
        self.f.flush()
    def Debug(self, s):
        if self.atLevel <= 10: 
            print("{} D {}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), s))
            self.f.write("{} D {}\n".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), s))
            self.f.flush()
    def Info(self, s): 
        if self.atLevel <= 20: 
            print("{} I {}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), s))
            self.f.write("{} I {}\n".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), s))
            self.f.flush()
    def Warning(self, s):
        if self.atLevel <= 30: 
            print("{} W {}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), s))
            self.f.write("{} W {}\n".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), s))
            self.f.flush()
    def Error(self, s):
        if self.atLevel <= 40: 
            print("{} E {}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), s))
            self.f.write("{} E {}\n".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), s))
            self.f.flush()
    def Critical(self, s):
        if self.atLevel <= 50: 
            print("{} C {}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), s))
            self.f.write("{} C {}\n".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), s))
            self.f.flush()
    def PrintConfig(self):
        print("logging to {} at level {}".format(self.logTo, self.atLevel))
    def ChangeLogFile(self, fn):
        self.logTo = fn
        self.f.flush()
        self.f.close()
        self.f = open(self.logTo, "a+")
        self.f.write("------------- Creating a new Logger file at level {} ------------\n".format(self.atLevel))
def GetCurrentDate_YYYY_MM_DD():
    return datetime.datetime.now().strftime("%Y_%m_%d")
def BuildFilename(base, ext):
    return "{}_{}.{}".format(base, GetCurrentDate_YYYY_MM_DD(), ext)

if __name__ == "__main__":

    fn = BuildFilename("./log/testing", "log")
    log = Logger(fn, 10)
    log.Debug("This is debug comment")
    log.Info("This is info comment")
    log.Warning("This is a warning comment")
    log.Error("This is an error comment")
    log.Critical("This is a critical comment")
    
    fn = BuildFilename("./log/toto", "txt")
    log.ChangeLogFile(fn)
    log.PrintConfig()
    
    log.Debug("This is debug comment")
    log.Info("This is info comment")
    log.Warning("This is a warning comment")
    log.Error("This is an error comment")
    log.Critical("This is a critical comment")