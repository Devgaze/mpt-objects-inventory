#!/usr/bin/env python

import os
import json
from requests.auth import HTTPBasicAuth

#
# Expected configuration JSON file:
# 
# {
#    "API_URL": "{url goes here}",
#    "API_TOKEN": "{token goes here}"
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

        # Debug flags
        self.SKIP_UPDATE_CONFLUENCE_PAGE_FOR_DEBUG = False
        self.SKIP_DELETE_EXISTING_IMAGES_FOR_DEBUG = False
        self.SKIP_UPLOAD_IMAGES_TO_CONFLUENCE_FOR_DEBUG = False
        self.SKIP_ACTUAL_RENDERING_FOR_DEBUG = False

        # Token name: mpt-objects-inventory-token-{date}
        self.FIGMA_API_TOKEN = data['FIGMA_API_TOKEN']

        # Token name: mpt-objects-inventory-token-{date}
        self.CONFLUENCE_API_TOKEN = data['CONFLUENCE_API_TOKEN']
    
        self.CONFLUENCE_API_USERNAME = data['CONFLUENCE_API_USERNAME']

        self.MISSING_FIGMA_PAGE_PLACEHOLDER = data['MISSING_FIGMA_PAGE_PLACEHOLDER']

        self.CONFLUENCE_BASE_URL = data['CONFLUENCE_BASE_URL']

        self.CONFLUENCE_AUTH = HTTPBasicAuth(self.CONFLUENCE_API_USERNAME, self.CONFLUENCE_API_TOKEN)

        self.CONFLUENCE_SUMMARY_PAGE_URL = data['CONFLUENCE_SUMMARY_PAGE_URL']

        self.TEMP_RENDER_FOLDER = os.path.join(os.path.dirname(__file__), 'build')

        self.CONFLUENCE_OVERVIEW_PAGE_URL_STATE_DIAGRAMS = data['CONFLUENCE_OVERVIEW_PAGE_URL_STATE_DIAGRAMS']
        self.CONFLUENCE_OVERVIEW_PAGE_URL_DESKTOP_GRIDS = data['CONFLUENCE_OVERVIEW_PAGE_URL_DESKTOP_GRIDS']
        self.CONFLUENCE_OVERVIEW_PAGE_URL_DESKTOP_DETAILS = data['CONFLUENCE_OVERVIEW_PAGE_URL_DESKTOP_DETAILS']
        self.CONFLUENCE_OVERVIEW_PAGE_URL_DESKTOP_INFO_CARDS = data['CONFLUENCE_OVERVIEW_PAGE_URL_DESKTOP_INFO_CARDS']
        self.CONFLUENCE_OVERVIEW_PAGE_URL_MOBILE_LIST = data['CONFLUENCE_OVERVIEW_PAGE_URL_MOBILE_LIST']
        self.CONFLUENCE_OVERVIEW_PAGE_URL_MOBILE_DETAILS = data['CONFLUENCE_OVERVIEW_PAGE_URL_MOBILE_DETAILS']
        self.CONFLUENCE_OVERVIEW_PAGE_URL_EMAILS = data['CONFLUENCE_OVERVIEW_PAGE_URL_EMAILS']
        self.CONFLUENCE_OVERVIEW_PAGE_URL_SPOTLIGHT = data['CONFLUENCE_OVERVIEW_PAGE_URL_SPOTLIGHT']