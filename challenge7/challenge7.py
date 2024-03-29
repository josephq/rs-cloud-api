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
# Challenge 7:
# Write a script that will create 2 Cloud Servers and add them as nodes to a new Cloud Load Balancer.

# Start configurable options
server_base_name = 'Base'
num_servers = 2
image_name = 'CentOS 6.3'
ram_size = 512
lb_name = 'myLB'
# End configuration options

import pyrax
import pyrax.exceptions as exc
import time
import datetime
import os
import sys
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

cs = pyrax.cloudservers

# Get image by name
server_image = [img for img in cs.images.list()
                if image_name in img.name][0]

# Get flavor by RAM
server_flavor = [flavor for flavor in cs.flavors.list()
                 if flavor.ram == ram_size][0]

# Set up some arrays
server = {}
node = {}

# Capture time
serverCreateTime = datetime.datetime.now()

# Start building servers
for doServer in range(num_servers):
    doThisServer = server_base_name + str(doServer)
    print 'Creating server ', doThisServer
    server[doServer] = cs.servers.create(doThisServer, server_image.id, server_flavor.id)

# Outer loop to monitor build. Run until all servers complete.
serversComplete = 0
while serversComplete < num_servers:
    serversComplete = 0

# Inner loop to monitor build
    for doServer in range(num_servers):
        server[doServer].get()
        print datetime.datetime.now()
        print 'Server Name: ', server[doServer].name
        print 'Server ID: ', server[doServer].id
        print 'Server Status: ', server[doServer].status
        print 'Progress: ', server[doServer].progress
        print

        if server[doServer].status == 'ACTIVE':
            serversComplete += 1

    time.sleep(20)

# Build complete, add to LB
clb = pyrax.cloud_loadbalancers

# Create node for 1st server
node[0] = clb.Node(address=server[0].networks['private'][0], port=80, condition='ENABLED')

# Create LB
vip = clb.VirtualIP(type='PUBLIC')
lb = clb.create(lb_name, port=80, protocol='HTTP', virtual_ips=[vip], nodes=[node[0]])

# Wait for LB creation
while True:
    lb = clb.get(lb.id)
    if lb.status == 'ACTIVE':
        break
    time.sleep(60)

# Add remaining nodes to LB
for doServer in range(1, num_servers):
    node[doServer] = clb.Node(address=server[doServer].networks['private'][0], port=80, condition='ENABLED')
    lb.add_nodes([node[doServer]])

# Wait for LB updates
while True:
    lb = clb.get(lb.id)
    if lb.status == 'ACTIVE':
        break
    time.sleep(60)

# Work complete
print 'All servers complete and added to LB!'
print

for doServer in range(num_servers):

    print 'Server Name: ', server[doServer].name
    print 'Root Password: ', server[doServer].adminPass
    print 'Public IPs: ', server[doServer].networks['public'][0], '/', server[doServer].networks['public'][1]
    print 'Private IPv4: ', server[doServer].networks['private'][0]

print 'LB Information: '
for thisIP in lb.virtual_ips:
    if '.' in thisIP.address:
        lb_ip = thisIP.address
print 'Public IPv4:', lb_ip
automationCompleteTime = datetime.datetime.now()
totalDeployTime = automationCompleteTime-serverCreateTime
print
print 'Time: ', str(totalDeployTime)
sys.exit()
