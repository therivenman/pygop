import sys
import urllib, urllib2
import xml.etree.ElementTree as ET

defaultGatewayName = 'lighting'

class pygop(object):
	def __init__(self):
		self.deviceList = {}
		self.roomList = {}
		self.token = 0

		# connect to the gateway and get inital token

		command = 'GWRLogin'
		data = '<gip><version>1</version><email>admin</email><password>admin</password></gip>'

		result = self.__sendGopCommand(command, data)

		tree = ET.fromstring(result)
		for child in tree.iter('token'):
			self.token = child.text

	# API Functions

	def printHouseInfo(self):
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
		bulbDid = self.__nameToDid(name)

		if (bulbDid is not None):
			self.setBulbLevelByDid(bulbDid, onoff, level)
		else:
			print 'Device name does not exist'

	def setRoomLevelByRid(self, rid, onoff, level):
		command = 'RoomSendCommand'

		if ((onoff == 0) and (level == 0)): 
			data = '<gip><version>1</version><token>' + self.token + '</token><rid>' + str(rid) + '</rid><value>0</value></gip>'
		elif ((onoff != 0) and (level == 0)): 
			data = '<gip><version>1</version><token>' + self.token + '</token><rid>' + str(rid) + '</rid><value>1</value></gip>'
		else:
			data = '<gip><version>1</version><token>' + self.token + '</token><rid>' + str(rid) + '</rid><type>level</type><val>' + str(level) + '</val></gip>'

		self.__sendGopCommand(command, data)

	def setRoomLevelByName(self, name, onoff, level):
		# resolve name to did first
		roomRid = self.__nameToRid(name)

		if (roomRid is not None):
			self.setRoomLevelByRid(roomRid, onoff, level)
		else:
			print 'Room name does not exist'

	# private helper functions

	def __sendGopCommand(self, command, data):
		url = 'http://' + defaultGatewayName + '/gwr/gop.php'
		headers = { 'Host' : defaultGatewayName,
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
			self.roomList[room.find('name').text] = room.find('rid').text
			if (output):
				print 'Room: ' + room.find('name').text
				print ' Rid: ' + room.find('rid').text
			for device in room.findall('device'):
				self.deviceList[device.find('name').text] = device.find('did').text
				if (output):
					if (device.find('prodtype').text == "Light Fixture"):
						print '     Light Fixture:'
					elif (device.find('prodtype').text == "LED"):
						print '     LED Bulb:'
					elif (device.find('prodtype').text == "CFL"):
						print '     CFL Bulb:'
					else:
						print '     Unknown Device Type:'
					print '     Name: ' + device.find('name').text
					print '      Did: ' + device.find('did').text
					if (device.find('state').text == '1'):
						print '    State: On'
					else:
						print '    State: Off'
					print '    Level: ' +  device.find('level').text
					if (device.find('offline') is not None):
						print '     (Offline)'
					print ''

	def __nameToDid(self, name):
		#first do a scan to populate database
		if(self.deviceList == {}):
			self.__scanRooms(False)

		did =  self.deviceList.get(name)

		return did

	def __nameToRid(self, name):
		#first do a scan to populate database
		if (self.roomList == {}):
			self.__scanRooms(False)

		rid = self.roomList.get(name)

		return rid