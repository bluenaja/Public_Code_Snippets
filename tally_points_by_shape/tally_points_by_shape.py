# -*- coding: utf-8 -*-
"""
Created on Sat Aug 10 07:10:14 2019

@author: bluenaja

Description: 
    Takes an input file with the lat, lon coordinates of a number of geographic points, 
    retrieves a reference file with shape coordinates, counts the points from the
    input file that are found in each shape, and outputs the tallies to stdout. 
    
Call instruction examples: 
    CLI prompt> python tally_points_by_shape.py < input.tsv > output.tsv
    CLI prompt> python tally_points_by_shape.py < inputdir/input.tsv > outputdir/output.tsv

Input assumptions:
    - Points input file is .tsv with no header and 2 col, the 1st for lat and the 2nd for lon. 
    - Shape input file is .json. Shape vertices are lon-lat pairs. Only exterior
      (not interior) boundaries are specified. Therefore the current script doesn't handle 
      the case of a shape with one or more holes.
        
Output: 
    - A tab-delimited file is saved to a file specified in the CLI.
    - A point that is in more than one shape (as happens when shapes have a
      shared boundary or other intersection) counts toward the total for each 
      shape that contains it. This means that the total tally across shapes 
      may be greater than the total number of points. 

Possible enhancements:
    - Could name the shape file at the CLI rather than hardcode it. 
    - Could use geopandas data frame.

"""

# Helper functions
    
def get_shapes(relative_path_and_filename):
    """Read a GeoJSON file and return a dictionary of object name keys and Polygon object values.
    
    Keyword arguments:
    relative_path_and_filename -- e.g. 'example\shapes.json'
    
    Input assumptions:
    Input file represents geographic shapes as a GeoJSON (https://geojson.org/) FeatureCollection, 
    where each Feature object in the file has an id found in properties.id. Polygons vertices represent
    lon-lat pairs, in that order (eg. (-118, 34) for somewhere in LA County).
    
    Output:
    A flag indicating whether data were acquired from the specified file (flag = 1) or not (flag = -1)
    A dictionary of string: Polygon pairs. 
    Keys are the names of the Polygons. 
    Polygon are described by their vertices. Vertices are lon-lat pairs (input order is preserved). 
    
    Dependencies: 
    json module
    
    Tech notes: 
    For QA, recall that a vertex's coordinates may be retrieved with: x, y = some_poly.exterior.coords.xy
    
    """
    try:
        path = os.path.abspath(os.path.dirname(__file__))
        with open(os.path.join(path, relative_path_and_filename)) as json_file:
            d = json.load(json_file)            
        polygons = {i['properties']['id']:Polygon(i['geometry']['coordinates'][0]) for i in d['features']} #list-comprehension syntax for dictionary
        flag = 1
    except:
        flag = -1
        polygons = {}
        print('I/O error: no shape data acquired.')
            
    return(polygons, flag)

def get_points():
    """Read a tab-separated file containing latitude and longitude values and return a list of (lon, lat) values.
    
    Keyword arguments:
    None. Requires stdin for input file path + name. 
    
    Input assumptions:
    Input file has no header. 
    Input file has 2 columns. The first contains latitude and the second contains longitude. 
    
    Output:
    A flag that indicates whether data ingestions was (flag = 1) or was not (flag = -1) successful. 
    A list of Point objects:
    Each point is defined by a longitude (e.g. -118), latitude (e.g. 34) pair, in that order. 
    Note that the order of the values in the input lat-lon pairs is reversed to produce lon-lat pairs in the returned list. 
    
    Dependencies: 
    pandas module
     
    Tech notes: 
    For QA, recall that the syntax to print the coordinates of a point is: print(tuple(myPoint.coords)).
    
    """   
    points = -1

    if os.isatty(0):
        print('I/O error: no input file name provided.')
        flag = -1
    else:
        try:
            df = pd.read_csv(sys.stdin, delimiter='\t', header = None)
            df.columns = ['lat', 'lon'] 
            points = [Point(i,j) for (i, j) in zip(df['lon'], df['lat'])] 
            flag = 1
        except:
            print('I/O error: no point data acquired.')
            flag = -1

    return(points, flag)
    
def tally_points(polygons, points):
    """For each polygon in polygons, tally the points inside its external boundaries. Return a dictionary of polygon name keys and point count values.
    
    Keyword arguments:
    polygons -- dictionary of polygon name: Polygon object pairs. 
    points -- list of lon-lat pairs. 
    
    Input assumptions:
    Produced by get_shapes() and get_points(). See output notes for those functions.   
    Points and Polygon vertices are lon-lat pairs (same coordinate system is used for Points and Polygons).
    
    Output: Returns a dictionary of name:count pairs. 
    
    Dependencies: 
    pandas module
         
    """
    #traverse the 2 data structures and for each shape, count points that are found there. Enhancement would be to reduce time complexity.    
    d = dict()
    for name, poly in polygons.items():
        #print(name, ":", poly)
        count = 0
        for pt in points:
            if pt.within(poly):
                count += 1
        d.update({name:count})
    
    #return file name and dictionary for QA testing
    return(d)

# MAIN
    
def main():   
    """Get a set of shapes and a set of points and count the number of points in each shape. Return a dictionary and save output to file."""
    
    # Get shapes from hardcoded filename and location 
    relative_path_and_filename = 'example\shapes.json'
    polys, polys_flag = get_shapes(relative_path_and_filename)
    
    # Get points from CLI standard input
    points, points_flag = get_points()
    
    # If all-clear
    if points_flag == 1 and polys_flag == 1:
        
        # Count the points inside the polygons
        tally = tally_points(polys, points) 
        
        # Write results to file named on CLI
        tsv_writer = csv.writer(sys.stdout, delimiter='\t', lineterminator='\t')
        for key in tally.keys():
            tsv_writer.writerow((key, tally[key]))

    else:
        
        print('Aborting.')
            
if __name__ == "__main__":

    # Environment   
    import sys, os, csv, json, pandas as pd
    from shapely.geometry import Point, Polygon
    
    # Launch
    main()
