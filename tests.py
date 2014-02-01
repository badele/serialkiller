#!/usr/bin/env python
# -*- coding: utf-8 -*-

__authors__ = 'Bruno Adelé <bruno@adele.im>'
__copyright__ = 'Copyright (C) 2013 Bruno Adelé'
__description__ = """Unittest"""
__license__ = 'GPLv3'




import unittest
import hashlib
import random
import os

from serialkiller import lib
from serialkiller import sktypes


class TestPackages(unittest.TestCase):

    def _check_md5file(self, filename):
        return hashlib.md5(open(filename).read()).hexdigest()

    def _reset_file(self, filename):
        if os.path.exists(filename):
            os.remove(filename)

    def _generate_boolean(self, sensorname, nb):
        # Init Objects
        type = 'boolean'
        items = [0, 255]
        obj = lib.Sensor('/tmp/sensors', sensorname, type)

        for i in range(0,nb):
            value = random.choice(items)
            data = sktypes.newObj(type, time=i*60, value=value)
            obj.addValue(data)

    def _generate_byte(self, sensorname, nb):
        # Init Objects
        type = 'byte'
        obj = lib.Sensor('/tmp/sensors', sensorname, type)

        oldvalue = random.randint(0,255)
        for i in range(0,nb):
            same = random.randint(0,10)

            if same >= 7:
                value = random.randint(0,255)
                oldvalue = value
            else:
                value = oldvalue

            data = sktypes.newObj(type, time=i*60, value=value)
            obj.addValue(data)


    def test_create_sensors(self):
        # Init random
        random.seed(0)

        # Boolean
        sensorname = 'test:sensor:boolean'
        sensorconf = '/tmp/sensors/%s.conf' % sensorname.replace(':','/')
        sensordata = '/tmp/sensors/%s.data' % sensorname.replace(':','/')
        self._reset_file(sensorconf)
        self._reset_file(sensordata)
        self._generate_boolean(sensorname, 1000)
        self.assertEqual(self._check_md5file(sensorconf), '5c1fdaffde36866bc1ee844bbc0bae53')
        self.assertEqual(self._check_md5file(sensordata), '7fb2b1801c064a1964901ac93c3e0b7e')

        # byte
        sensorname = 'test:sensor:byte'
        sensorconf = '/tmp/sensors/%s.conf' % sensorname.replace(':','/')
        sensordata = '/tmp/sensors/%s.data' % sensorname.replace(':','/')
        self._reset_file(sensorconf)
        self._reset_file(sensordata)
        self._generate_byte(sensorname, 1000)
        self.assertEqual(self._check_md5file(sensorconf), '775f3b047327ca8704ce093945d23afa')
        self.assertEqual(self._check_md5file(sensordata), '9e2279491bf5f9afc3ab377038251c7f')


if __name__ == "__main__":
    unittest.main(verbosity=2)
