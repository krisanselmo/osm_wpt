# -*- coding: utf-8 -*-
"""
Created on Mon Oct 17 15:28:58 2016

@author: christophe.anselmo@gmail.com


TODO:
    - Add the possibility to query ways with overpass
            |--> Fix double wpt
    - Keep old WPT (partially functional)

"""

import gpxpy      # https://github.com/tkrajina/gpxpy
import overpass   # https://github.com/mvexel/overpass-api-python-wrapper
import osmapi     # https://github.com/metaodi/osmapi
import time
import sys
import xml.etree.cElementTree as ET
from math import radians, cos, sin, asin, sqrt
try:
    import matplotlib.pyplot as plt
except ImportError:
    pass


class point(object):
    def __init__(self, name, lon, lat, ele, node_id, index, new_gpx_index, query_name):
        self.name = name
        self.lat = lat
        self.lon = lon

        self.query_name = query_name
        self.osm_node_id = node_id
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
        return repr((self.osm_node_id, self.index, self.new_gpx_index,
                     self.query_name, self.name, self.lat, self.lon, self.ele))


def parse_route(gpx, reverse=False, simplify=False):
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

    if simplify is True:
        lat, lon, ele = uniquify(lat, lon, ele)

    if reverse is True:
        lat = lat[::-1]
        lon = lon[::-1]
        ele = ele[::-1]
    gpx_name = track.name
    return(gpx_name, lat, lon, ele)


def uniquify(lat, lon, ele):
    """
    Unique coordinate
    Piste d'amélioration
    https://www.peterbe.com/plog/uniqifiers-benchmark
    """
    lat2 = []
    lon2 = []
    ele2 = []
    str2 = []

    precision = 6
    for i in range(len(lat)):
        la = round(lat[i], precision)
        lo = round(lon[i], precision)
        str1 = str(la)+str(lo)
        if str1 not in str2:
            lat2.append(la)
            lon2.append(lo)
            ele2.append(ele[i])
            str2.append(str1)
    print len(lat2)
    return lat2, lon2, ele2


def plot_gpx_wpt(gpx):
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


def plot_overpass_feature():
    tree = ET.parse("Overpass.xml")
    root = tree.getroot()
    allnodes = root.findall('node')
    for node in allnodes:
        lat2 = float(node.get('lat'))
        lon2 = float(node.get('lon'))
        plt.plot(lon2, lat2, 'g+')


def get_overpass_feature(Pts, index_used, lat, lon, lim_dist, query_name):
    tree = ET.parse("Overpass.xml")
    root = tree.getroot()
    allnodes = root.findall('node')
    i_name = 1

    for node in allnodes:
        lat2 = float(node.get('lat'))
        lon2 = float(node.get('lon'))
        node_id = node.get('id')

        (match, near_lon, near_lat, index) = find_nearest(lon, lat, lon2, lat2, lim_dist)

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
                Pt = point(name, lon_new, lat_new, ele, node_id, index, new_gpx_index, query_name)
                Pts.append(Pt)
                index_used.append(index)
                i_name = i_name + 1
    return Pts


def get_overpass_way_feature(Pts, index_used, lat, lon, lim_dist, query_name):
    tree = ET.parse("Overpass.xml")
    root = tree.getroot()
    allways = root.findall('way')
    i_name = 1
    api = osmapi.OsmApi()

    for way in allways:

        for tag in way.findall('tag'):
            if tag.attrib['k'] == 'name':
                name = tag.attrib['v']

        way_id = way.get('id')

        nodes = api.WayGet(way_id)

        lat2 = []
        lon2 = []
        for node_id in nodes['nd']:
            N = api.NodeGet(node_id)
            lat2.append(N['lat'])
            lon2.append(N['lon'])
        (match, near_lon, near_lat, index) = find_nearest_way(lon, lat, lon2, lat2, lim_dist)

        if match == 1:

            [lon_new, lat_new, new_gpx_index] = add_new_point(lon, lat, near_lon, near_lat, index)
            name = query_name + str(i_name) # set default in case proper tag not found
            ele = '' # set default in case proper tag not found

            for tag in way.findall('tag'):
                if tag.attrib['k'] == 'name':
                    name = tag.attrib['v']

            # Because only 1 POI is possible per GPS point
            if index not in index_used:
                print query_name + " - " + name
                Pt = point(name, lon_new, lat_new, ele, node_id, index, new_gpx_index, query_name)
                Pts.append(Pt)
                index_used.append(index)
                i_name = i_name + 1
    return Pts


def find_nearest(lon, lat, lon2, lat2, lim_dist):
    """
    Purpose - Find if an OSM node matches with the gpx route and return the nearest
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


def find_nearest_way(lon, lat, lon2, lat2, lim_dist):
    """
    Purpose - Find if an OSM way matches with the gpx route and return the nearest
    coordinates and its index
    """
    dist2 = []
    i2 = []
    match = 0

    for j in range(len(lat2)):
        dist = []
        for i in range(len(lat)):
            d = haversine(lon[i], lat[i], lon2[j], lat2[j])
            dist.append(d)
        dist2.append(min(dist))
        i2.append(dist.index(min(dist)))

    if min(dist2) < lim_dist:
        match = 1
        i = i2[dist2.index(min(dist2))]
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
    precision = 6
    return round(lon_new, precision), round(lat_new, precision), i


def get_perp(X1, Y1, X2, Y2, X3, Y3):
    """
    Purpose - X1, Y1, X2, Y2 = Two points representing the ends of the line
    segment
              X3,Y3 = The offset point
    'Returns - X4,Y4 = Returns the point on the line perpendicular to the
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


