import subprocess
import sys
import importlib.util
import os
import re
import argparse
from collections import defaultdict

def help_parser():
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
    return parser.parse_args()