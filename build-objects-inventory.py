#!/usr/bin/env python3

import requests
import re
import os
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime
import glob
import json

from config import Config

cfg = Config()

TEMP_RENDER_FOLDER = 'build'


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


def get_frame_id_from_url(figma_url):
    match = re.search(r'node-id=([\d:-]+)', figma_url)
    if match:
        return match.group(1).replace(':', '%3A')
    return None


def render_figma_png(figma_url, out_filename, figma_token):
    file_key_match = re.search(r'figma\.com/(file|proto|design)/([a-zA-Z0-9]+)', figma_url)
    if not file_key_match:
        raise ValueError("Could not extract Figma file key from URL")
    file_key = file_key_match.group(2)
    print(f"File key: {file_key}")

    node_id = get_frame_id_from_url(figma_url)
    if not node_id:
        raise ValueError("Could not extract node-id from URL")
    print(f"Node ID: {node_id}")

    api_url = f"https://api.figma.com/v1/images/{file_key}?ids={node_id}&format=png&scale=2" # scale x2 for better quality
    headers = {
        "X-Figma-Token": figma_token
    }
    resp = requests.get(api_url, headers=headers)
    if resp.status_code == 403:
        raise RuntimeError(
            f"Figma API returned 403 Forbidden. This usually means your token is EXPIRED, incorrect, or does not have access to the file.\n"
            f"Request URL: {api_url}\n"
            f"File key and node id may be incorrect, or the Figma file may not be public/readable.\n"
            f"Response: {resp.text}"
        )
    resp.raise_for_status()
    json_result = resp.json()
    image_url = json_result['images'][node_id.replace('-', ':')] # weirdly the node-id is formatted with colons instead of hyphens here
    print(f"Image URL: {image_url}")
    
    # Download image
    img_resp = requests.get(image_url)
    img_resp.raise_for_status()
    with open(out_filename, 'wb') as f:
        f.write(img_resp.content)
    
    print(f"Rendered image saved as {out_filename}")


def render_figma_images(object_schema):

    os.makedirs(TEMP_RENDER_FOLDER, exist_ok=True)

    rendered_files = []

    object_name = object_schema['name']

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
        render_figma_png(last_value, f'{TEMP_RENDER_FOLDER}/{filename}', cfg.FIGMA_API_TOKEN)
        rendered_files.append(filename)

    return rendered_files


def delete_confluence_attachment(attachment_id, status):
    delete_url = f"{cfg.CONFLUENCE_BASE_URL}/rest/api/content/{attachment_id}?status={status}"
    delete_response = requests.delete(
        delete_url,
        headers={"Accept": "application/json"},
        auth=cfg.CONFLUENCE_AUTH
    )
    delete_response.raise_for_status()


def upload_image_version_to_confluence(page_id, image_path):

    # See: https://support.atlassian.com/confluence/kb/using-the-confluence-rest-api-to-upload-an-attachment-to-one-or-more-pages/
    request_url = f'{cfg.CONFLUENCE_BASE_URL}/rest/api/content/{page_id}/child/attachment'
    print(f"Uploading image version to Confluence: {image_path}")

    filename = os.path.basename(image_path)

    with open(image_path, 'rb') as file_handle:
        files = {
            'file': (filename, file_handle, 'image/png')
        }
        data = {
            "minorEdit": "true"
        }

        # First try to update the existing attachment version; if it does not exist, fall back to upload a new one
        # See: https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-attachments/#api-wiki-rest-api-content-id-child-attachment-put
        # We'll first check if an attachment with the filename exists, and if so, update it; otherwise, create new.

        # First, check if the attachment already exists by filename
        get_params = {
            "filename": filename,
            "expand": "version"
        }
        check_response = requests.get(
            request_url,
            headers={"Accept": "application/json"},
            auth=cfg.CONFLUENCE_AUTH,
            params=get_params
        )
        check_response.raise_for_status()
        attachment_result = check_response.json()
        results = attachment_result.get("results", [])

        if results:
            # Attachment exists, delete the existing attachment and upload a new one
            attachment_id = results[0]["id"]
            print(f"Deleting existing attachment with id: {attachment_id}")
            delete_confluence_attachment(attachment_id, "current")
            delete_confluence_attachment(attachment_id, "trashed")

        response = requests.post(
            request_url,
            headers={
                "Accept": "application/json",
                "X-Atlassian-Token": "no-check"
            },
            auth=cfg.CONFLUENCE_AUTH,
            files=files,
            data=data
        )

        response.raise_for_status()
        print(f"Successfully uploaded image version to Confluence")

        data = response.json()
        return data


