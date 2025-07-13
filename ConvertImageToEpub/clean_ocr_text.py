import os
import re
import datetime
import argparse
import config
import sys

# Importation du module de localisation
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from localization.main import get_translator
_ = get_translator()

parser = argparse.ArgumentParser(description=_('SCRIPT_DESCRIPTION'))
parser.add_argument('--chapter_unit', type=str, required=True,
                    help=_('CHAPTER_UNIT_HELP'))
args = parser.parse_args()
CHAPTER_UNIT_DIR = args.chapter_unit

OUTPUT_TEXT_SUBFOLDER_NAME = config.OUTPUT_TEXT_SUBFOLDER_NAME
INPUT_TEXT_DIR = os.path.join(CHAPTER_UNIT_DIR, OUTPUT_TEXT_SUBFOLDER_NAME)

OUTPUT_CLEANED_TEXT_SUBFOLDER_NAME = config.OUTPUT_CLEANED_TEXT_SUBFOLDER_NAME
OUTPUT_CLEANED_TEXT_DIR = os.path.join(CHAPTER_UNIT_DIR, OUTPUT_CLEANED_TEXT_SUBFOLDER_NAME)

ERROR_LOG_FILE = os.path.join(CHAPTER_UNIT_DIR, 'clean_errors.log') 

def log_error(message, filename="N/A"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] [{_('UNITÉ_CHAPITRE')}: {os.path.basename(CHAPTER_UNIT_DIR)}] [{_('FICHIER')}: {filename}] {_('ERREUR')}: {message}"
    
    with open(ERROR_LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_message + '\n')
    print(f"  {log_message}")

def clean_text(text):
    text = re.sub(r'\[ERREUR OCR SUR CE SEGMENT : \(1, \'Image too large: \(980, \d+\) Error during processing\.\'\)\]\n\n', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t\xA0]+', ' ', text)
    text = re.sub(r'^[ \t]+|[ \t]+$', '', text, flags=re.MULTILINE)
    text = re.sub(r'(?<=\w)(?:-?)\s*\n\s*(?=\w)', '', text)
    text = re.sub(r'\n-\s*', ' ', text)
    text = re.sub(r'\s+([,.!?;:])', r'\1', text)
    text = re.sub(r'([([{])\s+', r'\1', text)
    text = re.sub(r'\s+([)\]}])', r'\1', text)
    text = text.replace('\f', '\n\n')
    return text.strip()


if not os.path.exists(OUTPUT_CLEANED_TEXT_DIR):
    os.makedirs(OUTPUT_CLEANED_TEXT_DIR)
    print(_('OUTPUT_FOLDER_CREATED').format(OUTPUT_CLEANED_TEXT_DIR))

if os.path.exists(ERROR_LOG_FILE):
    os.remove(ERROR_LOG_FILE)
    print(_('PREVIOUS_LOG_DELETED').format(ERROR_LOG_FILE))

print(_('START_POST_PROCESSING').format(os.path.basename(CHAPTER_UNIT_DIR)))
print(_('CLEANED_FILES_SAVED').format(OUTPUT_CLEANED_TEXT_DIR))

if not os.path.exists(INPUT_TEXT_DIR):
    log_error(_('INPUT_FOLDER_NOT_FOUND').format(OUTPUT_TEXT_SUBFOLDER_NAME), "N/A")
else:
    for filename in os.listdir(INPUT_TEXT_DIR):
        if not filename.lower().endswith('.txt'):
            print(_('WARNING_NOT_TXT').format(filename))
            continue
        
        input_filepath = os.path.join(INPUT_TEXT_DIR, filename)
        output_filepath = os.path.join(OUTPUT_CLEANED_TEXT_DIR, filename)

        print(_('PROCESSING_FILE').format(filename))

        try:
            with open(input_filepath, 'r', encoding='utf-8') as f:
                raw_text = f.read()
            
            cleaned_text = clean_text(raw_text)

            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write(cleaned_text)
            
            print(_('CLEANING_SUCCESSFUL').format(filename, os.path.basename(output_filepath)))

        except Exception as e:
            log_error(_('ERROR_WHILE_CLEANING').format(filename, e), filename)

print(_('POST_PROCESSING_FINISHED').format(os.path.basename(CHAPTER_UNIT_DIR)))
print(_('CHECK_LOG_FOR_ERRORS').format(ERROR_LOG_FILE))