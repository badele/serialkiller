#!/usr/bin/env python
# -*- coding: utf-8 -*-

__authors__ = 'Bruno Adelé <bruno@adele.im>'
__copyright__ = 'Copyright (C) 2013 Bruno Adelé'
__description__ = """timeseries database with reduce system"""
__license__ = 'GPL'
__version__ = '0.0.2'

from serialkiller.sktypes import SkBase


class SkNumber(SkBase):
    """Generic Class for type"""
    def __init__(self, **kwargs):
        super(SkNumber, self).__init__(**kwargs)

        # Set default properties
        tmpdict = dict(self._defaultconfigs)
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
                'value': '== 0',
                'comment': True
            },
            'limit_succ': {
                'value': '== 255',
                'comment': True
            }}
        )
        self._defaultconfigs = tmpdict

    def convert_value(self, value):
        result = value

        if isinstance(value, str):
            result = result.lstrip('0')

        result = float(result)
        return result
