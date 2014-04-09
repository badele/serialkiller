#!/usr/bin/env python
# -*- coding: utf-8 -*-

__authors__ = 'Bruno Adelé <bruno@adele.im>'
__copyright__ = 'Copyright (C) 2013 Bruno Adelé'
__description__ = """Unittest"""
__license__ = 'GPLv3'

import unittest
import hashlib
import fnmatch
import random
import os
import re

from serialkiller import lib
from serialkiller import sktypes


class TestPackages(unittest.TestCase):
    def setUp(self):
        self._create_sensors()

    def _create_sensors(self):
        # Init random
        random.seed(0)

        # Number
        self._create_integer_sensor('number', 0, 4294967295, 1000)

    def _create_integer_sensor(self, ptype, mini, maxi, nb):
        sensorname = 'test:sensor:%s' % ptype
        sensorconf = '/tmp/sensors/%s.conf' % sensorname.replace(':', '/')
        sensordata = '/tmp/sensors/%s.data' % sensorname.replace(':', '/')
        self._reset_file(sensorconf)
        self._reset_file(sensordata)
        self._generate_integer(sensorname, ptype, mini, maxi, nb)

    def _create_float_sensor(self, ptype, mini, maxi, nb):
        sensorname = 'test:sensor:%s' % ptype
        sensorconf = '/tmp/sensors/%s.conf' % sensorname.replace(':', '/')
        sensordata = '/tmp/sensors/%s.data' % sensorname.replace(':', '/')
        self._reset_file(sensorconf)
        self._reset_file(sensordata)
        self._generate_float(sensorname, ptype, mini, maxi, nb)

    def _check_md5file(self, filename):
        """Check integrity file"""
        return hashlib.md5(open(filename).read()).hexdigest()

    def _reset_file(self, filename):
        """Delete file"""
        if os.path.exists(filename):
            os.remove(filename)

    def _generate_boolean(self, sensorname, nb):
        # Init Objects
        ptype = 'boolean'
        items = [0, 255]
        obj = lib.Sensor('/tmp/sensors', sensorname, ptype)

        for i in range(0, nb):
            value = random.choice(items)
            data = sktypes.newObj(ptype, time=i * 60, value=value)
            obj.addValue(data)

    def _generate_integer(self, sensorname, ptype, mini, maxi, nb):
        obj = lib.Sensor('/tmp/sensors', sensorname, ptype)

        oldvalue = random.randint(mini, maxi)
        for i in range(0, nb):
            same = random.randint(0, 10)

            if same >= 7:
                value = random.randint(mini, maxi)
                oldvalue = value
            else:
                value = oldvalue

            data = sktypes.newObj(ptype, time=i * 60, value=value)
            obj.addValue(data)

    def _generate_float(self, sensorname, ptype, mini, maxi, nb):
        obj = lib.Sensor('/tmp/sensors', sensorname, ptype)

        oldvalue = random.uniform(mini, maxi)
        for i in range(0, nb):
            same = random.randint(0, 10)

            if same >= 7:
                value = random.uniform(mini, maxi)
                oldvalue = value
            else:
                value = oldvalue

            data = sktypes.newObj(ptype, time=i * 60, value=value)
            obj.addValue(data)

    def _check_integrity(self, ptype, md5conf, md5data):
        sensorname = 'test:sensor:%s' % ptype
        sensorconf = '/tmp/sensors/%s.conf' % sensorname.replace(':', '/')
        sensordata = '/tmp/sensors/%s.data' % sensorname.replace(':', '/')
        self.assertEqual(self._check_md5file(sensorconf), md5conf)
        self.assertEqual(self._check_md5file(sensordata), md5data)

    def _checkobj(self, ptype):
        sensorname = 'test:sensor:%s' % ptype
        obj = lib.Sensor('/tmp/sensors', sensorname, ptype)
        obj.tail(addmetainfo=True)

        self.assertEqual(obj.last().type, 'Sk%s' % ptype.capitalize())
        self.assertGreater(obj.last().unavailable, 1396747071.51)

    def _check_last(self, ptype, value, text):
        sensorname = 'test:sensor:%s' % ptype
        obj = lib.Sensor('/tmp/sensors', sensorname, ptype)
        obj.tail(addmetainfo=True)
        self.assertEqual(obj.last().value, value)
        self.assertEqual(obj.last().text, text)

    def test_check_integrities(self):
        self._check_integrity('number', '69e03aeac61f142cabdfc264198d33f5', '08e72218139d6fc9cc1723f35bb21194')

    def test_check_last(self):
        self._check_last('number', 2935339775.0, '2935339775.0')

    def test_checkobj(self):
        self._checkobj('number')

if __name__ == "__main__":
    unittest.main(verbosity=2)
