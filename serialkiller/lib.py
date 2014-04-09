#!/usr/bin/env python
# -*- coding: utf-8 -*-

__authors__ = 'Bruno Adelé <bruno@adele.im>'
__copyright__ = 'Copyright (C) 2013 Bruno Adelé'
__description__ = """timeseries database with reduce system"""
__license__ = 'GPL'
__version__ = '0.0.2'

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
    def __init__(self, directory, sensorid, ptype='number', ext=".data"):
        # Check sensorid param
        ids = sensorid.split(':')
        if len(ids) != 3:
            raise Exception("Bad sensorid")

        # Init fields
        self._directory = directory
        self._sensorid = sensorid
        self._lines = []
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
            self.configs['type'] = ptype
            calctype = ptype

        # Try to load type object
        try:
            self._typeobj = sktypes.newObj(calctype)
        except ImportError:
            raise Exception("The %s type not exist" % ptype)

        self._configs = self.readConfigs(update=True)

    @property
    def sensorid(self):
        """Get sensorid"""
        return self._sensorid

    @property
    def lines(self):
        """Get lines"""

        return self._lines

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
        if 'title' not in self.configs:
            return ''

        return self.configs['title']

    def __del__(self):
        # Close file before destroy this object
        if self._file:
            fcntl.flock(self._file, fcntl.LOCK_UN)
            self._file.close()

    def getFilename(self, ext='.data'):
        """Get sensor fullname"""
        filename = '%s/%s' % (
            self._directory,
            self._sensorid.replace(':', '/')
        )

        if ext:
            filename += ext

        return filename

    def addAtEnd(self, obj):
        """Add a binary data at the end of file"""
        if self._file:
            try:
                fcntl.flock(self._file, fcntl.LOCK_EX)
                self._file.seek(0, 2)
                self._file.write(obj.rawdata)
            finally:
                fcntl.flock(self._file, fcntl.LOCK_UN)

    def addEvent(self, obj):
        self.addAtEnd(obj)

    def addValue(self, obj):
        try:
            fcntl.flock(self._file, fcntl.LOCK_EX)
            self.tail(2)
            if len(self.lines) < 2:
                # No enough datas for compare
                self.addAtEnd(obj)
            else:
                samevalue = True
                if 'roundvalue' in self.configs:
                    for roundname, roundvalue in self.configs['roundvalue'].iteritems():
                        roundvalue = float(roundvalue)
                        delta0 = abs(obj.values[roundname] - self.lines[0].values[roundname])
                        delta1 = abs(obj.values[roundname] - self.lines[1].values[roundname])
                        samevalue = samevalue and (delta0 <= roundvalue and delta1 <= roundvalue)
                else:
                    samevalue = str(obj.value) == str(self.lines[0].value) and str(obj.value) == str(self.lines[1].value)

                if samevalue:
                    self.rewind(self._file, 1)
                    self._file.truncate()
                    self._file.write(obj.rawdata)
                else:
                    self.addAtEnd(obj)

        finally:
            fcntl.flock(self._file, fcntl.LOCK_UN)

    def completeConfigsForType(self, configs=None):
        """Complete configs list with not seted configs"""
        if not configs:
            configs = dict()

        # noinspection PyProtectedMember
        for configname, value in self._typeobj._defaultconfigs.iteritems():
            if configname not in configs and '#%s' % configname not in configs:
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
                configs = changeconfigs
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

    def setProperty(self, pname, pvalue):
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
            self.setProperty(k, v)

        self.saveConfigs(self._configs)

    def readLines(self, fileobj, nb=1):
        """
        Source: http://stackoverflow.com/questions/136168/get-last-n-lines-of-a-file-with-python-similar-to-tail
        :param nb:
        :param addmetainfo:
        :return:
        """
        offset = None
        self._lines = []

        # File not opened
        if not fileobj:
            return ""

        try:
            fcntl.flock(fileobj, fcntl.LOCK_EX)

            avg_line_length = 74
            to_read = nb + (offset or 0)

            while 1:
                try:
                    fileobj.seek(-(avg_line_length * to_read), 2)
                except IOError:
                    # woops.  apparently file is smaller than what we want
                    # to step back, go to the beginning instead
                    fileobj.seek(0)

                pos = fileobj.tell()
                lines = fileobj.read().splitlines()
                if len(lines) >= to_read or pos == 0:
                    return lines[-to_read:offset and -offset or None]
                avg_line_length *= 1.3

                return ""

        finally:
            fcntl.flock(fileobj, fcntl.LOCK_UN)

    def rewind(self, fileobj, nb):
        # No file
        if not fileobj:
            return 0

        # Calc content size
        size = 1  # first find empty line with \n
        lines = self.readLines(fileobj, nb)
        for line in lines:
            size += len(line)

        # Rewind
        try:
            fcntl.flock(fileobj, fcntl.LOCK_EX)
            fileobj.seek(-size, 1)
        finally:
            fcntl.flock(fileobj, fcntl.LOCK_UN)

        return size

    def forward(self, fileobj, nb):

        # No file
        if not fileobj:
            return 0

        # Get and verify skline size
        try:
            fcntl.flock(fileobj, fcntl.LOCK_EX)
            size_start = ord(fileobj.read(1))
            fileobj.seek(size_start)
            size_end = ord(fileobj.read(1))
            if size_start != size_end:
                raise Exception("No same size")

            fileobj.seek(0)

        except:
            return 0
        finally:
            fcntl.flock(fileobj, fcntl.LOCK_UN)

        # Forward
        try:
            fcntl.flock(fileobj, fcntl.LOCK_EX)
            fileobj.seek(0, 2)
            endfile = fileobj.tell()

            fileobj.seek(0)
            if nb == 0:
                return size_end

            for i in range(nb):
                fileobj.seek(size_end - 1, 1)
                pos = fileobj.tell()

                if pos > endfile:
                    return 0

                size_end = ord(fileobj.read(1))

            fileobj.seek(-1, 1)
            size_start = ord(fileobj.read(1))
            fileobj.seek(-1, 1)

        finally:
            fcntl.flock(fileobj, fcntl.LOCK_UN)

        return size_start

    def readObj(self, fileobj, size):
        bline = fileobj.read(size)
        if not bline:
            return None

        obj = sktypes.newObj(self.type)
        obj.decodeBinary(bline)

        return obj

    def readBlockSize(self, fileobj):
        try:
            fcntl.flock(fileobj, fcntl.LOCK_EX)
            sizetoread = fileobj.read(4)
            fileobj.seek(-1, 1)
        except:
            sizetoread = 0

        return sizetoread

    def tail(self, nb=1, addmetainfo=False):
        self._lines = []

        # Try read lines
        lines = self.readLines(self._file, nb)
        if len(lines) == 0:
            return 0

        # # Read the lines
        for line in lines:
            obj = sktypes.newObj(self.type, rawdata=line)
            self.lines.append(obj)

        # Complete extra info
        if addmetainfo:
            self.addMetaInfo(self._lines)

        return 0

    def last(self):
        size = len(self.lines)
        if size <= 0:
            return None

        return self.lines[size - 1]

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
            unavailableconf = 600
            obj.unavailable = None
            if 'unavailable' in self.configs:
                unavailableconf = float(self.configs['unavailable'])

            now = time.time()
            delta = now - obj.time
            obj.unavailable = None
            if delta >= unavailableconf:
                obj.unavailable = delta

            # check limitation state
            obj.state = ''
            check = ['crit', 'warn', 'succ', 'info', 'unkn']
            for limitname in check:
                # Check crit in order 'crit', 'warn', 'succ', 'info', 'unkn'
                if not obj.state:
                        if 'limit' in self.configs and 'limits' in self.configs['limit']:
                            if limitname in self.configs['limit']['limits']:
                                # octalprotection = obj.value.lstrip('0')
                                test = 'float(%s) %s' % (obj.value, self.configs['limit']['limits'][limitname])
                                result = eval(test)

                                if result:
                                    obj.state = limitname

    def datasToJSON(self):
        jsondatas = []

        for d in self.lines:
            jsondatas.append(d.value)

        return jsondatas

    def reduce(self, **kwargs):

        tmpfile = None
        try:
            fcntl.flock(self._file, fcntl.LOCK_EX)

            # Copy file
            shutil.copy2(self._filename, self.getFilename('.copy'))

            tmpfile = open(self.getFilename('.copy'))
            if tmpfile:
                fcntl.flock(tmpfile, fcntl.LOCK_EX)

                # Empty the file
                self._file.seek(0)
                self._file.truncate()
                tmpfile.seek(0)

                line = tmpfile.readline()
                while line:
                    data = sktypes.newObj(self.type, rawdata=line)
                    self.addValue(data)

                    line = tmpfile.readline()

        finally:
            fcntl.flock(self._file, fcntl.LOCK_UN)
            if tmpfile:
                fcntl.flock(tmpfile, fcntl.LOCK_UN)
                os.remove(self.getFilename('.copy'))

    def SensorInfos(self, **kwargs):
        """Get sensor informations"""
        self._lines = []

        tail = None
        if 'tail' in kwargs:
            tail = int(kwargs['tail'])

        self.tail(nb=tail, addmetainfo=True)

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

        # Compute statistic
        oldvalue = None
        for obj in self._lines:
            size += 1
            #sizesum += obj.size
            valuesum += float(obj.value)

            if oldvalue:
                deltasum += abs(oldvalue - float(obj.value))

            oldvalue = float(obj.value)

            # Check value
            if float(obj.value) < minvalue:
                minvalue = float(obj.value)
                minvaluedate = obj.time

            if float(obj.value) > maxvalue:
                maxvalue = float(obj.value)
                maxvaluedate = obj.time

            # Check time
            if obj.time < mindate:
                mindate = obj.time

            if obj.time > maxdate:
                maxdate = obj.time

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
            elif kwargs['format'] == 'csv':
                content = self.convertSensorDatas2CSV(**kwargs)
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
            }
        )

        return content

    def convertSensorDatas2Txt(self, **kwargs):
        lines = []
        for r in self.lines:
            lines.append([format_datetime(r.time), r.convert2text(self.configs)])

        header = ['Time', 'Value']
        return tabulate(lines, headers=header)

    def convertSensorDatas2CSV(self, **kwargs):
        content = ""

        for r in self._lines:
            content += '%s,%s\n' % (r.time, r.value)

        return content


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
            try:
                obj = Sensor(self._directory, sensor)
                obj.tail(2, addmetainfo=True)

                lsize = len(obj.lines)
                if lsize > 0:
                    idx = min(1, lsize - 1)
                    lasts[sensor] = dict()
                    lasts[sensor]['configs'] = obj.configs
                    lasts[sensor]['last'] = obj.lines[idx]
            except Exception:
                print "Exception on %s sensor" % sensor
                raise

        return lasts

    def convertSensorsListTo(self, **kwargs):
        # Convert
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
        for sensorid, value in iter(sorted(lasts.iteritems())):
            state = ''
            last = value['last']

            if last.unavailable:
                state = 'X'

            # Add last value
            line = [sensorid, state, format_datetime(last.time), last.metadata['configs']['title'], last.text]
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
