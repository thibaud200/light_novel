# light_novel
python code to convert png or jpg images files to epub files

first you'll need to install : 
  - python from the donload page : https://www.python.org/downloads/ 
  - calibre from the calibre site : https://calibre-ebook.com/fr/download 
  - tesseract from the site : https://github.com/tesseract-ocr/tesseract?tab=readme-ov-file#installing-tesseract or https://tesseract-ocr.github.io/tessdoc/Downloads.html 

Make sure that all the 3 apps above are in the PATH(windows or ather) so it's easier 
 
Then you need to install the dependencies : 
  For windows :
  - pip install Pillow
  - pip install pytesseract

For Mac :
  - brew install tesseract
  - brew install Pillow

For linux :
  - sudo apt install tesseract-ocr
  - sudo apt install Pillow

les scripts se décomposent en deux groupes :  
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
  - then save it to the directory specified   
  
