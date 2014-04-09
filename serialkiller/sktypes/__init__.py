#!/usr/bin/env python
# -*- coding: utf-8 -*-

__authors__ = 'Bruno Adelé <bruno@adele.im>'
__copyright__ = 'Copyright (C) 2013 Bruno Adelé'
__description__ = """timeseries database with reduce system"""
__license__ = 'GPL'
__version__ = '0.0.2'

import sys
import time
import struct
from collections import defaultdict

# Load object type module
def import_objtype(modname, name):
    impmodule = __import__(modname, fromlist=[name])
    return getattr(impmodule, name)


# Intencies object type
def newObj(name, **kwargs):
    modname = 'serialkiller.sktypes.sk%s' % name
    objtype = import_objtype(modname, 'Sk%s' % name.capitalize())

    return objtype(**kwargs)


class SkBase(object):
    def __init__(self, **kwargs):
        self._metadata = dict()
        self._values = None
        self._rawdata = None

        if 'rawdata' in kwargs:
            self.rawdata = kwargs['rawdata']
        else:
            self.values = kwargs

        self._defaultconfigs = {
            'title': {
                'value': 'Please set title for %(sensorid)s sensor'
            },
            'unavailable': {
                'value': 200,
                'comment': True
            },
            'type': {
                'value': '%(type)s'
            },
        }

    # Get dynamically property
    def __getattr__(self, attr):
        if not self._values:
            values = self.rawdata2Values()
            values = self.convertValues(values)
            self._values = values

        return self.values[attr]

    @property
    def type(self):
        """Get type"""
        return self.__class__.__name__

    @property
    def values(self):
        """Get values"""

        return self._values

    @values.setter
    def values(self, values):
        self._values = values

        if 'time' not in self._values:
            self._values['time'] = time.time()

        self.convertValues(self._values)
        self._rawdata = self.values2rawdata(self._values)

    @property
    def rawdata(self):
        """Get rawdata"""
        result = self.values2rawdata(self.values)
        return result

    @rawdata.setter
    def rawdata(self, rawdata):
        self._rawdata = rawdata

        # Reset values
        values = self.rawdata2Values(rawdata)
        values = self.convertValues(values)
        self._values = values

    @property
    def metadata(self):
        """Get metadata"""

        return self._metadata

    @metadata.setter
    def metadata(self, metadata):
        self._metadata = metadata

    def rawdata2Values(self, rawdata):
        values = dict()
        datas = rawdata.split(';')

        # Get time value
        values['time'] = datas[0]

        # If 2 items => not named value
        if len(datas) == 2:
            values['value'] = datas[1]
        # If more 2 items => named value
        else:
            for keyvalue in datas[1:]:
                k, v = keyvalue.split('=')
                values[k] = v

        return values

    def values2rawdata(self, values):
        rawdata = ""

        if 'time' not in values:
            raise Exception('Time not found in values')

        rawdata += str(self._values['time'])
        keys = sorted(self.values.keys())

        if 'value' in self._values:
            rawdata += ";%s" % str(self._values['value'])
        else:
            # TODO: generate multiples values
            pass

        rawdata += "\n"

        return rawdata

    def convert2text(self, configs):
        # Convert with format property
        if 'format' in configs:
            result = eval(configs['format'])
            return result

        # Convert with convert property
        if 'convert' in configs:
            key = self.value
            return configs['convert'][key]

        return str(self.value)

    def convertValues(self, values):

        # Convert text time in float
        values['time'] = float(values['time'])

        # Convert others values
        for k, v in values.iteritems():
            values[k] = self.convert2Value(k, v)

        return values

    def convert2Value(self, propertyname, value):
        # noinspection PyProtectedMember
        if 'convert_%s' % propertyname not in dir(self):
            return value

        converter = getattr(self, 'convert_%s' % propertyname)
        return converter(value)
