<!DOCTYPE html>
<html>
  <head>
    <title>Sensors list</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Refresh" CONTENT="300; URL=http://domotique.adele.im/">
    <!-- Bootstrap -->
    <link rel="stylesheet" href="//netdna.bootstrapcdn.com/bootstrap/3.0.3/css/bootstrap.min.css">
    <script src="/static/css/Chart.js"></script>

    <!-- HTML5 Shim and Respond.js IE8 support of HTML5 elements and media queries -->
    <!-- WARNING: Respond.js doesn't work if you view the page via file:// -->
    <!--[if lt IE 9]>
      <script src="https://oss.maxcdn.com/libs/html5shiv/3.7.0/html5shiv.js"></script>
<script src="//netdna.bootstrapcdn.com/bootstrap/3.0.3/js/bootstrap.min.js"></script>
    <![endif]-->
  </head>
  <body>
    <div class="page-header">
      <h1>{{ sensorid }} states({{ samples }} samples)<small>&nbsp;{{ generated_time|datetime }}</small></h1>
    </div>

    <canvas id="canvas" width="1420" height="256" ></canvas>
<script>

                var lineChartData = {
                        labels : {{dates}},
                        datasets : [
                                {
                                        fillColor : "rgba(151,187,205,0.5)",
                                        strokeColor : "rgba(151,187,205,1)",
                                        pointColor : "rgba(151,187,205,1)",
                                        pointStrokeColor : "#fff",
                                        data : {{datas}}
                                }
                        ]
                        
                }


        var myLine = new Chart(document.getElementById("canvas").getContext("2d")).Line(lineChartData);
        
        </script>


    <!-- jQuery (necessary for Bootstrap's JavaScript plugins) -->
    <script src="https://code.jquery.com/jquery.js"></script>
    <!-- Include all compiled plugins (below), or include individual files as needed -->

    <script src="//netdna.bootstrapcdn.com/bootstrap/3.0.3/js/bootstrap.min.js"></script>
  </body>
</html>
