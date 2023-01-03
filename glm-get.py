import argparse
import subprocess
import datetime

# Get current UTC time
#current_time = datetime.now(timezone.utc)
#print(current_time)

#purpose of this is to create an argument parser with a description
parser = argparse.ArgumentParser(description="Download glm data from Google Cloud")

# start & end date arguments
parser.add_argument(
    "start_date", 
    help = "start of the time range we want to download", 
    
)

parser.add_argument(
    "end_date",
    help = "end of the time range we want to download",

)

parser.add_argument(
    "bucket_name",
    help = "lets you choose between goes-16 (1) and goes-17 (2)"

)

#basically parses all the arguments/actually puts everything together
args = parser.parse_args()
bucketName = "gcp-public-data-goes-17"

# allows the user to decide between goes-16 and goes-17
if args.bucket_name == "goes-16" or args.bucket_name == "1":
    bucketName = "gcp-public-data-goes-16";
elif args.bucket_name == "goes-17" or args.bucket_name == "2":
    bucketName = "gcp-public-data-goes-17";

startDateObj = datetime.datetime.strptime(args.start_date, '%m/%d/%y')
startDayCount = (startDateObj - datetime.datetime(startDateObj.year, 1, 1)).days + 1

endDateObj = datetime.datetime.strptime(args.end_date, '%m/%d/%y')
endDayCount = (endDateObj - datetime.datetime(endDateObj.year, 1, 1)).days + 1

totalDays = endDayCount - startDayCount
glmDataType = "GLM-L2-LCFA"

#sets a starting value for the program as the year of the inputted start date
year = str(startDateObj.year)

while totalDays >= 0:
    day = str(startDayCount).zfill(3)
    path = "gs://" + bucketName + "/" + glmDataType + "/" + year + "/" + day
    completed = subprocess.run('gsutil -m cp -r ' + path + ' .', shell=True)

    #allows the program to continue iterating through each day
    totalDays -= 1
    startDayCount += 1
    if completed.returncode != 0:
        break




