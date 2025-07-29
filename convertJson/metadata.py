import subprocess
import sys
import importlib.util
import os
import json
import re
import argparse
from collections import defaultdict
from ebooklib import epub

# ANSI codes for terminal colors
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def load_book_metadata(meta_filepath):
    book_metadata = {
        "book_full_title": None,
        "book_author": None,
        "book_synopsis":None,
        "series_name": None,
        "book_category": None,
        "book_language": None
    }

    if os.path.exists(meta_filepath):
        try:
            with open(meta_filepath, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)

                title = loaded_data.get('title')
                authors = loaded_data.get('authors')
                synopsis = loaded_data.get('summary')
                tags = loaded_data.get('tags')
                language = loaded_data.get('language')

                if not any([title, authors, tags, language, synopsis]) and 'novel' in loaded_data:
                    novel_data = loaded_data['novel']
                    title = novel_data.get('title')
                    authors = novel_data.get('authors')
                    synopsis = novel_data.get('summary')
                    tags = novel_data.get('tags')
                    language = novel_data.get('language')

                book_metadata['book_full_title'] = title
                book_metadata['book_author'] = authors[0] if isinstance(authors, list) and authors else None
                book_metadata['book_synopsis'] = synopsis
                book_metadata['series_name'] = title
                book_metadata['book_category'] = tags
                book_metadata['book_language'] = language

                print(f"{GREEN}Book metadata loaded from meta.json:{RESET}")
                for key, value in book_metadata.items():
                    print(f"  DEBUG - {key}: {value}")

        except Exception as e:
            print(f"{RED}Error reading meta.json: {e}{RESET}")
    else:
        print(f"{YELLOW}Warning: meta.json not found. Metadata will be mostly empty.{RESET}")

    return book_metadata