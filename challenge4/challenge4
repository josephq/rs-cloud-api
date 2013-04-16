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
# Challenge 4:
# Write a script that uses Cloud DNS to create a new A record when passed a FQDN and IP address as arguments.

import os
import sys
import argparse
import pyrax
import pyrax.exceptions as exc
import ConfigParser

# Authentication
# Configure credentials/region
# Example creds_file:
#
# [rackspace_cloud]
# username = someuser
# api_key = someapikey
# region = DFW

# Configure credentials/region

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

parser = argparse.ArgumentParser()
parser.add_argument('-n', '--fqdn', action='store', dest='fqdn', help='Name of A record')
parser.add_argument('-i', '--ip', action='store', dest='ip', help='IP for A record')
args = parser.parse_args()

if not(args.fqdn and args.ip):
    parser.print_help()
    exit(1)

dns = pyrax.cloud_dns

thisName, thisTLD = args.fqdn.split('.')[-2:]
thisDomain = thisName + '.' + thisTLD

try:
    dom = dns.find(name=thisDomain)

except pyrax.exceptions.NotFound:
    print 'Domain', thisDomain, 'not found. Create it?'
    prompt = raw_input('y/n ')

    if prompt == 'y':
        emailAddr = raw_input('Email address: ')
        dom = dns.create(name=thisDomain, emailAddress=emailAddr)
    else:
        print 'Exiting.'
        exit(0)

recs = [{
        'type': 'A',
        'name': args.fqdn,
        'data': args.ip,
        }
        ]

try:
    print dom.add_records(recs)
except:
    err = sys.exc_info()[0]
    print err
    sys.exit(1)
