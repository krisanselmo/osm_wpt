Add OSM waypoints on gpx
======
[![License](https://img.shields.io/pypi/l/osmapi.svg)](https://github.com/krisanselmo/osm_wpt/blob/master/LICENSE)

This script aims at automatically adding waypoints (WPT) on a GPX route. These waypoints are particularly useful when you follow a route on your GPS to know or remind you the points you pass. It can be for example, the name of a mountain pass, the name of a peak or the position of a source of drinking water, etc.

Here is a standard gpx file cointaining only the route to follow:
![image1](https://cloud.githubusercontent.com/assets/1937089/19481162/56d2f34a-954d-11e6-8f64-9121a9b0be76.png)

After processing, new interesting waypoints are automatically added on the gpx route.
![image1](https://cloud.githubusercontent.com/assets/1937089/19481195/6f72bb56-954d-11e6-8c2b-59dcf30ff800.png)

### Prerequisites

[**gpxpy**](https://github.com/tkrajina/gpxpy) 
```bash
pip install gpxpy
```
[**overpass**](https://github.com/mvexel/overpass-api-python-wrapper)
```bash
pip install overpass
```
[**osmapi**](https://github.com/metaodi/osmapi)
```bash
pip install osmapi
```

### Usage

```bash
osm_wpt_on_gpx.py inputfile.gpx outputfile.gpx
```

### Tips for use with Suunto / Garmin

For Suunto users the outputed gpx can be imported on movescount [**map**](http://www.movescount.com/map). Note that unfortunately the waypoint types are not recognized by movescount. 

For Garmin users and in particular with the Fēnix 3 watch, the gpx file can be transfered on the directory: **Garmin/NewFiles/**. For others watches or more details on the file transfert, I recommand to read [**this**](http://www.scarletfire.co.uk/transfer-gpx-file-to-garmin/).