def download_current_confluence_page(object_schema):

    confluence_page_url = object_schema['confluence-page']
    page_id = confluence_page_url.split('/pages/')[1].split('/')[0]

    request_url = f'{cfg.CONFLUENCE_BASE_URL}/rest/api/content/{page_id}?expand=body.storage,version'
    print(f"Downloading Confluence page via API: {request_url}")
    resp = requests.get(
        request_url, 
        headers={"Accept": "application/json"}, 
        auth=cfg.CONFLUENCE_AUTH
        )
    resp.raise_for_status()
    data = resp.json()
    html_content = data['body']['storage']['value']
    soup = BeautifulSoup(html_content, "html.parser")
    html_content = soup.prettify()
    with open(f"{TEMP_RENDER_FOLDER}/current-confluence-page-{page_id}.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Downloaded and saved current Confluence page to {TEMP_RENDER_FOLDER}/current-confluence-page-{page_id}.html")
    print()


def populate_template(template, data):
    for key, value in data.items():
        if key not in template:
            raise Exception(f"Key {key} not found in template")
        if value is None:
            value = 'Undefined'
        template = template.replace(key, value)

    unmatched_vars = re.findall(r"\{\{.*?\}\}", template)
    if unmatched_vars:
        raise Exception(f"Unmatched variables found in template: {unmatched_vars}")

    return template


def update_page_content(page_id, new_content):
        
    api_url = f"{cfg.CONFLUENCE_BASE_URL}/rest/api/content/{page_id}"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    resp = requests.get(api_url, headers=headers, auth=cfg.CONFLUENCE_AUTH)
    resp.raise_for_status()
    current_title = resp.json()['title']
    current_version = resp.json()["version"]["number"]

    payload = {
            "id": page_id,
            "type": "page",
            "title": current_title,
            "body": {
                "storage": {
                    "value": new_content,
                    "representation": "storage"
                }
            },
            "version": {
            "number": current_version + 1
        }
    }
    put_response = requests.put(api_url, headers=headers, json=payload, auth=cfg.CONFLUENCE_AUTH)
    put_response.raise_for_status()
    return put_response.json()


def update_confluence_page(rendered_files, object_schema):

    confluence_page_url = object_schema['confluence-page']
    page_id = confluence_page_url.split('/pages/')[1].split('/')[0]

    object_name = object_schema['name']

    print(f"Uploading {len(rendered_files)} images to Confluence page: {page_id}...")
    counter = 1
    for rendered_file in rendered_files:
        print()
        print(f"Uploading image {counter} of {len(rendered_files)}...")
        upload_image_version_to_confluence(page_id, f'{TEMP_RENDER_FOLDER}/{rendered_file}')
        counter += 1

    with open("confluence-templates/object-page.html", "r", encoding="utf-8") as f:
        page_template = f.read()
    
    with open("confluence-templates/roles-table.html", "r", encoding="utf-8") as f:
        roles_table_template = f.read()

    with open("confluence-templates/single-table.html", "r", encoding="utf-8") as f:
        single_table_template = f.read()

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
            '{{last-updated}}': datetime.now().strftime("%b %d, %Y at %H:%M:%S"),
        }
    )

    with open(f"{TEMP_RENDER_FOLDER}/confluence-page-updated-{page_id}.html", "w", encoding="utf-8") as f:
        f.write(page_template)

    print()
    print(f"Updating Confluence page: {page_id}...")
    update_page_content(page_id, page_template)

    print(f"Successfully updated Confluence page: {page_id}")
    print()

def get_all_schema_files():
    schema_files = glob.glob('./schemas/*.json')
    return schema_files


def main():

    all_schema_files = get_all_schema_files()
    print(f"Found {len(all_schema_files)} schema files")
    index = 1
    for schema_file in all_schema_files:
        print(f" {index}: {schema_file}")
        index += 1

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
        download_current_confluence_page(object_schema)

        print()
        print(f"Updating Confluence page for {schema_file}...")
        update_confluence_page(rendered_files, object_schema)

if __name__ == '__main__':
    main()
