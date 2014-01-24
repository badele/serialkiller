<!DOCTYPE html>
<html>
  <head>
    <title>Sensors list</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Refresh" CONTENT="300; URL=http://domotique.adele.im/">
    <!-- Bootstrap -->
    <link rel="stylesheet" href="//netdna.bootstrapcdn.com/bootstrap/3.0.3/css/bootstrap.min.css">
    <script type="text/javascript" src="/static/js/d3.v3.min.js"></script>

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

    <style>
.area {
    fill: #CBDDE6;
    stroke-width: 0;
    opacity: 0.7;
}


svg {
  font: 10px sans-serif;
}

.axis {
  shape-rendering: crispEdges;
}

.axis path, .axis line {
  fill: none;
  stroke-width: .5px;
}

.x.axis path {
  stroke: #000;
}

<!-- .x.axis line { -->
<!--   stroke: #fff; -->
<!--   stroke-opacity: .5; -->
<!-- } -->

.y.axis line {
  stroke: #ddd;
}

path.line {
stroke: #4682B4;
stroke-width: 2;
fill: none;

}

rect.pane {
  cursor: move;
  fill: none;
  pointer-events: all;
}


    </style>

    <script>
var datas = {{datas}};

// Calc margin
var margin = {top: 60, right: 60, bottom: 60, left:60},
    width = 1420 - margin.left - margin.right,
    height = 512 - margin.top - margin.bottom;


// Range
var x = d3.time.scale().range([0, width]);
var y = d3.scale.linear().range([height, 0]);

// Axis
var xAxis = d3.svg.axis()
    .scale(x)
    .orient("bottom")
    .tickSize(-height)
    .tickPadding(6);

var yAxis = d3.svg.axis()
    .scale(y)
    .orient("left")
    .tickSize(-width)
    .tickPadding(6);

// Graph Functions
var line = d3.svg.line()
//.interpolate("basis")
			.x(function(d,i) { return x(new Date(d.time * 1000 )); })
			.y(function(d) { return y(d.value); });

var area = d3.svg.area()
//.interpolate("basis")
    .x(function(d) { return x(new Date(d.time * 1000 )); })
    .y0(y(0))
    .y1(function(d) { return y(d.value); });

var zoom = d3.behavior.zoom()
    .on("zoom", draw);


// SVG graph
var svg = d3.select("body").append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
  .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

// Clip zone for drawing graph
svg.append("clipPath")
    .attr("id", "clip")
  .append("rect")
    .attr("x", 0)
    .attr("y", 0)
    .attr("width", width)
    .attr("height", height);

svg.append("g")
    .attr("class", "y axis");

svg.append("g")
    .attr("class", "x axis")
    .attr("transform", "translate(0," + height + ")");

svg.append("path")
        .datum(datas)
        .attr("class", "area")
        .attr("clip-path", "url(#clip)");

svg.append("path")
    .datum(datas)
    .attr("class", "line")
    .attr("clip-path", "url(#clip)");

svg.append("rect")
    .attr("class", "pane")
    .attr("width", width)
    .attr("height", height)
    .call(zoom);

x.domain(d3.extent(datas, function(d) { return d.time * 1000 ;}));
y.domain(d3.extent(datas, function(d) { return d.value ;}));

zoom.x(x);
draw();

function draw() {
  svg.select("g.x.axis").call(xAxis);
  svg.select("g.y.axis").call(yAxis);
  svg.select("path.area").attr("d", area);
  svg.select("path.line").attr("d", line);
}
    </script>

  </body>
</html>
