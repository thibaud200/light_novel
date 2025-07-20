      - convertJson : python script that works exclusivaly after you got the json files with lightnovel_crowler see : https://github.com/dipu-bd/lightnovel-crawler for the crawler
========================================================================================================================================================================================

# ConvertJson  : python script that allowes you to convert json files to epub (with metadata)

the script needs the json files from the crawler
	- meta.json (in the parent directory
	- json files on the sub directory "json"

## 1. Prérequities

1. **Install the following tools and ensure they are in your system's `PATH`**:
   - [Python](https://www.python.org/downloads/)

2. **Install dependencies**:

** Windows :**
```bash
pip install lxml
pip install EbookLib
```

** Mac :**
```bash
brew install lxml
brew install EbookLib
```

** Linux :**
```bash
sudo apt install lxml
sudo apt install EbookLib
```
theres a help section in the script 

```bash
python convertJson.py -h
usage: convertJson.py [-h] -i INPUT_DIR [-o OUTPUT_DIR] -m {chapter,volume} [-b BOUNDARIES | -sb SIMPLE_BOUNDARIES]
                      [-u]

Convert JSON chapters into EPUB volumes or individual files.

options:
  -h, --help            show this help message and exit
  -i, --input_dir INPUT_DIR
                        Path to the main input directory. This directory must contain a 'meta.json' file at its root,
                        and JSON chapter files within its subfolders (e.g., 'volume 01').
  -o, --output_dir OUTPUT_DIR
                        Path to the directory where merged EPUB files will be saved. By default, the input directory
                        (-i) will be used.
  -m, --mode {chapter,volume}
                        Conversion mode: 'chapter' : Each JSON file is an individual EPUB. 'volume' : Chapters are
                        merged into EPUBs by ranges (requires -b or -sb).
  -b, --boundaries BOUNDARIES
                        Dictionary of chapter boundaries as a string. Ex: "{1: [(1, 20)], 2: [(21, 60)]}". Keys are
                        target volume numbers, values are lists of tuples (start, end) of chapter IDs. Each (start,
                        end) tuple will create a distinct EPUB file. Required in 'volume' mode, mutually exclusive
                        with -sb.
  -sb, --simple-boundaries SIMPLE_BOUNDARIES
                        Number of chapters per volume. Ex: "-sb 50" (means 50 chapters per volume). Required in
                        'volume' mode, mutually exclusive with -b.
  -u, --merge_unspecified
                        Optional. If specified, chapters not covered by boundaries (in 'volume' mode) or not included
                        in the filter (in 'chapter' mode) will be merged into a single, separate EPUB file. By
                        default, they are ignored and a warning is displayed.
``` 