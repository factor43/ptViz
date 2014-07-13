
import string
import sys
import msvcrt
import json
import math
from pprint import pprint


sourceDataPath = "../src_data/"
outputDataPath = "../html/data/"

tripIDToRouteMapping = {}
tripIDToModeMapping = {}

def TransportModeFromRouteID( routeID ):
	tramRoutes = ["Tram"]
	trainRoutes = ["BEL","BLACKW","GAW","GAWC","GRNG","OSBORN","OUTHA","SALIS","SEAFRD","TONS"]
	
	if trainRoutes.count(routeID) > 0:
		return 1
	elif tramRoutes.count(routeID) > 0:
		return 2
	
	# Bus is default/most common
	return 0

# finds which trips are weekday services
# creates mapping from trip ID to route (and route type)
def buildTripMetaData():
	tripFileName = sourceDataPath + "google_transit/trips.txt" 
	inputFile = open(tripFileName, 'r')

	totalTripCnt = 0
	mondayTrips = 0

	mondayServiceIDs = [1,2,6,8,9,18,21,26,44,45,53]

	for line in inputFile:
		
		totalTripCnt = totalTripCnt+1;
		
		# skip header
		if totalTripCnt is 1:
			continue
		
		fields = string.split(line.rstrip(),",")
		serviceID = int(fields[1])
		
		if mondayServiceIDs.count(serviceID) is 1:
			mondayTrips = mondayTrips + 1
			
			tripID = int(fields[2])
			
			# create mapping from tripID to routeID
			tripIDToRouteMapping[ tripID ] = fields[0]
			tripIDToModeMapping[ tripID ] = TransportModeFromRouteID(fields[0])
		
		#print words[ len(words) - 2 ]

	inputFile.close()

	print "totalTripCnt",totalTripCnt
	print "mondayTrips",mondayTrips
	print "len(tripIDToRouteMapping)",len(tripIDToRouteMapping)


def convertTimeToMinutes( inTime ):
	hours,minutes,seconds = map(int,string.split(inTime,":"))
	return (seconds/60) + minutes + (60 * hours)
	
def processStopTimes():
	tripFileName = sourceDataPath + "google_transit/stop_times.txt" 
	inputFile = open(tripFileName, 'r')

	earlyTime = sys.maxint
	lateTime = 0

	totalStopCnt = 0
	mondayStopCnt = 0
	for line in inputFile:
		totalStopCnt = totalStopCnt+1;
		
		# skip header
		if totalStopCnt is 1:
			continue
		
		fields = string.split(line.rstrip(),",")
		tripID = int(fields[0])
		
		if len(fields[1]) > 0 and len(fields[2]) > 0:
		
			arrive = convertTimeToMinutes(fields[1])
			depart = convertTimeToMinutes(fields[2])
			
		#	if arrive >= 1440:
		#		arrive -= 1440
		#		depart -= 1440
			
			# is this a monday trip?
			if tripIDToRouteMapping.has_key(tripID):
				mondayStopCnt = mondayStopCnt+1;
				
				earlyTime = min(earlyTime,arrive)
				lateTime = max(lateTime,depart)

	"""
			if arrive < earlyTime:
				earlyTime = min(earlyTime,arrive)
				print "earlyTime",fields[1],earlyTime
				
			if depart > lateTime:
				lateTime = max(lateTime,depart)
				print "lateTime",fields[2],lateTime
		
			if depart < arrive:
				print "wtf"
				print "fields[1]",fields[1]
				print "fields[2]",fields[2]
				msvcrt.getch()
	"""


	inputFile.close()

	print "totalStopCnt",totalStopCnt
	print "mondayStopCnt",mondayStopCnt

	print "earlyTime",earlyTime
	print "lateTime",lateTime
	




def normalizeXY(x):
	return (112 * x) - 1

def lat2y(lat):
	yOffset = 0.661
	return normalizeXY(math.log(math.tan(math.pi/4.0+lat*(math.pi/180.0)/2.0)) + yOffset)
	
