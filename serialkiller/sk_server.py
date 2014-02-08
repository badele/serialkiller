# -*- coding: utf-8 -*-

__authors__ = 'Bruno Adelé <bruno@adele.im>'
__copyright__ = 'Copyright (C) 2013 Bruno Adelé'
__description__ = """timeseries database with reduce system"""
__license__ = 'GPL'
__version__ = '0.0.2'
__apiversion__ = '1.0'

# System
import logging
import urlparse

# Third party
from flask import Flask, jsonify
from flask_failsafe import failsafe

# serialkiller
from serialkiller import lib
from serialkiller import sktypes


# Init application
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('SERIALKILLER_SETTINGS', silent=False)


@app.route('/', methods=['GET'])
@app.route('/api/%s/' % __apiversion__, methods=['GET'])
def index():
    """List all serialkiller API functions"""
    func_list = {}
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            func_list[rule.rule] = app.view_functions[rule.endpoint].__doc__
    return jsonify(func_list)


@app.route('/api/%s/list' % __apiversion__, methods=['GET'])
def listLastsSensor():
    """List all last sensors"""
    obj = lib.SerialKillers(app.config['STORAGE'])
    content = obj.convertSensorsListTo(format='html')
    return content


@app.route('/api/%s/addEvent/<sensorid>/<type>/<values>' % __apiversion__, methods=['GET'])
def addEvent(sensorid, type, values):
    """Add a new event, no deduplicate"""
    obj = lib.Sensor(app.config['STORAGE'], sensorid, type)
    params = dict(urlparse.parse_qsl(values))
    data = sktypes.newObj(type, **params)
    obj.addEvent(data)
    return "ok"


@app.route('/api/%s/addValue/<sensorid>/<type>/<values>' % __apiversion__, methods=['GET'])
def addValue(sensorid, type, values):
    """Add a new value, deduplicate line"""
    obj = lib.Sensor(app.config['STORAGE'], sensorid, type)
    params = dict(urlparse.parse_qsl(values))
    data = sktypes.newObj(type, **params)
    obj.addValue(data)
    return "ok"


@app.route('/api/%s/sensor/<sensorid>' % __apiversion__, methods=['GET'])
def SensorDatas(sensorid):
    """List all last sensors"""
    obj = lib.Sensor(app.config['STORAGE'], sensorid)
    obj.tail(nb=5000)
    content = obj.convertSensorDatasTo(format='html')
    return content


@app.route('/<hostid>:<sensor>:<itemid>.html', methods=['GET'])
def SensorDatasBis(hostid, sensor, itemid):
    """List all last sensors"""
    sensorid = "%s:%s:%s" % (hostid, sensor, itemid)
    return SensorDatas(sensorid)


def main():
    app.static_folder = 'server/static'
    logging.basicConfig(filename=app.config['LOG'], level=logging.DEBUG)
    app.run(host=app.config['HOST'], port=app.config['PORT'], debug=app.config['DEBUG'])


@failsafe
def standalone():
    main()


if __name__ == "__main__":
    main()
