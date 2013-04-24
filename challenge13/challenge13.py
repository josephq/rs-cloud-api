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
# Challenge 13:
# Write an application that nukes everything in your Cloud Account. It should:
# - Delete all Cloud Servers
# - Delete all Custom Images
# - Delete all Cloud Files Containers and Objects
# - Delete all Databases
# - Delete all Networks
# - Delete all CBS Volumes

import pyrax
import pyrax.exceptions as exc
import os
import sys


def nuke(region):
    try:
        pyrax.set_credential_file(creds_file, region)
    except exc.AuthenticationFailed:
        print 'Failed to authenticate'
        sys.exit(1)

    # Get pyrax objects
    cs = pyrax.cloudservers
    cf = pyrax.cloudfiles
    cdb = pyrax.cloud_databases
    cnw = pyrax.cloud_networks
    cbs = pyrax.cloud_blockstorage

    for server in cs.servers.list():
        server.delete()

    for image in cs.images.list():
        if image.metadata['image_type'] != 'base':
            cs.images.delete(image.id)

    for container in cf.get_all_containers():
        container.delete_all_objects()
        container.delete()

    for db in cdb.list():
        db.delete()

    for net in cnw.list():
        if net.name != 'public' and net.name != 'private':
            net.delete()

    for vol in cbs.list():
        if vol.status != 'available':
            vol.detach()
            pyrax.utils.wait_until(vol, 'status', ['available'], interval=30)
        vol.delete()

creds_file = os.path.expanduser('~/.rackspace_cloud_credentials')
nuke('ORD')
nuke('DFW')
