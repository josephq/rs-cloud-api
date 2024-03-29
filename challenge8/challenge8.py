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
# under the License.`
#
# Challenge 8:
# Write a script that will create a static webpage served out of Cloud Files.
# The script must create a new container, cdn enable it, enable it to serve an index file,
# create an index file object, upload the object to the container, and create a CNAME record
# pointing to the CDN URL of the container.

# Begin configurable options
container_name = 'static'
index_file = 'index.html'
index_content = 'hello world'
domain = 'static.net'
email_addr = 'static@static.net'
CNAME = 'static.static.net'
# End configurable options

import os
import sys
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

# Create cloudfiles object
cf = pyrax.cloudfiles


# Create container
def create_container(arg):
    try:
        container = cf.create_container(arg)
        print container.name
    except:
        print 'Operation failed.'
        print sys.exc_info()[:2]
        sys.exit(1)


# CDN enable container
def cdn_enable(arg):
    try:
        cf.make_container_public(arg)
        print 'CDN enabled'
    except:
        print 'Operation failed.'
        print sys.exc_info()[:2]
        sys.exit(1)


# Upload (object)
def upload(remote, local):
    try:
        object = cf.upload_file(remote, local)
        print object.name
    except:
        print 'Operation failed.'
        print sys.exc_info()[:2]
        sys.exit(1)


# Set container metadata
def set_meta(cont, key, value):
    try:
        meta = {key: value}
        cf.set_container_metadata(cont, meta)
    except:
        print 'Operation failed.'
        print sys.exc_info()[:2]
        sys.exit(1)


cf.create_container(container_name)
cdn_enable(container_name)
set_meta(container_name, 'X-Container-Meta-Web-Index', index_file)
with open(index_file, 'a') as f:
    f.write(index_content)
upload(container_name, index_file)
container = cf.get_container(container_name)

dns = pyrax.cloud_dns

try:
    dom = dns.find(name=domain)

except pyrax.exceptions.NotFound:
    dom = dns.create(name=domain, emailAddress=email_addr)

recs = [{
        'type': 'CNAME',
        'name': CNAME,
        'data': container.cdn_uri,
        }
        ]

try:
    print dom.add_records(recs)
except:
    print sys.exc_info()[:2]
    sys.exit(1)
