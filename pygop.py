import sys
import urllib, urllib2
import xml.etree.ElementTree as ET

defaultGatewayName = 'lighting.local'

class pygop(object):
	def __init__(self):
		self.bulbList = {}
		self.token = 0

		# connect to the gateway and get inital token

		command = 'GWRLogin'
		data = '<gip><version>1</version><email>admin</email><password>admin</password></gip>'

		result = self.__sendGopCommand(command, data)

		tree = ET.fromstring(result)
		for child in tree.iter('token'):
			self.token = child.text

	# API Functions

	def printRoomInfo(self):
		#get data for all rooms and print to the screen
		self.__scanRooms(True)


	def setBulbLevelByDid(self, did, onoff, level):
		command = 'DeviceSendCommand'

		if ((onoff == 0) and (level == 0)): 
			data = '<gip><version>1</version><token>' + self.token + '</token><did>' + str(did) + '</did><value>0</value></gip>'
		elif ((onoff != 0) and (level == 0)): 
			data = '<gip><version>1</version><token>' + self.token + '</token><did>' + str(did) + '</did><value>1</value></gip>'
		else:
			data = '<gip><version>1</version><token>' + self.token + '</token><did>' + str(did) + '</did><type>level</type><val>' + str(level) + '</val></gip>'

		self.__sendGopCommand(command, data)

	def setBulbLevelByName(self, name, onoff, level):
		# resolve name to did first
		self.setBulbLevelByDid(self.__nameToDid(name), onoff, level)

	## private helper functions

	def __sendGopCommand(self, command, data):
		url = 'http://' + defaultGatewayName + '/gwr/gop.php'
		headers = { 'Host' : 'lighting.local',
					'Content-Type': 'application/x-www-form-urlencoded'}

		values = {'cmd' : command,
		          'data' : data,
		          'fmt' : 'xml'}

		data = urllib.urlencode(values)
		req = urllib2.Request(url, data, headers)
		response = urllib2.urlopen(req)
		page_content = response.read()
		return page_content

	def __scanRooms(self, output):
		command = 'RoomGetCarousel'
		data = '<gip><version>1</version><token>' + self.token + '</token><fields>name,power,product,class,image,imageurl,control</fields></gip>'

		result = self.__sendGopCommand(command, data)

		tree = ET.fromstring(result)
		for room in tree.findall('room'):
			if (output):
				print 'Room: ' + room.find('name').text
			for device in room.findall('device'):
				self.bulbList[device.find('name').text] = device.find('did').text
				if (output):
					print '     Name:' + device.find('name').text
					print '      Did:' + device.find('did').text
					if (device.find('offline') is not None):
						print '     (Offline)'

	def __nameToDid(self, name):
		#first do a scan to populate bulbList
		if(self.bulbList == {}):
			self.__scanRooms(False)

		#find did by name
		did =  self.bulbList.get(name)

		if(did is not None):
			return did
		else:
			sys.exit('That bulb name does not exist')
