import csv
import json
import numpy as np
import cv2
from datetime import datetime, timedelta
import argparse
import glob, os

def dir_path(string):
    if os.path.isdir(string):
        return string
    else:
        raise NotADirectoryError(string)

parser = argparse.ArgumentParser(description='Convert database dump to json for heatmap')
parser.add_argument('--save', action='store_true', help='Save birdview images on /output_bb')
parser.add_argument('--saveaggregate', action='store_true', help='Save birdview images on /output_bb as aggregate')
parser.add_argument('--json', action='store_true', help='Save output json')
parser.add_argument('--animatedjson', action='store_true', help='Save output json')
parser.add_argument('--legacy', action='store_true', help='Support for satellite-proto-B/C')
parser.add_argument('--path', type=dir_path, default='data', help='Where to find the csv data')

args = parser.parse_args()

files = [file for file in glob.glob(args.path + "/" + "*.csv")]

result = []
global_max_x = 0
global_max_y = 0
global_min_x = 9999999
global_min_y = 9999999
pY_max = None
pX_max = None

def getMaxMin(data, index):
	global global_max_x, global_min_x, global_min_y, global_max_y
	global pX_max, pY_max
	for d in data:
		if d[0] > global_max_x:
			global_max_x = d[0]
			pX_max = index
		if d[0] < global_min_x:
			global_min_x = d[0]

		if d[1] > global_max_y:
			global_max_y = d[1]
			pY_max = index
		if d[1] < global_min_y:
			global_min_y = d[1]

if args.legacy:
	points_index = 3
	timestamp_index = 7
	counter_index = 1
	date_format = '%Y-%m-%dT%H:%M:%S'
else:
	points_index = 9
	timestamp_index = 14
	counter_index = 2
	date_format ='%Y-%m-%d %H:%M:%S'

for file in files:
	with open(file, newline='') as csvfile:
		r = csv.reader(csvfile, delimiter=',')
		print(f"Reading {file}")
		for idx, row in enumerate(r):
			if idx > 0:
				pp = json.loads(row[points_index])
				getMaxMin(pp, idx-1)
				result.append({
					"index": int(row[counter_index]),
					"timestamp": datetime.strptime(row[timestamp_index][0:19], date_format),
					"pp": pp
				})

offset_x = 0 if global_min_x >= 0 else abs(global_min_x)
offset_y = 0 if global_min_y >= 0 else abs(global_min_y)
global_max_x = global_max_x + offset_x
global_max_y = global_max_y + offset_y

print(f"Found x max at index [{pX_max}] and p y max at index [{pY_max}]")
print(f"X max {result[pX_max]}")
print(f"Y max {result[pY_max]}")
print(f"Globals ({global_max_x}, {global_max_y}), Offsets ({offset_x}, {offset_y})")

# Offset all data so that min x == 0 and min y == 0
# And flip on x axis
for r in result:
	for p in r["pp"]:
		p[0] = p[0] + offset_x
		p[1] = p[1] + offset_y
		p[0] = (global_max_x+1) - p[0]

# Sort by timestamp
result.sort(key=lambda x: x["timestamp"])

# Create a named colour
color = [255,255,255]
color2 = [0,255,255]

# Save individual bird views
if args.save:
	for idx, r in enumerate(result):
		img = np.zeros((global_max_y+1, global_max_x+1, 3), dtype=np.uint8)
		for p in r["pp"]:
			# Draw the point
			img = cv2.circle(img, (p[0],p[1]), 4, color, 2)

		# Save
		cv2.imwrite("output_bb/birdview_" + str(r["index"]) + ".png", img)

# Save aggregated birdview
if args.saveaggregate:
	img = np.zeros((global_max_y+1, global_max_x+1, 3), dtype=np.uint8)
	for idx, r in enumerate(result):
		for p in r["pp"]:
			# Draw the point
			img = cv2.circle(img, (p[0],p[1]), 4, color, 2)

		# Save
	cv2.imwrite("output_bb/birdview_aggregate.png", img)

# Save json output (only people points)
if args.json:
	json_string = {
		'width': global_max_x,
		'height': global_max_y,
		'data': [r["pp"] for r in result]
	}
	with open('output.json', 'w') as outfile:
		outfile.write("var data = ")
	with open('output.json', 'a') as outfile:
		json.dump(json_string, outfile)

# Save animatedjson output (only people points)
if args.animatedjson:
	print(result[0]["timestamp"], type(result[0]["timestamp"]))
	delta = timedelta(minutes=10)
	start_window = result[0]["timestamp"]
	end_window = start_window + delta

	data = []
	bucket = []
	for r in result:
		if r["timestamp"] < end_window:
			bucket.extend(r["pp"])
		else:
			data.append({"start": start_window, "end": end_window, "points": bucket})
			print(f"Generated new bucket from {start_window} to {end_window} with # points --> {len(bucket)}")
			bucket = []
			start_window = end_window
			end_window = start_window + delta
			bucket.extend(r["pp"])

	# Append dangling bucket
	data.append({"start": start_window, "end": end_window, "points": bucket})
	print(f"Generated new bucket from {start_window} to {end_window} with # points --> {len(bucket)}")
		
	json_string = {
		'width': global_max_x,
		'height': global_max_y,
		'data': data
	}
	with open('output_animated.json', 'w') as outfile:
		outfile.write("var data = ")
	with open('output_animated.json', 'a') as outfile:
		json.dump(json_string, outfile, default=str)
