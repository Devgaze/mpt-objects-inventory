from config import Config

from confluence import Confluence
from schema import SchemaRecord
from util import populate_template, read_file

cfg = Config()
confluence = Confluence()

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
                <p style="text-align: center;"><ac:emoticon ac:emoji-fallback="❌" ac:emoji-id="atlassian-cross_mark" ac:emoji-shortname=":cross_mark:" ac:name="cross"></ac:emoticon> <span style="color: rgb(191,38,0);">Error</span></p>
            '''

        return f'''
            <p style="text-align: center;"><ac:emoticon ac:emoji-fallback="✅" ac:emoji-id="2705" ac:emoji-shortname=":white_check_mark:" ac:name="blue-star"></ac:emoticon> <a href="{schema_record.figma_link}">Figma</a></p>
        '''


    def populate_notifications_count(object_schema):
        count = len(object_schema.email_notifications_vendor_array) + len(object_schema.email_notifications_operations_array) + len(object_schema.email_notifications_client_array)
        if count == 0:
            return '<p style="text-align: center;"><span style="color: rgb(200,200,200);">—</span></p>'
        return f'<p style="text-align: center;"><strong>{count}</strong></p>'

    summary_table_row_template = read_file("confluence-templates/summary-table-row.html")

    object_rows = []

    object_number = 0
    for object_schema in sorted(object_schemas, key=lambda x: x.object_name.lower()):

        object_number += 1
        placeholders = {
            '{{object-number}}': object_number,
            '{{object-details-link}}': f'''<p><ac:link><ri:page ri:content-title="{object_schema.confluence_page_title}"></ri:page><ac:link-body><strong>{object_schema.object_name}</strong></ac:link-body></ac:link></p>''',
            '{{state-diagram-link}}': populate_cell(object_schema.state_diagram),
            
            '{{object-desktop-grid-vendor-link}}': populate_cell(object_schema.desktop_grid_view_vendor),
            '{{object-desktop-grid-operations-link}}': populate_cell(object_schema.desktop_grid_view_operations),
            '{{object-desktop-grid-client-link}}': populate_cell(object_schema.desktop_grid_view_client),
            
            '{{object-desktop-details-vendor-link}}': populate_cell(object_schema.desktop_details_view_vendor),
            '{{object-desktop-details-operations-link}}': populate_cell(object_schema.desktop_details_view_operations),
            '{{object-desktop-details-client-link}}': populate_cell(object_schema.desktop_details_view_client),
            
            '{{object-desktop-infocard-vendor-link}}': populate_cell(object_schema.desktop_infocard_view_vendor),
            '{{object-desktop-infocard-operations-link}}': populate_cell(object_schema.desktop_infocard_view_operations),
            '{{object-desktop-infocard-client-link}}': populate_cell(object_schema.desktop_infocard_view_client),
            
            '{{object-mobile-list-vendor-link}}': populate_cell(object_schema.mobile_list_view_vendor),
            '{{object-mobile-list-operations-link}}': populate_cell(object_schema.mobile_list_view_operations),
            '{{object-mobile-list-client-link}}': populate_cell(object_schema.mobile_list_view_client),

            '{{object-mobile-details-vendor-link}}': populate_cell(object_schema.mobile_details_view_vendor),
            '{{object-mobile-details-operations-link}}': populate_cell(object_schema.mobile_details_view_operations),
            '{{object-mobile-details-client-link}}': populate_cell(object_schema.mobile_details_view_client),

            '{{object-email-notifications-count}}': populate_notifications_count(object_schema),

            '{{object-desktop-spotlight-vendor-link}}': populate_cell(object_schema.desktop_spotlight_vendor),
            '{{object-desktop-spotlight-operations-link}}': populate_cell(object_schema.desktop_spotlight_operations),
            '{{object-desktop-spotlight-client-link}}': populate_cell(object_schema.desktop_spotlight_client),
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