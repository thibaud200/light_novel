import subprocess
import sys
import importlib.util
import os
import json
import re
from collections import defaultdict
from ebooklib import epub
from utils import check_and_install_dependencies
from helps import help_parser
from metadata import load_book_metadata
from epub import create_epub_book, create_single_chapter_epub

# ANSI codes for terminal colors
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

# --- Utility functions for EPUB creation ---

def main():
    args = help_parser()

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
    print(f"{YELLOW}######################################################################################")
    print(f"{YELLOW}#        Allows to convert json chapter files from the lightnovel-crawler            #")
    print(f"{YELLOW}#        Allows you to specify how to group the chapters in the volumes              #")
    print(f"{YELLOW}#                                                                                    #")
    print(f"{YELLOW}#        https://github.com/thibaud200/light_novel/tree/main/convertJson             #")
    print(f"{YELLOW}######################################################################################{RESET}")
    check_and_install_dependencies()
    main()