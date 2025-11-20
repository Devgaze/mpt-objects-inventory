#! /usr/bin/env python3

import os
import re
from datetime import datetime

def populate_multitable_template(multitable_template, multitable_row_template, schema_values_array):

    if schema_values_array is None or len(schema_values_array) == 0:
        return '<p>Not defined</p>'

    def get_header_value(schema_record):
        if schema_record:
            _title = schema_record.title
            if _title is None:
                _title = schema_record.parent.object_name

            return f'<td data-highlight-colour="#f4f5f7"><p style="text-align: center;"><a href="{schema_record.figma_link}"><strong>{_title}</strong></a></p></td>'
        return '<td data-highlight-colour="#f4f5f7"></td>'

    def get_cell_value(schema_record):
        if schema_record is None:
            return '<td></td>'

        base_filename = os.path.basename(schema_record.filename)
        return f'<td><ac:image ac:align="center" ac:alt="{base_filename}" ac:custom-width="true" ac:layout="center" ac:original-height="3082" ac:original-width="1888" ac:width="343"><ri:attachment ri:filename="{base_filename}"></ri:attachment></ac:image></td>'

    multitable_rows = ""
    for i in range(0, len(schema_values_array), 5):
        block = schema_values_array[i:i+5]
        template_data = {
            '{{cell11}}': get_header_value(block[0] if len(block) > 0 else None),
            '{{cell12}}': get_header_value(block[1] if len(block) > 1 else None),
            '{{cell13}}': get_header_value(block[2] if len(block) > 2 else None),
            '{{cell14}}': get_header_value(block[3] if len(block) > 3 else None),
            '{{cell15}}': get_header_value(block[4] if len(block) > 4 else None),

            '{{cell21}}': get_cell_value(block[0] if len(block) > 0 else None),
            '{{cell22}}': get_cell_value(block[1] if len(block) > 1 else None),
            '{{cell23}}': get_cell_value(block[2] if len(block) > 2 else None),
            '{{cell24}}': get_cell_value(block[3] if len(block) > 3 else None),
            '{{cell25}}': get_cell_value(block[4] if len(block) > 4 else None),
        }
        multitable_rows += populate_template(multitable_row_template, template_data)

    multitable_template = multitable_template.replace('{{multitable-rows}}', multitable_rows)
    return multitable_template


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


def read_file(filename):
    # Make filename relative to the location of this module
    module_dir = os.path.dirname(__file__)
    filename = os.path.join(module_dir, filename)
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read()


def get_timestamp():
    return datetime.now().strftime("%b %d, %Y at %H:%M:%S")