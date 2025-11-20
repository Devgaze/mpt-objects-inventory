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
from renderers.object import update_object_confluence_page
from renderers.summary import write_summary_page
from renderers.overview import write_overview_pages

cfg = Config()
confluence = Confluence()


MAX_THREADS = 1



def remove_all_existing_attachments(object_schema_tuple):

    idx, object_schema = object_schema_tuple

    if cfg.SKIP_DELETE_EXISTING_IMAGES_FOR_DEBUG:
        print(f"  DEBUG: Skipping deletion of existing images for {object_schema.object_name}")
        return

    confluence_page_url = object_schema.confluence_page_url
    confluence.remove_all_page_attachments(confluence_page_url)


def upload_images_to_confluence(object_schema):

    if cfg.SKIP_UPLOAD_IMAGES_TO_CONFLUENCE_FOR_DEBUG:
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


def main():

    os.makedirs(cfg.TEMP_RENDER_FOLDER, exist_ok=True)

    all_schema_files = sorted(glob.glob('./schemas/*.json'), key=lambda x: x.lower())

    # Debug: Limit to only specific schema files
    # all_schema_files = [f for f in all_schema_files if 'order' in os.path.basename(f).lower()]

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
        list(executor.map(update_object_confluence_page, object_schemas))

    # Step 6: Write summary page

    print()
    print('=' * 120)
    print('Phase 6: Write summary page')
    print('=' * 120)

    write_summary_page(object_schemas)

    # Step 7: Write overview pages

    print()
    print('=' * 120)
    print('Phase 7: Write overview pages')
    print('=' * 120)

    write_overview_pages(object_schemas)

if __name__ == '__main__':
    main()
