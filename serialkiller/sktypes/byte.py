#!/usr/bin/env python
# -*- coding: utf-8 -*-

__authors__ = 'Bruno Adelé <bruno@adele.im>'
__copyright__ = 'Copyright (C) 2013 Bruno Adelé'
__description__ = """timeseries database with reduce system"""
__license__ = 'GPL'
__version__ = '0.0.1'

import struct

from serialkiller.sktypes import default


class byte(default):
    """Generic Class for type"""
    def __init__(self, **kwargs):
        super(byte, self).__init__(**kwargs)
        self._codebin = 0x2

        # Set default properties
        tmpdict = dict(self._defaultproperties)
        tmpdict.update({
            'convert': {
                'value': {
                    0: 'Off',
                    255: 'On',
                },
                'comment': True
            },
            'autoset': {
                'value': 1,
                'comment': True
            },
            'limit_crit': {
                'value': '> 90',
                'comment': True
            },
            'limit_warn': {
                'value': '>= 75',
                'comment': True
            },
            'limit_succ': {
                'value': '< 75',
                'comment': True
            }}
        )
        self._defaultproperties = tmpdict

    @default.value.setter
    def value(self, value):
        if value:
            self._params['value'] = int(value)
        else:
            self._params['value'] = value

        self.checkParams()

    def typeToBinary(self):
        """Convert to Binary"""
        line = struct.pack('=BdB', self.codebin, self.time, self.value)
        return line

    def decodeBinary(self, content):
        """Binary to skline"""

        (sizes, typeid, datetime, value, sizee) = struct.unpack('=BBdBB', content)

        self.params['size'] = sizes
        self.params['time'] = datetime
        self.params['value'] = value


    def checkParams(self):
        super(byte, self).checkParams()

        # Check value
        if not self.value:
            return

        if type(self.value) == str or type(self.value):
            self.params['value'] = int(self.value)

        if self.value >= 0 and self.value <= 255:
            return

        print self.params['value']
        raise Exception("Value %s not authorized in %s type" % (self.value, self.type))
