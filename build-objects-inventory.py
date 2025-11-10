#!/usr/bin/env python3

import requests
import re
import os
import glob
import json
import os

from datetime import datetime

from config import Config
from confluence import Confluence
from figma import Figma

cfg = Config()
confluence = Confluence()
figma = Figma()


def read_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read()


def get_timestamp():
    return datetime.now().strftime("%b %d, %Y at %H:%M:%S")


def render_figma_images(object_schema):

    rendered_files = []
    object_name = object_schema['name']

    supported_schema_keys = [
        'desktop.grid-view.vendor',
        'desktop.grid-view.operations',
        'desktop.grid-view.client',
        'desktop.details-view.vendor',
        'desktop.details-view.operations',
        'desktop.details-view.client',
        'desktop.infocard-view.vendor',
        'desktop.infocard-view.operations',
        'desktop.infocard-view.client',
        'state-diagram',
        'mobile.list-view.vendor',
        'mobile.list-view.operations',
        'mobile.list-view.client',
        'mobile.details-view.vendor',
        'mobile.details-view.operations',
        'mobile.details-view.client',
    ]

    counter = 1
    for path in supported_schema_keys:
        print()
        print(f"Processing Figma path: {path} ({counter} of {len(supported_schema_keys)})")
        counter += 1
        
        # retrieve field (if exists) using path (which is a string in the format 'key1.key2...')
        keys = path.split('.')

        last_key = None
        last_value = object_schema
        for key in keys:
            if isinstance(last_value, dict) and key in last_value:
                last_value = last_value[key]
                last_key = key
            else:
                last_value = None
                last_key = None
                break
        
        if last_key is None:
            raise ValueError(f"Reference not found for path: {path}")

        if last_value is None:
            last_value = cfg.MISSING_FIGMA_PAGE_PLACEHOLDER
        
        filename = object_name + '-' + path.replace('.', '-') + '.png'
        print(f"Rendering {last_value} to {filename}")
        image_filename = figma.render_figma_png(last_value, f'{cfg.TEMP_RENDER_FOLDER}/{filename}')
        rendered_files.append(filename)

    return rendered_files



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



