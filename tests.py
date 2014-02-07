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

        # Boolean
        sensorname = 'test:sensor:boolean'
        sensorconf = '/tmp/sensors/%s.conf' % sensorname.replace(':', '/')
        sensordata = '/tmp/sensors/%s.data' % sensorname.replace(':', '/')
        self._reset_file(sensorconf)
        self._reset_file(sensordata)
        self._generate_boolean(sensorname, 1000)

        # Integer
        self._create_integer_sensor('byte', 0, 255, 1000)
        self._create_integer_sensor('ushort', 0, 65535, 1000)
        self._create_integer_sensor('ulong', 0, 4294967295, 1000)

        # Float
        self._create_float_sensor('float', .2250738585072014e-30, 1.7976931348623157e+30, 1000)

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
        self.assertEqual(obj.last().unavailable, True)
        self.assertEqual(obj.last().metadata['unavailable'], True)

    def _check_last(self, ptype, value, text, tobinary):
        sensorname = 'test:sensor:%s' % ptype
        obj = lib.Sensor('/tmp/sensors', sensorname, ptype)
        obj.tail(addmetainfo=True)
        self.assertEqual(obj.last().value, value)
        self.assertEqual(obj.last().text, text)
        self.assertEqual(obj.last().typeToBinary(), tobinary)

    def test_check_integrities(self):
        self._check_integrity('boolean', '5c1fdaffde36866bc1ee844bbc0bae53', '7fb2b1801c064a1964901ac93c3e0b7e')
        self._check_integrity('byte', '775f3b047327ca8704ce093945d23afa', '9e2279491bf5f9afc3ab377038251c7f')
        self._check_integrity('ushort', '0dab730a79c64306ac8ba89be9b5f029', '9e6cd5b47c6229abb7d25c6da64952d8')
        self._check_integrity('ulong', '2040be0749b1660b842c09c21326d5c1', 'f95e7b368998a0e0cfabf9c12104c1a9')
        self._check_integrity('float', '4ff8acfab4abf095dba2db2af1166fca', '0c28b1b0006410d94cfe1a8ba34a0934')

    def test_check_last(self):
        self._check_last('boolean', 0, 'Off' ,'\x03\x00\x00\x00\x00\x80D\xed@\x00')
        self._check_last('byte', 138, '138' ,'\x02\x00\x00\x00\x00\x80D\xed@\x8a')
        self._check_last('ushort', 40295, '40295' ,'\x04\x00\x00\x00\x00\x80D\xed@g\x9d')
        self._check_last('ulong', 130047754, '130047754' ,'\x05\x00\x00\x00\x00\x80D\xed@\n_\xc0\x07')
        self._check_last('float', 3.210708047208364e+27, '3210708047208364204214976512.00', '\x06\x00\x00\x00\x00\x80D\xed@^\xfd%m')

    def test_checkobj(self):
        self._checkobj('boolean')
        self._checkobj('byte')
        self._checkobj('ushort')
        self._checkobj('ulong')
        self._checkobj('float')

    def test_codebin(self):
        codebins = []
        for root, dirnames, filenames in os.walk('./serialkiller/sktypes'):
            for filename in fnmatch.filter(filenames, 'sk*.py'):
                fullname = os.path.join(root, filename)
                lines = open(fullname).read()

                m = re.search(r'self._codebin = (0x[0-9]+)', lines)
                if m:
                    codebins.append((m.group(1)))

        # Check if the codebins not used it multiples type files
        before = len(codebins)
        after = len(set(codebins))
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main(verbosity=2)
