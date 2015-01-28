import shelve
import sys
import ssl
import uuid
import urllib, urllib2
import xml.etree.ElementTree as ET
try:
	import settings
except:
	sys.exit("Couldn't load settings.py file, check the README.")

# disable ssl cert validation for python versions >= 2.7.9
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

__version__ = "0.0.2"
cache_filename = "pygop.cache"
GOPReturnCodes = {  '200': 'Command Succesful',
                    '401': 'Invalid Token',
                    '404': 'Invalid Command',
                    '500': 'Incorrect Did/Rid'}

class pygop(object):
    def __init__(self, gatewayName=None):

        self.gatewayIP = settings.GATEWAY_IP

        self.token = self.__login()

        if not self.token:
            sys.exit("Couldn't login to the gateway.")

        self.carousel = self.__scanRooms()
        if not self.carousel:
            sys.exit("Couldn't enumerate rooms or devices")

    # API Functions

    def printHouseInfo(self):
        'Gets data for all rooms and prints it to the screen'
        self.carousel = self.__scanRooms(invalidate=True)
        if not self.carousel:
            print "Couldn't enumerate rooms or devices"
            return False

        for room in self.carousel["rooms"]:
            print 'Room: %s' % room["name"]
            print ' Rid: %s' % room["rid"]
            print ""

            for device in room["devices"]:
                if device["type"] == "LED":
                    print "   Type: LED Bulb"
                elif device["type"] == "CFL":
                    print "   Type: CFL Bulb"
                elif device["type"] == "Light Fixture":
                    print "   Type: Light Fixture"
                else:
                    print "   Type: Unknown"

                print "   Name: %s" % device["name"]

                print "    Did: %s" % device["did"]

                print "  State: %s" % ("On" if device["state"] == "1" else "Off")

                if (device["offline"]):
                    print "   (Offline)"

                if (device["level"]):
                    print "  Level: %s" % device["level"]

                print ""

    # Set Level APIs

    def setBulbLevelByDid(self, did, onoff, level=0):

        'Sets the bulb on/off or dim level. [did, (1 - on, 0 off), dim level (1-100)]\n' \
        'Note: To set the bulb on or off, the level parameter must be 0.'
        command = 'DeviceSendCommand'

        if (level == 0):
            data = '<gip><version>1</version><token>%s</token><did>%d</did><value>%d</value></gip>' % (self.token, did, onoff)
        else:
            data = '<gip><version>1</version><token>%s</token><did>%d</did><type>level</type><value>%d</value></gip>' % (self.token, did, level)

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

        result = self.__identify(self.setRoomLevelByRid, rid)
        if(result is False):
            print 'Failed to identifyRoomByRid'
            return False

        return True

    def identifyRoomByName(self, name):
        'Identifies a room by dimming the bulbs in it. [name]'

        result = self.__identify(self.setRoomLevelByName, name)
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

        return True

    def __sendGopCommand(self, command, data):
        url = 'https://%s/gwr/gop.php' % self.gatewayIP

        headers = { 'Host' : self.gatewayIP,
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

    def __scanRooms(self, invalidate=False):
        try:
            carousel = self.__readCache("carousel", invalidate)
            return carousel
        except:
            command = 'RoomGetCarousel'
            data = '<gip><version>1</version><token>' + self.token + '</token><fields>name,power,product,class,image,imageurl,control</fields></gip>'
            result = self.__sendGopCommand(command, data)

            if result:
                carousel = { "rooms" : [] }

                tree = ET.fromstring(result)
                for room in tree.findall('room'):
                    roomid = room.find('rid').text
                    roomname = room.find('name').text
                    current_room = { "name" :  roomname, "rid" : roomid, "devices" : [] }

                    for device in room.findall('device'):
                        deviceid = device.find('did').text
                        devicename = device.find('name').text
                        devicetype = device.find('prodtype').text
                        devicestate = device.find('state').text
                        deviceoffline =  True if device.find('offline') is not None else False
                        devicelevel = None if device.find('level') is None else device.find('level').text

                        current_room["devices"].append({ "name"   : devicename,
                                                         "did"    : deviceid ,
                                                         "type"   : devicetype,
                                                         "state"  : devicestate,
                                                         "offline" : deviceoffline,
                                                         "level"  : devicelevel })

                carousel["rooms"].append(current_room)
                self.__writeCache("carousel", carousel)
                return carousel

        return None

    def __nameToDid(self, name):
        for room in self.carousel["rooms"]:
            for device in room["devices"]:
                if device["name"].lower() == name.lower():
                    return device["did"]

        return None

    def __nameToRid(self, name):
        for room in self.carousel["rooms"]:
            if room["name"].lower() == name.lower():
                return room["rid"]

        return None

    def __getXMLTagValue(self, xml, tag):
        tree = ET.fromstring(xml)
        value = tree.find(tag)

        if (value is not None):
            return value.text
        else:
            return None

    def __login(self):
        try:
            token = self.__readCache("token")
            return token

        except:
            loginuuid = uuid.uuid4()

            command = 'GWRLogin'
            data = '<gip><version>1</version><email>%s</email><password>%s</password></gip>' % (loginuuid, loginuuid)
            result = self.__sendGopCommand(command, data)

            if result:
                token = self.__getXMLTagValue(result, 'token')
                self.__writeCache("token", token)
                return token

        return None

    def __readCache(self, key, invalidate=False):
        if invalidate:
            # This is based on the assumption that we will
            # write to the cache if it does not contain
            # the key we were looking for. The exception
            # will be handled in the calling function
            # which will query the gateway for data
            # and then write it to the cache afterwards
            raise KeyError

        try:
            s = shelve.open(cache_filename)
            value = s[key]
        finally:
            s.close()

        return value

    def __writeCache(self, key, value):
        try:
            s = shelve.open(cache_filename, writeback=True)
            s[key] = value
        finally:
            s.close()
