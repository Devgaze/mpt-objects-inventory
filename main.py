#!/usr/bin/env python3

import requests
import re
import os
import glob
import json
import os
import concurrent.futures

from datetime import datetime

from config import Config
from confluence import Confluence
from schema import ObjectSchema, SchemaRecord

cfg = Config()
confluence = Confluence()


SKIP_DELETE_EXISTING_IMAGES_FOR_DEBUG = False
SKIP_UPLOAD_IMAGES_TO_CONFLUENCE_FOR_DEBUG = False
SKIP_UPDATE_CONFLUENCE_PAGE_FOR_DEBUG = False

MAX_THREADS = 1


def read_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read()


def get_timestamp():
    return datetime.now().strftime("%b %d, %Y at %H:%M:%S")



def populate_template(template, data):
    for key, value in data.items():
        if key not in template:
            raise Exception(f"Key {key} not found in template")
        if value is None:
            value = 'Undefined'
        template = template.replace(key, str(value))

    unmatched_vars = re.findall(r"\{\{.*?\}\}", template)
    if unmatched_vars:
        raise Exception(f"Unmatched variables found in template: {unmatched_vars}")

    return template


def remove_all_existing_attachments(object_schema_tuple):

    idx, object_schema = object_schema_tuple

    if SKIP_DELETE_EXISTING_IMAGES_FOR_DEBUG:
        print(f"  DEBUG: Skipping deletion of existing images for {object_schema.object_name}")
        return

    confluence_page_url = object_schema.confluence_page_url
    confluence.remove_all_page_attachments(confluence_page_url)


def upload_images_to_confluence(object_schema):

    if SKIP_UPLOAD_IMAGES_TO_CONFLUENCE_FOR_DEBUG:
        print(f"  DEBUG: Skipping upload of images to Confluence for {object_schema.object_name}")
        return

    confluence_page_url = object_schema.confluence_page_url
    page_id = confluence.get_confluence_page_id_from_url(confluence_page_url)

    object_name = object_schema.object_name

    unique_filenames = set()
    for value in object_schema.all_values.values():
        filename = value.get_filename()
        if filename not in unique_filenames:
            unique_filenames.add(filename)

    print(f"Uploading {len(unique_filenames)} images to Confluence page: {page_id}...")
    counter = 1
    for filename in unique_filenames:
        print()
        print(f"Uploading image {counter} of {len(unique_filenames)}...")
        confluence.upload_image_to_confluence(confluence_page_url, filename)
        counter += 1


