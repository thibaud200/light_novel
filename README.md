# light_novel OCR to EPUB pipeline (with checkpointing and parallel OCR support)

Python scripts to convert PNG or JPG image files into EPUB files using OCR (Tesseract) and Calibre.  
It's my first real script in Python — I'm more familiar with Java — so I know it can surely be perfected.

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
```

** Mac :**
```bash
brew install tesseract
pip install Pillow
```

** Linux :**
```bash
sudo apt install tesseract-ocr
pip install Pillow
```

---

## 2. How the scripts work

The scripts are divided into two groups:  
1. `orchestrator.py`, `extract_cbz.py`, `split_large_images.py`, `OCR.py`, `clean_ocr_txt.py`  
   → takes the files and converts them to text files (`*.txt`) so they can be managed by Calibre  
2. `epub_orchestrator.py`  
   → takes the text files and processes them with Calibre in command-line mode to convert them into EPUB files

### Group 1: OCR pipeline
Just launch `orchestrator.py`. It handles:

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

## 3. Organisation recommanded for the Folders

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
