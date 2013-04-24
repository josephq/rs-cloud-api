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
# Challenge 9:
# Write an application that when passed the arguments FQDN, image, and flavor
# it creates a server of the specified image and flavor with the same name as the fqdn,
# and creates a DNS entry for the fqdn pointing to the server's public IP.

import pyrax
import pyrax.exceptions as exc
import time
import datetime
import os
import sys
import re
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


class list_images(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        for image in cs.images.list():
            print 'Image Name:', image.name
            print 'Image ID:', image.id
            print


class list_flavors(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        for flavor in cs.flavors.list():
            print 'Flavor Name:', flavor.name
            print 'Flavor ID:', flavor.id
            print


class create_server(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):

        for arg in values:
            if [flv for flv in cs.flavors.list() if arg == flv.id]:
                server_flavor = cs.flavors.get(arg)
            elif [img for img in cs.images.list() if arg == img.id]:
                server_image = cs.images.get(arg)
            elif '.' in arg:
                server_fqdn = arg

        try:
            print 'Flavor:', server_flavor.name
        except:
            print 'You must provide a flavor ID'
            parser.print_help()
            exit(-1)

        try:
            print 'Image:', server_image.name
        except:
            print 'You must provide an image ID'
            parser.print_help()
            exit(-1)

        try:
            print 'FQDN:', server_fqdn
        except:
            print 'You must provide an FQDN'
            parser.print_help()
            exit(-1)

        server = cs.servers.create(server_fqdn, server_image, server_flavor)

        while server.status != 'ACTIVE':
            server.get()
            print
            print 'Server Name:', server.name
            print 'Server ID:', server.id
            print 'Server Status:', server.status
            print 'Progress:', server.progress
            time.sleep(30)

        for ip in server.networks['public']:
            if '.' in ip:
                publicIPv4 = ip

        print
        print 'Server Name: ', server.name
        print 'Root Password: ', server.adminPass
        print 'Public IPv4: ', publicIPv4
        print 'Private IPv4: ', server.networks['private'][0]
        print

        thisName, thisTLD = server_fqdn.split('.')[-2:]
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
                print 'Exiting'
                exit(0)

        recs = [{
                'type': 'A',
                'name': server_fqdn,
                'data': publicIPv4,
                }
                ]

        try:
            record = dom.add_records(recs)
            record = dom.find_record(name=server_fqdn, record_type='A')
            print record.type, 'record created for', record.name, 'with data', record.data
        except:
            err = sys.exc_info()[0]
            print err
            sys.exit(1)


cs = pyrax.cloudservers
dns = pyrax.cloud_dns

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--create-server', nargs=3, action=create_server, help='Create server FlavorID ImageID FQDN')
parser.add_argument('--list-images', nargs=0, action=list_images)
parser.add_argument('--list-flavors', nargs=0, action=list_flavors)

args = parser.parse_args()

if not len(sys.argv) > 1:
    print parser.print_help()
