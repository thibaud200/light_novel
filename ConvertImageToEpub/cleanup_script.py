import os
import shutil
import datetime
import config
import sys

# Importation du module de localisation
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from localization.main import get_translator
_ = get_translator()

# --- CONFIGURATION (DOIT CORRESPONDRE À orchestrator.py) ---
GLOBAL_BOOKS_ROOT_DIR = config.GLOBAL_BOOKS_ROOT_DIR

PROCESSED_IMAGES_SUBFOLDER_NAME = config.PROCESSED_IMAGES_SUBFOLDER_NAME
OUTPUT_TEXT_SUBFOLDER_NAME = config.OUTPUT_TEXT_SUBFOLDER_NAME
OUTPUT_CLEANED_TEXT_SUBFOLDER_NAME = config.OUTPUT_CLEANED_TEXT_SUBFOLDER_NAME
FINAL_COLLECTED_TEXTS_SUBFOLDER_NAME = config.FINAL_COLLECTED_TEXTS_SUBFOLDER_NAME

EXCLUDE_DIR_NAMES = config.EXCLUDE_DIR_NAMES
DELETE_UNZIPPED_FOLDERS = False 
CLEANUP_LOG_FILE = os.path.join(GLOBAL_BOOKS_ROOT_DIR, 'cleanup_log.log')

def log_cleanup_message(message, level="INFO"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] [{level}] {message}"
    os.makedirs(os.path.dirname(CLEANUP_LOG_FILE), exist_ok=True)
    with open(CLEANUP_LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_message + '\n')
    print(log_message)

def clean_folder(folder_path):
    if os.path.exists(folder_path):
        try:
            shutil.rmtree(folder_path)
            log_cleanup_message(_('FOLDER_DELETED_CLEANUP').format(os.path.basename(folder_path)))
            return True
        except Exception as e:
            log_cleanup_message(_('ERROR_DELETING_FOLDER_CLEANUP').format(os.path.basename(folder_path), e), "ERROR")
            return False
    else:
        log_cleanup_message(_('FOLDER_NOT_FOUND_CLEANUP').format(os.path.basename(folder_path)), "INFO")
        return False

def natsort_key(s):
    import re
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

# --- Processus principal de nettoyage ---
if __name__ == "__main__":
    log_cleanup_message(_('START_CLEANUP_SCRIPT'))
    log_cleanup_message(_('ROOT_DIR_TO_CLEAN').format(GLOBAL_BOOKS_ROOT_DIR))
    log_cleanup_message(_('DELETE_UNZIPPED_ENABLED').format(DELETE_UNZIPPED_FOLDERS))

    if os.path.exists(CLEANUP_LOG_FILE):
        os.remove(CLEANUP_LOG_FILE)

    all_excluded_by_name = EXCLUDE_DIR_NAMES.union({FINAL_COLLECTED_TEXTS_SUBFOLDER_NAME.lower()})

    processed_count = 0
    skipped_count = 0

    for book_folder_name in sorted(os.listdir(GLOBAL_BOOKS_ROOT_DIR), key=natsort_key):
        book_folder_path = os.path.join(GLOBAL_BOOKS_ROOT_DIR, book_folder_name)

        if not os.path.isdir(book_folder_path):
            log_cleanup_message(_('IGNORED_NON_DIR_CLEANUP').format(book_folder_name), "INFO")
            skipped_count += 1
            continue

        if book_folder_name.lower() in all_excluded_by_name:
            log_cleanup_message(_('IGNORED_EXCLUDED_DIR_CLEANUP').format(book_folder_name), "INFO")
            skipped_count += 1
            continue

        log_cleanup_message(f"\n=========================================================")
        log_cleanup_message(_('CLEANING_BOOK_FOLDER').format(book_folder_name))
        log_cleanup_message(f"=========================================================")

        clean_folder(os.path.join(book_folder_path, PROCESSED_IMAGES_SUBFOLDER_NAME))
        clean_folder(os.path.join(book_folder_path, OUTPUT_TEXT_SUBFOLDER_NAME))
        clean_folder(os.path.join(book_folder_path, OUTPUT_CLEANED_TEXT_SUBFOLDER_NAME))

        for chapter_item_name in sorted(os.listdir(book_folder_path), key=natsort_key):
            chapter_item_path = os.path.join(book_folder_path, chapter_item_name)

            if not os.path.isdir(chapter_item_path):
                continue

            if chapter_item_name.lower() in all_excluded_by_name:
                log_cleanup_message(_('IGNORED_SYSTEM_SUBFOLDER_CLEANUP').format(chapter_item_name), "INFO")
                continue

            log_cleanup_message(_('PROCESSING_CHAPTER_UNIT').format(chapter_item_name))
            
            clean_folder(os.path.join(chapter_item_path, PROCESSED_IMAGES_SUBFOLDER_NAME))
            clean_folder(os.path.join(chapter_item_path, OUTPUT_TEXT_SUBFOLDER_NAME))
            clean_folder(os.path.join(chapter_item_path, OUTPUT_CLEANED_TEXT_SUBFOLDER_NAME))

            if DELETE_UNZIPPED_FOLDERS and chapter_item_name.lower().endswith('_unzipped'):
                log_cleanup_message(_('DELETING_UNZIPPED_FOLDER').format(chapter_item_name))
                clean_folder(chapter_item_path)
        
        processed_count += 1

    log_cleanup_message(f"\n--- {_('CLEANUP_FINISHED')} ---")
    log_cleanup_message(_('TOTAL_PROCESSED_FOLDERS').format(processed_count))
    log_cleanup_message(_('TOTAL_SKIPPED_FOLDERS').format(skipped_count))
    log_cleanup_message(_('CHECK_LOG_DETAILS').format(CLEANUP_LOG_FILE))