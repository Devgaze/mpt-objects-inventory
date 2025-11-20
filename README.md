# SoftwareOne Marketplace — Objects Inventory

This tool generates and maintains the visual inventory of platform objects for the SoftwareOne Marketplace Platform. It renders object views from Figma, uploads images to Confluence, and updates object pages and a summary page automatically.

- Object definitions live in `schemas/*.json`
- Images and HTML previews are written to `build/`
- Confluence pages are updated in place

## What it does

- Renders PNGs from Figma for each object view (desktop, mobile, infocards, settings) and the state diagram.
- Uploads or replaces the images as attachments on each object’s Confluence page.
- Regenerates each object page body using HTML templates.
- Regenerates the global summary page with per-object status and links.

## Install and run

Fast path:

```bash
./run.sh
```

On each run you will see six phases:

1) Initialize schemas 
2) Render Figma images
3) Remove existing page attachments
4) Upload images
5) Update object pages
6) Update summary page

## Schemas

Place object schema files in `./schemas/` (one per object). Minimal required fields:

- Empty strings are treated as “not defined”.
- Each non-empty value must be a Figma URL containing `file/proto/design/<fileKey>` and `node-id=`; the renderer extracts both to request PNGs from Figma.

## Output

- `build/<Object Name>/...png` — all rendered images
- `build/<Object Name>/object-page.html` — the HTML used to update the object’s Confluence page
- `build/summary-page.html` — the HTML used to update the global summary page

If the new HTML matches the current Confluence content (normalized), the update is skipped.

## Confluence and templates

HTML bodies are generated from templates in `confluence-templates/`:

- `object-page.html` — full object page layout
- `roles-table.html`, `single-table.html` — reusable table fragments for roles (vendor, operations, client)
- `multitable.html`, `multitable-row.html` — generic multi-row table
- `summary-page.html`, `summary-table-row.html` — global summary page

Attachments are fully replaced on each run to ensure a consistent, up-to-date page. Pages are forced to “full width.”

## Context

The Marketplace Platform is API-first and serves three account types: Vendors, Operations, and Clients. For broader platform terms and APIs, see the public docs at `https://docs.platform.softwareone.com`.
