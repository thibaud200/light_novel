# config.py

# --- Global path for the files of the Orchestrator ---
ORCHESTRATOR_LOG_FILE_PATH = 'D:\\novel\\orchestrator_log.log'
GLOBAL_ERROR_LOG_FILE_PATH = 'D:\\novel\\global_errors.log'
PROGRESS_LOG_FILE_PATH = 'D:\\novel\\processed_chapters.progress'
GLOBAL_BOOKS_ROOT_DIR = 'D:\\novel'
SCRIPTS_DIR = 'D:\\novel'

# --- Paramèters for the OCR and the treatement for the image ---
OCR_LANGUAGE = 'eng'
MAX_IMAGE_HEIGHT = 10000

# --- Name of the subdirectories (shouldn't be modified) folders are deleted after it is transfer to FINAL_COLLECTED_TEXTS_SUBFOLDER_NAME---
PROCESSED_IMAGES_SUBFOLDER_NAME = 'images_processed'
OUTPUT_TEXT_SUBFOLDER_NAME = 'sortieTXT'
OUTPUT_CLEANED_TEXT_SUBFOLDER_NAME = 'sortieTXT_cleaned'
# --- Name of the final subdirectory for the text files ---
FINAL_COLLECTED_TEXTS_SUBFOLDER_NAME = 'final_texts'

# --- exclusion folder List---
EXCLUDE_DIR_NAMES = {"traiter", "script", "backup", "temp", "sortie", "scripts", "a traiter", "__pycache__"}

# --- Paramèters parallel treatement  ---
MAX_CONCURRENT_CHAPTER_UNITS = 4