def update_confluence_page(rendered_files, object_schema):

    confluence_page_url = object_schema['confluence-page']
    page_id = confluence.get_confluence_page_id_from_url(confluence_page_url)

    object_name = object_schema['name']

    print(f"Uploading {len(rendered_files)} images to Confluence page: {page_id}...")
    counter = 1
    for rendered_file in rendered_files:
        print()
        print(f"Uploading image {counter} of {len(rendered_files)}...")
        confluence.upload_image_to_confluence(confluence_page_url, f'{cfg.TEMP_RENDER_FOLDER}/{rendered_file}')
        counter += 1

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
            '{{filename}}': f'{object_name}-state-diagram.png',
            '{{figma-link}}': object_schema['state-diagram'],
        }
    )

    grid_view_table_section = populate_template(
        roles_table_template,
        {
            '{{highlight-colour-column-1}}': LIGHT_BLUE,
            '{{highlight-colour-column-2}}': LIGHT_RED,
            '{{highlight-colour-column-3}}': LIGHT_GREEN,
            '{{filename-column-1}}': f'{object_name}-desktop-grid-view-vendor.png',
            '{{filename-column-2}}': f'{object_name}-desktop-grid-view-operations.png',
            '{{filename-column-3}}': f'{object_name}-desktop-grid-view-client.png',
            '{{figma-link-column-1}}': object_schema['desktop']['grid-view']['vendor'],
            '{{figma-link-column-2}}': object_schema['desktop']['grid-view']['operations'],
            '{{figma-link-column-3}}': object_schema['desktop']['grid-view']['client'],
        }
    )

    details_view_table_section = populate_template(
        roles_table_template,
        {
            '{{highlight-colour-column-1}}': LIGHT_BLUE,
            '{{highlight-colour-column-2}}': LIGHT_RED,
            '{{highlight-colour-column-3}}': LIGHT_GREEN,
            '{{filename-column-1}}': f'{object_name}-desktop-details-view-vendor.png',
            '{{filename-column-2}}': f'{object_name}-desktop-details-view-operations.png',
            '{{filename-column-3}}': f'{object_name}-desktop-details-view-client.png',
            '{{figma-link-column-1}}': object_schema['desktop']['details-view']['vendor'],
            '{{figma-link-column-2}}': object_schema['desktop']['details-view']['operations'],
            '{{figma-link-column-3}}': object_schema['desktop']['details-view']['client'],
        }
    )

    desktop_infocard_view_table_section = populate_template(
        roles_table_template,
        {
            '{{highlight-colour-column-1}}': LIGHT_BLUE,
            '{{highlight-colour-column-2}}': LIGHT_RED,
            '{{highlight-colour-column-3}}': LIGHT_GREEN,
            '{{filename-column-1}}': f'{object_name}-desktop-infocard-view-vendor.png',
            '{{filename-column-2}}': f'{object_name}-desktop-infocard-view-operations.png',
            '{{filename-column-3}}': f'{object_name}-desktop-infocard-view-client.png',
            '{{figma-link-column-1}}': object_schema['desktop']['infocard-view']['vendor'],
            '{{figma-link-column-2}}': object_schema['desktop']['infocard-view']['operations'],
            '{{figma-link-column-3}}': object_schema['desktop']['infocard-view']['client'],
        }
    )

    mobile_list_view_table_section = populate_template(
        roles_table_template,
        {
            '{{highlight-colour-column-1}}': LIGHT_BLUE,
            '{{highlight-colour-column-2}}': LIGHT_RED,
            '{{highlight-colour-column-3}}': LIGHT_GREEN,
            '{{filename-column-1}}': f'{object_name}-mobile-list-view-vendor.png',
            '{{filename-column-2}}': f'{object_name}-mobile-list-view-operations.png',
            '{{filename-column-3}}': f'{object_name}-mobile-list-view-client.png',
            '{{figma-link-column-1}}': object_schema['mobile']['list-view']['vendor'],
            '{{figma-link-column-2}}': object_schema['mobile']['list-view']['operations'],
            '{{figma-link-column-3}}': object_schema['mobile']['list-view']['client'],
        }
    )

    mobile_details_view_table_section = populate_template(
        roles_table_template,
        {
            '{{highlight-colour-column-1}}': LIGHT_BLUE,
            '{{highlight-colour-column-2}}': LIGHT_RED,
            '{{highlight-colour-column-3}}': LIGHT_GREEN,
            '{{filename-column-1}}': f'{object_name}-mobile-details-view-vendor.png',
            '{{filename-column-2}}': f'{object_name}-mobile-details-view-operations.png',
            '{{filename-column-3}}': f'{object_name}-mobile-details-view-client.png',
            '{{figma-link-column-1}}': object_schema['mobile']['details-view']['vendor'],
            '{{figma-link-column-2}}': object_schema['mobile']['details-view']['operations'],
            '{{figma-link-column-3}}': object_schema['mobile']['details-view']['client'],
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
            '{{last-updated}}': get_timestamp(),
        }
    )

    with open(f"{cfg.TEMP_RENDER_FOLDER}/confluence-page-updated-{page_id}.html", "w", encoding="utf-8") as f:
        f.write(page_template)

    print()
    print(f"Updating Confluence page: {page_id}...")
    confluence.update_confluence_page(confluence_page_url, page_template)

    print(f"Successfully updated Confluence page: {page_id}")
    print()


def get_all_schema_files():
    schema_files = glob.glob('./schemas/*.json')
    return schema_files


