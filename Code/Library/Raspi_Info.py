#------------------------------------
import psutil
import platform
#------------------------------------
import fcntl
import socket
import struct
#------------------------------------
from gpiozero import CPUTemperature
#------------------------------------
from datetime import datetime
#------------------------------------
#-----------------------------------------------------------------------------
#   getSystemDict
#-----------------------------------------------------------------------------
def getSystemDict():
    aDict ={}
    uname = platform.uname()
    aDict = {"System":  uname.system,
             "Node":     uname.node,
             "Release":  uname.release,
             "Version":  uname.version,
             "Machine":  uname.machine #,
             #"Processor": uname.processor
            }
    return aDict
#-----------------------------------------------------------------------------
#   getBootTimeDict
#-----------------------------------------------------------------------------
def getBootTimeDict():
    aDict ={}
    boot_time_timestamp = psutil.boot_time()
    bt = datetime.fromtimestamp(boot_time_timestamp)
    aDict = {"Year":    bt.year,
             "Month":    bt.month,
             "Day":      bt.day,
             "Hour":     bt.hour,
             "Minute":   bt.minute,
             "Second":   bt.second
            }
    return aDict
#-----------------------------------------------------------------------------
#   getCPUDict
#-----------------------------------------------------------------------------
def getCPUDict():
    aDict ={}
    cpufreq = psutil.cpu_freq()
    aDict = {"Physical cores":       psutil.cpu_count(logical=False),
             "Total cores":           psutil.cpu_count(logical=True),
             "Max Frequency MHz":     cpufreq.max,
             "Min Frequency MHz":     cpufreq.min,
             "Current Frequency MHz": cpufreq.current,
             "CPU Usage":             "{}%".format(psutil.cpu_percent())
            }
    return aDict
#----------------------------------------------
#   getMemDict
#----------------------------------------------
def getMemDict():
    aDict ={}
    svmem = psutil.virtual_memory()
    aDict = {"Total":       get_size(svmem.total),
             "Available":    get_size(svmem.available),
             "Used":         get_size(svmem.used),
             "Percentage":   "{}%".format(svmem.percent)
            }
    return aDict
#----------------------------------------------
#   getSWAPDict
#----------------------------------------------
def getSWAPDict():
    aDict ={}
    swap = psutil.swap_memory()
    aDict = {"Total":       get_size(swap.total),
             "Free":         get_size(swap.free),
             "Used":         get_size(swap.used),
             "Percentage":   "{}%".format(swap.percent)
            }
    return aDict
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# NETWORK
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# getMAC        "00:00:00:00:00:00"
#-----------------------------------------------------------------------------
def getMAC(ifname):
    try:
        mac = open('/sys/class/net/' + ifname + '/address').readline()
    except:
        mac = "00:00:00:00:00:00"
    return mac[0:17]
#-----------------------------------------------------------------------------
# getNetmask    "0.0.0.0"
#-----------------------------------------------------------------------------
def getNetmask(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        netmask = fcntl.ioctl(s, 0x891b, struct.pack('256s', bytes(ifname[:15], 'utf-8')))[20:24]
        return socket.inet_ntoa(netmask)
    except:
        return "0.0.0.0"
#-----------------------------------------------------------------------------
# getIP         "0.0.0.0"
#-----------------------------------------------------------------------------
def getIP(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        ip = fcntl.ioctl(s, 0x8915, struct.pack('256s', bytes(ifname[:15], 'utf-8')))[20:24]
        return socket.inet_ntoa(ip)
    except:
        return "0.0.0.0"
#-----------------------------------------------------------------------------
#   getNetworkDict
#-----------------------------------------------------------------------------
def getNetworkDict():
    aDict ={}
    aDict = {"Network-eth0":  
                {"IP":      getIP("eth0"),
                "MAC":      getMAC("eth0"),
                "Netmask":  getNetmask("eth0")
                },
            "Network-wlan0":
                {"IP":      getIP("wlan0"),
                "MAC":      getMAC("wlan0"),
                "Netmask":  getNetmask("wlan0")
                }
            }
    return aDict
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# DISK
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# get_size in KB, MB, GB, TB, PB
#-----------------------------------------------------------------------------
def get_size(bytes, suffix="B"):
    """
    Scale bytes to its proper format
    e.g:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'
    """
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor
#-----------------------------------------------------------------------------
# getDiskInfoFromMountpoint     return a dict
#-----------------------------------------------------------------------------
def getDiskInfoFromMountpoint(s): # /  or /boot
    DiskInfo = {}
    partitions = psutil.disk_partitions()
    for partition in partitions:
        if partition.mountpoint == s:
            try:
                partition_usage = psutil.disk_usage(partition.mountpoint)
                DiskInfo = {
                    "MountPoint": s,
                    "Device":   partition.device,
                    "FS":       partition.fstype,
                    "Used":     get_size(partition_usage.used),
                    "Free":     get_size(partition_usage.free),
                    "Percent":  "{}%".format(partition_usage.percent)
                }
            except PermissionError:
                # this can be catched due to the disk that isn't ready
                continue
    return DiskInfo
#-----------------------------------------------------------------------------
# getDiskDict
#-----------------------------------------------------------------------------
def getDiskDict(): # /  or /boot
    aDict ={}
    rootDict = getDiskInfoFromMountpoint("/")
    bootDict = getDiskInfoFromMountpoint("/boot")
    if bool(bootDict):
        aDict = {"DiskRoot" : rootDict,
            "DiskBoot": bootDict
        }
    else:
        aDict = {"DiskRoot" : rootDict}
    return aDict
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# Temperature
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#----------------------------------------------
#   getTempDict
#----------------------------------------------
def getTempDict():
    aDict ={}
    cpu = CPUTemperature()
    aDict = {"Temperature": cpu.temperature }
    return aDict
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# System Info
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# getSystemInfoDict     
#-----------------------------------------------------------------------------
def getSystemInfoDict(): # returns a dictionnary
    #----------------------------------------------
    platformDict = getSystemDict()
    #----------------------------------------------
    BootTimeDict = getBootTimeDict()
    #----------------------------------------------
    CPUDict = getCPUDict()
    #----------------------------------------------
    MemDict = getMemDict()
    SWAPDict = getSWAPDict()
    #----------------------------------------------
    cpu = CPUTemperature()
    #----------------------------------------------
    DiskDict = getDiskDict()
    #----------------------------------------------
    NetworkDict = getNetworkDict()
    #----------------------------------------------
    SysDict = {}
    SysDict = { "Platform": platformDict, 
                "BootTime": BootTimeDict, 
                "CPU": CPUDict,
                "Memory": MemDict,
                "Swap": SWAPDict,
                "Network": NetworkDict,
                "Disk": DiskDict,
                "Temperature":  cpu.temperature
              }
    return SysDict
