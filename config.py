#!/usr/bin/env python

import os
import json
from requests.auth import HTTPBasicAuth

#
# Expected configuration JSON file:
# 
# {
#    "API_URL": "{url goes here}"",
#    "API_TOKEN": "{token goes here}""
# }
#

class Config:

    def __init__(self):

        configFileName = os.path.expanduser('~/.mpt-objects-inventory-config.json')

        print(f'loading configuration from: {configFileName}...')
        f = open(configFileName, 'r')
        txt = f.read()
        f.close()
        data = json.loads(txt)

        # Token name: mpt-objects-inventory-token-{date}
        self.FIGMA_API_TOKEN = data['FIGMA_API_TOKEN']

        # Token name: mpt-objects-inventory-token-{date}
        self.CONFLUENCE_API_TOKEN = data['CONFLUENCE_API_TOKEN']
    
        self.CONFLUENCE_API_USERNAME = 'service-user.mpt@softwareone.com'

        self.MISSING_FIGMA_PAGE_PLACEHOLDER = 'https://www.figma.com/design/rHxTpbi2gpbZ4dmVlyeY2S/Object-Diagrams?node-id=14494-411&t=9t14B4asXC7wJTrH-0'

        self.CONFLUENCE_BASE_URL = 'https://softwareone.atlassian.net/wiki'

        self.CONFLUENCE_AUTH = HTTPBasicAuth(self.CONFLUENCE_API_USERNAME, self.CONFLUENCE_API_TOKEN)