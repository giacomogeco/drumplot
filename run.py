from drumplot import *
import sys
import os

import math
import datetime
import time
import calendar
import imp

import matplotlib
matplotlib.use('TkAgg')
import fnmatch

#------------------------ LOAD INPUTS from configfile
#print '... loading input parameters'
network = 'oyace'
path_config = os.curdir+'/configFiles/'+network+'/'
#file_config = glob.glob(path_config+'*.txt')
listOfFiles = os.listdir(path_config)
pattern = "*.txt"
i=0
file_config=[]
for entry in listOfFiles:
    print(entry)
    if fnmatch.fnmatch(entry, pattern):
        if entry.find('_') < 0:
            file_config.insert(i, entry)
            i+=1

nfile_config = len(file_config)
modname = 'stationparameters'

colors = ['blue','blue','blue','blue']

# Render Loop
tstart = datetime.datetime.utcnow()
tstart = tstart.replace(second=0)
tstart = tstart.replace(microsecond =0)
while 1:
    # Get the timestamps
    tmax = datetime.datetime.utcnow()
    if tmax > tstart :
        print('>>> starting drumplot <<<')
        tmin  = calendar.timegm(tstart.utctimetuple())
        tmin = math.floor(tmin/900)*900
        tmin = datetime.datetime.utcfromtimestamp(tmin)
        print('>>> from ' + str(tmin) + ' to ' + str(tmax), ' <<<')
        dt = tmax-tmin

        for i in file_config:
            file = path_config + i
            sensor = imp.load_source(modname, file)
            key = sensor.key  # sys.argv[1]
            station = sensor.id  # sys.argv[2]
            path = sensor.imgdir  # sys.argv[3]

            # RENDERING
            if dt.seconds >= 60 :
                voltage, temperature, gps, ndata, status = renderDrumplot(key, station, path, tmin.strftime('%Y-%m-%d%%20%H:%M:00'), tmax.strftime('%Y-%m-%d%%20%H:%M:%S'),sensor)
            else:
                print('>>> drumplot scrolling line <<<')
                tdelta = datetime.timedelta(minutes=15)
                tmin = tmax - tdelta
                voltage, temperature, gps, ndata, status = renderDrumplot(key, station, path, tmin.strftime('%Y-%m-%d%%20%H:%M:00'), tmax.strftime('%Y-%m-%d%%20%H:%M:%S'),sensor)

            dataP = 100 * (ndata / (dt.seconds * sensor.smp))
            print('>>> ' + str(round(dataP,1)) + '% of data <<<')
            # POSTING STATUS
            #TODO ask beni for voltage ad gps status
            upTime = tmax.strftime('%Y-%m-%dT%H:%M:%S.FFFZ')

            r = drumplotPostStatus(sensor, upTime, voltage, temperature, gps)

            tstart = tstart + datetime.timedelta(minutes = +1)

    drumplotSaveLog('pLog.txt')

    time.sleep(5)