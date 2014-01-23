<!DOCTYPE html>
<html>
  <head>
    <title>Sensors list</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Refresh" CONTENT="30; URL=http://domotique.adele.im/">
    <!-- Bootstrap -->
    <link rel="stylesheet" href="//netdna.bootstrapcdn.com/bootstrap/3.0.3/css/bootstrap.min.css">

    <!-- HTML5 Shim and Respond.js IE8 support of HTML5 elements and media queries -->
    <!-- WARNING: Respond.js doesn't work if you view the page via file:// -->
    <!--[if lt IE 9]>
      <script src="https://oss.maxcdn.com/libs/html5shiv/3.7.0/html5shiv.js"></script>
<script src="//netdna.bootstrapcdn.com/bootstrap/3.0.3/js/bootstrap.min.js"></script>
    <![endif]-->
  </head>
  <body>
    <div class="page-header">
      <h1>Sensors states<small>&nbsp;{{ generated_time|datetime }}</small></h1>
    </div>
    <!-- Table -->
    <table class="table">
      <thead>
        <tr>
          <th>SensorId</th>
          <th>Type</th>
          <th>Date</th>
          <th>Since</th>
          <th>Title</th>
          <th>Value</th>
        </tr>
      </thead>
      <tbody>
      {% for k, v in lasts.items() %}
        <tr>
          <td><a href="/{{ k }}.html">{{ k }}</a></td>
          <td>{{ v['configs'].type }}</td>
          {% if v['last'].unavailable %}
          <td><span class="label label-danger">{{ v['last'].time|datetime }}</span></td>
          {% else %}
          <td><span class="label label-info">{{ v['last'].time|datetime }}</span></td>
{% endif %}
          <td>{{ v['last'].since|sincetime }}</td>
          <td>{{ v['configs']['title'] }}</td>
          {% if state[v['last'].state] %}
          <td><span class="label label-{{state[v['last'].state]}}">{{ v['last'].text }}</span></td>
          {% else %}
          <td>{{ v['last'].text }}</td>
{% endif %}
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


    <!-- jQuery (necessary for Bootstrap's JavaScript plugins) -->
    <script src="https://code.jquery.com/jquery.js"></script>
    <!-- Include all compiled plugins (below), or include individual files as needed -->

    <script src="//netdna.bootstrapcdn.com/bootstrap/3.0.3/js/bootstrap.min.js"></script>
  </body>
</html>
