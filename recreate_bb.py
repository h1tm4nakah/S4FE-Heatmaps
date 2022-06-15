import csv
import json
import numpy as np
import cv2
from datetime import datetime

result = []

with open("data/f9c4adf0-b0db-11ec-9118-e45f01385fc3.csv", newline='') as csvfile:
	r = csv.reader(csvfile, delimiter=',')
	for idx, row in enumerate(r):
		if idx > 0:
			bb = json.loads(row[8])
			result.append({
				"img": row[1] + "_" + row[2] + ".jpg",
				"idx": int(row[2]),
				"timestamp": datetime.strptime(row[14][0:19], '%Y-%m-%d %H:%M:%S'),
				"bb": bb
			})

result.sort(key=lambda x: x["timestamp"])

for r in result:
	img = cv2.imread("data/static/samples/frame" + r["img"])
	for bb in r["bb"]:
		# (X, Y, W, H)
		# start point = top-left corner
		# end point = bottom-right corner
		start_point = (bb[0], bb[1])
		end_point   = (int(bb[0] + bb[2]), (int(bb[1] + bb[3])))
		img = cv2.rectangle(img, start_point, end_point, [255, 120, 0], 2)
		img = cv2.circle(img, (bb[0],bb[1]), 4, [0, 255, 0], 2)
		img = cv2.circle(img, (int(bb[0] + (bb[2]/2)), (int(bb[1] + bb[3]))), 4, [0, 0, 255], 2)

	cv2.imwrite("output/result" + str(r["idx"]) + ".png", img)
