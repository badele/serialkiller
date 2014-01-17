#!/usr/bin/env python
# -*- coding: utf-8 -*-

__authors__ = 'Bruno Adelé <bruno@adele.im>'
__copyright__ = 'Copyright (C) 2013 Bruno Adelé'
__description__ = """timeseries database with reduce system"""
__license__ = 'GPL'
__version__ = '0.0.1'

import sys
import time
import struct

# Load object type module
def import_objtype(modname, name):
    impmodule = __import__(modname, fromlist=[name])
    return getattr(impmodule, name)


# Intencies object type
def newObj(name, **kwargs):
    modname = 'serialkiller.sktypes.%s' % name
    objtype = import_objtype(modname, name)

    return objtype(**kwargs)


class default(object):
    """Generic Class for type"""
    def __init__(self, **kwargs):

        # Set parameters
        self._params = kwargs

        if 'time' not in kwargs:
            self.time = None

        if 'value' not in kwargs:
            self.value = None

        # Check if parameters is correct
        self.checkParams()

        self._codebin = 0x0
        self._defaultproperties = {
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

    @property
    def type(self):
        """Get type"""
        return self.__class__.__name__

    @property
    def codebin(self):
        """Get codebin for use with toBinary"""
        return self._codebin

    @property
    def params(self):
        """Get Value"""
        return self._params

    @params.setter
    def params(self, value):
        self._params = value

    @property
    def size(self):
        """Get Obj size"""
        return self._params['size']

    @property
    def value(self):
        """Get Value"""
        return self._params['value']

    @value.setter
    def value(self, value):
        self._params['value'] = value
        self.checkParams()

    @property
    def text(self):
        """Get text"""
        return self._params['text']

    @property
    def time(self):
        """Get Time"""
        return self._params['time']

    @time.setter
    def time(self, value):
        if value:
            self._params['time'] = float(value)
        else:
            self._params['time'] = time.time()

    def toBinary(self):
        """Convert to Binary"""
        content = self.typeToBinary()
        size = len(content) + 2
        lsize = struct.pack('=B', size)
        bline = "%s%s%s" % (lsize, content, lsize)

        return bline

    def checkParams(self):
        #Check time format
        if 'time' in self.params:
            if type(self.time) == str:
                self.params['time'] = float(self.time)

    def convert2text(self, textconverter):
        if 'convert' not in textconverter:
            return self.value

        key = str(self.value)
        return textconverter['convert']['value'][key]

    def typeToBinary(self):
        mess = "%s.%s" % (self.__class__, sys._getframe().f_code.co_name)
        raise NotImplementedError(mess)

    def decodeBinary(self, content):
        """Convert from Binary"""
        mess = "%s.%s" % (self.__class__, sys._getframe().f_code.co_name)
        raise NotImplementedError(mess)
