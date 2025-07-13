import sys
import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urlparse

# The file name where the links are saved
output_file = "link_novels.txt"

def is_valid_url(url_string):
    """
    Checks if the string provided is a valid URL.
    """
    try:
        result = urlparse(url_string)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def get_links_from_url(list_url):
    """
    Download a web page and extrait the links of novels.
    """
    print(f"Extraction of the links from {list_url}...")
    try:
        response = requests.get(list_url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        novel_links = soup.find_all('a', href=lambda href: href and '/novel/' in href)

        links_set = set()
        for link in novel_links:
            full_url = requests.compat.urljoin(list_url, link['href'])
            links_set.add(full_url)
        
        return links_set

    except requests.exceptions.RequestException as e:
        print(f"Connexion error for {list_url}: {e}")
        return set()

def update_link_file(new_links):
    """
    Updates the file with the links and checks for redondancies.
    """
    existing_links = set()
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            for line in f:
                existing_links.add(line.strip())

    all_links = existing_links.union(new_links)
    
    with open(output_file, 'w') as f:
        sorted_links = sorted(list(all_links))
        for link in sorted_links:
            f.write(f"{link}\n")

    print(f"{len(new_links)} extract links. The files contains {len(all_links)} unique links.")

def process_file(file_path):
    """
    Traite un fichier contenant une liste d'URLs.
    """
    all_extracted_links = set()
    try:
        with open(file_path, 'r') as f:
            urls_to_process = [line.strip() for line in f if line.strip()]
        
        for url in urls_to_process:
            extracted_links = get_links_from_url(url)
            all_extracted_links.update(extracted_links)
        
        if all_extracted_links:
            update_link_file(all_extracted_links)

    except FileNotFoundError:
        print(f"Error: The file '{file_path}' wasn't found.")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please give a URL or a file in argument.")
        print("Exemple (URL): python scraper_liste.py https://www.wuxiabox.com/list/...")
        print("Exemple (File): python scraper_liste.py urls_a_traiter.txt")
        sys.exit(1)

    argument = sys.argv[1]
    
    # Checks if the argument is a URL or a file
    if is_valid_url(argument):
        extracted_links = get_links_from_url(argument)
        if extracted_links:
            update_link_file(extracted_links)
    elif os.path.isfile(argument):
        process_file(argument)
    else:
        print(f"Error: The argument '{argument}' is not a valid URL nor a valid existing.")
        sys.exit(1)