#!/usr/bin/env python
import sys

if sys.version_info[0] != 2 or sys.version_info[1] < 7:
    sys.exit("This script requires Python version 2.7")

import pygop
from argparse import ArgumentParser

def logOnOff(name, onoff):
    if (args.quiet is False):
        if (onoff == 1):
            print "Turning %s on" % name
        else:
            print "Turning %s off" % name

def logLevel(name, level):
    if (args.quiet is False):
        print "Setting dim level %s on '%s'." % (level, name)

def logIdentify(name):
    if (args.quiet is False):
        print 'Identifying %s' % name

# set up parser and args
# %prog variable doesn't work with the parser in usage for some reason
usage = "%s [-hvqp] [-s 0/1] [-l 1-100] [-i] [-d did] [-r rid] [-n bulb_name] [-m room_name]" % sys.argv[0]
description = "Command Line Utility for the pygop module"
version = "%s %s" % (sys.argv[0], pygop.__version__)
parser = ArgumentParser(usage=usage, description=description)

parser.add_argument("-v", "--version", action="version", version=version)
parser.add_argument("-q", "--quiet", action="store_true", default=False,
            dest="quiet", help="Surpress program output")
parser.add_argument("-p", "--print-info", action="store_true", default=False,
            dest="printInfo", help="Print rooms and devices to the console")

action_group = parser.add_mutually_exclusive_group()
action_group.add_argument("-s", "--set", action="store", type=int, dest="onoff",
            help="Set the bulb/fixture on - 1 or off - 0", default=None)
action_group.add_argument("-l", "--level", action="store", type=int, dest="level",
            help="Set the dim level of the bulb/fixture (1-100)", default=None)
action_group.add_argument("-i", "--identify", action="store_true", default=False, dest="identify",
            help="Identifies a room or bulb ID or name")

identifier_group = parser.add_mutually_exclusive_group()
identifier_group.add_argument("-d", "--did", action="store", type=int, dest="did",
            help="Specify the did (device identifier)", default=None)
identifier_group.add_argument("-r", "--rid", action="store", type=int, dest="rid",
            help="Specify the rid (room identifier)", default=None)
identifier_group.add_argument("-n", "--name", action="store", type=str, dest="name",
            help="Specify the name of the bulb/fixture", default=None)
identifier_group.add_argument("-m", "--rname", action="store", type=str, dest="rname",
            help="Specify the name of the room", default=None)

# parse arguments
args = parser.parse_args()

# # if no arguments print usage
if (len(sys.argv) < 2):
     parser.print_help()
     sys.exit()

pygop = pygop.pygop()

if (args.printInfo):
    pygop.printHouseInfo()
elif (args.identify):
    if (args.did is not None):
        if (pygop.identifyBulbByDid(args.did)):
            logIdentify(args.did)
    elif (args.rid is not None):
        if (pygop.identifyRoomByRid(args.rid)):
            logIdentify(args.rid)
    elif (args.name):
        if (pygop.identifyBulbByName(args.name)):
            logIdentify(args.name)
    elif (args.rname):
        if (pygop.identifyRoomByName(args.rname)):
            logIdentify(args.rname)
    else:
        parser.error('Name or did required to identify bulb/fixture')
elif (args.onoff is not None):
    if (args.onoff < 0 or args.onoff > 1):
        parser.error("Set value out of bounds (0 or 1)")
    else:
        if (args.did is not None):
            if (pygop.setBulbLevelByDid(args.did, args.onoff)):
                logOnOff(args.did, args.onoff)
        elif (args.rid is not None):
            if (pygop.setRoomLevelByRid(args.rid, args.onoff)):
                logOnOff(args.rid, args.onoff)
        elif (args.name):
            if (pygop.setBulbLevelByName(args.name, args.onoff)):
                logOnOff(args.name, args.onoff)
        elif (args.rname):
            if (pygop.setRoomLevelByName(args.rname, args.onoff)):
                logOnOff(args.rname, args.onoff)
        else:
            parser.error('Name or did required to set bulb/fixture on or off.')
elif (args.level is not None):
    if(args.level < 1 or args.level > 100):
        parser.error("Dim level out of bounds (1-100)")
    else:
        if (args.did is not None):
            if (pygop.setBulbLevelByDid(args.did, 0, args.level)):
                logLevel(args.did, args.level)
        elif (args.rid is not None):
            if (pygop.setRoomLevelByRid(args.rid, 0, args.level)):
                logLevel(args.rid, args.level)
        elif (args.name):
            if (pygop.setBulbLevelByName(args.name, 0, args.level)):
                logLevel(args.name, args.level)
        elif (args.rname):
            if (pygop.setRoomLevelByName(args.rname, 0, args.level)):
                logLevel(args.rname, args.level)
        else:
            parser.error('Name or did required to set bulb/fixture dim level.')
else:
    parser.error("Please choose an action (set,level,identify)")