def update_confluence_page(object_schema):

    if SKIP_UPDATE_CONFLUENCE_PAGE_FOR_DEBUG:
        print(f"  DEBUG: Skipping update of Confluence page for {object_schema.object_name}")
        object_schema.confluence_page_title = confluence.get_confluence_page_title(confluence_page_url)
        return

    confluence_page_url = object_schema.confluence_page_url
    page_id = confluence.get_confluence_page_id_from_url(confluence_page_url)
    object_name = object_schema.object_name

    page_template = read_file("confluence-templates/object-page.html")
    roles_table_template = read_file("confluence-templates/roles-table.html")
    single_table_template = read_file("confluence-templates/single-table.html")

    WHITE = '#ffffff'
    LIGHT_BLUE = '#eaf4ff'
    LIGHT_RED = '#fff4f0'
    LIGHT_GREEN = '#edfff7'

    state_diagram = populate_template(
        single_table_template,
        {
            '{{highlight-colour}}': WHITE,
            '{{filename}}': os.path.basename(object_schema.state_diagram.filename),
            '{{figma-link}}': object_schema.state_diagram.figma_link,
        }
    )

    grid_view_table_section = populate_template(
        roles_table_template,
        {
            '{{highlight-colour-column-1}}': LIGHT_BLUE,
            '{{highlight-colour-column-2}}': LIGHT_RED,
            '{{highlight-colour-column-3}}': LIGHT_GREEN,
            '{{filename-column-1}}': os.path.basename(object_schema.desktop_grid_view_vendor.filename),
            '{{filename-column-2}}': os.path.basename(object_schema.desktop_grid_view_operations.filename),
            '{{filename-column-3}}': os.path.basename(object_schema.desktop_grid_view_client.filename),
            '{{figma-link-column-1}}': object_schema.desktop_grid_view_vendor.figma_link,
            '{{figma-link-column-2}}': object_schema.desktop_grid_view_operations.figma_link,
            '{{figma-link-column-3}}': object_schema.desktop_grid_view_client.figma_link,
        }
    )

    details_view_table_section = populate_template(
        roles_table_template,
        {
            '{{highlight-colour-column-1}}': LIGHT_BLUE,
            '{{highlight-colour-column-2}}': LIGHT_RED,
            '{{highlight-colour-column-3}}': LIGHT_GREEN,
            '{{filename-column-1}}': os.path.basename(object_schema.desktop_details_view_vendor.filename),
            '{{filename-column-2}}': os.path.basename(object_schema.desktop_details_view_operations.filename),
            '{{filename-column-3}}': os.path.basename(object_schema.desktop_details_view_client.filename),
            '{{figma-link-column-1}}': object_schema.desktop_details_view_vendor.figma_link,
            '{{figma-link-column-2}}': object_schema.desktop_details_view_operations.figma_link,
            '{{figma-link-column-3}}': object_schema.desktop_details_view_client.figma_link,
        }
    )

    desktop_infocard_view_table_section = populate_template(
        roles_table_template,
        {
            '{{highlight-colour-column-1}}': LIGHT_BLUE,
            '{{highlight-colour-column-2}}': LIGHT_RED,
            '{{highlight-colour-column-3}}': LIGHT_GREEN,
            '{{filename-column-1}}': os.path.basename(object_schema.desktop_infocard_view_vendor.filename),
            '{{filename-column-2}}': os.path.basename(object_schema.desktop_infocard_view_operations.filename),
            '{{filename-column-3}}': os.path.basename(object_schema.desktop_infocard_view_client.filename),
            '{{figma-link-column-1}}': object_schema.desktop_infocard_view_vendor.figma_link,
            '{{figma-link-column-2}}': object_schema.desktop_infocard_view_operations.figma_link,
            '{{figma-link-column-3}}': object_schema.desktop_infocard_view_client.figma_link,
        }
    )

    if object_schema.desktop_settings_vendor.figma_link is not None \
        or object_schema.desktop_settings_operations.figma_link is not None \
        or object_schema.desktop_settings_client.figma_link is not None:

        desktop_settings_table_section = populate_template(
            roles_table_template,
            {
                '{{highlight-colour-column-1}}': LIGHT_BLUE,
                '{{highlight-colour-column-2}}': LIGHT_RED,
                '{{highlight-colour-column-3}}': LIGHT_GREEN,
                '{{filename-column-1}}': os.path.basename(object_schema.desktop_settings_vendor.filename),
                '{{filename-column-2}}': os.path.basename(object_schema.desktop_settings_operations.filename),
                '{{filename-column-3}}': os.path.basename(object_schema.desktop_settings_client.filename),
                '{{figma-link-column-1}}': object_schema.desktop_settings_vendor.figma_link,
                '{{figma-link-column-2}}': object_schema.desktop_settings_operations.figma_link,
                '{{figma-link-column-3}}': object_schema.desktop_settings_client.figma_link,
            }
        )

    else:

        desktop_settings_table_section = '<p>No settings views specified</p>'

    mobile_list_view_table_section = populate_template(
        roles_table_template,
        {
            '{{highlight-colour-column-1}}': LIGHT_BLUE,
            '{{highlight-colour-column-2}}': LIGHT_RED,
            '{{highlight-colour-column-3}}': LIGHT_GREEN,
            '{{filename-column-1}}': os.path.basename(object_schema.mobile_list_view_vendor.filename),
            '{{filename-column-2}}': os.path.basename(object_schema.mobile_list_view_operations.filename),
            '{{filename-column-3}}': os.path.basename(object_schema.mobile_list_view_client.filename),
            '{{figma-link-column-1}}': object_schema.mobile_list_view_vendor.figma_link,
            '{{figma-link-column-2}}': object_schema.mobile_list_view_operations.figma_link,
            '{{figma-link-column-3}}': object_schema.mobile_list_view_client.figma_link,
        }
    )

    mobile_details_view_table_section = populate_template(
        roles_table_template,
        {
            '{{highlight-colour-column-1}}': LIGHT_BLUE,
            '{{highlight-colour-column-2}}': LIGHT_RED,
            '{{highlight-colour-column-3}}': LIGHT_GREEN,
            '{{filename-column-1}}': os.path.basename(object_schema.mobile_details_view_vendor.filename),
            '{{filename-column-2}}': os.path.basename(object_schema.mobile_details_view_operations.filename),
            '{{filename-column-3}}': os.path.basename(object_schema.mobile_details_view_client.filename),
            '{{figma-link-column-1}}': object_schema.mobile_details_view_vendor.figma_link,
            '{{figma-link-column-2}}': object_schema.mobile_details_view_operations.figma_link,
            '{{figma-link-column-3}}': object_schema.mobile_details_view_client.figma_link,
        }
    )
    page_template = populate_template(
        page_template,
        {
            '{{state-diagram}}': state_diagram,
            '{{desktop-grid-table-section}}': grid_view_table_section,
            '{{desktop-details-table-section}}': details_view_table_section,
            '{{desktop-infocard-table-section}}': desktop_infocard_view_table_section,
            '{{mobile-list-table-section}}': mobile_list_view_table_section,
            '{{mobile-details-table-section}}': mobile_details_view_table_section,
            '{{desktop-settings-table-section}}': desktop_settings_table_section,
        }
    )

    with open(f"{cfg.TEMP_RENDER_FOLDER}/{object_name}/object-page.html", "w", encoding="utf-8") as f:
        f.write(page_template)

    print()
    print(f"Updating Confluence page: {confluence_page_url}...")
    object_schema.confluence_page_title = confluence.update_confluence_page_contents(confluence_page_url, page_template)

    print(f"   ... successfully updated Confluence page: {confluence_page_url}")
    print()


