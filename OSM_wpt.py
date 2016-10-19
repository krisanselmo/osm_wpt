# -*- coding: utf-8 -*-
"""
Created on Mon Oct 17 15:28:58 2016

@author: christophe.anselmo@gmail.com


TODO: 
    - Add the possibility to query ways in addition of nodes
    - Insert new point close to the WPT on the WPT

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
    def __init__(self, name, lat, lon, ele, node_id, query_name):
        self.name = name
        self.lat = lat
        self.lon = lon
        
        self.query_name = query_name
        self.node_id = node_id
        
        if (ele == ''):
            self.ele = 0
        else:    
            try:
                self.ele = float(ele)
            except:
               self.ele = 0
               
    def __repr__(self):
        return repr((self.node_id, self.query_name, self.name, self.lat, self.lon, self.ele))
        
        
def Parse_route(gpx):
    lat = []
    lon = []
    ele = []
    
    if not (gpx.tracks):
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
    return(gpx_name,lat,lon,ele)   


def Plot_gpx_wpt(gpx):
    for waypoint in gpx.waypoints:
        lon = waypoint.longitude
        lat = waypoint.latitude
        print 'waypoint {0} -> ({1},{2})'.format(waypoint.name.encode('utf-8'), lat, lon)
        plt.plot(lon, lat, 'ro')


def plot_gpx_route(lon,lat,title):
    fig = plt.figure(facecolor = '0.05')
    ax = plt.Axes(fig, [0., 0., 1., 1.], )
    ax.set_aspect(1.2)
    ax.set_axis_off()
    ax.set_title(title,color='white', fontsize=15)
    fig.add_axes(ax)
    plt.plot(lon, lat, color = 'red', lw = 1, alpha = 1)
    plt.hold(True)
    return plt
        
    
def Get_Overpass_Feature(Pts,index_used,lat,lon,query_name):
    tree = ET.parse("Overpass.xml")
    root = tree.getroot()
    allnodes=root.findall('node')
    i_name = 1
    
    for node in allnodes:
        lat2 = node.get('lat')
        lon2 = node.get('lon')
        node_id = node.get('id')
        
        (match, near_lon, near_lat,index) = Find_nearest(lon,lat,float(lon2),float(lat2))  
        
        if (match == 1):
#                    
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
                Pt = Point(name, near_lat, near_lon, ele, node_id, query_name)
                Pts.append(Pt)             
                index_used.append(index)
                i_name = i_name + 1
    return Pts     
    
    
def Find_nearest(lon,lat,lon2,lat2):
    """
    Find if an OSM node matches with the gpx route and return the nearest 
    coordinates and its index 
    """
    dist = []
    match = 0
    lim_dist = 0.05 # in kilometers
    for i in range(len(lat)):  
        d = haversine(lon[i], lat[i], lon2, lat2)
        dist.append(d)
    i = dist.index(min(dist))
    if (min(dist) < lim_dist):  
        match = 1
    return(match, lon[i], lat[i], i)


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
    margin = 0.01
    minlon = min(lon) - margin
    maxlon = max(lon) + margin
    minlat = min(lat) - margin
    maxlat = max(lat) + margin
#    api = overpass.API()
#    par défaut: http://overpass-api.de/api/interpreter
    api = overpass.API(endpoint='http://api.openstreetmap.fr/oapi/interpreter')
    
    pos_str = str(minlat) + ',' + str(minlon) + ',' +\
    str(maxlat) + ',' + str(maxlon)
    overpass_query_str = 'node['+ query + ']('+ pos_str + ')'
    
    is_replied = 0
    i = 1 # index while (max 5)
    while ((is_replied != 1) and (i < 5)):
        try:
            response = api.Get(overpass_query_str, responseformat="xml")
            save_XML("Overpass.xml",response)   
            is_replied = 1
        except Exception, e:
            print e
#            raise ValueError("Overpass ne repond pas")
            i = i +1
            time.sleep(5) 
            # print 'MultipleRequestsError'
    
    
def save_XML(fname,response):
    # Save XML
    f = open(fname, "wb")
    f.write(response.encode('utf-8'))
    f.close()    
    
    
def Create_gpx(gpx_data,Pts):

    gpx = gpxpy.gpx.GPX()

    for route in gpx_data.routes:
        gpx.routes.append(route)
        
    for track in gpx_data.tracks:
        gpx.tracks.append(track)    
        
    for waypoint in gpx_data.waypoints:    
        gpx.waypoints.append(waypoint)
    
    for Pt in Pts:
#        gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(Pt.lat, Pt.lon, elevation=Pt.ele, name=Pt.name, comment=Pt.query_name, symbol=Pt.query_name, type=Pt.query_name))
        gpx.waypoints.append(gpxpy.gpx.GPXWaypoint(Pt.lat, Pt.lon, elevation=Pt.ele, name=Pt.name, symbol=Pt.query_name, type=Pt.query_name))
    f = open('out.gpx', "wb")
    f.write(gpx.to_xml())
    f.close()    
    
    
if __name__ == "__main__":

    fpath = 'test.gpx'
    
    gpx_file = open(fpath, 'r')
    gpx = gpxpy.parse(gpx_file)
    (gpx_name,lat,lon,ele) = Parse_route(gpx)
    gpx_file.close()
    
    index_used = []
    Pts = []
    
    query = '"natural" = "saddle"'
    Overpass_Query(lon, lat, query)
    Pts = Get_Overpass_Feature(Pts,index_used,lat,lon, 'saddle')
 
    query = '"natural" = "peak"'
    Overpass_Query(lon, lat, query)
    Pts = Get_Overpass_Feature(Pts,index_used,lat,lon, 'peak')
     
    query = '"waterway"="waterfall"'
    Overpass_Query(lon, lat, query)
    Pts = Get_Overpass_Feature(Pts,index_used,lat,lon, 'waterfall')
    
    query = '"information"="guidepost"'
    Overpass_Query(lon, lat, query)
    Pts = Get_Overpass_Feature(Pts,index_used,lat,lon, 'guidepost')
    	
    query = '"natural"="cave_entrance"'
    Overpass_Query(lon, lat, query)
    Pts = Get_Overpass_Feature(Pts,index_used,lat,lon, 'cave_entrance')
    
    query = '"tourism"="viewpoint"'
    Overpass_Query(lon, lat, query)
    Pts = Get_Overpass_Feature(Pts,index_used,lat,lon, 'viewpoint')
	    	
    query = '"amenity"="drinking_water"'
    Overpass_Query(lon, lat, query)
    Pts = Get_Overpass_Feature(Pts,index_used,lat,lon, 'water') 
    
    query = '"tourism"="alpine_hut"'
    Overpass_Query(lon, lat, query)
    Pts = Get_Overpass_Feature(Pts,index_used,lat,lon, 'alpine_hut') 


    plot_gpx = 0
    if (plot_gpx == 1):
        plot_gpx_route(lon,lat,gpx_name)   # Plot route 
        Plot_gpx_wpt(gpx)                  # Plot waypoints from the input gpx
        for Pt in Pts:
            plt.plot(Pt.lon, Pt.lat, 'bo') # Plot new waypoints
        plt.show()
    
    
    print 'Number of gpx points in route : ' + str(len(lat))
    print str(len(index_used)) + ' Waypoint(s)'
    Create_gpx(gpx,Pts)

    
    
    

    
    