import sys
import os
import json
import numpy as np
from scipy.signal import butter, lfilter

import urllib.request
import requests
import math
import datetime
import time
import calendar
import imp

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
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

#------------------------ FILTER
def butter_bandpass(lowcut, highcut, fs, order):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

def butter_bandpass_filter(data, lowcut, highcut, fs, order):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = lfilter(b, a, data)
    return y


# Reads data and draws a drumplot
# The image is saved as a png with tmin in the filename
def renderDrumplot(key, station, path, tmin, tmax, sensor):
    print('... Loading data')

    # Prepare the request
    domain = 'http://control.wyssenavalanche.com'
    location = 'app/api/ida/raw.php'
    args = "key={key}&id={id}&json=true&tmin={tmin}&tmax={tmax}".format(id=station, tmin=tmin, tmax=tmax, key=key)
    req = "{d}/{p}?{args}".format(d=domain, p=location, args=args)

    # Load the data
    with urllib.request.urlopen(req) as url:
        data = json.loads(url.read().decode())

    x = np.array(data["values"])

    if x.size == 0:
        x=0
        y=0
        ndata = 0
        temperature = ''
        voltage = ''
        gps = ''
        status = 'OFF-LINE'
        print('!!! W A R N I N G !!! No data from sensor: ' + sensor.id)
    else:
        y = x[:, 1]
        ndata = len(y)
        # Filtering
        y = y - np.mean(y)
        # ------------------------ FILTER
        if sensor.filter:
            print('>>> filtering data <<<')
            #y.filter('bandpass', freqmin=I.fqmin, freqmax=I.fqmax)  # >> filter (Butterworth-Bandpass)
            #b, a = butter_bandpass(I.fqmin, I.fqmax, I.fs, order=3)
            y = butter_bandpass_filter(y, sensor.fqMin, sensor.fqMax, sensor.smp, sensor.filterOrder)

        temperature = ''
        voltage = ''
        gps = ''
        status = 'ON-LINE'

    # Output the graph
    my_dpi = 96
    fig = plt.figure(figsize=(600 / my_dpi, 100 / my_dpi), frameon=False)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis('off')
    plt.ylim(-5, 5)
    plt.xlim(0, 45000)

    i15 = [("00", 0), ("15", 1), ("30", 2), ("45", 3)]
    i15=dict(i15)
    t15=tmin[16:18]
    clr = colors[i15[t15]]
    ax.plot(y, clr, linewidth=1.0)

    # Render and save the graph
    print('... Saveing image')
    name = (sensor.stationame+'-'+sensor.id+'-drumplot-{}').format(tmin.replace('%20', ' ').replace(':', ''))
    print(name)
    if not os.path.exists(path):
        os.makedirs(path)
    fig.savefig('{path}/{name}.png'.format(path=path, name=name), transparent=True, dpi=my_dpi)

    plt.close(fig)

    return voltage, temperature, gps, ndata, status


def drumplotPostStatus(sensor, upTime, voltage, temperature, gps):
    #"2018-09-21T15:00:47.663Z"
    #url = "https://jarvis.gtsu.org/geco/api/v1/status/"

    payload = {
        "array_id": sensor.network,
        "sensor_id": sensor.id,
        "timestamp": upTime,
        "battery": voltage,
        "temperature": temperature,
        "gsm_signal": gps
    }

    headers = {
        'content-type': "application/json",
        'authorization': "Token 38ed5e544b9289afa4154773c2c132e091dd2b47"
    }

    response = requests.request("POST", sensor.statusPostUrl, json=payload, headers=headers)

    return response.text


# Render now
tstart = datetime.datetime.utcnow()
tstart = tstart.replace(second=0)
tstart = tstart.replace(microsecond =0)
print(tstart)
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
            else :
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

    time.sleep(5)
