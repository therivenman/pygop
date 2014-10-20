import sys
import urllib, urllib2
import xml.etree.ElementTree as ET
from time import sleep

__version__ = "0.0.1"

defaultGatewayName = 'lighting.local'
GOPReturnCodes = {	'200': 'Command Succesful',
					'404': 'Invalid Command',
					'500': 'Incorrect Did/Rid'}

class pygop(object):
	def __init__(self):
		self.deviceList = {}
		self.roomList = {}
		self.token = 0

		# connect to the gateway and get initial token

		command = 'GWRLogin'
		data = '<gip><version>1</version><email>admin</email><password>admin</password></gip>'

		result = self.__sendGopCommand(command, data)

		if (result is False):
			sys.exit('Failed to get XML response.  Exiting')

		self.token = self.__getXMLTagValue(result, 'token')
		if (self.token is None):
			sys.exit('Unable to get token.  Exiting')

	# API Functions

	def printHouseInfo(self):
		'Gets data for all rooms and prints it to the screen'
		self.__scanRooms(True)

	# Set Level APIs

	def setBulbLevelByDid(self, did, onoff, level=0):
		'Sets the bulb on/off or dim level. [did, (1 - on, 0 off), dim level (1-100)]\n' \
		'Note: To set the bulb on or off, the level parameter must be 0.'
		command = 'DeviceSendCommand'

		if (level == 0):
			data = '<gip><version>1</version><token>%s</token><did>%s</did><value>%d</value></gip>' % (self.token, did, onoff)
		else:
			data = '<gip><version>1</version><token>%s</token><did>%s</did><type>level</type><value>%d</value></gip>' % (self.token, did, level)

		result = self.__sendGopCommand(command, data)

		if(result is False):
			print 'Failed to setBulbLevelByDid'
			return False

		return True

	def setBulbLevelByName(self, name, onoff, level=0):
		'Sets the bulb on/off or dim level. [name, (1 - on, 0 off), dim level (1-100)]\n' \
		'Note: To set the bulb on or off, the level parameter must be 0.'
		# resolve name to did first
		bulbDid = self.__nameToDid(name)

		if (bulbDid is not None):
			result = self.setBulbLevelByDid(bulbDid, onoff, level)

			if(result is False):
				print 'Failed to setBulbLevelByName'
				return False
		else:
			print 'Device name does not exist'
			return False

		return True

	def setRoomLevelByRid(self, rid, onoff, level=0):
		'Sets the room on/off or dim level. [rid, (1 - on, 0 off), dim level (1-100)]\n' \
		'Note: To set the room on or off, the level parameter must be 0.'
		command = 'RoomSendCommand'

		if (level == 0):
			data = '<gip><version>1</version><token>%s</token><rid>%s</rid><value>%d</value></gip>' % (self.token, rid, onoff)
		else:
			data = '<gip><version>1</version><token>%s</token><rid>%s</rid><type>level</type><value>%d</value></gip>' % (self.token, rid, level)

		result = self.__sendGopCommand(command, data)

		if(result is False):
			print 'Failed to setRoomLevelByRid'
			return False

		return True

	def setRoomLevelByName(self, name, onoff, level=0):
		'Sets the room on/off or dim level. [name, (1 - on, 0 off), dim level (1-100)]\n' \
		'Note: To set the room on or off, the level parameter must be 0.'
		# resolve name to did first
		roomRid = self.__nameToRid(name)

		if (roomRid is not None):
			result = self.setRoomLevelByRid(roomRid, onoff, level)
			if(result is False):
				print 'Failed to setRoomLevelByName'
				return False
		else:
			print 'Room name does not exist'
			return False

		return True

	# Identify APIs

	def identifyBulbByDid(self, did):
		'Identifies a bulb by dimming it. [did]'

		result = self.__identify(self.setBulbLevelByDid, did)
		if(result is False):
			print 'Failed to identifyBulbByDid'
			return False

		return True

	def identifyBulbByName(self, name):
		'Identifies a bulb by dimming it. [name]'

		result = self.__identify(self.setBulbLevelByName, name)
		if(result is False):
			print 'Failed to identifyBulbByName'
			return False

		return True

	def identifyRoomByRid(self, rid):
		'Identifies a room by dimming the bulbs in it. [rid]'

		result = self.__identify(self.identifyRoomByRid, rid)
		if(result is False):
			print 'Failed to identifyRoomByRid'
			return False

		return True

	def identifyRoomByName(self, name):
		'Identifies a room by dimming the bulbs in it. [did]'

		result = self.__identify(self.identifyRoomByName, name)
		if(result is False):
			print 'Failed to identifyRoomByName'
			return False

		return True

	# private helper functions

	def __identify(self, action, identifier):

		# turn the target on
		result = action(identifier, 1)
		if(result is False):
			print 'Failed to identify %s' % identifier
			return False

		# dim between 50 and 70 percent a few times
		for level in range(1,7):
			result = action(identifier, 1, 50 + level%2 * 20)
			if(result is False):
				print 'Failed to identify %s' % identifier
				return False

			sleep(75.0/1000)

		return True

	def __sendGopCommand(self, command, data):
		url = 'http://' + defaultGatewayName + '/gwr/gop.php'
		headers = { 'Host' : defaultGatewayName,
					'Content-Type': 'application/x-www-form-urlencoded'}

		values = {'cmd' : command,
		          'data' : data,
		          'fmt' : 'xml'}

		data = urllib.urlencode(values)
		req = urllib2.Request(url, data, headers)

		# handle any connection errors
		try:
			response = urllib2.urlopen(req)
		except urllib2.URLError as e:
			if hasattr(e, 'reason'):
				print 'Failed to reach the lighting server. Check to make ' \
				'sure you\'re connected to the same network as the gateway ' \
				'and it\'s online.'
				print 'Reason: ', e.reason
			elif hasattr(e, 'code'):
				print 'The server couldn\'t fulfill the request.'
				print 'Error code: ', e.code

			return False
		else:
			result = response.read()

			# Print GOP Error if there is one
			rc = self.__getXMLTagValue(result, 'rc')
			if (rc is not None):
				if (rc != '200'):
					print rc + ': ' + GOPReturnCodes[rc]
					return False

			return result

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

					if (device.find('offline') is not None):
						print '     (Offline)'
					else:
						print '    Level: ' +  device.find('level').text
					print ''

	def __nameToDid(self, name):
		#first do a scan to populate database
		if(self.deviceList == {}):
			self.__scanRooms(False)

		did = self.deviceList.get(name)

		return did

	def __nameToRid(self, name):
		#first do a scan to populate database
		if (self.roomList == {}):
			self.__scanRooms(False)

		rid = self.roomList.get(name)

		return rid

	def __getXMLTagValue(self, xml, tag):
		tree = ET.fromstring(xml)
		value = tree.find(tag)

		if (value is not None):
			return value.text
		else:
			return None

