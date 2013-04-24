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
# Challenge 3: Write a script that accepts a directory as an argument as well as a container name.
# The script should upload the contents of the specified directory to the container
# (or create it if it doesn't exist).
# The script should handle errors appropriately.

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

cf = pyrax.cloudfiles


class upload_folder(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        try:
            folder = cf.upload_folder(values[0], container=values[1])
        except:
            for val in sys.exc_info()[:2]:
                print val
            sys.exit(1)


parser = argparse.ArgumentParser()
parser.add_argument('--upload-folder', nargs=2, action=upload_folder, help='DIRECTORY CONTAINER')
args = parser.parse_args()

if not len(sys.argv) > 1:
    print parser.print_help()