def write_summary_page(object_schemas):

    print()
    print(f"Writing summary page...")

    def populate_cell(figma_link):

        if figma_link is None:
            return '''
        <p style="text-align: center;"><ac:emoticon ac:emoji-fallback=":cross_mark:" ac:emoji-id="atlassian-cross_mark" ac:emoji-shortname=":cross_mark:" ac:name="cross"></ac:emoticon> <span style="color: rgb(191,38,0);">None</span></p>
        '''

        return f'''
        <p style="text-align: center;"><ac:emoticon ac:emoji-fallback="✅" ac:emoji-id="2705" ac:emoji-shortname=":white_check_mark:" ac:name="blue-star"></ac:emoticon> <a href="{figma_link}">Figma</a></p>
        '''

    summary_table_row_template = read_file("confluence-templates/summary-table-row.html")

    object_rows = []

    object_number = 0
    for object_schema in sorted(object_schemas, key=lambda x: x['name']):

        object_number += 1
        placeholders = {
            '{{object-number}}': object_number,
            '{{object-details-link}}': f'''<p><ac:link><ri:page ri:content-title="{object_schema['page_title']}"></ri:page><ac:link-body><strong>{object_schema['name']}</strong></ac:link-body></ac:link></p>''',
            '{{state-diagram-link}}': populate_cell(object_schema['state-diagram']),
            
            '{{object-desktop-grid-view-vendor-link}}': populate_cell(object_schema['desktop']['grid-view']['vendor']),
            '{{object-desktop-grid-view-operations-link}}': populate_cell(object_schema['desktop']['grid-view']['operations']),
            '{{object-desktop-grid-view-client-link}}': populate_cell(object_schema['desktop']['grid-view']['client']),
            
            '{{object-desktop-details-view-vendor-link}}': populate_cell(object_schema['desktop']['details-view']['vendor']),
            '{{object-desktop-details-view-operations-link}}': populate_cell(object_schema['desktop']['details-view']['operations']),
            '{{object-desktop-details-view-client-link}}': populate_cell(object_schema['desktop']['details-view']['client']),
            
            '{{object-desktop-infocard-view-vendor-link}}': populate_cell(object_schema['desktop']['infocard-view']['vendor']),
            '{{object-desktop-infocard-view-operations-link}}': populate_cell(object_schema['desktop']['infocard-view']['operations']),
            '{{object-desktop-infocard-view-client-link}}': populate_cell(object_schema['desktop']['infocard-view']['client']),
            
            '{{object-mobile-list-view-vendor-link}}': populate_cell(object_schema['mobile']['list-view']['vendor']),
            '{{object-mobile-list-view-operations-link}}': populate_cell(object_schema['mobile']['list-view']['operations']),
            '{{object-mobile-list-view-client-link}}': populate_cell(object_schema['mobile']['list-view']['client']),

            '{{object-mobile-details-view-vendor-link}}': populate_cell(object_schema['mobile']['details-view']['vendor']),
            '{{object-mobile-details-view-operations-link}}': populate_cell(object_schema['mobile']['details-view']['operations']),
            '{{object-mobile-details-view-client-link}}': populate_cell(object_schema['mobile']['details-view']['client']),
            
        }

        object_row = populate_template(summary_table_row_template, placeholders)
        object_rows.append(object_row)

    summary_page_template = read_file("confluence-templates/summary-page.html")
    summary_page_template = populate_template(summary_page_template, {
        '{{summary-page-rows}}': '\n'.join(object_rows),
        '{{last-updated}}': get_timestamp(),
    })

    with open(f"{cfg.TEMP_RENDER_FOLDER}/summary-page.html", "w", encoding="utf-8") as f:
        f.write(summary_page_template)

    print(f"Successfully wrote summary page to {cfg.TEMP_RENDER_FOLDER}/summary-page.html")
    
    print()
    print(f"Updating Confluence summary page...")
    confluence.update_confluence_page(cfg.CONFLUENCE_SUMMARY_PAGE_URL, summary_page_template)

    print(f"Successfully updated Confluence summary page")
    print()


def main():

    os.makedirs(cfg.TEMP_RENDER_FOLDER, exist_ok=True)

    all_schema_files = get_all_schema_files()
    print(f"Found {len(all_schema_files)} schema files")
    index = 1
    for schema_file in all_schema_files:
        print(f" {index}: {schema_file}")
        index += 1

    object_schemas = []

    counter = 1
    for schema_file in all_schema_files:

        print()
        print(f"Processing {schema_file} ({counter} of {len(all_schema_files)})...")
        counter += 1

        with open(schema_file, 'r', encoding='utf-8') as f:
            object_schema = json.load(f)

        print()
        print(f"Rendering Figma images for {schema_file}...")
        rendered_files = render_figma_images(object_schema)

        print()
        print(f"Downloading current Confluence page for {schema_file}...")
        page_url = object_schema['confluence-page']
        page_title = confluence.download_current_confluence_page(page_url)
        object_schema['page_title'] = page_title

        print()
        print(f"Updating Confluence page for {schema_file}...")
        update_confluence_page(rendered_files, object_schema)

        object_schemas.append(object_schema)

    write_summary_page(object_schemas)


if __name__ == '__main__':
    main()
