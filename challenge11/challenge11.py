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
# Challenge 11:
# Write an application that will:
# - Create an SSL terminated load balancer (Create self-signed certificate.)
# - Create a DNS record that should be pointed to the load balancer.
# - Create Three servers as nodes behind the LB.
# - Each server should have a CBS volume attached to it. (Size and type are irrelevant.)
# - All three servers should have a private Cloud Network shared between them.
# - Login information to all three servers returned in a readable format as the result of the script,
#   including connection information.

# Start defaults
server_base_name = 'BaseName'
num_servers = 3
image_name = 'CentOS 6.3'
ram_size = 512
lb_name = 'myLB'
lb_delay = 5
lb_timeout = 5
lb_attempts = 3
lb_fqdn = 'lb.qwertyexample.com'
network_name = 'my_net'
network_cidr = '192.168.0.0/24'
mountpoint = '/dev/xvdb'
Country = 'US'
State = 'Texas'
Locale = 'San Antonio'
Org = 'Rackspace'
OU = 'Cloud'
# End defaults

import pyrax
import pyrax.exceptions as exc
import time
import datetime
import os
import sys
from OpenSSL import crypto, SSL
import argparse
import ConfigParser
import re

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

# Get pyrax objects
cs = pyrax.cloudservers
cnw = pyrax.cloud_networks
cbs = pyrax.cloud_blockstorage
clb = pyrax.cloud_loadbalancers
dns = pyrax.cloud_dns

# Command line options
parser = argparse.ArgumentParser()
parser.add_argument('-r', '--retry', action='store_true', dest='retry', help='Always retry failures')

args = parser.parse_args()

# Functions


def rawDefault(msg, default):
    retval = raw_input(msg + ' [' + str(default) + '] :')
    if not retval:
        return default
    else:
        return retval


def TryAgain(msg):
    print
    for val in sys.exc_info()[:2]:
        print val
    if args.retry:
        print 'Retrying...'
        return
    else:
        TryAgain = ''
        while TryAgain != 'n' and TryAgain != 'y':
            TryAgain = raw_input(msg + ' Try again? [y/n]')
            if TryAgain == 'n':
                print 'Exiting...'
                sys.exit()
            if TryAgain == 'y':
                print
                return TryAgain
                break


# User input
print 'Challenge 11:'
print 'Write an application that will:'
print 'Create an SSL terminated load balancer (Create self-signed certificate.)'
print 'Create a DNS record that should be pointed to the load balancer.'
print 'Create Three servers as nodes behind the LB.'
print 'Each server should have a CBS volume attached to it. (Size and type are irrelevant.)'
print 'All three servers should have a private Cloud Network shared between them.'
print 'Login information to all three servers returned in a readable format as the result of the script,'
print 'including connection information.'
print

server_base_name = rawDefault('Base name for servers', server_base_name)

while True:
    num_servers = rawDefault('Number of servers', num_servers)
    try:
        num_servers = int(num_servers)
        if num_servers > 0:
            break
        else:
            print 'Number must be > 0'
            num_servers = 1
    except:
        print 'You must enter a valid integer.'
        num_servers = ''

while True:
    image_name = rawDefault('Image Name', image_name)
    try:
        # Get image by name
        server_image = [img for img in cs.images.list()
                        if image_name in img.name][0]
        print 'Found', server_image.name
        break
    except:
        print 'Image not found, try again.'
        image_name = ''

while True:
    try:
        # Get flavor by RAM
        ram_size = int(rawDefault('Flavor RAM size', ram_size))
        server_flavor = [flavor for flavor in cs.flavors.list()
                         if flavor.ram == ram_size][0]
        print 'Found', server_flavor.name
        break
    except:
        print 'Available flavor not found, try again.'
        ram_size = ''

while True:
    lb_name = rawDefault('LB Name', lb_name)
    try:
        lb = clb.find(name=lb_name)
        print 'LB with name', lb_name, 'already found. Try again.'
        lb_name = ''
    except:
        if lb_name:
            break

