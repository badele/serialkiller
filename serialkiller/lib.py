#!/usr/bin/env python
# -*- coding: utf-8 -*-

__authors__ = 'Bruno Adelé <bruno@adele.im>'
__copyright__ = 'Copyright (C) 2013 Bruno Adelé'
__description__ = """timeseries database with reduce system"""
__license__ = 'GPL'
__version__ = '0.0.1'

# System
import os
import re
import time
import json
import fnmatch
from datetime import datetime

# Others
import jinja2
from tabulate import tabulate

# Serialkiller
from serialkiller import sktypes


def saveto(filename, content):
    out = open(filename, 'wb')
    out.write(content)
    out.close()


class SerialKiller(object):
    def __init__(self, directory, sensorid, type='byte', ext=".data"):
        # Check sensorid param
        ids = sensorid.split(':')
        if len(ids) != 3:
            raise Exception("Bad sensorid")

        # Init fields
        self._directory = directory
        self._sensorid = sensorid
        self._file = None
        self._filename = self.getFilename(ext)
        self._properties = {}

        # Create node directory
        self.createNodeDirectories()

        # Create file if nos exists
        if not os.path.isfile(self._filename):
            self._file = open(self._filename, 'w')
            self._file.close()

        # Try open file
        if os.path.isfile(self._filename):
            self._file = open(self._filename, 'r+')

        # Try to get type from sensor configuration exist
        confname = self.getFilename('.conf')
        calctype = None
        if os.path.isfile(confname):
            self._properties = self.readProperties()
            calctype = self.properties['type'] 

        # Not found type in sensor configuration
        if not calctype:
            self.properties['type'] = type
            calctype = type

        # Try to load type object
        sktypes.newObj(calctype)
        try:
            self._typeobj = sktypes.newObj(calctype)
        except ImportError:
            raise Exception("The %s type not exist" % type)

        self._properties = self.readProperties()

    @property
    def sensorid(self):
        """Get sensorid"""
        return self._sensorid

    @property
    def properties(self):
        """Get properties"""

        return self._properties

    @property
    def type(self):
        """Get type"""
        if 'type' not in self.properties:
            raise Exception("No type found")

        return self._properties['type']

    @property
    def title(self):
        """Get title"""
        if 'title' not in self.properties:
            return ''

        return self._properties['title']

    def __del__(self):
        # Close file before destroy this object
        if self._file:
            self._file.close()

    def getFilename(self, ext='.data'):
        # Return filename
        filename = '%s/%s' % (
            self._directory,
            self._sensorid.replace(':', '/')
        )

        if ext:
            filename += ext

        return filename

    def add2Log(self, obj):
        if self._file:
            self._file.seek(0, 2)
            self._file.write(obj.toBinary())

    def addEvent(self, obj):
        self.add2Log(obj)

    def addValue(self, obj):
        lasts = self.tail(2)
        if len(lasts) < 2:
            self.add2Log(obj)
        else:
            if obj.value == lasts[0].value and obj.value == lasts[1].value:
                self.rewind(1)
                self._file.write(obj.toBinary())
            else:
                self.add2Log(obj)

    def completeProperties(self, properties=dict()):
        """Complete properties list with not seted properties"""
        for k, v in self._typeobj._defaultproperties.iteritems():
            if not k in properties and '#%s' % k:
                comment = ''
                if 'comment' in v and v['comment']:
                    comment = '#'

                if isinstance(v['value'], str):
                    properties['%s%s' % (comment, k)] = str(v['value']) % {
                        'sensorid': self._sensorid,
                        'type': self.type
                    }
                else:
                    properties['%s%s' % (comment, k)] = v['value']

        return properties

    def readProperties(self):
        # Try open file
        lines = []
        filename = self.getFilename('.conf')

        properties = {}
        if os.path.isfile(filename):
            lines = open(filename).read()
            properties = json.loads(lines)
        else:
            properties = self.completeProperties(properties)
            self.saveProperties(properties)

        return properties

    def saveProperties(self, properties):
        filename = self.getFilename('.conf')
        with open(filename, 'w') as f:
            jsontext = json.dumps(
                properties, sort_keys=True,
                indent=4, separators=(',', ': ')
            )
            f.write(jsontext)
            f.close()

    def setProperty(self, pname, pvalue, savetofile=True):
        commented = '#%s' % pname
        if pvalue:
            if commented in self._properties:
                del self._properties[commented]
            self._properties[pname] = pvalue.strip()
        else:
            if pname in self._properties:
                self._properties[commented] = self._properties[pname]
                #del self._properties[pname]

        self.saveProperties(self._properties)

    def setProperties(self, **kwargs):
        for k, v in kwargs.iteritems():
            self.setProperty(k, v, False)

        self.saveProperties(self._properties)

    def rewind(self, nb):

        # No file
        if not self._file:
            return 0

        # Get and verify skline size
        try:
            self._file.seek(-1, 2)
            size_end = ord(self._file.read(1))
            self._file.seek(-size_end, 2)
            size_start = ord(self._file.read(1))
            if size_start != size_end:
                raise Exception("No same size")
        except:
            return 0

        # Rewind
        pos = self._file.tell()
        for i in range(nb - 1):
            if pos >= 0 and pos - size_start - 1 < 0:
                break

            self._file.seek(-size_start - 1, 1)
            size_start = ord(self._file.read(1))
            pos = self._file.tell()

        self._file.seek(-1, 1)

        # Return the last skline size
        return size_start

    def readObj(self, size):
        bline = self._file.read(size)
        if not bline:
            return None

        obj = sktypes.newObj(self.type)
        obj.decodeBinary(bline)

        return obj

    def tail(self, nb=1):
        lasts = []

        # No file
        if not self._file:
            return lasts

        # Read the nb skline
        sizetoread = self.rewind(nb)
        if sizetoread:
            obj = self.readObj(sizetoread)
            while obj:
                lasts.append(obj)
                obj = self.readObj(obj.size)

        return lasts

    def lastValue(self):
        result = self.tail(1)
        if not result:
            return None

        return result[0]

    def importDatas(self, filename, separator=';', preduce=True):

        count = 0
        with open(filename) as datas:
            for d in datas:
                count += 1
                line = d.strip()
                (ltime, value) = line.split(separator)
                data = sktypes.newObj(self.type, time=ltime, value=value)
                if preduce:
                    self.addValue(data)
                else:
                    self.addEvent(data)

        return count

    def createNodeDirectories(self):
        dirname = os.path.dirname(self._filename)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)

    def convertSensorDatasTo(self, **kwargs):
        if 'format' in kwargs:
            if kwargs['format'] == 'html':
                content = self.convertSensorDatas2Html(**kwargs)
            else:
                content = self.convertSensorDatas2Txt(**kwargs)
        else:
            content = self.convertSensorDatas2Txt(**kwargs)

        return content

    def convertSensorDatas2Html(self, **kwargs):
        tail = 15
        if 'tail' in kwargs:
            tail = int(kwargs['tail'])

        result = self.tail(tail)

        dates = []
        datas = []
        memdate = ''
        memtime = ''
        for r in result:
            testdate = format_datetime(r.time, '%m-%d')
            if testdate != memdate:
                memdate = testdate
                memtime = format_datetime(r.time, '%H:%M')
                dates.append(format_datetime(r.time, '%m-%d %H:%M'))
            else:
                testtime = format_datetime(r.time, '%H:%M')
                if testtime != memtime:
                    memtime = testtime
                    dates.append(format_datetime(r.time, '%H:%M'))
                else:
                    dates.append('')
            datas.append(r.value)

        pydir = os.path.dirname(os.path.realpath(__file__))
        tplfile = '%s/server/templates/sensordatas.tpl' % pydir

        # Prepare template
        tplenv = jinja2.Environment(
            loader=jinja2.FileSystemLoader(searchpath="/")
        )
        tplenv.filters['datetime'] = format_datetime

        template = tplenv.get_template(os.path.abspath(tplfile))

        # Render
        content = template.render(
            {
                'static': '/static',
                'sensorid': self.sensorid,
                'samples': len(result),
                'lasts': result,
                'dates': dates,
                'datas': datas,
                'generated_time': time.time(),
                'state': {
                    'info': 'info',
                    'crit': 'danger',
                    'warn': 'warning',
                    'succ': 'success',
                    'unkn': 'default',
                },
            }
        )

        return content

    def convertSensorDatas2Txt(self, **kwargs):
        tail = 15
        if 'tail' in kwargs:
            tail = int(kwargs['tail'])

        result = self.tail(tail)

        lines = []
        for r in result:
            lines.append([format_datetime(r.time), r.convert2text(self.properties)])

        header = ['Time', 'Value']
        return tabulate(lines, headers=header)


