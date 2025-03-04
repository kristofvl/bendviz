#!/usr/bin/env python3
import csv
import numpy as np
import pandas as pd

for process in [79]:
	proc = str(process)  # here we set the subject to compress
	# arbitrarily skipped datapoints and quantization, just to test
	skipSize = 1; quant = 100
	numChannels = 20  # # of sensors
	print(proc)

	# read process CSV file
	with open(proc+'.csv') as f:
		reader = csv.reader(f, delimiter = ',')
		adata = list(reader)

	# create and fill data structure:
	sensors = np.zeros([numChannels,int(len(adata)/skipSize)])  # add one extra (might be left 0)
	i=0
	for row in adata[1:-1:skipSize]:  # first row is header
		for sensor in range(1,numChannels):  # columns 1-20 contain the sensor values
			try:
				sensors[sensor-1][i] = row[sensor]  # (float(row[sensor])*quant)
			except:
				print("Error value:"+str(row[sensor]))
				sensors[sensor-1][i] = 0
		i+=1

	print(sensors)

	# get minima, maxima, iqr:
	m = np.zeros([numChannels,2])
	for i in range(numChannels):
		m[i][0] = np.amin(sensors[i][0:-2])  # min(sensors[i])
		m[i][1] = np.amax(sensors[i][0:-2]) # max(sensors[i])
		print("min: "+str(m[i][0])+", max:"+str(m[i][1]))
	# adjust channels in plot:
	torquesMin = [ m[0][0], m[1][0], m[2][0], m[6][0], m[7][0], m[12][0], m[13][0], m[14][0], m[18][0] ]
	torquesMax = [ m[0][1], m[1][1], m[2][1], m[6][1], m[7][1], m[12][1], m[13][1], m[14][1], m[18][1] ]
	tmin = np.amin( torquesMin )
	tspan = (np.amax(torquesMax)-np.amin(torquesMin))
	distMin = [ m[3][0],m[4][0],m[5][0],m[8][0],m[9][0],m[11][0],m[15][0],m[16][0],m[17][0],m[19][0]]
	distMax = [ m[3][1],m[4][1],m[5][1],m[8][1],m[9][1],m[11][1],m[15][1],m[16][1],m[17][1],m[19][1]]
	dmin = np.amin( distMin )
	dspan = np.amax(distMax)-np.amin(distMin)
	for i in range(len(sensors[0])-1):
		for channel in range(numChannels):
			if m[channel][0] == m[channel][1]:
				sensors[channel][i] = 0
			else:
				if channel in [0,1,2,6,7,12,13,14,18]:  # Torque:
					sensors[channel][i] =  int( quant* ((sensors[channel][i]-tmin)/tspan - 0.5) )
				elif channel in [3,4,5,8,9,11,15,16,17,19]:  # Dist/ Angle:
					sensors[channel][i] =  int( quant* ((sensors[channel][i]-dmin)/dspan - 0.5) )
				else:
					sensors[channel][i] =  int( quant* ((sensors[channel][i]-m[channel][0])/(m[channel][1]-m[channel][0]) - 0.5) )
				# move in plot:
			if channel<3:
				sensors[channel][i] += 450
			elif channel<6:
				sensors[channel][i] += 400
			elif channel<10:
				sensors[channel][i] += 300
			elif channel<12:
				sensors[channel][i] += 220
			elif channel<18:
				sensors[channel][i] += 100


	# write to file:
	with open('dta'+proc+'.js',"w") as f:
		i=0
		for sensor in ["bendDieLatT","bendDieRotT","bendDieVerT","bendDieLatM","bendDieRotA","bendDieVerM",
			"colletAxT","colletRotT","colletAxMov","colletRotMov",
			"mandrelAxLoad","mandrelAxMov",
			"pressAxT","pressLatT","pressLeftAxT","pressAxMov","pressLatMov","pressLeftAxMov",
			"clampLatT","clampLatMov"]:
			f.write("var "+sensor+"=[")
			f.write(",".join( list( map (str, [int(x) for x in sensors[i][:-2] ]) ) ) )  # -1: remove last potential 0*
			f.write("];\n")
			i+=1
		f.write("var info='Diameter tube [mm]: "+str(adata[1][12])+
			"<br/>Wall thickness tube [mm]: "+str(adata[1][13])+
			"<br/>Mandrel extraction before bending end: "+str(adata[1][14])+
			"<br/>Collet boost: "+str(adata[1][15])+
			"<br/>Clearance pressure die [mm]: "+str(adata[1][16])+
			"';")