def long2x(lon):
	xOffset = 2.4125
	return normalizeXY( lon*(math.pi/180.0) - xOffset )


allStops = {}
allStopList = []

totalBoardingAtStop = {}
boardingsAtTripStop = {}	#Index by (tripID, stopID) tuple
transportTypeAtStop = {}

stopIDtoStopCode = {}


def buildStopJSON():
	
	tripFileName = sourceDataPath + "google_transit/stops.txt" 
	inputFile = open(tripFileName, 'r')

	totalStopCnt = 0
	minLat = sys.maxint
	minLong = sys.maxint
	maxLat = -sys.maxint
	maxLong = -sys.maxint

	for line in inputFile:
		
		totalStopCnt = totalStopCnt+1;
		
		# skip header
		if totalStopCnt is 1:
			continue
		
		stopEntry = {}
		fields = string.split(line.rstrip(),",")
		
		stopEntry["ID"] = fields[0]
		stopEntry["Name"] = fields[2]
		
		slat = float(fields[4])
		slong = float(fields[5])
		
		stopEntry["X"] = long2x(slong)
		stopEntry["Y"] = lat2y(slat)
		stopCode = int(fields[1])
		stopEntry["TotalBoarded"] = totalBoardingAtStop.get(stopCode, 0)
		stopEntry["Mode"] = transportTypeAtStop.get(stopCode, 0)
		#stopEntry["type"] = 0
		
		
		stopIDtoStopCode[int(fields[0])] = stopCode
		
		minLat = min(minLat,slat)
		minLong = min(minLong,slong)
		
		maxLat = max(maxLat,slat)
		maxLong = max(maxLong,slong)
		
		allStopList.append( stopEntry )
		
	inputFile.close()

	allStops["stops"] = allStopList


	with open(outputDataPath + 'stops.json', 'w') as outfile:
		json.dump(allStops, outfile, indent=4)

	print "totalStopCnt",totalStopCnt
	
	print "minLat",minLat
	print "maxLat",maxLat
	print "minLong",minLong
	print "maxLong",maxLong
	
	print "minY",lat2y(minLat)
	print "maxY",lat2y(maxLat)
	print "minX",long2x(minLong)
	print "maxX",long2x(maxLong)
	
	print "y range",(lat2y(maxLat) - lat2y(minLat))
	print "x range",(long2x(maxLong) - long2x(minLong))



def processSuburbs():
	
	minLat = sys.maxint
	minLong = sys.maxint
	maxLat = -sys.maxint
	maxLong = -sys.maxint
	
	with open('suburbs.geojson') as f:
		data = json.load(f)
		
	for feature in data['features']:
		#print feature['geometry']['type']
		#print feature['geometry']['coordinates'][0]
		#print len(feature['geometry']['coordinates'][0])
		
		for vert in feature['geometry']['coordinates'][0]:
			
			print "vert[0]",vert[0]
			print "vert[1]",vert[1]
			#msvcrt.getch()
			
			slong = float(vert[0])
			slat = float(vert[1])
			
			minLat = min(minLat,slat)
			minLong = min(minLong,slong)
			
			maxLat = max(maxLat,slat)
			maxLong = max(maxLong,slong)

	print "minLat",minLat
	print "maxLat",maxLat
	print "minLong",minLong
	print "maxLong",maxLong


def processPassengers():
	
	inputFile = open(sourceDataPath + "PTSBoardingSummary.CSV/PTSBoardingSummary.CSV", 'r')

	fo = open('mostRecentWeek.csv', "wb")

	uniqueWeeks = {}
	
	totalCnt = 0
	for line in inputFile:

		#msvcrt.getch()
		totalCnt = totalCnt + 1
		# skip header
		if totalCnt is 1:
			fo.write( line );
			continue
		
		fields = string.split(line.rstrip(),",")
		d,t = string.split(fields[5]," ")
		
		uniqueWeeks[d] = uniqueWeeks.get(d, 0) + 1
		
		# Hmm - this is the most recent week that seems to have valid / "sensible" numbers
		# all subsequent weeks are significantly lower by nearly a factor of 10 (although not yet school holidays??)
		# don't have time to investigate - just keep hacking!
		if "2014-06-22" in d:
			fo.write( line );

	inputFile.close()
	
	print "len(uniqueWeeks) ",len(uniqueWeeks) 
	print "totalCnt",totalCnt 
	pprint(uniqueWeeks) 
	
	fo.close()
	
	