def write_summary_page(object_schemas):

    print()
    print(f"Writing summary page...")

    def populate_cell(schema_record):

        if schema_record.status == SchemaRecord.SCHEMA_RECORD_STATUS_NOT_FOUND:
            return '''
                <p style="text-align: center;"><span style="color: rgb(200,200,200);">—</span></p>
            '''

        elif schema_record.status == SchemaRecord.SCHEMA_RECORD_STATUS_ERROR:
            return '''
                <p style="text-align: center;"><ac:emoticon ac:emoji-fallback=":cross_mark:" ac:emoji-id="atlassian-cross_mark" ac:emoji-shortname=":cross_mark:" ac:name="cross"></ac:emoticon> <span style="color: rgb(191,38,0);">Error</span></p>
            '''

        return f'''
            <p style="text-align: center;"><ac:emoticon ac:emoji-fallback="✅" ac:emoji-id="2705" ac:emoji-shortname=":white_check_mark:" ac:name="blue-star"></ac:emoticon> <a href="{schema_record.figma_link}">Figma</a></p>
        '''

    summary_table_row_template = read_file("confluence-templates/summary-table-row.html")

    object_rows = []

    object_number = 0
    for object_schema in sorted(object_schemas, key=lambda x: x.object_name.lower()):

        object_number += 1
        placeholders = {
            '{{object-number}}': object_number,
            '{{object-details-link}}': f'''<p><ac:link><ri:page ri:content-title="{object_schema.confluence_page_title}"></ri:page><ac:link-body><strong>{object_schema.object_name}</strong></ac:link-body></ac:link></p>''',
            '{{state-diagram-link}}': populate_cell(object_schema.state_diagram),
            
            '{{object-desktop-grid-view-vendor-link}}': populate_cell(object_schema.desktop_grid_view_vendor),
            '{{object-desktop-grid-view-operations-link}}': populate_cell(object_schema.desktop_grid_view_operations),
            '{{object-desktop-grid-view-client-link}}': populate_cell(object_schema.desktop_grid_view_client),
            
            '{{object-desktop-details-view-vendor-link}}': populate_cell(object_schema.desktop_details_view_vendor),
            '{{object-desktop-details-view-operations-link}}': populate_cell(object_schema.desktop_details_view_operations),
            '{{object-desktop-details-view-client-link}}': populate_cell(object_schema.desktop_details_view_client),
            
            '{{object-desktop-infocard-view-vendor-link}}': populate_cell(object_schema.desktop_infocard_view_vendor),
            '{{object-desktop-infocard-view-operations-link}}': populate_cell(object_schema.desktop_infocard_view_operations),
            '{{object-desktop-infocard-view-client-link}}': populate_cell(object_schema.desktop_infocard_view_client),
            
            '{{object-mobile-list-view-vendor-link}}': populate_cell(object_schema.mobile_list_view_vendor),
            '{{object-mobile-list-view-operations-link}}': populate_cell(object_schema.mobile_list_view_operations),
            '{{object-mobile-list-view-client-link}}': populate_cell(object_schema.mobile_list_view_client),

            '{{object-mobile-details-view-vendor-link}}': populate_cell(object_schema.mobile_details_view_vendor),
            '{{object-mobile-details-view-operations-link}}': populate_cell(object_schema.mobile_details_view_operations),
            '{{object-mobile-details-view-client-link}}': populate_cell(object_schema.mobile_details_view_client),
            
        }

        object_row = populate_template(summary_table_row_template, placeholders)
        object_rows.append(object_row)

    summary_page_template = read_file("confluence-templates/summary-page.html")
    summary_page_template = populate_template(summary_page_template, {
        '{{summary-page-rows}}': '\n'.join(object_rows),
    })

    with open(f"{cfg.TEMP_RENDER_FOLDER}/summary-page.html", "w", encoding="utf-8") as f:
        f.write(summary_page_template)

    print(f"Successfully wrote summary page to {cfg.TEMP_RENDER_FOLDER}/summary-page.html")
    
    print()
    print(f"Updating Confluence summary page...")
    confluence.update_confluence_page_contents(cfg.CONFLUENCE_SUMMARY_PAGE_URL, summary_page_template)

    print(f"Successfully updated Confluence summary page")
    print()


