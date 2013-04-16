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
# Challenge 10:
# Write an application that will:
# - Create 2 servers, supplying a ssh key to be installed at /root/.ssh/authorized_keys.
# - Create a load balancer
# - Add the 2 new servers to the LB
# - Set up LB monitor and custom error page.
# - Create a DNS record based on a FQDN for the LB VIP.
# - Write the error page html to a file in cloud files for backup.

# Start configurable options
server_base_name = 'BaseName'
num_servers = 2
image_name = 'CentOS 6.3'
ram_size = 512
lb_name = 'myLB'
lb_delay = 5
lb_timeout = 5
lb_attempts = 3
lb_err_html = '<html><body>ERROR</body></html>'
lb_fqdn = 'lb.qwertyexample.com'  # Domain must exist
cf_container = 'html'  # Container must exist
cf_object = 'err.html'
key_path = '/root/.ssh/authorized_keys'
ssh_rsa = 'ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAu+hqVrvwq/zLAr6IU3zegdSfIvDEvnIhOgasDR1PQi9O+afLSkTEsue76UkfyE3NnQ4Tkc94HYmVujNQ/YaA0g0JtyUc9+J++Noat3g8Tj40r7Flj4xltO7DMkM5Z8bWPGDb2SEW3bRi9Vz6Kv9kPr4boJEKFv84aOMFhJZ7GrLIFvxEoG9wBh8H5KVlx6PEvMwBycyPM8+csvjW2UeVnYyD3Npl90G5ljmM+pGWEjfM8O6X/5GvViyKJO4dYmcHRfo/G8PBYFADsgXYXzyIoAjvWAi1KnWnpl5hEazTZBHs7z0i43UfePTLxvAG6/MB2qi8FO9QZRAmiAELX5GX7Q== anybody@anywhere'
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

files = {key_path: ssh_rsa}

# Capture time
serverCreateTime = datetime.datetime.now()

# Start building servers
for doServer in range(num_servers):
    doThisServer = server_base_name + str(doServer)
    print 'Creating server ', doThisServer
    server[doServer] = cs.servers.create(doThisServer, server_image.id, server_flavor.id, files=files)

serversComplete = 0
# Outer loop to monitor build. Run until all servers complete.
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
print 'Creating nodes...'
node[0] = clb.Node(address=server[0].networks['private'][0], port=80, condition='ENABLED')

# Create LB
print 'Creating load balancer...'
vip = clb.VirtualIP(type='PUBLIC')
lb = clb.create(lb_name, port=80, protocol='HTTP', virtual_ips=[vip], nodes=[node[0]])

# Wait for LB creation
print 'Waiting for load balancer to become active...'
while True:
    lb = clb.get(lb.id)
    print 'LB Status:', lb.status
    if lb.status == 'ACTIVE':
        break
    time.sleep(30)

# Add remaining nodes to LB
print 'Adding nodes to load balancer...'
for doServer in range(1, num_servers):
    node[doServer] = clb.Node(address=server[doServer].networks['private'][0], port=80, condition='ENABLED')
    lb.add_nodes([node[doServer]])

# Wait for LB updates
print 'Waiting for load balancer updates...'
while True:
    lb = clb.get(lb.id)
    print 'LB Status:', lb.status
    if lb.status == 'ACTIVE':
        break
    time.sleep(60)

# Add TCP Connection Health Monitor
print 'Adding health monitor to load balancer...'
lb.add_health_monitor(type='CONNECT', delay=lb_delay, timeout=lb_timeout, attemptsBeforeDeactivation=lb_attempts)

# Wait for LB updates
print 'Waiting for load balancer updates...'
while True:
    lb = clb.get(lb.id)
    print 'LB Status:', lb.status
    if lb.status == 'ACTIVE':
        break
    time.sleep(60)

# Add error page to LB
print 'Adding error page to load balancer...'
lb.set_error_page(lb_err_html)

# Wait for LB updates
print 'Waiting for load balancer updates...'
while True:
    lb = clb.get(lb.id)
    print 'LB Status:', lb.status
    if lb.status == 'ACTIVE':
        break
    time.sleep(60)

# Add A record for LB
dns = pyrax.cloud_dns

thisName, thisTLD = lb_fqdn.split('.')[-2:]
thisDomain = thisName + '.' + thisTLD

dom = dns.find(name=thisDomain)

for thisIP in lb.virtual_ips:
    if '.' in thisIP.address:
        lb_ip = thisIP.address

print 'Adding A record for', lb_fqdn, 'with IP', lb_ip

recs = [{
        'type': 'A',
        'name': lb_fqdn,
        'data': lb_ip,
        }
        ]

dom.add_records(recs)

# Upload error page to cloudfiles
print 'Uploading error page to cloud files at', cf_container, cf_object
cf = pyrax.cloudfiles
cf.store_object(cf_container, cf_object, lb_err_html)

#Work complete
print
print 'Complete!'
print

for doServer in range(num_servers):

    print 'Server Name: ', server[doServer].name
    print 'Root Password: ', server[doServer].adminPass
    print 'Public IPs: ', server[doServer].networks['public'][0], '/', server[doServer].networks['public'][1]
    print 'Private IPv4: ', server[doServer].networks['private'][0]

print 'LB Information: '
print 'Public IPv4:', lb_ip
automationCompleteTime = datetime.datetime.now()
totalDeployTime = automationCompleteTime-serverCreateTime
print
print 'Time: ', str(totalDeployTime)