def processPassengersRecent():
	
	inputFile = open("mostRecentWeek.csv", 'r')
	
	maxBoarded = 0
	totalBoarded = 0
	totalCnt = 0
	for line in inputFile:
		
		totalCnt = totalCnt + 1
		if totalCnt is 1:
			continue
		
		fields = string.split(line.rstrip(),",")
		boarded = int(fields[4].replace("\"",""))
		
		try:
			stopID = int(fields[2].replace("\"",""))
			totalBoardingAtStop[stopID] = totalBoardingAtStop.get(stopID, 0) + boarded
			
			routeID = fields[1].replace("\"","")
			
			tripID = int(fields[0].replace("\"",""))
			
			boardingsAtTripStop[ (tripID, stopID) ] = boarded
			
			b2 = boardingsAtTripStop.get((tripID, stopID), 0)

		#	print "stopID",stopID
		#	print "tripID",tripID
		#	print "boarded",boarded
		#	print "b2",b2
		#	msvcrt.getch()
			transportTypeAtStop[stopID] = TransportModeFromRouteID(routeID)

		except ValueError:
			continue
		
		totalBoarded += boarded
		maxBoarded = max(maxBoarded,boarded)
	
	inputFile.close()

	print "maxBoarded",maxBoarded
	print "totalBoarded",totalBoarded
	

def buildTripsJSON():
	
	tripFileName = sourceDataPath + "google_transit/stop_times.txt" 
	inputFile = open(tripFileName, 'r')

	allTripsList = []

	lastTrip = None;
	lastTripID = -1
	
	
	totalBoardCnt = 0;
	
	totalCnt = 0
	for line in inputFile:
		
		totalCnt = totalCnt + 1
		if totalCnt is 1:
			continue
			
		fields = string.split(line.rstrip(),",")
		
		tripID = int(fields[0])
		
		
		#if tripID != 21179:
		#	continue
		
		arrTime = fields[1]
		depTime = fields[2]
		stopID = int(fields[3])
		mode = 0
		route = "ROUTE"
		
		if fields[1] is not '' and fields[2] is not '':
			if tripID != lastTripID:
				lastTrip = {}
				lastTrip["TripID"] = tripID
				lastTrip["Mode"] = tripIDToModeMapping.get(tripID,"UNKNOWN")
				lastTrip["Route"] = tripIDToRouteMapping.get(tripID,"UNKNOWN")
				lastTrip["Stops"] = []
				lastTripID = tripID
				allTripsList.append(lastTrip)
			
			stopElement = {}
			stopElement["ID"] = stopID
			stopElement["TArr"] = convertTimeToMinutes(fields[1])
			stopElement["TDep"] = convertTimeToMinutes(fields[2])
			
			stopCode = stopIDtoStopCode.get(stopID, -1)
			
			stopElement["PCnt"] = boardingsAtTripStop.get((tripID, stopCode), 0)
			
			totalBoardCnt += boardingsAtTripStop.get((tripID, stopCode), 0)
			
			lastTrip["Stops"].append(stopElement)
		
	inputFile.close()
	
	allTrips = {}
	allTrips["Trips"] = allTripsList
	with open(outputDataPath + 'trips.json', 'w') as outfile:
		json.dump(allTrips, outfile)
	
	print "tripStops",totalCnt
	print "totalBoardCnt in TRIPS",totalBoardCnt


buildTripMetaData()

#processPassengers()

processPassengersRecent()

buildStopJSON()

#processSuburbs()

buildTripsJSON()