while True:
    lb_fqdn = rawDefault('FQDN for LB VIP', lb_fqdn)
    try:
        thisName, thisTLD = lb_fqdn.split('.')[-2:]
        thisDomain = thisName + '.' + thisTLD
    except:
        lb_fqdn = ''

    try:
        dom = dns.find(name=thisDomain)
        record = dom.find_record(name=lb_fqdn, record_type='A')
        print 'Record already exists. Try again.'
        lb_fqdn = ''

    except(pyrax.exceptions.NotFound, pyrax.exceptions.DomainRecordNotFound):
        print 'Domain', thisDomain, 'not found. Create it?'
        prompt = raw_input('y/n ')

        if prompt == 'y':
            emailAddr = ''
            while not emailAddr:
                emailAddr = raw_input('Email address: ')
            try:
                dom = dns.create(name=thisDomain, emailAddress=emailAddr)
                break
            except pyrax.exceptions.DomainCreationFailed:
                print sys.exc_info()[1]
                if re.match('Domain already exists', str(sys.exc_info()[1])):
                    print 'Found domain actually already exists. Continuing.'
                    break
            except:
                print 'Error adding domain'
                print 'Error was:'
                for val in sys.exc_info()[:2]:
                    print val
                print 'Try again.'
        else:
            print 'Try again.'
            lb_fqdn = ''

    except:
        print 'You must enter a FQDN.'

print 'Certificate information:'
Country = rawDefault('Country', Country)
State = rawDefault('State', State)
Locale = rawDefault('Locale', Locale)
Org = rawDefault('Organization', Org)
OU = rawDefault('OU', OU)
CN = rawDefault('CN', lb_fqdn)

while True:
    network_name = rawDefault('Cloud Network name', network_name)

    try:
        thisNetwork = cnw.find(name=network_name)
        print 'Network named', thisNetwork.label, 'found.'
        print 'Try again.'
        network_name = ''
    except:
        break

while True:
    network_cidr = rawDefault('Cloud Network CIDR', network_cidr)

    try:
        # Create cloud network
        print 'Creating cloud network...'
        isolated = cnw.create(network_name, cidr=network_cidr)
        break
    except (pyrax.exceptions.NetworkCIDRInvalid, pyrax.exceptions.NetworkCIDRMalformed):
        print 'Invalid or malformed CIDR. Try again'
        network_cidr = ''
    except:
        print 'Got an error adding Cloud Network'
        print 'Error was:'
        for val in sys.exc_info()[:2]:
            print val
        sys.exit(1)

networks = isolated.get_server_networks(public=True, private=True)

# Create a self-signed cert
print 'Creating private key/self signed certificate...'
key = crypto.PKey()
key.generate_key(crypto.TYPE_RSA, 1024)

cert = crypto.X509()
cert.get_subject().C = Country
cert.get_subject().ST = State
cert.get_subject().L = Locale
cert.get_subject().O = Org
cert.get_subject().OU = OU
cert.get_subject().CN = CN
cert.set_serial_number(1000)
cert.gmtime_adj_notBefore(0)
cert.gmtime_adj_notAfter(10*365*24*60*60)
cert.set_issuer(cert.get_subject())
cert.set_pubkey(key)
cert.sign(key, 'sha1')

certificate = crypto.dump_certificate(crypto.FILETYPE_PEM, cert)
private_key = crypto.dump_privatekey(crypto.FILETYPE_PEM, key)

# Set up some arrays
server = {}
node = {}
vol = {}

# Capture time
serverCreateTime = datetime.datetime.now()

# Start building servers
print

for doServer in range(num_servers):
    doThisServer = server_base_name + str(doServer)
    print 'Creating server ', doThisServer
    while True:
        try:
            server[doServer] = cs.servers.create(doThisServer, server_image.id, server_flavor.id, nics=networks)
            break
        except:
            TryAgain('Error creating server.')

print

serversComplete = 0
# Outer loop to monitor build. Run until all servers complete.
while serversComplete < num_servers:
    serversComplete = 0

  # Inner loop to monitor build
    for doServer in range(num_servers):
        doThisServer = server_base_name + str(doServer)
        try:
            server[doServer].get()
        except:
            print 'Unable to get', doThisServer, 'status'
            print
            break

        if server[doServer].status == 'ERROR':
            print 'Server', doThisServer, 'in ERROR status. Recreating.'
            try:
                server[doServer].delete()
            except:
                print 'Error deleting server. Exiting'
                sys.exit()
            while True:
                try:
                    server[doServer] = cs.servers.create(doThisServer, server_image.id, server_flavor.id, nics=networks)
                    break
                except:
                    TryAgain('Error creating server.')

        print datetime.datetime.now()
        print 'Server Name: ', server[doServer].name
        print 'Server ID: ', server[doServer].id
        print 'Server Status: ', server[doServer].status
        print 'Progress: ', str(server[doServer].progress)
        print

        if server[doServer].status == 'ACTIVE':
            serversComplete += 1

    time.sleep(20)

# Provision block storage
print 'Creating block storage volumes...'
for doCBS in range(num_servers):
    doThisCBS = server_base_name + str(doCBS)
    while True:
        try:
            vol[doCBS] = cbs.create(name=doThisCBS, size=100, volume_type='SATA')
            break
        except:
            TryAgain('Error creating volume.')

