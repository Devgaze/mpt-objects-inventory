#! /usr/bin/env python3

import sys
import os
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config
from confluence import Confluence
from util import populate_template, populate_multitable_template, read_file

cfg = Config()
confluence = Confluence()



def render_overview_page(confluence_page_url, overview_name, values_array):

    print()
    print(f"Writing overview page for {overview_name}...")

    # copying required files to the overview folder for this overview page
    overview_prefix = overview_name.lower().replace(' ', '-')
    os.makedirs(f"{cfg.TEMP_RENDER_FOLDER}/{overview_prefix}", exist_ok=True)

    def get_filename(postfix = ''):
        return cfg.TEMP_RENDER_FOLDER + '/' + overview_prefix + '/' + overview_prefix + '-' + object_name_prefix + postfix + '.png'

    unique_filenames = {}
    fixed_values_array = []
    for value in values_array:
        object_name_prefix = value.parent.object_name.lower().replace(' ', '-')
        fixed_value = value.copy()
        new_filename = get_filename('')
        if new_filename in unique_filenames:
            postfix = 1
            while True:
                postfix += 1
                new_filename = get_filename(f"-{postfix}")
                if new_filename not in unique_filenames:
                    break
                
        unique_filenames[new_filename] = True
        shutil.copyfile(value.filename, new_filename)
        fixed_value.filename = new_filename
        fixed_values_array.append(fixed_value)

    confluence.remove_all_page_attachments(confluence_page_url)
    for value in fixed_values_array:
        confluence.upload_image_to_confluence(confluence_page_url, value.filename)

    page_template = read_file("confluence-templates/overview-page.html")

    multitable_template = read_file("confluence-templates/multitable.html")
    multitable_row_template = read_file("confluence-templates/multitable-row.html")

    overview_table = populate_multitable_template(
        multitable_template,
        multitable_row_template,
        fixed_values_array
    )

    page_template = populate_template(
        page_template,
        {
            '{{overview-name}}': overview_name,
            '{{overview-table}}': overview_table,
        }
    )

    with open(f"{cfg.TEMP_RENDER_FOLDER}/{overview_prefix}/overview-page.html", "w", encoding="utf-8") as f:
        f.write(page_template)

    print()
    print(f"Updating Confluence page: {confluence_page_url}...")
    confluence.update_confluence_page_contents(confluence_page_url, page_template)

    print(f"   ... successfully updated Confluence page with overview of {overview_name}: {confluence_page_url}")
    print()


def write_overview_pages(object_schemas):

    state_diagram_array = []
    for object_schema in object_schemas:
        state_diagram_array.append(object_schema.state_diagram)

    render_overview_page(cfg.CONFLUENCE_OVERVIEW_PAGE_URL_STATE_DIAGRAMS, "State Diagrams", state_diagram_array)

    desktop_grid_view_array = []
    for object_schema in object_schemas:
        desktop_grid_view_array.append(object_schema.desktop_grid_view_vendor)
        desktop_grid_view_array.append(object_schema.desktop_grid_view_operations)
        desktop_grid_view_array.append(object_schema.desktop_grid_view_client)

    render_overview_page(cfg.CONFLUENCE_OVERVIEW_PAGE_URL_DESKTOP_GRIDS, "Desktop Grids", desktop_grid_view_array)

    desktop_details_view_array = []
    for object_schema in object_schemas:
        desktop_details_view_array.append(object_schema.desktop_details_view_vendor)
        desktop_details_view_array.append(object_schema.desktop_details_view_operations)
        desktop_details_view_array.append(object_schema.desktop_details_view_client)

    render_overview_page(cfg.CONFLUENCE_OVERVIEW_PAGE_URL_DESKTOP_DETAILS, "Desktop Details", desktop_details_view_array)

    desktop_infocard_view_array = []
    for object_schema in object_schemas:
        desktop_infocard_view_array.append(object_schema.desktop_infocard_view_vendor)
        desktop_infocard_view_array.append(object_schema.desktop_infocard_view_operations)
        desktop_infocard_view_array.append(object_schema.desktop_infocard_view_client)

    render_overview_page(cfg.CONFLUENCE_OVERVIEW_PAGE_URL_DESKTOP_INFO_CARDS, "Desktop Infocard", desktop_infocard_view_array)

    mobile_list_view_array = []
    for object_schema in object_schemas:
        mobile_list_view_array.append(object_schema.mobile_list_view_vendor)
        mobile_list_view_array.append(object_schema.mobile_list_view_operations)
        mobile_list_view_array.append(object_schema.mobile_list_view_client)

    render_overview_page(cfg.CONFLUENCE_OVERVIEW_PAGE_URL_MOBILE_LIST, "Mobile List", mobile_list_view_array)

    mobile_details_view_array = []
    for object_schema in object_schemas:
        mobile_details_view_array.append(object_schema.mobile_details_view_vendor)
        mobile_details_view_array.append(object_schema.mobile_details_view_operations)
        mobile_details_view_array.append(object_schema.mobile_details_view_client)

    render_overview_page(cfg.CONFLUENCE_OVERVIEW_PAGE_URL_MOBILE_DETAILS, "Mobile Details", mobile_details_view_array)

    email_notifications_array = []
    for object_schema in object_schemas:
        email_notifications_array.extend(object_schema.email_notifications_vendor_array)
        email_notifications_array.extend(object_schema.email_notifications_operations_array)
        email_notifications_array.extend(object_schema.email_notifications_client_array)

    render_overview_page(cfg.CONFLUENCE_OVERVIEW_PAGE_URL_EMAILS, "Email Notifications", email_notifications_array)

    desktop_spotlight_array = []
    for object_schema in object_schemas:
        desktop_spotlight_array.append(object_schema.desktop_spotlight_vendor)
        desktop_spotlight_array.append(object_schema.desktop_spotlight_operations)
        desktop_spotlight_array.append(object_schema.desktop_spotlight_client)

    render_overview_page(cfg.CONFLUENCE_OVERVIEW_PAGE_URL_SPOTLIGHT, "Spotlight", desktop_spotlight_array)
