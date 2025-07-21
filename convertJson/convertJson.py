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

def check_and_install_dependencies():
    """
    Vérifie si les dépendances nécessaires sont installées et les installe si ce n'est pas le cas.
    """
    required_packages = {
        "ebooklib": "EbookLib", # format: {module_name: package_name_for_pip}
        "lxml": "lxml"          # lxml is an EbookLib dependancy
    }

    print("Checking and installing dependancies if needed...")

    for module_name, package_name in required_packages.items():
        if importlib.util.find_spec(module_name) is None:
            print(f"The dependancy '{package_name}' ({module_name}) was not found. Installation en progress...")
            try:
                # Execute pip for package install
                # sys.executable est le chemin vers l'interpréteur Python en cours d'exécution
                subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
                print(f"'{package_name}' installed with success.")
            except subprocess.CalledProcessError as e:
                print(f"ERREUR : Impossible to install '{package_name}'. Check manual install with 'pip install {package_name}'.")
                print(f"Error details : {e}")
                sys.exit(1)
        else:
            print(f"The dependancy '{package_name}' ({module_name}) is already installed.")

# --- Utility functions for EPUB creation ---

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

def main():
    parser = argparse.ArgumentParser(description="Convert JSON chapters into EPUB volumes or individual files.")
    parser.add_argument("-i", "--input_dir", required=True, help="Path to the main input directory. This directory must contain a 'meta.json' file\n"
             "at its root, and JSON chapter files within its subfolders (e.g., 'volume 01').")
    parser.add_argument("-o", "--output_dir", default=None, help="Path to the directory where merged EPUB files will be saved.\n"
             "By default, the input directory (-i) will be used.")
    parser.add_argument("-m", "--mode", choices=["chapter", "volume"], required=True, help="Conversion mode: \n"
             "  'chapter' : Each JSON file is an individual EPUB.\n"
             "  'volume'  : Chapters are merged into EPUBs by ranges (requires -b or -sb).")
    
    # --- Groupe d'arguments mutuellement exclusifs pour les limites de chapitres ---
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-b", "--boundaries", type=str, default="{}", help="Dictionary of chapter boundaries as a string. \n"
             "Ex: \"{1: [(1, 20)], 2: [(21, 60)]}\". \n"
             "Keys are target volume numbers, values are lists of \n"
             "tuples (start, end) of chapter IDs. \n"
             "Each (start, end) tuple will create a distinct EPUB file. \n"
             "Required in 'volume' mode, mutually exclusive with -sb.")
    group.add_argument("-sb", "--simple-boundaries", type=int, help="Number of chapters per volume. \n"
             "Ex: \"-sb 50\" (means 50 chapters per volume). \n"
             "Required in 'volume' mode, mutually exclusive with -b.")

    parser.add_argument("-u", "--merge_unspecified", action="store_true", help="Optional. If specified, chapters not covered by boundaries \n"
             "(in 'volume' mode) or not included in the filter (in 'chapter' mode) \n"
             "will be merged into a single, separate EPUB file. \n"
             "By default, they are ignored and a warning is displayed.")
    args = parser.parse_args()

    input_dir = args.input_dir
    output_dir = args.output_dir or input_dir
    mode = args.mode
    merge_unspecified = args.merge_unspecified

    # Correction: La recherche de la couverture doit se faire dans input_dir
    possible_cover_names = ['cover.jpg', 'cover.png', 'cover.jpeg']
    cover_filepath = None
    for name in possible_cover_names:
        temp_path = os.path.join(input_dir, name) #
        if os.path.exists(temp_path):
            cover_filepath = temp_path
            break
    
    if cover_filepath:
        print(f"{GREEN}Detected cover file: {cover_filepath}{RESET}")
    else:
        # Warning message if no cover file found in the input_dir
        print(f"{YELLOW}No cover file found in input directory ({input_dir}). Covers will not be added.{RESET}")


    meta_filepath = os.path.join(input_dir, "meta.json")
    book_metadata = load_book_metadata(meta_filepath)
    
    # Load of the chapters ID before calcuating the boundaries
    chapters_by_id = {}
    for root, _, files in os.walk(input_dir):
        for filename in files:
            if filename == "meta.json" or not filename.endswith(".json"):
                continue
            path = os.path.join(root, filename)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if all(k in data for k in ["id", "title", "body"]):
                        chap_id = int(data["id"])
                        chapters_by_id[chap_id] = {
                            "id": chap_id,
                            "title": data["title"],
                            "body": data["body"],
                            "original_filename": filename
                        }
            except Exception as e:
                print(f"{RED}Failed to load {filename}: {e}{RESET}")

    sorted_ids = sorted(chapters_by_id.keys())
    
    # --- boundaries (volume_chapter_boundaries) ---
    volume_chapter_boundaries = {}
    if args.simple_boundaries is not None:
        if mode == "chapter":
            parser.error("--simple-boundaries (-sb) is only valid in 'volume' mode.")

        chapters_per_volume = args.simple_boundaries
        if chapters_per_volume <= 0:
            parser.error("--simple-boundaries (-sb) must be a positive integer.")

        if not sorted_ids:
            print(f"{YELLOW}Warning: No chapters found to apply simple boundaries. No volumes will be created.{RESET}")
        
        current_volume = 1
        for i in range(0, len(sorted_ids), chapters_per_volume):
            start_chap_id = sorted_ids[i]
            end_chap_id_index = min(i + chapters_per_volume - 1, len(sorted_ids) - 1)
            end_chap_id = sorted_ids[end_chap_id_index]
            
            volume_chapter_boundaries[current_volume] = [(start_chap_id, end_chap_id)]
            current_volume += 1
        
        print(f"{GREEN}Simple boundaries generated: {volume_chapter_boundaries}{RESET}")

    else: # if --simple-boundaries is not used, then --boundaries must be used
        try:
            volume_chapter_boundaries = eval(args.boundaries)
            assert isinstance(volume_chapter_boundaries, dict)
            if mode == "volume" and not volume_chapter_boundaries:
                 parser.error("In 'volume' mode, --boundaries (-b) cannot be empty if --simple-boundaries is not used.")
        except Exception as e:
            print(f"{RED}Invalid boundaries format for -b: {e}{RESET}")
            return

    if mode == "volume": # Check coherence of options
        if args.boundaries == "{}" and args.simple_boundaries is None:
            parser.error("In 'volume' mode, either --boundaries (-b) or --simple-boundaries (-sb) must be provided.")
    elif mode == "chapter": # Check coherence of options
        if args.boundaries != "{}" or args.simple_boundaries is not None:
            parser.error("In 'chapter' mode, --boundaries (-b) or --simple-boundaries (-sb) are not applicable. "
                          "They are only used for merging chapters into volumes.")

    processed_ids = set()

    if mode == "chapter":
        print(f"\n{GREEN}Mode: chapter (1 EPUB per file){RESET}")
        ids_to_process = []
        if volume_chapter_boundaries:
            for ranges in volume_chapter_boundaries.values():
                for start, end in ranges:
                    ids_to_process.extend([i for i in sorted_ids if start <= i <= end])
            ids_to_process = sorted(set(ids_to_process))
        else:
            ids_to_process = sorted_ids

        for chap_id in ids_to_process:
            chapter = chapters_by_id[chap_id]
            output_path = os.path.join(output_dir, f"{os.path.splitext(chapter['original_filename'])[0]}.epub")
            if create_single_chapter_epub(chapter, output_path, book_metadata, cover_filepath):
                processed_ids.add(chap_id)

    elif mode == "volume":
        print(f"\n{GREEN}Mode: volume (merge chapters by boundaries){RESET}")
        for vol, ranges in volume_chapter_boundaries.items():
            for start, end in ranges:
                chapters = [chapters_by_id[i] for i in sorted_ids if start <= i <= end]
                if not chapters:
                    continue
                
                series_name_val = book_metadata.get('series_name')
                series_position_val = str(vol) # The volume number is the position (string)
                calibre_series_index_val = float(vol) # Calibre preferes a float

                book_obj, cover_html_page = create_epub_book( # Déstructuration du tuple retourné
                    identifier=f"vol_{vol}_{start}_{end}",
                    title=f"{book_metadata.get('book_full_title')} - Volume {vol} ({start}-{end})",
                    author=book_metadata.get('book_author'),
                    synopsis=book_metadata.get('book_synopsis'),
                    series_name=series_name_val,
                    series_position=series_position_val,
                    calibre_series_index=calibre_series_index_val,
                    category=book_metadata.get('book_category'),
                    language=book_metadata.get('book_language'),
                    cover_path=cover_filepath
                )
                items = []
                
                if cover_html_page:
                    items.append(cover_html_page) # Ajout de la page de couverture en début de items

                for chap in chapters:
                    c = epub.EpubHtml(title=chap["title"], file_name=f"chap_{chap['id']}.xhtml", lang=book_metadata.get('book_language'))
                    c.content = chap["body"]
                    book_obj.add_item(c)
                    items.append(c)
                    processed_ids.add(chap['id'])
                
                book_obj.toc = tuple(items[1:]) if cover_html_page else tuple(items) # Le TOC ne commence généralement pas par la page de couverture
                book_obj.spine = ['nav'] + items
                book_obj.add_item(epub.EpubNcx())
                book_obj.add_item(epub.EpubNav())
                out_path = os.path.join(output_dir, f"volume_{vol}_{start}_{end}.epub")
                try:
                    epub.write_epub(out_path, book_obj, {})
                    print(f"Created: {out_path}")
                except Exception as e:
                    print(f"{RED}Error writing {out_path}: {e}{RESET}")

    unspecified = sorted(set(sorted_ids) - processed_ids)
    if unspecified:
        print(f"{RED}Unspecified chapters: {unspecified}{RESET}")
        if merge_unspecified:
            series_name_val = book_metadata.get('series_name')
            series_position_val = None # Pas de position spécifique pour les non-spécifiés
            calibre_series_index_val = None

            book_obj, cover_html_page = create_epub_book( # Déstructuration du tuple retourné
                identifier="unspecified_chapters",
                title=f"{book_metadata.get('book_full_title')} - Unspecified Chapters",
                author=book_metadata.get('book_author'),
                synopsis=book_metadata.get('book_synopsis'),
                series_name=series_name_val,
                series_position=series_position_val,
                calibre_series_index=calibre_series_index_val,
                category=book_metadata.get('book_category'),
                language=book_metadata.get('book_language'),
                cover_path=cover_filepath
            )
            
            items = []
            if cover_html_page:
                items.append(cover_html_page)

            c = epub.EpubHtml(title="Unspecified Chapters", file_name="unspecified.xhtml", lang=book_metadata.get('book_language'))
            c.content = "\n".join([chapters_by_id[i]['body'] for i in unspecified])
            book_obj.add_item(c)
            items.append(c)
            
            book_obj.toc = tuple(items[1:]) if cover_html_page else tuple(items)
            book_obj.spine = ['nav'] + items
            book_obj.add_item(epub.EpubNcx())
            book_obj.add_item(epub.EpubNav())
            out_path = os.path.join(output_dir, "unspecified_chapters.epub")
            try:
                epub.write_epub(out_path, book_obj, {})
                print(f"{GREEN}Created: {out_path}{RESET}")
            except Exception as e:
                print(f"{RED}Error writing unspecified EPUB: {e}{RESET}")

    print("\nProcess complete.")

if __name__ == "__main__":
    check_and_install_dependencies()
    main()