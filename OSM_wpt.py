# -*- coding: utf-8 -*-
"""
Created on Mon Oct 17 15:28:58 2016

@author: christophe.anselmo@gmail.com


TODO: 
    - Add the possibility to query ways with overpass
    - Keep old WPT (partially functional)

"""

import gpxpy      #https://github.com/tkrajina/gpxpy
import overpass   #https://github.com/mvexel/overpass-api-python-wrapper
try:
    import matplotlib.pyplot as plt
except ImportError:
    pass
import xml.etree.cElementTree as ET
import time
from math import radians, cos, sin, asin, sqrt


class Point(object):
    def __init__(self, name, lon, lat, ele, node_id, index, new_gpx_index, query_name):
        self.name = name
        self.lat = lat
        self.lon = lon

        self.query_name = query_name
        self.OSM_node_id = node_id
        self.index = index
        self.new_gpx_index = new_gpx_index

        if ele == '':
            self.ele = 0
        else:
            try:
                self.ele = float(ele)
            except:
                self.ele = 0

    def __repr__(self):
        return repr((self.OSM_node_id, self.index, self.new_gpx_index,
                     self.query_name, self.name, self.lat, self.lon, self.ele))


def Parse_route(gpx):
    lat = []
    lon = []
    ele = []

    if not gpx.tracks:
        for track in gpx.routes:
            for point in track.points:
                lat.append(point.latitude)
                lon.append(point.longitude)
                ele.append(point.elevation)
    else:
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    lat.append(point.latitude)
                    lon.append(point.longitude)
                    ele.append(point.elevation)

    gpx_name = track.name
    return(gpx_name, lat, lon, ele)


def Plot_gpx_wpt(gpx):
    for waypoint in gpx.waypoints:
        lon = waypoint.longitude
        lat = waypoint.latitude
        print 'waypoint {0} -> ({1},{2})'.format(waypoint.name.encode('utf-8'), lat, lon)
        plt.plot(lon, lat, 'yo')


def plot_gpx_route(lon, lat, title):
    fig = plt.figure(facecolor='0.05')
    ax = plt.Axes(fig, [0., 0., 1., 1.], )
    ax.set_aspect(1.2)
    ax.set_axis_off()
    ax.set_title(title, color='white', fontsize=15)
    fig.add_axes(ax)
    plt.plot(lon, lat, '+-', color='red', lw=1, alpha=1)
    plt.hold(True)
    return plt


def Plot_Overpass_Feature():
    tree = ET.parse("Overpass.xml")
    root = tree.getroot()
    allnodes = root.findall('node')
    for node in allnodes:
        lat2 = float(node.get('lat'))
        lon2 = float(node.get('lon'))
        plt.plot(lon2, lat2, 'g+')

def Get_Overpass_Feature(Pts, index_used, lat, lon, lim_dist, query_name):
    tree = ET.parse("Overpass.xml")
    root = tree.getroot()
    allnodes = root.findall('node')
    i_name = 1

    for node in allnodes:
        lat2 = float(node.get('lat'))
        lon2 = float(node.get('lon'))
        node_id = node.get('id')

        (match, near_lon, near_lat, index) = Find_nearest(lon, lat, lon2, lat2, lim_dist)

        if match == 1:

            [lon_new, lat_new, new_gpx_index] = add_new_point(lon, lat, lon2, lat2, index)
            name = query_name + str(i_name) # set default in case proper tag not found
            ele = '' # set default in case proper tag not found

            for tag in node.findall('tag'):
                if tag.attrib['k'] == 'name':
                    name = tag.attrib['v']
                if tag.attrib['k'] == 'ele':
                    ele = tag.attrib['v']

            # Because only 1 POI is possible per GPS point
            if index not in index_used:
                print query_name + " - " + name + " - " + ele
                Pt = Point(name, lon_new, lat_new, ele, node_id, index, new_gpx_index, query_name)
                Pts.append(Pt)
                index_used.append(index)
                i_name = i_name + 1
    return Pts


def Find_nearest(lon, lat, lon2, lat2, lim_dist):
    """
    Find if an OSM node matches with the gpx route and return the nearest
    coordinates and its index
    """
    dist = []
    match = 0

    for i in range(len(lat)):
        d = haversine(lon[i], lat[i], lon2, lat2)
        dist.append(d)
    i = dist.index(min(dist))
    if min(dist) < lim_dist:
        match = 1
        print 'Distance to node: ' + str(min(dist)*1e3) + ' m'
    return(match, lon[i], lat[i], i)


def add_new_point(lon, lat, lon2, lat2, index):
    if (index == 0) or (index+1 == len(lat)):
        return None, None, None

    d_prev = haversine(lon[index-1], lat[index-1], lon2, lat2)
    d_next = haversine(lon[index+1], lat[index+1], lon2, lat2)

    if d_prev < d_next:
        i = index-1
    else:
        i = index+1

    [lon_new, lat_new, exist] = get_perp(lon[i], lat[i], lon[index], lat[index], lon2, lat2)
    if exist == 1:
        i = index
    return lon_new, lat_new, i

def get_perp(X1, Y1, X2, Y2, X3, Y3):
    """
    Purpose - X1,Y1,X2,Y2 = Two points representing the ends of the line
    segment
              X3,Y3 = The offset point
    'Returns - X4,Y4 = Returns the Point on the line perpendicular to the
    offset or None if no such point exists
    """
    XX = X2 - X1
    YY = Y2 - Y1
    if (XX*XX) + (YY*YY) == 0:
        return X2, Y2, 1
    ShortestLength = ((XX*(X3 - X1)) + (YY*(Y3 - Y1)))/((XX*XX) + (YY*YY))
    X4 = X1 + XX * ShortestLength
    Y4 = Y1 + YY * ShortestLength
