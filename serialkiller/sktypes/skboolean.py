#!/usr/bin/env python
# -*- coding: utf-8 -*-

__authors__ = 'Bruno Adelé <bruno@adele.im>'
__copyright__ = 'Copyright (C) 2013 Bruno Adelé'
__description__ = """timeseries database with reduce system"""
__license__ = 'GPL'
__version__ = '0.0.2'

from serialkiller.sktypes.skbyte import SkByte


class SkBoolean(SkByte):
    """Generic Class for type"""
    def __init__(self, **kwargs):
        super(SkBoolean, self).__init__(**kwargs)
        self._codebin = 0x3

        # Set default properties
        tmpdict = dict(self._defaultconfigs)
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
        self._defaultconfigs = tmpdict

    def checkMetadata(self):
        super(SkBoolean, self).checkMetadata()

        # Check value
        if not self.value:
            return

        checkvalue = None
        if type(self.value) == str or type(self.value):
            checkvalue = int(self.value)

        if checkvalue == 0 or checkvalue == 255:
            self.metadata['value'] = checkvalue
            return

        raise Exception("Value %s not authorized in %s type" % (self.value, self.type))
