#!/usr/bin/env python
# -*- coding: utf-8 -*-

__authors__ = 'Bruno Adelé <bruno@adele.im>'
__copyright__ = 'Copyright (C) 2013 Bruno Adelé'
__description__ = """timeseries database with reduce system"""
__license__ = 'GPL'
__version__ = '0.0.1'

from serialkiller.sktypes.byte import byte


class boolean(byte):
    """Generic Class for type"""
    def __init__(self, **kwargs):
        super(boolean, self).__init__(**kwargs)
        self._codebin = 0x3

        # Set default properties
        tmpdict = dict(self._defaultproperties)
        tmpdict.update({
            'convert': {
                'value': {
                    0: 'Off',
                    255: 'On',
                },
            },
            'autoset': {
                'value': 1,
                'comment': True
            },
            'limit_crit': {
                'value': '== 0',
                'comment': True
            },
            'limit_succ': {
                'value': '== 255',
                'comment': True
            }}
        )
        self._defaultproperties = tmpdict


    def checkParams(self):
        super(boolean, self).checkParams()

        # Check value
        if not self.value:
            return

        if type(self.value) == str or type(self.value):
            self.params['value'] = int(self.value)

        if self.value == 0 or self.value == 255:
            return

        raise Exception("Value %s not authorized in %s type" % (self.value, self.type))