#    if X4 < X2 and X4 > X1 and Y4 < Y2 and Y4 > Y1:
    return X4, Y4, 0
#    else:
#        return X2,Y2,1


def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    From : http://stackoverflow.com/a/4913653
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r


def Overpass_Query(lon, lat, query):
    margin = 0.001
    minlon = min(lon) - margin
    maxlon = max(lon) + margin
    minlat = min(lat) - margin
    maxlat = max(lat) + margin
#    api = overpass.API()
#   Default : http://overpass-api.de/api/interpreter
    api = overpass.API(endpoint='http://api.openstreetmap.fr/oapi/interpreter')

    pos_str = str(minlat) + ',' + str(minlon) + ',' +\
    str(maxlat) + ',' + str(maxlon)
    overpass_query_str = 'node['+ query + ']('+ pos_str + ')'

    is_replied = 0
    i = 1 # index while (max 5)
    while (is_replied != 1) and (i < 5):
        try:
            response = api.Get(overpass_query_str, responseformat="xml")
            save_XML("Overpass.xml", response)
            is_replied = 1
        except Exception, e:
            print e
#            raise ValueError("Overpass ne repond pas")
            i = i +1
            time.sleep(5)
            # print 'MultipleRequestsError'


def save_XML(fname, response):
    # Save XML
    f = open(fname, "wb")
    f.write(response.encode('utf-8'))
    f.close()


def Create_gpx(gpx_data, Pts, keep_old_WPT=True):

    gpx = gpxpy.gpx.GPX()

    # Create first track in our GPX:
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)

    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    for i in range(len(lat)):
        if i in index_used:
            Pt = filter(lambda Pt: Pt.index == i, Pts)
            P = Pt[0]
            if (P.new_gpx_index < i) and P.new_gpx_index is not None:
                gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(P.lat, P.lon, elevation=ele[i]))
        gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(lat[i], lon[i], elevation=ele[i]))
        if i in index_used:

            if (P.new_gpx_index > i) and P.new_gpx_index is not None:
                gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(P.lat, P.lon, elevation=ele[i]))

    if keep_old_WPT is True:
        for waypoint in gpx_data.waypoints:
            gpx.waypoints.append(waypoint)

    for Pt in Pts:

        ok = filter(lambda wpt: round(wpt.latitude*1e5) == round(Pt.lat*1e5), gpx_data.waypoints)
        if len(ok) == 0:
            gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(
                Pt.lat, Pt.lon, elevation=Pt.ele, name=Pt.name,
                symbol=Pt.query_name, type=Pt.query_name))
    f = open('out.gpx', "wb")
    f.write(gpx.to_xml())
    f.close()


if __name__ == "__main__":

    # -----------------------------
    fpath = 'test.gpx'
    lim_dist = 0.05 # in kilometers
    keep_old_WPT = False
	# -----------------------------

    gpx_file = open(fpath, 'r')
    gpx = gpxpy.parse(gpx_file)
    (gpx_name, lat, lon, ele) = Parse_route(gpx)
    gpx_file.close()

    index_used = []
    Pts = []


    query = '"natural" = "saddle"'
    Overpass_Query(lon, lat, query)
    Pts = Get_Overpass_Feature(Pts, index_used, lat, lon, lim_dist, 'saddle')

    query = '"natural" = "peak"'
    Overpass_Query(lon, lat, query)
    Pts = Get_Overpass_Feature(Pts, index_used, lat, lon, lim_dist, 'peak')

    query = '"waterway"="waterfall"'
    Overpass_Query(lon, lat, query)
    Pts = Get_Overpass_Feature(Pts, index_used, lat, lon, lim_dist, 'waterfall')

    query = '"information"="guidepost"'
    Overpass_Query(lon, lat, query)
    Pts = Get_Overpass_Feature(Pts, index_used, lat, lon, lim_dist, 'guidepost')

    query = '"natural"="cave_entrance"'
    Overpass_Query(lon, lat, query)
    Pts = Get_Overpass_Feature(Pts, index_used, lat, lon, lim_dist, 'cave_entrance')

    query = '"tourism"="viewpoint"'
    Overpass_Query(lon, lat, query)
    Pts = Get_Overpass_Feature(Pts, index_used, lat, lon, lim_dist, 'viewpoint')

    query = '"amenity"="drinking_water"'
    Overpass_Query(lon, lat, query)
    Pts = Get_Overpass_Feature(Pts, index_used, lat, lon, lim_dist, 'water')

    query = '"tourism"="alpine_hut"'
    Overpass_Query(lon, lat, query)
    Pts = Get_Overpass_Feature(Pts, index_used, lat, lon, lim_dist, 'alpine_hut')


    plot_gpx = 0
    if plot_gpx == 1:
        plot_gpx_route(lon, lat, gpx_name)   # Plot route
        Plot_gpx_wpt(gpx)                  # Plot waypoints from the input gpx
        Plot_Overpass_Feature()
        for Pt in Pts:
            plt.plot(Pt.lon, Pt.lat, 'bo') # Plot new waypoints
        plt.show()

    print 'Number of gpx points in route : ' + str(len(lat))
    print str(len(index_used)) + ' Waypoint(s)'
    Create_gpx(gpx, Pts, keep_old_WPT)
