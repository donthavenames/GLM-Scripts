from datetime import datetime
import pandas as pd
from glmtools.io.glm import GLMDataset
from glmtools.io.imagery import open_glm_time_series, aggregate
import os
import xarray as xr
from dateutil import parser
import numpy as np
import netCDF4 as nc
from  matplotlib.colors import LinearSegmentedColormap
# from mpl_toolkits.basemap import Basemap
import cartopy.feature as cfeature

import matplotlib.pyplot as plt
import matplotlib as mpl         
import cartopy.crs as ccrs
import cartopy.io.img_tiles as cimgt

import argparse
import subprocess
import datetime

#purpose of this is to create an argument parser with a description
parser = argparse.ArgumentParser(description="Turn a downloaded datafile into an image.")

# start & end date arguments
parser.add_argument(
    "file", 
    help = "file folder with data you would like to convert", 
    
)

parser.add_argument(
    "folder_name", 
    help = "name of folder you would like to save to", 
    
)

args = parser.parse_args()

storm_center_lat = ([])
storm_center_lon = ([])

group_lat = np.array([])
group_lon = np.array([])

download_folder = args.folder_name
download_dir = os.path.join('./', download_folder)
if not os.path.isdir(download_dir):
    os.makedirs(download_dir)


def reduce_file(data_file):
    
    data = GLMDataset(data_file).dataset
    # time data in format "YYYY-MM-DD HH:MM:SS"
    time_str = data.time_coverage_start[:-3].replace('T', ' ')
    
    # extract data about groups
    groups = data[['group_energy','group_area']]
    groups = groups.drop(['group_parent_flash_id','lightning_wavelength','product_time','group_time_threshold','flash_time_threshold','lat_field_of_view','lon_field_of_view'])
    
    # group lat, lon
    group_lon, group_lat = groups['group_lon'].values, groups['group_lat'].values
    
    date = parser.parse(time_str, "")
    return [date, group_lat, group_lon]

# from a single netcdf file return [date, groups_lat, groups_lon]
def return_data():
    for index, row in df.iterrows():

        #if index != 1551: # debug purpose only
            #continue
        #if index > 1000 and index < 1010:
            #continue

        # 1549,2020-08-27 12:10:00,-93.23934491605976,31.176059435732316

        date_str = row["Date"] # = "2020-08-27 12:10:00"
        storm_center_lat = row["Lat"] # = -93.23934491605976
        storm_center_lon = row["Long"] # = 31.176059435732316
        

        
        # construct path to correct file
        # 
        date = parser.parse(date_str) # = 2020-08-27 12:10:00
        yday = date.timetuple().tm_yday # = 230
        hour = date.timetuple().tm_hour # = 12
        year = date.timetuple().tm_year # = 2020
        path = "../Data/GLM/{:d}/{:03d}/{:02d}/".format(year, yday, hour) # = "../Data/GLM/2020/230/12"

        
        group_lat = np.array([])
        group_lon = np.array([])
        
        try:
            if os.path.exists(path):
                print("success!")
                
            else:
                #used to trigger the except
                print(purpose_error)
            
        except FileNotFoundError:
            print("Path/File not found")
        
        except:
            print("Unknown Error")
        
        else:
            if os.path.exists(path):
                print("Path exists")
                for f in sorted(os.listdir(path)):
                    print("Before reduce: " + path)
                    (time_stamp, lat, lon) = reduce_file("{}{}".format(path, f))
                    print("After reduce:" + path)

                    group_lat = np.concatenate((group_lat, lat))
                    group_lon = np.concatenate((group_lon, lon))
                    time_diff = time_stamp - date
                    print(time_diff)
                    print(time_stamp, date)
                    if 0 <= time_diff.total_seconds() < 10 * 60:
                        group_lat = np.concatenate((group_lat, lat))
                        group_lon = np.concatenate((group_lon, lon))

                    elif time_diff.total_seconds() >= 10 * 60: # check if the time difference is greater than 10 mins or not
                        print("Time difference is too great")
                        break
        return storm_center_lat, storm_center_lon, group_lat, group_lon




def make_image(path_name):
    # convert lat, lon to storm center coordinates system and graphs it at the end
    lon = group_lon - storm_center_lon
    lat = group_lat - storm_center_lat

    nearby_lon = []
    nearby_lat = []
    for lon, lat in zip(group_lon, group_lat):
        if abs(lon - storm_center_lon) > 6 or abs(lat - storm_center_lat) > 6:
            continue
        nearby_lon.append(lon)
        nearby_lat.append(lat)

    nearby_lon = np.array(nearby_lon)
    nearby_lat = np.array(nearby_lat)

    # determine the region of interest
    # min_lat = min(nearby_lat)
    # max_lat = max(nearby_lat)
    # min_lon = min(nearby_lon)
    # max_lon = max(nearby_lon)

    min_lat = storm_center_lat - 6
    max_lat = storm_center_lat + 6
    min_lon = storm_center_lon - 6
    max_lon = storm_center_lon + 6

    print("extend = ")
    print(min_lat, max_lat)
    print(min_lon, max_lon)

    plt.figure(figsize=(7, 7))
    extent = [min_lon, max_lon, min_lat, max_lat]

    ax2 = plt.axes(projection=ccrs.PlateCarree())
    ax2.set_extent(extent, ccrs.PlateCarree())

    xynps = ax2.projection.transform_points(ccrs.PlateCarree(), nearby_lat, nearby_lon)
    # print(nearby_lat)
    # print(xynps)
    h = ax2.hist2d(nearby_lon, nearby_lat, bins=100, zorder=10, alpha=0.5, cmin = None, norm=mpl.colors.LogNorm())

    ax2.coastlines(resolution='110m')
    gl = ax2.gridlines(draw_labels=True)
    gl.top_labels = False
    gl.right_labels = False

    # center of storm
    ax2.plot([storm_center_lon], [storm_center_lat],
            color='red', marker='o',
            transform=ccrs.PlateCarree(),
            )
    print("center = ", storm_center_lon, storm_center_lat)
    # color bar
    cbar = plt.colorbar(h[3], ax=ax2, shrink=0.45, format='%.1f')  # h[3]: image

    plt.show()
    plt.savefig(path_name + '.png')


#loops through all the files in the directory
for root, dirs, files in os.walk('../' + args.file):
    for file_name in files:
        if file_name.endswith(".csv"):
            track_file = "../Scripts/Data/" + file_name
            df = pd.read_csv(track_file)
            df["Long"].to_numpy()
            return_data()
            make_image(track_file)
            plt.savefig(download_dir + "/" + track_file)
            

        