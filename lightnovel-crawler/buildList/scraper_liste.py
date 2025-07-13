import sys
import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urlparse, urlunparse, urljoin

def is_valid_url(url_string):
    """
    Checks if the provided string is a valid URL.
    """
    try:
        result = urlparse(url_string)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def get_links_from_url(list_url, link_pattern):
    """
    Downloads a web page and extracts novel links based on a pattern.
    """
    print(f"Extracting links from {list_url}...")
    try:
        response = requests.get(list_url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        
        novel_links = soup.find_all('a', href=lambda href: href and link_pattern in href)

        links_set = set()
        for link in novel_links:
            full_url = requests.compat.urljoin(list_url, link['href'])
            links_set.add(full_url)
        
        return links_set

    except requests.exceptions.RequestException as e:
        print(f"Connection error for {list_url}: {e}")
        return set()

def update_link_file(new_links, output_path):
    """
    Updates the link file by adding new unique links and removing duplicates.
    """
    existing_links = set()
    if os.path.exists(output_path):
        with open(output_path, 'r') as f:
            for line in f:
                existing_links.add(line.strip())

    all_links = existing_links.union(new_links)
    
    with open(output_path, 'w') as f:
        sorted_links = sorted(list(all_links))
        for link in sorted_links:
            f.write(f"{link}\n")

    print(f"{len(new_links)} links extracted. The file now contains {len(all_links)} unique links.")

def process_paginated_url(base_url, link_pattern, output_path):
    """
    Processes a paginated URL by looping through all pages.
    """
    all_extracted_links = set()
    page_number = 0
    while True:
        current_url = base_url.replace('-0.html', f'-{page_number}.html')
        
        print(f"Processing page: {current_url}")
        extracted_links = get_links_from_url(current_url, link_pattern)

        if not extracted_links:
            print("No new links found on this page. Ending pagination.")
            break
        
        all_extracted_links.update(extracted_links)
        page_number += 1
        
    if all_extracted_links:
        update_link_file(all_extracted_links, output_path)

def process_file(file_path, link_pattern, output_path):
    """
    Processes a file containing a list of URLs.
    """
    all_extracted_links = set()
    try:
        with open(file_path, 'r') as f:
            urls_to_process = [line.strip() for line in f if line.strip()]
        
        for url in urls_to_process:
            extracted_links = get_links_from_url(url, link_pattern)
            all_extracted_links.update(extracted_links)
        
        if all_extracted_links:
            update_link_file(all_extracted_links, output_path)

    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide a URL or a file path as an argument.")
        print("Example (URL): python scraper_liste.py https://www.wuxiabox.com/list/... --output-file=links.txt")
        print("Example (File): python scraper_liste.py urls_to_process.txt --output-file=links.txt")
        sys.exit(1)

    argument = sys.argv[1]
    
    link_pattern = '/novel/'  # Default pattern
    output_file = "link_novels.txt"  # Default output filename
    
    # Handle optional arguments
    if len(sys.argv) > 2:
        if '--pattern' in sys.argv:
            try:
                link_pattern = sys.argv[sys.argv.index('--pattern') + 1]
            except IndexError:
                print("Error: The '--pattern' flag requires an argument.")
                sys.exit(1)
        if '--output-file' in sys.argv:
            try:
                output_file = sys.argv[sys.argv.index('--output-file') + 1]
            except IndexError:
                print("Error: The '--output-file' flag requires an argument.")
                sys.exit(1)

    if '-0.html' in argument:
        process_paginated_url(argument, link_pattern, output_file)
    elif is_valid_url(argument):
        extracted_links = get_links_from_url(argument, link_pattern)
        if extracted_links:
            update_link_file(extracted_links, output_file)
    elif os.path.isfile(argument):
        process_file(argument, link_pattern, output_file)
    else:
        print(f"Error: The argument '{argument}' is not a valid URL or an existing file.")
        sys.exit(1)