cbs_complete = 0
# Monitor block storage creation
print
print 'Monitoring block storage status...'
while cbs_complete < num_servers:
    cbs_complete = 0
    for doCBS in range(num_servers):
        try:
            vol[doCBS].get()
        except:
            print 'Unable to get status for volume', doCBS
            break
        print 'Volume', doCBS, vol[doCBS].status
        if vol[doCBS].status == 'available':
            cbs_complete += 1
        time.sleep(20)

# Attach block storage
print
print 'Attaching volumes...'
for doCBS in range(num_servers):
    while True:
        try:
            vol[doCBS].attach_to_instance(server[doCBS], mountpoint=mountpoint)
            break
        except:
            TryAgain('Error attaching volume.')

cbs_complete = 0
# Monitor attaching
print
while cbs_complete < num_servers:
    cbs_complete = 0
    for doCBS in range(num_servers):
        try:
            vol[doCBS].get()
        except:
            print 'Unable to get status for volume', doCBS
            break
        print 'Volume', doCBS, vol[doCBS].status
        if vol[doCBS].status == 'in-use':
            cbs_complete += 1
        time.sleep(20)

# Build complete, add to LB

# Create node for 1st server
print
print 'Creating nodes...'
while True:
    try:
        node[0] = clb.Node(address=server[0].networks['private'][0], port=80, condition='ENABLED')
        break
    except:
        TryAgain('Error creating node.')

# Create LB
print
print 'Creating load balancer...'
while True:
    try:
        vip = clb.VirtualIP(type='PUBLIC')
        break
    except:
        TryAgain('Error creating VIP.')

while True:
    try:
        lb = clb.create(lb_name, port=80, protocol='HTTP', virtual_ips=[vip], nodes=[node[0]])
        break
    except:
        TryAgain('Error creating LB.')

# Wait for LB creation
print
print 'Waiting for load balancer to become active...'
while True:
    try:
        lb = clb.get(lb.id)
        print 'LB Status:', lb.status
        if lb.status == 'ACTIVE':
            break
    except:
        print 'Error getting LB status'
    time.sleep(30)

# Add remaining nodes to LB
if num_servers > 1:
    print
    print 'Adding nodes to load balancer...'
    for doServer in range(1, num_servers):
        while True:
            try:
                node[doServer] = clb.Node(address=server[doServer].networks['private'][0], port=80, condition='ENABLED')
                lb.add_nodes([node[doServer]])
                break
            except:
                TryAgain('Error adding node')

        # Wait for LB updates
        print
        print 'Waiting for load balancer updates...'
        while True:
            try:
                lb = clb.get(lb.id)
                print 'LB Status:', lb.status
                if lb.status == 'ACTIVE':
                    break
            except:
                print 'Error getting LB status'
            time.sleep(30)

# Add SSL termination
print
print 'Adding SSL termination...'
while True:
    try:
        lb.add_ssl_termination(
            securePort=443,
            enabled=True,
            secureTrafficOnly=False,
            certificate=certificate,
            privatekey=private_key,
        )
        break
    except:
        TryAgain('Error adding SSL termination.')

# Add A record for LB
for thisIP in lb.virtual_ips:
    if '.' in thisIP.address:
        lb_ip = thisIP.address

print
print 'Adding A record for', lb_fqdn, 'with IP', lb_ip

recs = [{
        'type': 'A',
        'name': lb_fqdn,
        'data': lb_ip,
        }
        ]

try:
    dom.add_records(recs)
except:
    print
    print 'Got an error adding DNS record'
    print 'Error was:'
    for val in sys.exc_info()[:2]:
        print val
    print 'Checking if record created...'
    try:
        record = dom.find_record(name=lb_fqdn, record_type='A')
        print 'Record found.'
    except:
        print 'Record not found.'

#Work complete
print
print 'Complete!'
print

for doServer in range(num_servers):

    print 'Server Name: ', server[doServer].name
    print 'Root Password: ', server[doServer].adminPass

    for thisIP in server[doServer].networks['public']:
        if '.' in thisIP:
            print 'Public IPv4: ', thisIP

    print 'Private IPv4: ', server[doServer].networks['private'][0]
    print network_name, 'IPv4:', server[doServer].networks[network_name][0]
    print

print 'LB Information: '
print 'Public IPv4:', lb_ip
automationCompleteTime = datetime.datetime.now()
totalDeployTime = automationCompleteTime-serverCreateTime
print
print 'Time: ', str(totalDeployTime)
