# Platform Objects Inventory Automation

This project is used to maintain the repository of platform objects in an automated way. It provides scripts and resources to fetch, update, and synchronize platform object definitions, diagrams, and documentation with external systems like Figma and your documentation platform.

## Features

- Automatically extracts and processes platform object schemas.
- Downloads and updates relevant Figma diagrams for each object.
- Syncs documentation and diagrams directly to your documentation pages.
- Ensures the inventory stays up-to-date with minimal manual intervention.

## Usage

To set up and use the automation:

1. **Install dependencies and run:**
   ```bash
   ./run.sh
   ```

2. **Schemas:**  
   Place all your platform object schema files in the `./schemas/` directory.

3. **Documentation and Figma Integration:**  
   The scripts are configured to read API keys and endpoints from the configuration file (see `cfg` references in source). Make sure your environment is set up with the correct API credentials.

## Notes

- Diagrams and files are rendered and temporarily stored before being pushed to the documentation platform.
- The update process can be customized by editing the schema files or the project scripts.

For details on adding new objects or troubleshooting, see comments in `build-objects-inventory.py`.
