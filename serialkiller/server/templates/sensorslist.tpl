<!DOCTYPE html>
<html>
<head>
    <title>Sensors list</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Refresh" CONTENT="30; URL=http://domotique.adele.im/">
    <!-- Bootstrap -->
    <link rel="stylesheet" href="/static/css/bootstrap.min.css">
    <link rel="stylesheet" href="/static/css/font-awesome.min.css">

    <!-- HTML5 Shim and Respond.js IE8 support of HTML5 elements and media queries -->
    <!-- WARNING: Respond.js doesn't work if you view the page via file:// -->
    <!--[if lt IE 9]>
    <script src="/static/js/html5shiv.js"></script>
    <script src="/static/js/bootstrap.min.js"></script>
    <link rel="stylesheet" href="path/to/font-awesome/css/font-awesome.min.css">

    <![endif]-->
</head>
<body>
<style>
    body {
        background-color: #2B2B2B;
        color: #dddddd;
    }

    d9d727
    .text-info {
        color: #4295BE;
    }

    .label-info {
        background-color: #4295BE;
    }

    .text-warning {
        color: #d9d727;
    }

    .label-warning {
        background-color: #d9d727;
    }

    .text-danger {
        color: #FF0000;
    }



    .label-danger {
        background-color: #FF0000;
    }

    .text-success {
        color: #00FF00;
    }

    .label-success {
        background-color: #00FF00;
    }


    .table > thead > tr > th, .table > tbody > tr > th, .table > tfoot > tr > th, .table > thead > tr > td, .table > tbody > tr > td, .table > tfoot > tr > td {
        border-top: 1px solid #DDDDDD;
        line-height: 0;
        padding: 8px;
        vertical-align: top;
    }

    footer {
        bottom: 0;
        clear: both;
        color: #777777;
        height: 3em;
        text-align: center;
    }
</style>
<div class="page-header">
    <h1>Sensors states<small>&nbsp;{{ generated_time|datetime }}</small></h1>
</div>

<!-- Table -->
<table class="table">
    <thead>
    <tr>
        <th>Value</th>
        <th>Since</th>
        <th>Title</th>
        <th>Date</th>
        <th>SensorId</th>
        <th>Type</th>
    </tr>
    </thead>
    <tbody>
    {% for sensorid, sensor in sensors.items()|sort %}
    <tr>
        {% if sensor.state %}
        <td>
            {% if 'limit' in sensor.configs and 'icons' in sensor.configs['limit'] %}
            <i class="fa {{sensor.configs['limit']['icons'][sensor['last'].state] }} fa-fw"></i>&nbsp;
            {% endif %}
            <span class="{% if 'limit' in sensor.configs and 'styles' in sensor.configs['limit'] %}{{sensor.configs['limit']['styles'][sensor['last'].state] }}{% endif%}">
               {{ sensor.last.text }}
            </span>
        </td>
        {% else %}
        <td><i class="fa fa-square-o fa-fw"></i>&nbsp;{{ sensor.last.text }}</td>
        {% endif %}
        <td>{{ sensor.last.since|sincetime }}</td>
        <td>{{ sensor.configs['title'] }}</td>
        {% if sensor.unavailable %}
        <td><span>{{ sensor.last.time|datetime }}</span><i class="text-danger fa fa-warning fa-fw"></i></td>
        {% else %}
        <td>{{ sensor.last.time|datetime }}</td>
        {% endif %}
        <td><a href="/{{ sensorid }}.html">{{ sensorid }}</a></td>
        <td>{{ sensor.configs.type }}</td>
    </tr>
    {% endfor %}
    </tbody>
</table>

<div>
    <b>In value: </b>
    <span class="label label-info">Information</span><b/>
    <span class="label label-success">Ok</span><b/>
    <span class="label label-warning">Warning</span><b/>
    <span class="label label-danger">Critical</span><b/>
    &nbsp;&nbsp;
    <b>In time: </b>
    <span class="label label-info">Ok</span><b/>
    <span class="label label-danger">Sensor unnavailable</span><b/>
</div>
<footer>
    <iframe src="http://ghbtns.com/github-btn.html?user=badele&repo=serialkiller&type=watch&count=true"
            allowtransparency="true" frameborder="0" scrolling="0" width="110" height="20"></iframe>

    <iframe src="http://ghbtns.com/github-btn.html?user=badele&repo=serialkiller&type=fork&count=true"
            allowtransparency="true" frameborder="0" scrolling="0" width="95" height="20"></iframe>
</br >
Created by Bruno Adelé
</br>
© <a href="https://github.com/badele/serialkiller">Serialkiller</a>
</footer>

        <!-- jQuery (necessary for Bootstrap's JavaScript plugins) -->
<script src="https://code.jquery.com/jquery.js"></script>
        <!-- Include all compiled plugins (below), or include individual files as needed -->

<script src="//netdna.bootstrapcdn.com/bootstrap/3.0.3/js/bootstrap.min.js"></script>
        </body>
</html>
