#!/usr/bin/python
# Copyright 2013 Joseph Quinn
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the 'License'); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# Challenge 2: Write a script that clones a server (takes an image and deploys the image as a new server).

import pyrax
import pyrax.exceptions as exc
import time
import datetime
import os
import sys
import argparse
import ConfigParser

# Authentication
# Configure credentials/region
# Example creds_file:
#
# [rackspace_cloud]
# username = someuser
# api_key = someapikey
# region = DFW

creds_file = os.path.expanduser('~/.rackspace_cloud_credentials')
config = ConfigParser.SafeConfigParser()
config.read(creds_file)
try:
    region = config.get('rackspace_cloud', 'region')
except ConfigParser.NoOptionError:
    region = 'DFW'
except:
    print sys.exc_info()[:2]
    sys.exit(1)

try:
    pyrax.set_credential_file(creds_file, region)
except exc.AuthenticationFailed:
    print 'Failed to authenticate'
    sys.exit(1)


def getVal(obj, key):
    for attr in dir(obj):
        if attr == key:
            return getattr(obj, attr)


def waitImage(server):
    sys.stdout.write('Waiting for image creation to begin...')
    sys.stdout.flush()
    while True:
        obj = cs.servers.find(name=server)
        sys.stdout.write('.')
        sys.stdout.flush()
        if getVal(obj, 'OS-EXT-STS:task_state') == 'image_snapshot':
            break
        time.sleep(15)
    sys.stdout.write('\nWaiting for image creation to complete...')
    sys.stdout.flush()
    while True:
        obj = cs.servers.find(name=server)
        sys.stdout.write('.')
        sys.stdout.flush()
        if getVal(obj, 'OS-EXT-STS:task_state') is None:
            break
        time.sleep(15)

parser = argparse.ArgumentParser()
parser.add_argument('-s', '--source', action='store', dest='sourceServer', help='Name of server to clone')
parser.add_argument('-i', '--image-name', action='store', dest='imageName', help='Name for new image')
parser.add_argument('-c', '--create', action='store', dest='createServer', help='Name for new server')
args = parser.parse_args()

if not(args.sourceServer and args.imageName and args.createServer):
    parser.print_help()
    exit(-1)

cs = pyrax.cloudservers

# Find server to clone
sourceServerObj = cs.servers.find(name=args.sourceServer)

# Create image
doImage = cs.servers.create_image(sourceServerObj.id, args.imageName)

# Wait for image to be created
waitImage(args.sourceServer)
print

# Get flavor of server to clone
doFlavor = sourceServerObj.flavor['id']

# Create new server from image
server = cs.servers.create(args.createServer, doImage, doFlavor)

# Wait for server build to complete
while True:
    server.get()
    print 'Server Status: ', server.status
    print 'Progress: ', server.progress
    if server.status == 'ACTIVE':
        break
    time.sleep(15)

# Print server details
print 'Server Name: ', server.name
print 'Root Password: ', server.adminPass
print 'Public IPs: ', server.networks['public'][0], '/', server.networks['public'][1]
print 'Private IPv4: ', server.networks['private'][0]
