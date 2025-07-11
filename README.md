# light_novel convert Image files to EPUB (with checkpointing and parallel OCR support) (the images files must contain only text to ensure it works)

just a reminder : I have only tested it on Windows environnement, but should work on the others

Python scripts to convert PNG or JPG image files into EPUB files using OCR (Tesseract) and Calibre.  
It's my first real script in Python — I'm more familiar with Java — so I know it can surely be perfected.

##  Future Roadmap
### GUI Improvements
   - EPUB Button: Add a button to the GUI to launch the epub_orchestrator.py script directly after the OCR phase.(most likeliy a new tab)

### script Improvement
   - Centralized Configuration: Integrate the settings of epub_orchestrator.py into a dedicated configuration file, making all paths and tools configurable via the interface.
   - Full Localization: Apply the same localization system (get_translator()) to the epub_orchestrator.py script to make its messages translatable.

---

## 1. Prérequities

1. **Install the following tools and ensure they are in your system's `PATH`**:
   - [Python](https://www.python.org/downloads/)
   - [Calibre](https://calibre-ebook.com/fr/download)
   - [Tesseract OCR](https://github.com/tesseract-ocr/tesseract?tab=readme-ov-file#installing-tesseract) or [https://tesseract-ocr.github.io/tessdoc/Downloads.html](https://tesseract-ocr.github.io/tessdoc/Downloads.html)

Make sure these 3 apps are in your system's `PATH` (Windows or other OS) to simplify usage.

2. **Install dependencies**:

** Windows :**
```bash
pip install Pillow
pip install pytesseract
pip install localization
pip install numpy
pip install scipy
pip install shapely
```

** Mac :**
```bash
brew install tesseract
brew install Pillow
brew install localization
brew install numpy
brew install scipy
brew install shapely
```

** Linux :**
```bash
sudo apt install tesseract-ocr
sudo apt install Pillow
sudo apt install localization
sudo apt install numpy
sudo apt install scipy
sudo apt install shapely
```

---

## 2. How the scripts work

The scripts are divided into two groups:  
1. `orchestrator.py`, `extract_cbz.py`, `split_large_images.py`, `OCR.py`, `clean_ocr_txt.py`  
   → takes the files and converts them to text files (`*.txt`) so they can be managed by Calibre
   To launch the script you just need to go where the scripts are and type :
   ```bash
   python orchestrator.py
   ```
3. `epub_orchestrator.py`  
   → takes the text files and processes them with Calibre in command-line mode to convert them into EPUB files
   To launch the script you just need to go where the scripts are and type :
   ```bash
   python epub_orchestrator.py
   ```

### Group 1: OCR pipeline
Just launch `orchestrator.py`. It handles:

- `config.py`: it's the config file for the scripts in Group 1
- `orchestrator.py`: Checks for existing `.txt` files. If already converted (tracked via `.progress`), it skips them.
- `extract_cbz.py`: Extracts `.cbz` files if your images are archived.
- `split_large_images.py`: Splits oversized images into smaller ones so Tesseract can process them.
- `OCR.py`: Runs OCR via Tesseract and merges multiple images for one chapter into a single `.txt` file.
- `clean_ocr_txt.py`: Cleans up common OCR issues and artifacts.

### Group 2: EPUB conversion

Run `epub_orchestrator.py`. It:

- Skips files already converted (tracked via `.progress`)
- Adds text files to Calibre using `calibredb`
- Converts them to EPUB with `ebook-convert`
- Sets metadata:
  - **Series name** = name of the parent directory
  - **Series index** = chapter number
  → Ensures correct series grouping and order in apps like Kavita
- Saves final EPUBs to the configured directory

---
## 3. Configuration Interface (Optional)
In addition to launching via the command line, you can use the graphical interface to configure and launch the orchestrator.py script in a user-friendly manner. The interface is an independent script located in the  subdirectory "interface".

### Interface Features
- Ease of Use : Modify access paths and settings without having to touch the code.

- Localization : The interface is capable of automatically detecting your system's language and displaying messages in French or English(English by defaut if no local language find).

- Project Organization : The interface and its localization files are grouped in an interface/ subdirectory to maintain a clean project tree.

### Using the Interface
1. Launch the Interface :
Execute the script from the project root, specifying its relative path :
```bash
Bash

python interface/ConvertImageToTXT.py
```
2. Configure and Launch :
The interface will open, allowing you to modify the settings. Once your changes are made, you can either save them or launch the orchestrator process directly.

---
## 4. Organisation recommanded for the Folders where are the files that need to be converted
The scripts can be in another folder or subfolder : just don't forget to modify le path for it ^^

Make sure the directories are organised like this:

```
MainDirectory/                                 <-- script root
├── MyBook1/                                   <-- one book
│   ├── chapter0001/                           <-- contains images
│   │   └── 1.png
│   ├── chapter0002/
│   ├── chapter0003/
│   │   ├── sortieTXT/                         <-- temp folder (auto-deleted)
│   │   ├── sortieTXT_cleaned/                 <-- temp folder (auto-deleted)
│   │   └── final_texts/                       <-- final TXT output
│   │       ├── Chapter_0001.txt
│   │       ├── Chapter_0002.txt
│   │       └── ...
│   └── ...
├── MyBook2/
│   ├── final_texts/
│   └── exports_epub/
│       ├── MyBook2 - Chapter 0001.epub
│       └── ...
├── sortie/                                    <-- final EPUB export
│   ├── MyBook1/
│   │   ├── MyBook1 - Chapter 0001.epub
│   │   ├── MyBook1 - Chapter 0002.epub
│   ├── MyBook2/
│       ├── MyBook2 - Chapter 0001.epub
│       ├── MyBook2 - Chapter 0002.epub
├── traiter/                                   <-- excluded via config.py
├── script/                                    <-- excluded via config.py
├── backup/                                    <-- excluded via config.py
├── temp/                                      <-- excluded via config.py
└── __pycache__/                               <-- excluded via config.py (created by Python)
```

---

✅ Everything is checkpointed with `.progress` files, and processing can be done in parallel per chapter where needed.
