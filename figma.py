#!/usr/bin/env python

from config import Config
import requests
import re

cfg = Config()


class Figma:

    def _get_frame_id_from_url(self, figma_url):

        match = re.search(r'node-id=([\d:-]+)', figma_url)
        if match:
            return match.group(1).replace(':', '%3A')
        return None


    def render_figma_png(self, figma_url, out_filename):

        # print(f"Rendering Figma PNG to file: {out_filename}...")

        file_key_match = re.search(r'figma\.com/(file|proto|design)/([a-zA-Z0-9]+)', figma_url)
        if not file_key_match:
            raise ValueError("Could not extract Figma file key from URL")
        file_key = file_key_match.group(2)
        # print(f"File key: {file_key}")

        node_id = self._get_frame_id_from_url(figma_url)
        if not node_id:
            raise ValueError("Could not extract node-id from URL")
        # print(f"Node ID: {node_id}")

        api_url = f"https://api.figma.com/v1/images/{file_key}?ids={node_id}&format=png&scale=2" # scale x2 for better quality
        headers = {
            "X-Figma-Token": cfg.FIGMA_API_TOKEN
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
        # print(f"Image URL: {image_url}")

        if image_url is None:
            print(f"Rendering failed for {figma_url} - no image URL found. Link is no longer valid?")
            raise ValueError(f"Rendering failed for {figma_url} - no image URL found. Link is no longer valid?")
        
        # Download image
        img_resp = requests.get(image_url)
        img_resp.raise_for_status()
        with open(out_filename, 'wb') as f:
            f.write(img_resp.content)
        
        # print(f"Rendered image saved as {out_filename}")
        return out_filename