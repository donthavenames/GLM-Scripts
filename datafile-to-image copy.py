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
    "start_file", 
    help = "file folder you would like to convert", 
    
)

parser.add_argument(
    "end_file",
    help = "end of the time range we want to convert",

)


#basically parses all the arguments/actually puts everything together
args = parser.parse_args()

startDateObj = datetime.datetime.strptime(args.start_date, '%m/%d/%y')
startDayCount = (startDateObj - datetime.datetime(startDateObj.year, 1, 1)).days + 1

endDateObj = datetime.datetime.strptime(args.end_date, '%m/%d/%y')
endDayCount = (endDateObj - datetime.datetime(endDateObj.year, 1, 1)).days + 1

totalDays = endDayCount - startDayCount

while totalDays >= 0:
    day = str(startDayCount)
    hour = 0
    hour_str = str(hour).zfill(2)
    path = "../GLM_Visualization" + day + "/" + hour_str + "/" + year + "/" + day
    completed = subprocess.run('gsutil -m cp -r ' + path + ' .', shell=True)
    hour += 1

    #allows the program to continue iterating through each day
    if (hour == 24):
        totalDays -= 1
        startDayCount += 1
        hour = 0
    
    if completed.returncode != 0:
        break


#the parser will parse the dates into numbers (the day of the year you start, day of the year you end)
#each one of these files will be converted into csv files for the program to read

#..\GLM_Visualization\344\00\OR_GLM-L2-LCFA_G17_s20223440000000_e20223440000200_c20223440000218.nc
# constants
track_file = "../Data/Laura/Hurricane_Laura_Trackfile_Spline.csv"

df = pd.read_csv(track_file)

df["Long"].to_numpy()

# from a single netcdf file return [date, groups_lat, groups_lon]
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


for index, row in df.iterrows():

    if index != 1551: # debug purpose only
         continue
    #if index > 1000 and index < 1010:
        #continue

    # 1549,2020-08-27 12:10:00,-93.23934491605976,31.176059435732316

    date_str = row["Date"] # = "2020-08-27 12:10:00"
#     continue
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
        
    
        

# convert lat, lon to storm center coordinates system
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

