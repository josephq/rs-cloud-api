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
# Challenge 5: Write a script that creates a Cloud Database instance.
# This instance should contain at least one database, and the database should have at least one user that can connect to it.

import os
import sys
import pyrax
import pyrax.exceptions as exc
import time
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

cdb = pyrax.cloud_databases

Xinstance = raw_input('Instance name:')

print 'Available flavors'
for flavor in cdb.list_flavors():
    print flavor.name

while True:
    Xflavor = raw_input('Flavor:')
    if [flv for flv in cdb.list_flavors() if Xflavor == flv.name]:
        break
    else:
        print 'You must provide a valid flavor.'

Xdb = raw_input('Database name:')

while True:
    Xvolume = raw_input('Volume size (1-50):')
    if Xvolume.isdigit():
        if int(Xvolume) > 0 and int(Xvolume) < 51:
            break
        else:
            print 'Volume size must be 1-50'
    else:
        print 'Volume size must be 1-50'

Xname = raw_input('User name:')
Xpassword = raw_input('Password:')

inst = cdb.create(Xinstance, flavor=Xflavor, volume=Xvolume)

print 'Waiting for instance creation...'

while True:
    time.sleep(5)
    id = inst.id
    inst = cdb.get(id)
    print 'Status: ', inst.status
    if inst.status == 'ACTIVE':
        break

print 'Creating database.'
db = inst.create_database(Xdb)

print 'Creating user.'
user = inst.create_user(name=Xname, password=Xpassword, database_names=db)

print 'Complete!'
print 'Hostname:', inst.hostname
