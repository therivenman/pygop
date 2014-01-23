import urllib, urllib2
import xml.etree.ElementTree as ET

defaultGatewayName = 'lighting.local'

class pygop(object):
	def __init__(self):
		# connect to the gateway and get inital token

		command = 'GWRLogin'
		data = '<gip><version>1</version><email></email><password>18d718bcc71b6e353394dc0f6f9f6f67b60f6036b59828b8bc7bd7ca31e5f5d2</password></gip>'

		the_page = self.__sendCommand(command, data)

		tree = ET.fromstring(the_page)
		for child in tree.iter('token'):
			self.token = child.text

	def getRooms(self):
		#get data for all rooms and print to the screen
		command = 'RoomGetCarousel'
		data = '<gip><version>1</version><token>' + self.token + '</token><fields>name,power,product,class,image,imageurl,control</fields></gip>'

		the_page = self.__sendCommand(command, data)

		tree = ET.fromstring(the_page)
		for room in tree.findall('room'):
			print 'Room: ' + room.find('name').text
			for device in room.findall('device'):
				print '     Name:' + device.find('name').text
				print '      Did:' + device.find('did').text

	def setBulbLevel(self, did, onoff, level):

		command = 'DeviceSendCommand'

		if ((onoff == 0) and (level == 0)): 
			data = '<gip><version>1</version><token>' + self.token + '</token><did>' + str(did) + '</did><value>0</value></gip>'
		elif ((onoff != 0) and (level == 0)): 
			data = '<gip><version>1</version><token>' + self.token + '</token><did>' + str(did) + '</did><value>1</value></gip>'
		else:
			data = '<gip><version>1</version><token>' + self.token + '</token><did>' + str(did) + '</did><type>level</type><val>' + str(level) + '</val></gip>'

		self.__sendCommand(command, data)

	def __sendCommand(self, command, data):
		url = 'http://' + defaultGatewayName + '/gwr/gop.php'
		headers = { 'Host' : 'lighting.local',
					'Content-Type': 'application/x-www-form-urlencoded'
					}

		values = {'cmd' : command,
		          'data' : data,
		          'fmt' : 'xml'}

		data = urllib.urlencode(values)
		req = urllib2.Request(url, data, headers)
		response = urllib2.urlopen(req)
		the_page = response.read()
		return the_page
