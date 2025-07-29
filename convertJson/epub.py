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

# Renvoie maintenant un tuple (book, cover_html_page)
def create_epub_book(identifier, title, author, synopsis, series_name, series_position, calibre_series_index, category, language, cover_path):
    book = epub.EpubBook()
    book.set_identifier(identifier)

    if title:
        book.set_title(title)
    if author:
        book.add_author(author)
    if synopsis:
        book.add_metadata('DC', 'description', synopsis)
    if series_name and series_position is not None and calibre_series_index is not None:
        book.add_metadata(
            'OPF', 'meta', series_name,
            {
                'property': 'belongs-to-collection',
                'id': 'series_id'
            }
        )
        book.add_metadata(
            'OPF', 'meta', 'series',
            {
                'refines': '#series_id',
                'property': 'collection-type'
            }
        )
        book.add_metadata(
            'OPF', 'meta', str(series_position),
            {
                'refines': '#series_id',
                'property': 'group-position'
            }
        )
        book.add_metadata(
            None, 'meta', '',
            {
                'name': 'calibre:series',
                'content': series_name
            }
        )
        book.add_metadata(
            None, 'meta', '',
            {
                'name': 'calibre:series_index',
                'content': str(calibre_series_index)
            }
        )

    if category:
        if isinstance(category, list):
            for cat in category:
                 if cat.strip(): book.add_metadata('DC', 'subject', cat.strip())
        elif isinstance(category, str):
            for cat in [c.strip() for c in category.split(',') if c.strip()]:
                book.add_metadata('DC', 'subject', cat)

    if language:
        book.add_metadata('DC', 'language', language)

    cover_item = None
    cover_html_page = None

    if cover_path and os.path.exists(cover_path):
        try:
            with open(cover_path, 'rb') as cover_file:
                cover_data = cover_file.read()

            # set_cover adds the image to the book and to the manifest.
            book.set_cover("cover.jpg", cover_data) 

            print(f"{GREEN}  Cover image '{os.path.basename(cover_path)}' and cover HTML page added.{RESET}")
        except Exception as e:
            print(f"{RED}  Error adding cover image '{os.path.basename(cover_path)}': {e}{RESET}")
    elif cover_path:
        print(f"{YELLOW}  Warning: Cover file not found at '{cover_path}'. Skipping cover.{RESET}")

    return book, cover_html_page

def create_single_chapter_epub(chapter_data, output_path, book_metadata, cover_path):
    epub_file_name_without_ext = os.path.splitext(os.path.basename(output_path))[0]
    identifier = f"chap_{chapter_data['id']}"

    series_name_val = book_metadata.get('series_name')
    series_position_val = chapter_data['id']
    calibre_series_index_val = float(chapter_data['id'])

    book_obj, cover_html_page = create_epub_book(
        identifier=identifier,
        title=epub_file_name_without_ext,
        author=book_metadata.get('book_author'),
        synopsis=book_metadata.get('book_synopsis'),
        series_name=series_name_val,
        series_position=series_position_val,
        calibre_series_index=calibre_series_index_val,
        category=book_metadata.get('book_category'),
        language=book_metadata.get('book_language'),
        cover_path=cover_path
    )

    c = epub.EpubHtml(title=chapter_data['title'], file_name=f"chap_{chapter_data['id']}.xhtml", lang=book_metadata.get('book_language'))
    c.content = chapter_data['body']
    book_obj.add_item(c)

    spine_items = ['nav']
    if cover_html_page:
        spine_items.append(cover_html_page) # Ajout de la page de couverture en début de spine

    spine_items.append(c)

    book_obj.toc = (c,)
    book_obj.spine = spine_items
    book_obj.add_item(epub.EpubNcx())
    book_obj.add_item(epub.EpubNav())

    try:
        epub.write_epub(output_path, book_obj, {})
        print(f"  Individual EPUB created: {os.path.basename(output_path)}")
        return True
    except Exception as e:
        print(f"{RED}  Error creating EPUB for chapter {chapter_data['id']}: {e}{RESET}")
        return False