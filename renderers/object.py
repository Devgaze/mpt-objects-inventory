#! /usr/bin/env python3

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config
from confluence import Confluence
from util import populate_template, populate_multitable_template, read_file

cfg = Config()
confluence = Confluence()

def update_object_confluence_page(object_schema):

    confluence_page_url = object_schema.confluence_page_url

    if cfg.SKIP_UPDATE_CONFLUENCE_PAGE_FOR_DEBUG:
        print(f"  DEBUG: Skipping update of Confluence page for the object: {object_schema.object_name}")
        object_schema.confluence_page_title = confluence.get_confluence_page_title(confluence_page_url)
        return

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

    desktop_spotlight_table_section = populate_template(
        roles_table_template,
        {
            '{{highlight-colour-column-1}}': LIGHT_BLUE,
            '{{highlight-colour-column-2}}': LIGHT_RED,
            '{{highlight-colour-column-3}}': LIGHT_GREEN,
            '{{filename-column-1}}': os.path.basename(object_schema.desktop_spotlight_vendor.filename),
            '{{filename-column-2}}': os.path.basename(object_schema.desktop_spotlight_operations.filename),
            '{{filename-column-3}}': os.path.basename(object_schema.desktop_spotlight_client.filename),
            '{{figma-link-column-1}}': object_schema.desktop_spotlight_vendor.figma_link,
            '{{figma-link-column-2}}': object_schema.desktop_spotlight_operations.figma_link,
            '{{figma-link-column-3}}': object_schema.desktop_spotlight_client.figma_link,
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

    multitable_template = read_file("confluence-templates/multitable.html")
    multitable_row_template = read_file("confluence-templates/multitable-row.html")

    email_notifications_vendor_table = populate_multitable_template(
        multitable_template,
        multitable_row_template,
        object_schema.email_notifications_vendor_array
    )

    email_notifications_operations_table = populate_multitable_template(
        multitable_template,
        multitable_row_template,
        object_schema.email_notifications_operations_array
    )

    email_notifications_client_table = populate_multitable_template(
        multitable_template,
        multitable_row_template,
        object_schema.email_notifications_client_array
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
            '{{email-notifications-vendor-table}}': email_notifications_vendor_table,
            '{{email-notifications-operations-table}}': email_notifications_operations_table,
            '{{email-notifications-client-table}}': email_notifications_client_table,
            '{{desktop-spotlight-table-section}}': desktop_spotlight_table_section,
        }
    )

    with open(f"{cfg.TEMP_RENDER_FOLDER}/{object_name}/object-page.html", "w", encoding="utf-8") as f:
        f.write(page_template)

    print()
    print(f"Updating Confluence page: {confluence_page_url}...")
    object_schema.confluence_page_title = confluence.update_confluence_page_contents(confluence_page_url, page_template)

    print(f"   ... successfully updated Confluence page: {confluence_page_url}")
    print()