def main():

    os.makedirs(cfg.TEMP_RENDER_FOLDER, exist_ok=True)

    all_schema_files = sorted(glob.glob('./schemas/*.json'), key=lambda x: x.lower())

    # Debug: Limit to only specific schema files
    # all_schema_files = [f for f in all_schema_files if 'account' in os.path.basename(f).lower()]

    print(f"Found {len(all_schema_files)} schema files")
    index = 1
    for schema_file in all_schema_files:
        print(f" {index}: {schema_file}")
        index += 1

    object_schemas = []

    # Phase 1: initialize ObjectSchema objects

    print()
    print('=' * 120)
    print('Phase 1: Initialize ObjectSchema objects')
    print('=' * 120)

    counter = 1
    for schema_file in all_schema_files:

        print()
        print(f"Initializing object schema for {schema_file} ({counter} of {len(all_schema_files)})...")
        counter += 1

        object_schema = ObjectSchema(schema_file)
        object_schemas.append(object_schema)

    # Step 2: Render all Figma images for all ObjectSchema objects

    print()
    print('=' * 120)
    print('Phase 2: Render all Figma images for all ObjectSchema objects')
    print('=' * 120)

    def render_images_with_progress(object_schema_tuple):
        idx, object_schema, total = object_schema_tuple
        object_schema.render_object_images()
        return object_schema.object_name

    total_schemas = len(object_schemas)
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = []
        for idx, object_schema in enumerate(object_schemas, start=1):
            futures.append(
                executor.submit(render_images_with_progress, (idx, object_schema, total_schemas))
            )
        for future in concurrent.futures.as_completed(futures):
            future.result()


    # Step 3: Remove all existing attachments from Confluence pages for all ObjectSchema objects

    print()
    print('=' * 120)
    print('Phase 3: Remove all existing attachments from Confluence pages for all object schemas')
    print('=' * 120)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        list(executor.map(remove_all_existing_attachments, enumerate(object_schemas)))

    # Step 4: Upload images to Confluence pages for all ObjectSchema objects

    print()
    print('=' * 120)
    print('Phase 4: Upload images to Confluence pages for all object schemas')
    print('=' * 120)

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        list(executor.map(upload_images_to_confluence, object_schemas))

    # Step 5: Update Confluence pages for all ObjectSchema objects

    print()
    print('=' * 120)
    print('Phase 5: Update Confluence pages for all object schemas')
    print('=' * 120)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        list(executor.map(update_confluence_page, object_schemas))


    # Step 6: Write summary page

    print()
    print('=' * 120)
    print('Phase 6: Write summary page')
    print('=' * 120)

    write_summary_page(object_schemas)


if __name__ == '__main__':
    main()
