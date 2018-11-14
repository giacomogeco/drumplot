
import datetime as dt
from datetime import datetime
import time
import calendar
import json
import numpy as np
from numpy import vstack
import urllib
import pymysql.cursors



def isrpLoadSensorParameters(station_id):
    # Connect to the database
    conn = pymysql.connect(host='85.10.202.61',
                           user='geco',
                           password='geco-company-2018',
                           db='GeCoMonit',
                           cursorclass=pymysql.cursors.DictCursor)
    try:

        with conn.cursor() as cursor:
            # Read a single record
            sql = "SELECT * FROM `sensors` WHERE `station_id` = " + "'" + station_id + "'"
            out = cursor.execute(sql)
            out = cursor.fetchall()
            sensorsType = np.dtype({'names': ('smp', 'id', 'gain', 'type', 'lon', 'lat', 'ele', 'statio_id'),
                                    'formats': ('uint8', 'uint8', 'f16', 'U32', 'f8', 'f8', 'uint8', 'U3')})
            nSensors = len(out)
            sensors = np.zeros(nSensors, dtype=sensorsType)
            sensors = out
    finally:
        conn.close()

    return sensors

to = "2018-11-14T05:00:00"
te = "2018-11-14T05:30:00"
station_id = 'LVN'


sensors = isrpLoadSensorParameters(station_id)

ti_str = datetime.strptime(to, '%Y-%m-%dT%H:%M:%S')
tf_str = datetime.strptime(te, '%Y-%m-%dT%H:%M:%S')
t1 = ti_str - dt.timedelta(minutes=+1)
t2 = tf_str + dt.timedelta(minutes=+1)
tmin = t1.strftime('%Y-%m-%d%%20%H:%M:%S')
tmax = t2.strftime('%Y-%m-%d%%20%H:%M:%S')

idx = 0
dat = []
for i in range(0,len(sensors)):
    try:
        domain = sensors[i]['serverAdrs']
        location = sensors[i]['serverApi']
        key = sensors[i]['serverKey']
        station = sensors[i]['id']
        args = "key={key}&id={id}&limit=1000&tmin={tmin}&tmax={tmax}&json=true".format(id=station, tmin=tmin, tmax=tmax,
                                                                            key=key)
        req = "{d}/{p}?{args}".format(d=domain, p=location, args=args)
        print(req)
        #TODO check server running and send ServerStatusFlag
        t1_start = time.perf_counter()
        with urllib.request.urlopen(req) as url:
            data = json.loads(url.read().decode())
        t1_stop = time.perf_counter()
        etime = int(t1_stop - t1_start)
        print('Server Response Time ID ' + str(sensors[i]['id']) + ' = ' + str(etime) + ' secs')

        out = np.array(data["values"])
        if out.size == 0:
            print('Empty Data from ID ' + str(sensors[i]['id']))
            continue
        else:
            print('Data from ID ' + str(sensors[i]['id']) + ' = ' + str(out.size))
            s = out[:, 0]
            d = out[:, 1]

            # ii = np.where(s > 0)
            # s = s[ii]
            # d = d[ii]

            ti = calendar.timegm(ti_str.utctimetuple()) * 1000
            tf = calendar.timegm(tf_str.utctimetuple()) * 1000
            ii = np.where((s > np.asarray(ti)) & (s < np.asarray(tf)))
            s = s[ii]
            d = d[ii]

            print(d.size)

            if idx == 0:
                dat = d
                secs = s
                idx = 1
            else:
                dat = vstack((dat, d))

                secs = vstack((secs, s))

    except:
        print("Server ID " + str(sensors[i]['id']) + " failed")

        continue

timestamp = secs