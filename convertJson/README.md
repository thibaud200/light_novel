    
# ConvertJson  : python script that allowes you to convert json files to epub (with metadata)

<b>🚨 **ATTENTION :** this python script works exclusivaly after you got the json files with lightnovel_crowler see : https://github.com/dipu-bd/lightnovel-crawler for the crawler</b>

⚠️ The script doen't use Calibre for the Epub. The code is based on the `EbookLib` library

the script needs the json files from the crawler (the crawler will automaticaly create the right archetecture for the directories and filesà
	- meta.json (in the parent directory)
	- json files on the sub directory "json"

##  1. Prérequities (⚠️ **Important **)

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

## 2. How the scripts work

Input directory hierarchy neeeded (witch is provided by the crawler by default):

```bash
MainDirectoryBook/                                 <-- script root
├── epub/
│   ├── file1-100.epub
│   ├── file101-200.epub
│   ├── file201-300.epub
├── json/
│   ├── volume 01/
│   └── volume 02/
│       ├── 00001.json
|	├── 00002.json
│       └── ...
├── meta.json/
└── conver.jpg
```

The script takes parameters some are mandatory others are not:  

1. Mandatory :
   - `-i, --input_dir INPUT_DIR`
   - `-m, --mode {chapter,volume}`
   - `-b, --boundaries BOUNDARIES` (if mode is volume)
   - `-sb, --simple-boundaries SIMPLE_BOUNDARIES` (if mode is volume)
     
2. Optional  
   - `-u, --merge_unspecified` (if mode is volume)
   - `-o, --output_dir OUTPUT_DIR` (if mode is volume)

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
     
3. commande line example
   
   ### 1. Volume mode
   
   ```bash
   python convertJson.py -i "C:\novel\sortie\Green Skin" -m "volume" -b "{1: [(1, 100)], 2: [(101, 150)], 3: [(201, 350)]}"
   ```
This command takes the parameter after the -i to set the input directory.    
The -m parameter here is set to 'volume' so it need a range parameter here -b.    
Here the -b param here in the :    
     - '1: [(1, 100)]' parameter portion will take the chapters from 1 to 100 and merge them into volume 1   
     - '2: [(101, 150)]' parameter portion will take the chapters from 101 to 150 and merge them into volume 2    
     - ....and so on   
in this example because there's also this : 3: [(201, 350)] then the chapter beetween 151 to 200 will not be integrated / converted into epub if you want them in a epub then you need to add the `-u`    
    - the u parameter will tell the script to take all chapters that are not in the specified range to be taken into account and merge them into a seperate epub file     

```bash
python convertJson.py -i "C:\novel\sortie\Green Skin" -m "volume" -sb "50"
```
This command takes the parameter after the -i to set the input directory.    
The -m parameter here is set to 'volume' so it need a range parameter here -b.    
Here the -sb param here will tell to the script to take by order every 50 chapters and merge them into a volume    

   ### 2. Chapter mode

 ```bash
 python convertJson.py -i "C:\novel\sortie\Green Skin" -m "chapter"
 ```
this will convert each json file into an epub file
