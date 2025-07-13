import os
import re
from PIL import Image
import pytesseract
import datetime
import argparse
import config
import sys

# Importation du module de localisation
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from localization.main import get_translator
_ = get_translator()

# Configuration spécifique à ce script
OCR_LANGUAGE = config.OCR_LANGUAGE

parser = argparse.ArgumentParser(description=_('SCRIPT_DESCRIPTION'))
parser.add_argument('--chapter_unit', type=str, required=True,
                    help=_('CHAPTER_UNIT_HELP'))
args = parser.parse_args()
CHAPTER_UNIT_DIR = args.chapter_unit

PROCESSED_IMAGES_SUBFOLDER_NAME = config.PROCESSED_IMAGES_SUBFOLDER_NAME
BASE_INPUT_DIR = os.path.join(CHAPTER_UNIT_DIR, PROCESSED_IMAGES_SUBFOLDER_NAME)

OUTPUT_TEXT_SUBFOLDER_NAME = config.OUTPUT_TEXT_SUBFOLDER_NAME
OUTPUT_DIR = os.path.join(CHAPTER_UNIT_DIR, OUTPUT_TEXT_SUBFOLDER_NAME)

ERROR_LOG_FILE = os.path.join(CHAPTER_UNIT_DIR, 'ocr_errors.log') 

def log_error(message, image_name="N/A", level="ERROR"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] [{_('UNITÉ_CHAPITRE')}: {os.path.basename(CHAPTER_UNIT_DIR)}] [{_('IMAGE')}: {image_name}] {level}: {message}"
    
    with open(ERROR_LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_message + '\n')
    print(f"  {log_message}")

# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
    print(_('OUTPUT_FOLDER_CREATED').format(OUTPUT_DIR))

if os.path.exists(ERROR_LOG_FILE):
    os.remove(ERROR_LOG_FILE)
    print(_('PREVIOUS_LOG_DELETED').format(ERROR_LOG_FILE))

print(_('START_OCR').format(os.path.basename(CHAPTER_UNIT_DIR)))
print(_('TEXT_FILES_SAVED').format(OUTPUT_DIR))
print(_('OCR_LANGUAGE').format(OCR_LANGUAGE))


if not os.path.exists(BASE_INPUT_DIR):
    log_error(_('INPUT_FOLDER_NOT_FOUND').format(PROCESSED_IMAGES_SUBFOLDER_NAME), "N/A")
else:
    all_png_files_in_subdir = [f for f in os.listdir(BASE_INPUT_DIR) if f.lower().endswith('.png')]
    
    chapter_images = []
    excluded_original_files = [] 
    
    for f in all_png_files_in_subdir:
        if not f.lower().endswith('_original.png'):
            chapter_images.append(f)
        else:
            excluded_original_files.append(f)

    chapter_images.sort()

    if excluded_original_files:
        print(_('IGNORED_ORIGINAL_FILES').format(', '.join(excluded_original_files)))
    print(_('PNG_FILES_TO_PROCESS').format(os.path.basename(CHAPTER_UNIT_DIR), chapter_images))

    if not chapter_images:
        log_error(_('NO_PNG_FILES_FOUND').format(PROCESSED_IMAGES_SUBFOLDER_NAME), "N/A")
    else:
        full_extracted_text_for_chapter = []

        for img_filename in chapter_images:
            current_image_path = os.path.join(BASE_INPUT_DIR, img_filename)
            try:
                img = Image.open(current_image_path)
                
                config_tesseract = '--dpi 300 --psm 3 --oem 3' 
                extracted_text_segment = pytesseract.image_to_string(img, lang=OCR_LANGUAGE, config=config_tesseract)
                
                full_extracted_text_for_chapter.append(extracted_text_segment)
                print(_('OCR_SUCCESS').format(img_filename))

            except pytesseract.TesseractNotFoundError:
                log_error(_('TESSERACT_NOT_FOUND'), img_filename, level="CRITICAL")
                full_extracted_text_for_chapter.append(f"\n[{_('CRITICAL_TESSERACT_ERROR')}]\n")
                break
            except Exception as e:
                log_error(_('UNEXPECTED_PROCESSING_ERROR').format(e), img_filename, level="ERROR")
                full_extracted_text_for_chapter.append(f"\n[{_('OCR_SEGMENT_ERROR')}: {e}]\n")
                
        extracted_text = "\n\n".join(full_extracted_text_for_chapter)

        unit_base_name = os.path.basename(CHAPTER_UNIT_DIR)

        unit_base_name = unit_base_name.replace('_unzipped', '')
        
        chapter_num_match = re.match(r'^(?:Chapter\s*)?(\d+)\s*(?:[ -]+)?(.*)$', unit_base_name, re.IGNORECASE)

        formatted_chapter_number_str = ""
        raw_title_part = ""

        if chapter_num_match:
            chapter_number_int = int(chapter_num_match.group(1))
            formatted_chapter_number_str = f"{chapter_number_int:04d}"
            raw_title_part = chapter_num_match.group(2).strip()
        else:
            log_error(_('CHAPTER_NUMBER_NOT_FOUND').format(unit_base_name), "N/A", level="WARNING")
            raw_title_part = unit_base_name

        cleaned_title_part = re.sub(r'^(?:Chapter\s*\d+\s*[ -]+\s*)*', '', raw_title_part, flags=re.IGNORECASE).strip()
        cleaned_title_part = re.sub(r'[\\/:*?"<>|]', '', cleaned_title_part)
        cleaned_title_part = re.sub(r'[ -]+', '_', cleaned_title_part)
        cleaned_title_part = cleaned_title_part.strip('_')

        if formatted_chapter_number_str:
            output_filename_base = f"Chapter_{formatted_chapter_number_str}_{cleaned_title_part}"
        else:
            output_filename_base = f"Chapter_{cleaned_title_part}" if cleaned_title_part else "untitled_chapter"

        if not cleaned_title_part and formatted_chapter_number_str:
            output_filename_base = f"Chapter_{formatted_chapter_number_str}"
        elif not cleaned_title_part and not formatted_chapter_number_str:
            output_filename_base = "untitled_chapter"


        output_filepath = os.path.join(OUTPUT_DIR, f"{output_filename_base}.txt")

        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(extracted_text)

        print(_('PROCESSING_COMPLETE').format(os.path.basename(CHAPTER_UNIT_DIR), os.path.basename(output_filepath)))

print(_('OCR_FINISHED').format(os.path.basename(CHAPTER_UNIT_DIR)))
print(_('CHECK_LOG_FOR_ERRORS').format(ERROR_LOG_FILE))