def overpass_query(lon, lat, query):
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
    overpass_query_str = query + '('+ pos_str + ')'

    is_replied = 0
    i = 1 # index while (max 5)
    while (is_replied != 1) and (i < 5):
        try:
            response = api.Get(overpass_query_str, responseformat="xml")
            save_xml("Overpass.xml", response)
            is_replied = 1
        except Exception, e:
            print e
			# raise ValueError("Overpass ne repond pas")
            i = i +1
            time.sleep(5)
            # print 'MultipleRequestsError'


def save_xml(fname, response):
    # Save XML
    f = open(fname, "wb")
    f.write(response.encode('utf-8'))
    f.close()


def build_and_save_gpx(gpx_data, Pts, lat, lon, ele, index_used, gpxoutputname, keep_old_wpt=True):
    gpx = gpxpy.gpx.GPX()
    # Create first track in our GPX:
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    for i in range(len(lat)):
        if i in index_used:
            pt = filter(lambda pt: pt.index == i, Pts)
            P = pt[0]
            if (P.new_gpx_index < i) and P.new_gpx_index is not None:
                gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(P.lat, P.lon, elevation=ele[i]))
        gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(lat[i], lon[i], elevation=ele[i]))
        if i in index_used:

            if (P.new_gpx_index > i) and P.new_gpx_index is not None:
                gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(P.lat, P.lon, elevation=ele[i]))

    if keep_old_wpt is True:
        for waypoint in gpx_data.waypoints:
            gpx.waypoints.append(waypoint)

    for Pt in Pts:
        ok = filter(lambda wpt: round(wpt.latitude*1e5) == round(Pt.lat*1e5), gpx_data.waypoints)
        if len(ok) == 0:
            gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(
                Pt.lat, Pt.lon, elevation=Pt.ele, name=Pt.name,
                symbol=Pt.query_name, type=Pt.query_name))
    f = open(gpxoutputname, "wb")
    f.write(gpx.to_xml())
    f.close()


def osm_wpt(fpath, plot_gpx=False, lim_dist=0.05, keep_old_wpt=False, gpxoutputname='out.gpx'):
    '''
    plot_gpx to plot the route (False #default)
    lim_dist in kilometers (0.05 #default)
    keep_old_wpt (False #defaut)
    '''

    gpx_file = open(fpath, 'r')
    gpx = gpxpy.parse(gpx_file)
    (gpx_name, lat, lon, ele) = parse_route(gpx, reverse=False)
    gpx_file.close()
    print gpx_name + ' parsed'

    index_used = []
    Pts = []

    query = 'node["natural" = "saddle"]'
    overpass_query(lon, lat, query)
    Pts = get_overpass_feature(Pts, index_used, lat, lon, lim_dist, 'saddle')

    query = 'node["natural" = "peak"]'
    overpass_query(lon, lat, query)
    Pts = get_overpass_feature(Pts, index_used, lat, lon, lim_dist, 'peak')

    query = 'node["waterway"="waterfall"]'
    overpass_query(lon, lat, query)
    Pts = get_overpass_feature(Pts, index_used, lat, lon, lim_dist, 'waterfall')

    query = 'node["information"="guidepost"]'
    overpass_query(lon, lat, query)
    Pts = get_overpass_feature(Pts, index_used, lat, lon, lim_dist, 'guidepost')

    query = 'node["natural"="cave_entrance"]'
    overpass_query(lon, lat, query)
    Pts = get_overpass_feature(Pts, index_used, lat, lon, lim_dist, 'cave')

    query = 'node["tourism"="viewpoint"]'
    overpass_query(lon, lat, query)
    Pts = get_overpass_feature(Pts, index_used, lat, lon, lim_dist, 'viewpoint')

    query = 'node["amenity"="drinking_water"]'
    overpass_query(lon, lat, query)
    Pts = get_overpass_feature(Pts, index_used, lat, lon, lim_dist, 'water')

    query = 'node["tourism"="alpine_hut"]'
    overpass_query(lon, lat, query)
    Pts = get_overpass_feature(Pts, index_used, lat, lon, lim_dist, 'hut')

    query = 'way["tourism"="alpine_hut"]'
    overpass_query(lon, lat, query)
    Pts = get_overpass_way_feature(Pts, index_used, lat, lon, lim_dist, 'hut')

    query = 'way["water"="lake"]'
    overpass_query(lon, lat, query)
    Pts = get_overpass_way_feature(Pts, index_used, lat, lon, lim_dist, 'lake')

    query = 'way["natural"="glacier"]'
    overpass_query(lon, lat, query)
    Pts = get_overpass_way_feature(Pts, index_used, lat, lon, lim_dist, 'glacier')

    print 'Number of gpx points in route : ' + str(len(lat))
    print str(len(index_used)) + ' Waypoint(s)'
    build_and_save_gpx(gpx, Pts, lat, lon, ele, index_used, gpxoutputname, keep_old_wpt)

    if plot_gpx is True:
        plot_gpx_route(lon, lat, gpx_name)   # Plot route
        plot_gpx_wpt(gpx)                  # Plot waypoints from the input gpx
        plot_overpass_feature()
        for Pt in Pts:
            plt.plot(Pt.lon, Pt.lat, 'bo') # Plot new waypoints
        plt.show()


if __name__ == "__main__":
    fpath_out = 'out.gpx'  
    if len(sys.argv) > 1:
        fpath = sys.argv[1]
        if len(sys.argv) > 2:
            fpath_out = sys.argv[2]
    else:
        fpath = u'test.gpx'
        
    osm_wpt(fpath, plot_gpx=0, gpxoutputname=fpath_out)
