#!/usr/bin/env python

import re
import requests
import json
import os
import concurrent.futures
from bs4 import BeautifulSoup

from config import Config

cfg = Config()



class Confluence:

    def delete_confluence_attachment(self, attachment_id, status):
        delete_url = f"{cfg.CONFLUENCE_BASE_URL}/rest/api/content/{attachment_id}?status={status}"
        delete_response = requests.delete(
            delete_url,
            headers={"Accept": "application/json"},
            auth=cfg.CONFLUENCE_AUTH
        )
        delete_response.raise_for_status()


    def get_confluence_page_id_from_url(self, confluence_page_url):
        return confluence_page_url.split('/pages/')[1].split('/')[0]


    def make_page_full_width(self, page_url):

        page_id = self.get_confluence_page_id_from_url(page_url)
        property_key = "content-appearance-published"
        properties_base_url = f"{cfg.CONFLUENCE_BASE_URL}/api/v2/pages/{page_id}/properties"

        payload = {
            "key": property_key,
            "value": "full-width"
        }

        # Get all properties of the page first
        properties_response = requests.get(
            properties_base_url,
            headers={
                "Accept": "application/json"
            },
            auth=cfg.CONFLUENCE_AUTH
        )
        properties_response.raise_for_status()

        properties = properties_response.json()
        full_width_property = None
        for property in properties.get('results', []):
            _key = property['key']
            if _key == property_key:
                full_width_property = property
                break

        if full_width_property:
            # delete if existing
            response = requests.delete(
                f"{properties_base_url}/{full_width_property['id']}",
                headers={
                    "Accept": "application/json"
                },
                auth=cfg.CONFLUENCE_AUTH
            )
            response.raise_for_status()

        # Now force create the property with the correct value
        response = requests.post(
            properties_base_url,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            auth=cfg.CONFLUENCE_AUTH,
            json=payload
        )

        response.raise_for_status()


    def upload_image_to_confluence(self, page_url, image_path):

        page_id = self.get_confluence_page_id_from_url(page_url)

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
                self.delete_confluence_attachment(attachment_id, "current")
                self.delete_confluence_attachment(attachment_id, "trashed")

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


    def get_confluence_page_title(self, confluence_page_url):
        data = self.get_confluence_page_contents(confluence_page_url)
        return data['title']


    def get_confluence_page_contents(self, confluence_page_url):
        page_id = self.get_confluence_page_id_from_url(confluence_page_url)
        request_url = f'{cfg.CONFLUENCE_BASE_URL}/rest/api/content/{page_id}?expand=body.storage,version'
        resp = requests.get(
            request_url, 
            headers={"Accept": "application/json"}, 
            auth=cfg.CONFLUENCE_AUTH
        )
        resp.raise_for_status()
        return resp.json()


    def download_current_confluence_page(self, confluence_page_url):        
        page_id = self.get_confluence_page_id_from_url(confluence_page_url)
        data = self.get_confluence_page_contents(confluence_page_url)
        page_title = data['title']
        page_title_for_file = re.sub(r'[^a-zA-Z0-9_\-]', '-', page_title)
        html_content = data['body']['storage']['value']
        soup = BeautifulSoup(html_content, "html.parser")
        html_content = soup.prettify()
        with open(f"{cfg.TEMP_RENDER_FOLDER}/current-confluence-page-{page_id}-{page_title_for_file}.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"Downloaded and saved current Confluence page to {cfg.TEMP_RENDER_FOLDER}/current-confluence-page-{page_id}-{page_title_for_file}.html")
        print()

        return page_title


    def _remove_nondata_attributes(self, html):
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup.find_all(True):  # True = all tags
            if 'ri:version-at-save' in tag.attrs:
                del tag.attrs['ri:version-at-save']
        return str(soup)


    def remove_all_page_attachments(self, page_url):
        print(f"Removing all attachments from page: {page_url} ...")
        page_id = self.get_confluence_page_id_from_url(page_url)
        request_url = f'{cfg.CONFLUENCE_BASE_URL}/rest/api/content/{page_id}/child/attachment'
        resp = requests.get(request_url, headers={"Accept": "application/json"}, auth=cfg.CONFLUENCE_AUTH)
        resp.raise_for_status()
        attachments = resp.json()['results']

        if len(attachments) == 0:
            print(f"  ... no attachments found")
            return

        print(f"Found {len(attachments)} attachments")

        for attachment in attachments:
            attachment_status = attachment['status']
            self.delete_confluence_attachment(attachment['id'], "current")
            self.delete_confluence_attachment(attachment['id'], "trashed")

        print(f"  ... removed all attachments from page: {page_url}")


    def update_confluence_page_contents(self, page_url, new_content):

        old_content = self.get_confluence_page_contents(page_url)
        page_title = old_content['title']

        # Get the old page content (HTML, as string)
        old_html = self._remove_nondata_attributes(old_content['body']['storage']['value'])
        new_html = self._remove_nondata_attributes(new_content)

        # Normalize both HTMLs for comparison using BeautifulSoup's prettify (formatting)
        soup_old = BeautifulSoup(old_html, "html.parser")
        prettified_old = soup_old.prettify()
        soup_new = BeautifulSoup(new_html, "html.parser")
        prettified_new = soup_new.prettify()

        # If the formatted content is identical, do not proceed with update
        if prettified_old.strip() == prettified_new.strip():
            print("NO CHANGES DETECTED! Skipping update.")
            return page_title

        page_id = self.get_confluence_page_id_from_url(page_url)

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

        # also just to make sure all these pages look alike, we make it full width
        self.make_page_full_width(page_url)

        return page_title