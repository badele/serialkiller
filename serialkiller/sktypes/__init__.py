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

# Codebin
# 0x2 = SkByte
# 0x3 = SkBoolean
# 0x4 = SkUshort
# 0x5 = SkUlong
# 0x6 = SkFloat


# Load object type module
def import_objtype(modname, name):
    impmodule = __import__(modname, fromlist=[name])
    return getattr(impmodule, name)


# Intencies object type
def newObj(name, **kwargs):
    modname = 'serialkiller.sktypes.sk%s' % name
    objtype = import_objtype(modname, 'Sk%s' % name.capitalize())

    return objtype(**kwargs)


class SkDefault(object):
    """Generic Class for type"""
    def __init__(self, **kwargs):

        # Set parameters
        self._metadata = kwargs

        if 'time' not in kwargs:
            self.time = None

        if 'value' not in kwargs:
            self.value = None

        # Check if parameters is correct
        self.checkMetadata()

        self._codebin = 0x0
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

    @property
    def type(self):
        """Get type"""
        return self.__class__.__name__

    @property
    def codebin(self):
        """Get codebin for use with toBinary"""
        return self._codebin

    @property
    def value(self):
        """Get Value"""
        return self.returnMetadata('value')

    @value.setter
    def value(self, pvalue):
        self._metadata['value'] = pvalue
        self.checkMetadata()

    @property
    def time(self):
        """Get Time"""
        return self.returnMetadata('time')

    @time.setter
    def time(self, value):
        if value:
            self._metadata['time'] = float(value)
        else:
            self._metadata['time'] = time.time()

    @property
    def metadata(self):
        """Get Value"""
        return self._metadata

    @metadata.setter
    def metadata(self, value):
        self._metadata = value

    # =======================
    # Get Metadata properties
    # =======================
    @property
    def size(self):
        """Get Obj size"""
        return self.returnMetadata('size')

    @property
    def state(self):
        """Get Value"""
        return self.returnMetadata('state')

    @property
    def unavailable(self):
        """Get Value"""
        return self.returnMetadata('unavailable')

    @property
    def text(self):
        """Get text"""
        return self.returnMetadata('text')

    # =======================
    # Get Metadata properties
    # =======================

    @state.setter
    def state(self, value):
        self._metadata['state'] = value

    @unavailable.setter
    def unavailable(self, value):
        self._metadata['unavailable'] = value

    @text.setter
    def text(self, value):
        self._metadata['text'] = value

    def returnMetadata(self, metadataname):
        if metadataname not in self._metadata:
            return None

        return self._metadata[metadataname]

    def toBinary(self):
        """Convert to Binary"""
        content = self.typeToBinary()
        size = len(content) + 2
        lsize = struct.pack('=B', size)
        bline = "%s%s%s" % (lsize, content, lsize)

        return bline

    def checkMetadata(self):
        #Check time format
        if 'time' in self.metadata:
            if type(self.time) == str:
                self.time = float(self.time)

    def convert2text(self, configs):
        if 'convert' not in configs:
            if self.type == 'SkFloat':
                return "%.2f" % self.value

            return str(self.value)

        key = str(self.value)
        return configs['convert'][key]

    def typeToBinary(self):
        # noinspection PyProtectedMember
        mess = "%s.%s" % (self.__class__, sys._getframe().f_code.co_name)
        raise NotImplementedError(mess)

    def decodeBinary(self, content):
        """Convert from Binary"""
        # noinspection PyProtectedMember
        mess = "%s.%s" % (self.__class__, sys._getframe().f_code.co_name)
        raise NotImplementedError(mess)