class SerialKillers(object):
    def __init__(self, directory=""):
        # Init fields
        self._directory = directory

        # Create directory if not exists
        if directory:
            if not os.path.isdir(directory):
                os.makedirs(directory)

    def getSensorsIds(self):
        matches = []
        for root, dirnames, filenames in os.walk(self._directory):
            for filename in fnmatch.filter(filenames, '*.data'):
                fullname = os.path.join(root, filename)
                m = re.match(r'.*?/([^/]+)/([^/]+)/([^/]+)\.data', fullname)
                if m:
                    sensorid = '%s:%s:%s' % (m.group(1), m.group(2), m.group(3))
                    matches.append(sensorid)

        return matches

    def getLastsValue(self):
        lasts = {}
        for sensor in self.getSensorsIds():
            obj = SerialKiller(self._directory, sensor)
            p = obj._properties
            v = obj.tail(2)

            if v:
                lsize = len(v)
                idx = min(1, lsize - 1)
                lasts[sensor] = {}
                lasts[sensor]['type'] = v[idx].type
                lasts[sensor]['time'] = v[idx].time
                lasts[sensor]['value'] = v[idx].value
                lasts[sensor]['text'] = v[idx].convert2text(p)
                lasts[sensor]['properties'] = p
                lasts[sensor]['unavailable'] = False
                if idx > 0:
                    lasts[sensor]['since'] = v[1].time - v[0].time
                else:
                    lasts[sensor]['since'] = None

                # Check if unavailable data
                unavailable = 600
                if 'unavailable' in p:
                    unavailable = float(p['unavailable'])

                now = time.time()
                delta = now - lasts[sensor]['time']
                if delta  >= unavailable:
                    lasts[sensor]['unavailable'] = True

                # check limitation state
                state = ''
                check = ['crit', 'warn', 'succ', 'info', 'unkn']
                for c in check:
                # Check crit
                    if not state and 'limit_%s' % c in p:
                        test = '%s %s' % (lasts[sensor]['value'], lasts[sensor]['properties']['limit_%s' % c])
                        res = eval(test)
                        if res:
                            state = '%s' % c

                if state:
                    lasts[sensor]['state'] = state

        return lasts

    def convertSensorsListTo(self, **kwargs):
        # Convert
        content = ""
        if 'format' in kwargs:
            if kwargs['format'] == 'html':
                content = self.convertSensorsList2Html()
            else:
                content = self.convertSensorsList2Txt()
        else:
            content = self.convertSensorsList2Txt()

        return content

    def convertSensorsList2Txt(self):
        lasts = self.getLastsValue()

        lines = []
        for sensorid, sensor in lasts.iteritems():
            # Set value
            if 'title' in sensor['properties']:
                title = sensor['properties']['title']
            else:
                title = ""
            text = sensor['text']
            ltime = sensor['time']
            state = ''
            if sensor['unavailable']:
                state = 'X'

            # Add last value
            print sensor
            line = [sensorid, state, format_datetime(ltime), title, text ]
            lines.append(line)

        header = ['SensorId', 'S', 'Time', 'Title', 'Value']

        return tabulate(lines, headers=header)

    def convertSensorsList2Html(self):
        # Get lasts values
        lasts = self.getLastsValue()

        pydir = os.path.dirname(os.path.realpath(__file__))
        tplfile = '%s/server/templates/sensorslist.tpl' % pydir

        # Prepare template
        tplenv = jinja2.Environment(
            loader=jinja2.FileSystemLoader(searchpath="/")
        )
        tplenv.filters['datetime'] = format_datetime
        tplenv.filters['sincetime'] = format_since

        template = tplenv.get_template(os.path.abspath(tplfile))

        # Render
        content = template.render(
            {
                'lasts': lasts,
                'generated_time': time.time(),
                'state': {
                    'info': 'info',
                    'crit': 'danger',
                    'warn': 'warning',
                    'succ': 'success',
                    'unkn': 'default',
                },
            }
        )

        return content

    def autosetSensors(self):
        lasts = self.getLastsValue()

        for k, v in lasts.iteritems():
            if 'state' in v:
                if v['state'] == 'unkn':
                    print "AUTOFLAG FOR %s" % k


def format_datetime(value, fmt='%Y-%m-%d %H:%M:%S'):
    return format(datetime.fromtimestamp(value), fmt)


def format_since(delta):
    if not delta or delta < 0:
        return "Unknow"

    delta = int(delta)

    if delta < 10:
        return "just now"
    if delta < 60:
        return str(delta) + " seconds ago"
    if delta < 120:
        return "a minute ago"
    if delta < 3600:
        return str(delta / 60) + " minutes ago"
    if delta < 7200:
        return "an hour ago"
    if delta < 86400:
        return str(delta / 3600) + " hours ago"

    if delta < 172800:
        return "Yesterday"
    if delta < 2678400:
        return str(delta / 86400) + " days ago"
    if delta < 31536000:
        return str(delta / 2678400) + " months ago"

    return str(delta / 31536000) + " years ago"
