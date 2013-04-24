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
# Challenge 12:
# Write an application that will:
# Create a route in mailgun so that when an email is sent it calls your Challenge 1 script that builds 3 servers.
# Assume that challenge 1 can be kicked off by accessing http://cldsrvr.com/challenge1
# Assume the Mailgun API key exists at ~/.mailgunapi. Assume no formatting, the api key will be the only data in the file.

from werkzeug import *
import requests
import os
import json


def create_route(api_key, description, recipient, url):
    return requests.post(
        'https://api.mailgun.net/v2/routes',
        auth=('api', api_key),
        data=MultiDict([('priority', 1),
                        ('description', '\'' + description + '\''),
                        ('expression', 'match_recipient(\'' + recipient + '\')'),
                        ('action', 'forward(\'' + url + '\')'),
                        ('action', 'stop()')]))


def read_api():
    creds_file = os.path.expanduser('~/.mailgunapi')
    with open(creds_file) as f:
        api_key = f.read()
    f.close()
    return api_key.strip()


api_key = read_api()
created_route = create_route(api_key, 'Challenge 12', 'joseph.quinn@apichallenges.mailgun.org', 'http://cldsrvr.com/challenge1')
json_data = json.loads(created_route._content)

print 'Created!'
print 'Description:', json_data['route']['description']
print 'Created:', json_data['route']['created_at']
print 'Actions:', json_data['route']['actions'][0]
print 'Priority:', json_data['route']['priority']
print 'Expression:', json_data['route']['expression']
print 'ID', json_data['route']['id']
