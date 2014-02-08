#!/usr/bin/env python
# -*- coding: utf-8 -*-

__authors__ = 'Bruno Adelé <bruno@adele.im>'
__copyright__ = 'Copyright (C) 2013 Bruno Adelé'
__description__ = """timeseries database with reduce system"""
__license__ = 'GPL'
__version__ = '0.0.2'

# System
import os
import sys
import fnmatch
import argparse
from datetime import datetime

from tabulate import tabulate

from serialkiller import lib
from serialkiller import sktypes


configs = {
    'STORAGE': '/tmp/sensors',
}


def addValue(args):
    requireSensorID(args)
    requireSensorType(args)
    obj = lib.Sensor(args.directory, args.sensorid, args.type)

    params = extractParams(args)
    data = sktypes.newObj(args.type, **params)
    obj.addValue(data)


def addEvent(args):
    requireSensorID(args)
    requireSensorType(args)
    obj = lib.Sensor(args.directory, args.sensorid, args.type)

    params = extractParams(args)
    data = sktypes.newObj(args.type, **params)
    obj.addEvent(data)


def getLastsValue(args):
    params = extractParams(args)

    if 'tail' not in params:
        params['tail'] = 1

    obj = lib.Sensor(args.directory, args.sensorid)
    obj.tail(nb=params['tail'])

    return obj.datas


def sensorDatas(args):

    params = extractParams(args)

    if 'tail' not in params:
        params['tail'] = 25

    if 'format' not in params:
        params['format'] = 'txt'

    obj = lib.Sensor(args.directory, args.sensorid)
    obj.tail(nb=params['tail'])
    content = obj.convertSensorDatasTo(**params)

    if 'filename' in params:
        filename = params['filename']
        lib.saveto(filename, content.encode('utf-8'))
    else:
        print content


def sensorInfos(args):
    requireSensorID(args)
    params = extractParams(args)

    obj = lib.Sensor(args.directory, args.sensorid, args.type)
    infos = obj.SensorInfos(**params)

    if not infos:
        print "Not enought datas for %s" % args.sensorid
        sys.exit(1)

    showresult = [
        ['Sensorid', args.sensorid],
        ['Sensor Type', obj.configs['type']],
        ['NB lines', str(infos['nblines'])],
        ['Min date', format_datetime(infos['mindate'])],
        ['Max date', format_datetime(infos['maxdate'])],
        ['Min value', '%s (%s)' % (str(infos['minvalue']), format_datetime(infos['minvaluedate']))],
        ['Max value', '%s (%s)' % (str(infos['maxvalue']), format_datetime(infos['maxvaluedate']))],
        #        ['Avg size', str(infos['avgsize'])],
        ['Avg value', str(infos['avgvalue'])],
        ['Avg delta (round ratio)', str(infos['avgdelta'])],
        ['Total size', '%s Mo' % str(infos['avgsize'] * infos['nblines'] / 1024 / 1024.0)],
    ]

    header = ['Title', 'Value']
    print tabulate(showresult, headers=header)


def sensorReduce(args):
    requireSensorID(args)
    params = extractParams(args)

    obj = lib.Sensor(args.directory, args.sensorid, args.type)

    if 'roundvalue' not in obj.configs:
        raise Exception('Please set roundvalue in sensor configuration')

    obj.reduce(**params)


def setProperty(args):
    requireSensorID(args)
    requireSensorType(args)
    obj = lib.Sensor(args.directory, args.sensorid, args.type)

    params = extractParams(args)
    obj.setConfigs(**params)


def importSensorIds(args):
    requireSensorID(args)
    requireSensorType(args)
    params = extractParams(args)
    if 'filename' not in params:
        print("Please set filename value")
        sys.exit(1)

    obj = lib.Sensor(args.directory, args.sensorid, args.type)
    imported = obj.importDatas(params['filename'])
    print "%s lines imported" % imported


def generateGraphs(args):
    params = extractParams(args)
    if 'directory' not in params:
        print("Please set -v directory=")
        sys.exit(1)

    if 'tail' not in params:
        params['tail'] = 1000

    obj = lib.SerialKillers(args.directory)
    sensorsids = obj.getSensorsIds()

    for sensorid in sensorsids:
        print "generate graphs for %s" % sensorid
        gen = lib.Sensor(args.directory, sensorid)
        gen.tail(nb=params['tail'])
        content = gen.convertSensorDatas2Html(**params)

        filename = "%s/%s.html" % (params['directory'], sensorid)
        lib.saveto(filename, content.encode('utf-8'))


