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
import fcntl
import fnmatch
import shutil
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


class Sensor(object):
    def __init__(self, directory, sensorid, type='byte', ext=".data"):
        # Check sensorid param
        ids = sensorid.split(':')
        if len(ids) != 3:
            raise Exception("Bad sensorid")

        # Init fields
        self._directory = directory
        self._sensorid = sensorid
        self._datas = []
        self._file = None
        self._filename = self.getFilename(ext)
        self._configs = {}

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
            self._configs = self.readConfigs()
            calctype = self.configs['type']

        if not calctype:
            # Not found type in sensor configuration
            self.configs['type'] = type
            calctype = type

        # Try to load type object
        sktypes.newObj(calctype)
        try:
            self._typeobj = sktypes.newObj(calctype)
        except ImportError:
            raise Exception("The %s type not exist" % type)

        self._configs = self.readConfigs(update=True)

    @property
    def sensorid(self):
        """Get sensorid"""
        return self._sensorid

    @property
    def datas(self):
        """Get datas"""

        return self._datas

    @property
    def configs(self):
        """Get configs"""

        return self._configs

    @property
    def type(self):
        """Get type"""
        if 'type' not in self.configs:
            raise Exception("No type found")

        return self._configs['type']

    @property
    def title(self):
        """Get title"""
        if 'title' not in self.config:
            return ''

        return self.configs['title']

    def __del__(self):
        # Close file before destroy this object
        if self._file:
            fcntl.flock(self._file, fcntl.LOCK_UN)
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
            try:
                fcntl.flock(self._file, fcntl.LOCK_EX)
                self._file.seek(0, 2)
                self._file.write(obj.toBinary())
            finally:
                fcntl.flock(self._file, fcntl.LOCK_UN)

    def addEvent(self, obj):
        self.add2Log(obj)

    def addValue(self, obj):
        self.tail(2)
        if len(self.datas) < 2:
            # No enough datas for compare
            self.add2Log(obj)
        else:
            if 'roundvalue' in self.configs:
                roundvalue = self.configs['roundvalue']
                delta0 = abs(obj.value - self.datas[0].value)
                delta1 = abs(obj.value - self.datas[1].value)
                samevalue = delta0 <= roundvalue and delta1 <= roundvalue
            else:
                samevalue = obj.value == self.datas[0].value and obj.value == self.datas[1].value

            if samevalue:
                try:
                    fcntl.flock(self._file, fcntl.LOCK_EX)
                    self.rewind(1)
                    self._file.write(obj.toBinary())
                finally:
                    fcntl.flock(self._file, fcntl.LOCK_UN)
            else:
                self.add2Log(obj)

    def completeConfigsForType(self, configs=dict()):
        """Complete configs list with not seted configs"""
        for configname, value in self._typeobj._defaultconfigs.iteritems():
            if not configname in configs and '#%s' % configname:
                # t
                comment = ''
                if 'comment' in value and value['comment']:
                    comment = '#'

                if isinstance(value['value'], str):
                    configs['%s%s' % (comment, configname)] = str(value['value']) % {
                        'sensorid': self._sensorid,
                        'type': self.type
                    }
                else:
                    configs['%s%s' % (comment, configname)] = value['value']

        return configs

    def readConfigs(self, update=False):
        # Try open file
        lines = []
        filename = self.getFilename('.conf')

        configs = {}

        exists = os.path.isfile(filename)
        if exists:
            lines = open(filename).read()
            configs = json.loads(lines)

        if exists and update or not exists:
            oldconfig_size = len(configs)
            changeconfigs = self.completeConfigsForType(configs)
            changeconfigs_size = len(changeconfigs)
            changed = (oldconfig_size - changeconfigs_size) != 0
            if changed:
                self.saveConfigs(configs)

        return configs

    def saveConfigs(self, configs):
        filename = self.getFilename('.conf')
        with open(filename, 'w') as f:
            jsontext = json.dumps(
                configs, sort_keys=True,
                indent=4, separators=(',', ': ')
            )
            f.write(jsontext)
            f.close()

    def setProperty(self, pname, pvalue, savetofile=True):
        commented = '#%s' % pname
        if pvalue:
            if commented in self._configs:
                del self._configs[commented]
            self._configs[pname] = pvalue.strip()
        else:
            if pname in self._configs:
                self._configs[commented] = self._configs[pname]
                #del self._properties[pname]

        self.saveConfigs(self._configs)

    def setConfigs(self, **kwargs):
        for k, v in kwargs.iteritems():
            self.setProperty(k, v, False)

        self.saveConfigs(self._configs)

    def rewind(self, nb):

        # No file
        if not self._file:
            return 0

        # Get and verify skline size
        try:
            fcntl.flock(self._file, fcntl.LOCK_EX)
            self._file.seek(-1, 2)
            size_end = ord(self._file.read(1))
            self._file.seek(-size_end, 2)
            size_start = ord(self._file.read(1))
            if size_start != size_end:
                raise Exception("No same size")
        except:
            return 0
        finally:
            fcntl.flock(self._file, fcntl.LOCK_UN)

        # Rewind
        try:
            fcntl.flock(self._file, fcntl.LOCK_EX)
            pos = self._file.tell()
            for i in range(nb - 1):
                if pos >= 0 and pos - size_start - 1 < 0:
                    break

                self._file.seek(-size_start - 1, 1)
                size_start = ord(self._file.read(1))
                pos = self._file.tell()

            self._file.seek(-1, 1)
        finally:
            fcntl.flock(self._file, fcntl.LOCK_UN)

        return size_start

    def forward(self, nb):

        # No file
        if not self._file:
            return 0

        # Get and verify skline size
        try:
            fcntl.flock(self._file, fcntl.LOCK_EX)
            size_start = ord(self._file.read(1))
            self._file.seek(size_start)
            size_end = ord(self._file.read(1))
            if size_start != size_end:
                raise Exception("No same size")

            self._file.seek(0)

        except:
            return 0
        finally:
            fcntl.flock(self._file, fcntl.LOCK_UN)

        # Forward
        try:
            fcntl.flock(self._file, fcntl.LOCK_EX)
            self._file.seek(0, 2)
            endfile = self._file.tell()

            self._file.seek(0)
            if nb == 0:
                return size_end

            for i in range(nb):
                self._file.seek(size_end - 1, 1)
                pos = self._file.tell()

                if pos > endfile:
                    return 0

                size_end = ord(self._file.read(1))

            self._file.seek(-1, 1)
            size_start = ord(self._file.read(1))
            self._file.seek(-1, 1)

        finally:
            fcntl.flock(self._file, fcntl.LOCK_UN)

        # Return the last skline size
        return size_start

    def readObj(self, size):
        bline = self._file.read(size)
        if not bline:
            return None

        obj = sktypes.newObj(self.type)
        obj.decodeBinary(bline)

        return obj

    def loadToDatas(self):
        try:
            fcntl.flock(self._file, fcntl.LOCK_EX)
            sizetoread = ord(self._file.read(1))
            self._file.seek(-1, 1)

            obj = self.readObj(sizetoread)
            while obj:
                self._datas.append(obj)
                obj = self.readObj(obj.size)
        except TypeError:
            pass

        finally:
            fcntl.flock(self._file, fcntl.LOCK_UN)

    def tail(self, nb=1, addmetainfo=False):
        self._datas = []

        # No file
        if not self._file:
            return 0

        nb = (nb)

        # Read the nb skline
        self.rewind(nb)
        self.loadToDatas()

        # Complete extra info
        if addmetainfo:
            self.addMetaInfo(self.datas)

        return 0

    def last(self):
        size = len(self.datas)
        if size <= 0:
            return None

        return self.datas[size - 1]

    def addMetaInfo(self, values):
        """Add extra infos on a minimal type object"""
        for idx in range(len(values)):
            obj = values[idx]

            # Add configs information
            obj.metadata['configs'] = self.configs

            # Convert value in text
            obj.text = obj.convert2text(self.configs)

            # Check same value since
            if idx > 0:
                obj.since = values[idx].time - values[idx - 1].time
            else:
                obj.since = None

            # Check if unavailable data
            unavailable = 600
            obj.unavailable = False
            if 'unavailable' in self.configs:
                unavailable = float(self.configs['unavailable'])

            now = time.time()
            delta = now - obj.time
            obj.unavailable = delta >= unavailable

            # check limitation state
            obj.state = ''
            check = ['crit', 'warn', 'succ', 'info', 'unkn']
            for limitname in check:
                # Check crit in order 'crit', 'warn', 'succ', 'info', 'unkn'
                if not obj.metadata['state'] and 'limit_%s' % limitname in self.configs:
                    test = '%s %s' % (obj.value, self.configs['limit_%s' % limitname])
                    res = eval(test)
                    if res:
                        state = '%s' % limitname

            if state:
                obj.state = state

    def datasToJSON(self):
        jsondatas = []

        for d in self.datas:
            jsondatas.append(d.metadata)

        return jsondatas

    def reduce(self):
        self._datas = []

        try:
            fcntl.flock(self._file, fcntl.LOCK_EX)

            # Copy file
            print "Copy"
            shutil.copy2(self._filename,self.getFilename('.copy'))

            # Load current content
            print "LOAD"
            self._file.seek(0)
            self.loadToDatas()
            orig = self._datas
            print "LEN: %s" % len(orig)

            # Empty the file
            print "Empty"
            self._file.seek(0)
            self._file.truncate()

            print "REDUCE"
            for d in orig:
                self.addValue(d)
        finally:
            fcntl.flock(self._file, fcntl.LOCK_UN)

    def SensorInfos(self, **kwargs):
        """Get sensor informations"""
        self._datas = []

        tail = None
        if 'tail' in kwargs:
            tail = int(kwargs['tail'])

        try:
            fcntl.flock(self._file, fcntl.LOCK_EX)

            if tail:
                # Rewind nb lines
                self.rewind(nb=tail)
            else:
                # Full file
                self._file.seek(0)

            infos = {}
            size = 0
            sizesum = 0
            valuesum = 0
            deltasum = 0
            minvalue = 4294967295
            maxvalue = -4294967295
            minvaluedate = 4294967295
            maxvaluedate = 0
            mindate = 4294967295
            maxdate = 0

            # Get the size of first block
            try:
                sizetoread = ord(self._file.read(1))
                self._file.seek(-1, 1)
            except:
                sizetoread = 0

            # Compute statistic
            oldvalue = None
            if sizetoread > 0:
                obj = self.readObj(sizetoread)
                while obj:
                    size += 1
                    sizesum += obj.size
                    valuesum += obj.value

                    if oldvalue:
                        deltasum += abs(oldvalue - obj.value)

                    oldvalue = obj.value

                    # Check value
                    if obj.value < minvalue:
                        minvalue = obj.value
                        minvaluedate = obj.time

                    if obj.value > maxvalue:
                        maxvalue = obj.value
                        maxvaluedate = obj.time

                    # Check time
                    if obj.time < mindate:
                        mindate = obj.time

                    if obj.time > maxdate:
                        maxdate = obj.time

                    obj = self.readObj(obj.size)

        finally:
            fcntl.flock(self._file, fcntl.LOCK_UN)

        infos['mindate'] = mindate
        infos['maxdate'] = maxdate
        infos['minvalue'] = minvalue
        infos['maxvalue'] = maxvalue
        infos['minvaluedate'] = minvaluedate
        infos['maxvaluedate'] = maxvaluedate
        infos['avgvalue'] = valuesum / size
        infos['avgdelta'] = deltasum / size
        infos['avgsize'] = sizesum / size
        infos['nblines'] = size

        return infos

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
        datas = self.datasToJSON()
        jsondatas = json.dumps(datas, separators=(',', ': '))

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
                'samples': len(datas),
                'datas': jsondatas,
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
        lines = []
        for r in self.datas:
            lines.append([format_datetime(r.time), r.convert2text(self.configs)])

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


    def getLastSensorsValue(self):
        lasts = dict()
        for sensor in self.getSensorsIds():
            obj = Sensor(self._directory, sensor)
            obj.tail(2, addmetainfo=True)

            lsize = len(obj.datas)
            if lsize > 0:
                idx = min(1, lsize - 1)
                lasts[sensor] = dict()
                lasts[sensor]['configs'] = obj.configs
                lasts[sensor]['last'] = obj.datas[idx]

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
        lasts = self.getLastSensorsValue()

        lines = []
        for sensorid, value in lasts.iteritems():
            state = ''
            if value.unavailable:
                state = 'X'

            # Add last value
            line = [sensorid, state, format_datetime(value.time), value.metadata['configs']['title'], value.text]
            lines.append(line)

        header = ['SensorId', 'S', 'Time', 'Title', 'Value']

        return tabulate(lines, headers=header)

    def convertSensorsList2Html(self):
        # Get lasts values
        lasts = self.getLastSensorsValue()

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
        lasts = self.getLastSensorsValue()

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
