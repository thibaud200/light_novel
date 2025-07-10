# light_novel OCR to EPUB pipeline (with checkpointing and parallel OCR support)

Python scripts to convert PNG or JPG image files into EPUB files using OCR (Tesseract) and Calibre.

---

## 1. Prérequis

1. **Install the following tools and ensure they are in your system's `PATH`**:
   - [Python](https://www.python.org/downloads/)
   - [Calibre](https://calibre-ebook.com/fr/download)
   - [Tesseract OCR](https://github.com/tesseract-ocr/tesseract?tab=readme-ov-file#installing-tesseract) or [https://tesseract-ocr.github.io/tessdoc/Downloads.html](https://tesseract-ocr.github.io/tessdoc/Downloads.html)

Check so that those 3 apps are in the PATH `PATH` (Windows ou other) to simplify the use.

2. **Install dependencies**:
```bash
**Pour Windows :**
pip install Pillow  
pip install pytesseract  
```
```bash
**Pour Mac :**  
brew install tesseract  
brew install Pillow  
```
```bash
** Linux :**
sudo apt install tesseract-ocr  
sudo apt install Pillow
```
## 2. How the scripts works
The scripts can be devided in two groups :  
  1- orchestrator.py + extract_cbz.py + split_large_images.py + OCR.py + clean_ocr_txt.py >>> takes the files and convert them to text files (*.txt) so that they can be manageable by Calibre  
  2- epub_orchestrator.py >>>> takes the text files (*.txt) and throws them at Calibre in command line mode to convert them in epub files  
  
1 => for this group you just need to launch the orchestrator.py files  
  - orchestrator.py : first its going to check if they are previous files that have been convert in text files if so then it won't redo them (info in *.progress file) that will be generated if needed  
  - extract_cbz.py : you may have png or jpg images files that sometimes are in *.cbz archives files if so it will extract the cbz files first  
  - split_large_images.py : sometimes the images files are to big for tesseract so it split them in multiples files so tesseract can manage them  
  - OCR.py : it treats the images files in tesseract so it can be convert in text files of course if there are multiples files for a chapter it will merge them in the same final text file  
  - clean_ocr_txt.py : it's just does a clean on the text file for some eakups  
  
2=> the epub_orchestrator.py : there is no multiple script files  
  - it will verify if the files are already been converted (*.progress file). if so it will skip it  
  - then take the file and add them to calibre (calibredb)  
  - convert them to epub with the convert command  
  - modify the metadata from the epub by taking the directory name as the value for the "Series" name and the chapter number for the index of the file
      =>So each file from the same book will be recognise as such and sorted by chapter number in kavita  
  - then save it to the directory specified   

3. Organisation des répertoires
Assurez-vous que les répertoires sont organisés comme suit :
```bash
|─MainDirectory                                 <-- répertoire pour les scripts
├── MyBook1\                                    <-- répertoire pour un livre
|   └── chapter0001\                            <-- contient les images pour le chapitre
|       ├── 1.png
|   └── chapter0002\                            <-- contient les images pour le chapitre
|   └── chapter0003\                            <-- contient les images pour le chapitre
|       ├── sortieTXT                           <-- DOSSIER TEMP pour la conversion en TXT (sera supprimé à la fin)
|       ├── sortieTXT_cleaned                   <-- DOSSIER TEMP pour la conversion en TXT (sera supprimé à la fin)
|       └── final_texts\                        <-- DOSSIER FINAL pour les fichiers texte
|           ├── Chapter_0001.txt
|           ├── Chapter_0002.txt
|           └── ...
|   └── chapter....\                            <-- contient les images pour le chapitre
├── MyBook2\
│   └── final_texts\
│       ├── Chapter_0001.txt
│       └── ...
│   └── exports_epub\
│       ├── MonNouveauLivre2 - Chapter 0001.epub
│       └── ...
├── sortie\                                     <-- DOSSIER D'EXPORTATION des EPUB après conversion
|   ├── MyBook1\
│       ├── MyBook1 - Chapter 0001.epub
│       ├── MyBook1 - Chapter 0002.epub
│       └── ...
|   ├── MyBook2\
│       ├── MyBook2 - Chapter 0001.epub
│       ├── MyBook2 - Chapter 0002.epub
│       └── ...
├── traiter\                                    <-- DOSSIER EXCLU via config.py
├── script\                                     <-- DOSSIER EXCLU via config.py
├── backup\                                     <-- DOSSIER EXCLU via config.py
├── temp\                                       <-- DOSSIER EXCLU via config.py
├── __pycache__\                                <-- DOSSIER EXCLU via config.py (créé par Python)
```