def sensorsList(args):
    obj = lib.SerialKillers(args.directory)
    params = extractParams(args)

    if 'format' not in params:
        params['format'] = 'txt'

    content = obj.convertSensorsListTo(**params)
    if 'filename' in params:
        filename = params['filename']
        lib.saveto(filename, content.encode('utf-8'))
    else:
        print content


def autosetSensors(args):
    obj = lib.SerialKillers(args.directory)
    obj.autosetSensors()


def getAvailableTypes():
    matches = []
    for root, dirnames, filenames in os.walk('sktypes'):
        for filename in fnmatch.filter(filenames, '*.py'):
            filename = filename.replace('.py', '')
            if '__init__' not in filename:
                matches.append(filename)

    return matches


def extractParams(args):
    """Extract params values"""

    if not args.value:
        return dict()

    params = {}
    for v in args.value:
        k, v = v.split('=')
        params[k] = v

    return params


def requireSensorID(args):
    if not args.sensorid:
        print("Please define sensorid")
        sys.exit(1)


def requireSensorType(args):
    if not args.type:
        print("Please define type value with -t")
        sys.exit(1)


def format_datetime(value, fmt='%Y-%m-%d %H:%M:%S'):
    return format(datetime.fromtimestamp(value), fmt)


def parse_arguments(cmdline=""):
    """Parse the arguments"""

    parser = argparse.ArgumentParser(
        description=__description__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        '-a', '--action',
        action='store',
        dest='action',
        default='addvalue',
        choices=[
            'addvalue',
            'addevent',
            'autosetsensors',
            'generategraphs',
            'import',
            'last',
            'sensordatas',
            'sensorinfos',
            'sensorslist',
            'setproperty',
            'reduce',
        ],
        help='Action'
    )

    parser.add_argument(
        '-d', '--dir',
        action='store',
        dest='directory',
        default=configs['STORAGE'],
        help='Directory location'
    )

    parser.add_argument(
        '-f', '--filename',
        action='store',
        dest='filename',
        default=None,
        help='Filename'
    )

    parser.add_argument(
        '-s', '--sensor',
        action='store',
        dest='sensorid',
        default=None,
        help='Sensor ID'
    )

    parser.add_argument(
        '-p', '--property',
        action='store',
        dest='property',
        default='title',
        choices=[
            'title',
            'limit_crit',
            'limit_warn',
            'limit_succ',
            'limit_unkn',
        ],
        help='Property name'
    )

    parser.add_argument(
        '-t', '--type',
        action='store',
        dest='type',
        choices=getAvailableTypes(),
        default=None,
        help='Type value'
    )

    parser.add_argument(
        '-v', '--values',
        action='store',
        dest='value',
        nargs='*',
        default=None,
        help='Item value'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s {version}'.format(version=__version__)
    )

    a = parser.parse_args(cmdline)
    return a


def loadConfig():
    filename = os.environ.get('SERIALKILLER_SETTINGS')

    with open(filename) as myfile:
        for line in myfile:
            name, var = line.partition("=")[::2]
            configs[name.strip()] = eval(var)


def main():
    # Load configuration
    loadConfig()

    # Parse arguments
    args = parse_arguments(sys.argv[1:])  # pragma: no cover

    if args.action:
        if 'addevent' in args.action:
            addEvent(args)

        if 'addvalue' in args.action:
            addValue(args)

        if 'autosetsensors' in args.action:
            autosetSensors(args)

        if 'last' in args.action:
            getLastsValue(args)

        if 'property' in args.action:
            setProperty(args)

        if 'import' in args.action:
            importSensorIds(args)

        if 'sensordatas' in args.action:
            sensorDatas(args)

        if 'sensorinfos' in args.action:
            sensorInfos(args)

        if 'sensorslist' in args.action:
            sensorsList(args)

        if 'generategraphs' in args.action:
            generateGraphs(args)

        if 'reduce' in args.action:
            sensorReduce(args)


if __name__ == '__main__':
    main()  # pragma: no cover
