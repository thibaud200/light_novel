import os
import json
import re
import math
from urllib.parse import urlparse

# --- Configuration ---
parent_directory = r"C:\novel"
output_file = "incomplets_novel.txt"

# excluded repositories list
excluded_dirs = ['scripts', 'sortie', 'traiter', '__pycache__', 'json', 'archives', 'epub']

# --- Logic of script ---

def get_novel_info(novel_path):
    """
    Gets the essentiel informations form à novel based on meta.json in the novel directory.
    """
    meta_path = os.path.join(novel_path, 'meta.json')
    if not os.path.exists(meta_path):
        return None, None, None
    
    try:
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta_data = json.load(f)
            
            total_chapters = len(meta_data.get('novel', {}).get('chapters', []))
            toc_url = meta_data.get('novel', {}).get('url')
            total_volumes = len(meta_data.get('novel', {}).get('volumes', []))
            
            return total_chapters, toc_url, total_volumes
            
    except Exception as e:
        print(f"Error reading {meta_path}: {e}")
        return None, None, None

def check_epub_completeness(epub_path, total_volumes):
    """
    Checks if all EPUB files expected are present 
    """
    if not os.path.exists(epub_path):
        return False, "The 'epub' directory doesn't exist."
    
    epub_files = [f for f in os.listdir(epub_path) if f.endswith('.epub')]
    
    if len(epub_files) == total_volumes:
        return True, "All EPUB files seems to be present."
    
    return False, f"Number EPUB files found ({len(epub_files)}) doesn't match the total of volume expected ({total_volumes})."

# --- Execution ---
incomplete_novels_urls = []
processed_count = 0

print(f"Start of the check in the directory : {parent_directory}")

for novel_dir in os.listdir(parent_directory):
    novel_path = os.path.join(parent_directory, novel_dir)
    
    # --- Exclusion of repository not welcome ---
    if not os.path.isdir(novel_path) or novel_dir in excluded_dirs:
        continue

    processed_count += 1
    print(f"\n--- Check of : {novel_dir} ---")
    
    total_chapters, toc_url, total_volumes = get_novel_info(novel_path)
    if total_volumes is None or toc_url is None:
        print("meta.json file not found or invalid. Ignored.")
        continue

    epub_path = os.path.join(novel_path, 'epub')
    is_complete, reason = check_epub_completeness(epub_path, total_volumes)
    
    if is_complete:
        print(f"Check success. {novel_dir} is complete.")
    else:
        print(f"Incomplet novel: {reason}")
        incomplete_novels_urls.append(toc_url)

if incomplete_novels_urls:
    with open(output_file, 'w') as f:
        for url in incomplete_novels_urls:
            f.write(f"{url}\n")
    print(f"\Done. {len(incomplete_novels_urls)} Incomplete found. See '{output_file}' for the list.")
else:
    print("\Done. All the novel have been checked and seems complete.")