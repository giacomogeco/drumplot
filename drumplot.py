import sys
import os
import json
import numpy as np
from scipy import signal
from scipy.signal import butter, lfilter

import urllib.request
from urllib.parse import unquote

import math

import datetime
import time
import calendar
import imp

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import glob
import fnmatch


#------------------------ LOAD INPUTS from configfile
#print '... loading input parameters'
network = 'geco'
path_config = os.curdir+'/configfiles/'+network+'/'
#file_config = glob.glob(path_config+'*.txt')
listOfFiles = os.listdir(path_config)
pattern = "*.txt"
i=0
file_config={}
for entry in listOfFiles:
    if fnmatch.fnmatch(entry, pattern):
        file_config[i]= entry
        i +=1

nfile_config = sys.getsizeof(file_config)
modname = 'stationparameters'

colors = ['black','red','blue','green']

#------------------------ FILTER
def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = lfilter(b, a, data)
    return y


# Reads data and draws a drumplot
# The image is saved as a png with tmin in the filename
def renderDrumplot(key, station, path, tmin, tmax, I):
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

    print(x)

    if x.size == 0:
        x=0
        y=0
        print('... No data')
    else:
        y = x[:, 1]
        # Filtering
        y = y - np.mean(y)
        # ------------------------ FILTER
        if I.filter:
            print('... filtering data')
            #y.filter('bandpass', freqmin=I.fqmin, freqmax=I.fqmax)  # >> filter (Butterworth-Bandpass)
            #b, a = butter_bandpass(I.fqmin, I.fqmax, I.fs, order=3)
            y = butter_bandpass_filter(y, I.fqmin, I.fqmax, I.fs, order=3)

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
    name = (I.stationame+'-'+I.id+'-drumplot-{}').format(tmin.replace('%20', ' ').replace(':', ''))
    print(name)
    if not os.path.exists(path):
        os.makedirs(path)
    fig.savefig('{path}/{name}.png'.format(path=path, name=name), transparent=True, dpi=my_dpi)

    plt.close(fig)


# Render now
tstart = datetime.datetime.utcnow()
tstart = tstart.replace(second=0)
tstart = tstart.replace(microsecond =0)
print(tstart)
while 1:
    # Get the timestamps
    tmax = datetime.datetime.utcnow()
    #print(tmax)
    if tmax > tstart :
        print('... start printig line')
        tmin  = calendar.timegm(tstart.utctimetuple())
        tmin = math.floor(tmin/900)*900
        tmin = datetime.datetime.utcfromtimestamp(tmin)
        print(tmin)
        print(tmax)
        dt = tmax-tmin
        print(dt.seconds)

        for i in file_config:
            file = path_config + file_config[i]
            I = imp.load_source(modname, file)
            key = I.key  # sys.argv[1]
            station = I.id  # sys.argv[2]
            path = I.imgdir  # sys.argv[3]

            if dt.seconds >= 60 :
                renderDrumplot(key, station, path, tmin.strftime('%Y-%m-%d%%20%H:%M:00'), tmax.strftime('%Y-%m-%d%%20%H:%M:%S'),I)
            else :
                print("... scrolling line")
                tdelta = datetime.timedelta(minutes=15)
                tmin = tmax - tdelta
                renderDrumplot(key, station, path, tmin.strftime('%Y-%m-%d%%20%H:%M:00'), tmax.strftime('%Y-%m-%d%%20%H:%M:%S'),I)

            tstart = tstart + datetime.timedelta(minutes = +1)
            print(tstart)

    time.sleep(5)
