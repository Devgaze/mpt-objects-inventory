#! /usr/bin/env python3

import os
import json

from figma import Figma
from config import Config

cfg = Config()
figma = Figma()


class SchemaRecord:

    SCHEMA_RECORD_STATUS_RENDERED = 'rendered'
    SCHEMA_RECORD_STATUS_NOT_FOUND = 'not-found'
    SCHEMA_RECORD_STATUS_ERROR = 'error'


    def __init__(self, parent, figma_link, unique_key, title = None):
        self.parent = parent
        self.figma_link = figma_link
        self.unique_key = unique_key
        self.filename = None
        self.title = title
        self.status = self.SCHEMA_RECORD_STATUS_ERROR


    def render_figma_image(self, output_folder):

        print(f'Rendering Figma image for {self.unique_key} url: {self.figma_link}...')

        if self.figma_link is None:
            self.filename = self.parent.page_not_found_image
            self.status = self.SCHEMA_RECORD_STATUS_NOT_FOUND
            print(f'  Page not found for {self.unique_key} - using {self.filename}')
            return

        try:
            self.filename = self.unique_key.replace('.', '-') + '.png'
            self.filename = os.path.join(output_folder, self.filename)
            if cfg.SKIP_ACTUAL_RENDERING_FOR_DEBUG:
                if not os.path.exists(self.filename):
                    self.filename = self.parent.no_content_image
                    self.status = self.SCHEMA_RECORD_STATUS_NOT_FOUND
                else:
                    self.status = self.SCHEMA_RECORD_STATUS_RENDERED
                print(f'  DEBUG: Skipping actual rendering - using existing image {self.filename}')
            else:
                figma.render_figma_png(self.figma_link, self.filename)
                self.status = self.SCHEMA_RECORD_STATUS_RENDERED
            print(f'  Successfully rendered Figma image for {self.unique_key} - {self.filename}')

        except Exception as e:
            print(f'  Error rendering Figma image for {self.unique_key}: {e} - using {self.parent.no_content_image}')
            self.filename = self.parent.no_content_image
            self.status = self.SCHEMA_RECORD_STATUS_ERROR
        
        return self.filename


    def get_filename(self):
        if self.filename is None:
            raise ValueError(f'Filename is not set for {self.unique_key}')
        return self.filename


    def copy(self):
        new_record = SchemaRecord(
            self.parent,
            self.figma_link,
            self.unique_key,
            self.title
        )
        new_record.filename = self.filename
        new_record.status = self.status
        return new_record


class ObjectSchema:

    def _create_schema_value(self, unique_key):

        keys = unique_key.split('.')
        last_key = None
        last_value = self._object_schema
        for sub_key in keys:
            if isinstance(last_value, dict) and sub_key in last_value:
                last_value = last_value[sub_key]
                last_key = sub_key
            else:
                last_value = None
                last_key = None
                break

        # for whatever reason many people specify an empty string for the figma link instead of null
        if last_value == '':
            last_value = None

        record = SchemaRecord(self, last_value, unique_key)
        if unique_key in self.all_values:
            raise ValueError(f'Schema value for {unique_key} already exists')
        self.all_values[unique_key] = record

        print(f'Initialized schema record for {unique_key} with figma link: {record.figma_link}')

        return record


    def _create_schema_array(self, unique_key):

        keys = unique_key.split('.')
        last_value = self._object_schema
        for sub_key in keys:
            if isinstance(last_value, dict) and sub_key in last_value:
                next_value = last_value[sub_key]
                if not isinstance(next_value, dict):
                    break
                
                last_value = next_value
                last_key = sub_key
            else:
                last_value = None
                last_key = None
                break

        if last_value is None:
            return []

        schema_records = []

        for key, value in last_value.items():
            element_name = key.lower().strip().replace(' ', '-')
            full_key = f'{unique_key}.{element_name}'
            record = SchemaRecord(self, value, full_key, key)
            print(f'Initialized schema record for {full_key} with title: {key} and figma link: {value}')
            if full_key in self.all_values:
                raise ValueError(f'Schema value for {full_key} already exists')
            self.all_values[full_key] = record
            schema_records.append(record)

        return schema_records


    def __init__(self, schema_file):

        self.page_not_found_image = os.path.join(os.path.dirname(__file__), 'media', 'page-not-found.png')
        self.no_content_image = os.path.join(os.path.dirname(__file__), 'media', 'no-content.png')

        with open(schema_file, 'r', encoding='utf-8') as f:
            self._object_schema = json.load(f)

        self.object_name = self._object_schema['name'].title()        
        self.confluence_page_url = self._object_schema['confluence-page']
        self.confluence_page_title = 'unknown'

        self.all_values = {}

        self.state_diagram = self._create_schema_value('state-diagram')
        
        self.desktop_grid_view_vendor = self._create_schema_value('desktop.grid.vendor')
        self.desktop_grid_view_operations = self._create_schema_value('desktop.grid.operations')
        self.desktop_grid_view_client = self._create_schema_value('desktop.grid.client')

        self.desktop_details_view_vendor = self._create_schema_value('desktop.details.vendor')
        self.desktop_details_view_operations = self._create_schema_value('desktop.details.operations')
        self.desktop_details_view_client = self._create_schema_value('desktop.details.client')

        self.desktop_infocard_view_vendor = self._create_schema_value('desktop.infocard.vendor')
        self.desktop_infocard_view_operations = self._create_schema_value('desktop.infocard.operations')
        self.desktop_infocard_view_client = self._create_schema_value('desktop.infocard.client')

        self.desktop_spotlight_vendor = self._create_schema_value('desktop.spotlight.vendor')
        self.desktop_spotlight_operations = self._create_schema_value('desktop.spotlight.operations')
        self.desktop_spotlight_client = self._create_schema_value('desktop.spotlight.client')

        self.desktop_settings_vendor = self._create_schema_value('desktop.settings.vendor')
        self.desktop_settings_operations = self._create_schema_value('desktop.settings.operations')
        self.desktop_settings_client = self._create_schema_value('desktop.settings.client')

        self.email_notifications_vendor_array = self._create_schema_array('email-notifications.vendor')
        self.email_notifications_operations_array = self._create_schema_array('email-notifications.operations')
        self.email_notifications_client_array = self._create_schema_array('email-notifications.client')

        self.mobile_list_view_vendor = self._create_schema_value('mobile.list.vendor')
        self.mobile_list_view_operations = self._create_schema_value('mobile.list.operations')
        self.mobile_list_view_client = self._create_schema_value('mobile.list.client')

        self.mobile_details_view_vendor = self._create_schema_value('mobile.details.vendor')
        self.mobile_details_view_operations = self._create_schema_value('mobile.details.operations')
        self.mobile_details_view_client = self._create_schema_value('mobile.details.client')

        self.object_render_folder = os.path.join(cfg.TEMP_RENDER_FOLDER, self.object_name)


    def __lt__(self, other):

        if not isinstance(other, ObjectSchema):
            return NotImplemented
        return self.object_name < other.object_name


    def render_object_images(self):

        print()
        print(f"Rendering Figma images for the object: {self.object_name}...")

        os.makedirs(self.object_render_folder, exist_ok=True)

        for value in self.all_values.values():
            value.render_figma_image(self.object_render_folder)
