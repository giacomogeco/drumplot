import os
import json
import numpy as np
from scipy.signal import butter, lfilter

import urllib.request
import requests
import datetime
import imp

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

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


def drumplotSaveLog(pTimeLogFile):
    pTimeLogFile = 'log/' + pTimeLogFile
    if os.path.exists(pTimeLogFile):
        file = open(pTimeLogFile, 'r')
        pT1 = file.read()
        pT1 = datetime.strptime(pT1, '%Y-%m-%d %H:%M:%S')
    else:
        pT1 = dt.datetime.utcnow()
        pT1 = pT1.replace(second=0)
        pT1 = pT1.replace(microsecond=0)
        file = open(pTimeLogFile, 'w')
        file.write(str(pT1))
        file.close()

pTimeLogFile = 'log/pTimeLogFile.txt'
if os.path.exists(pTimeLogFile):
    file = open(pTimeLogFile, 'r')
    pT1 = file.read()
    pT1 = datetime.strptime(pT1, '%Y-%m-%d %H:%M:%S')
else:
    pT1 = dt.datetime.utcnow()
    pT1 = pT1.replace(second=0)
    pT1 = pT1.replace(microsecond=0)
    file = open(pTimeLogFile, 'w')
    file.write(str(pT1))
    file.close()

# Reads data and draws a drumplot
# The image is saved as a png with tmin in the filename
def renderDrumplot(key, station, path, tmin, tmax, sensor):

    # Prepare the request
    domain = 'http://control.wyssenavalanche.com'
    location = 'app/api/ida/raw.php'
    args = "key={key}&id={id}&json=true&tmin={tmin}&tmax={tmax}".format(id=station, tmin=tmin, tmax=tmax, key=key)
    req = "{d}/{p}?{args}".format(d=domain, p=location, args=args)

    # Load the data
    print('>>> Loading data ...')
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


