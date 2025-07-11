import os
from PIL import Image
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

PROCESSED_IMAGES_SUBFOLDER_NAME = config.PROCESSED_IMAGES_SUBFOLDER_NAME
OUTPUT_SPLIT_IMAGES_BASE_DIR = os.path.join(CHAPTER_UNIT_DIR, PROCESSED_IMAGES_SUBFOLDER_NAME)

MAX_IMAGE_HEIGHT = config.MAX_IMAGE_HEIGHT
TARGET_IMAGE_BASENAME = '1'
SUPPORTED_IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.tiff', '.tif')

ERROR_LOG_FILE = os.path.join(CHAPTER_UNIT_DIR, 'split_errors.log') 

def log_error(message, image_name="N/A", level="ERROR"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] [{_('UNITÉ_CHAPITRE')}: {os.path.basename(CHAPTER_UNIT_DIR)}] [{_('IMAGE')}: {image_name}] {level}: {message}"
    
    with open(ERROR_LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_message + '\n')
    print(f"  {log_message}")

if not os.path.exists(OUTPUT_SPLIT_IMAGES_BASE_DIR):
    os.makedirs(OUTPUT_SPLIT_IMAGES_BASE_DIR)
    print(_('OUTPUT_FOLDER_CREATED').format(OUTPUT_SPLIT_IMAGES_BASE_DIR))

if os.path.exists(ERROR_LOG_FILE):
    os.remove(ERROR_LOG_FILE)
    print(_('PREVIOUS_LOG_DELETED').format(ERROR_LOG_FILE))

print(_('START_SPLITTING').format(os.path.basename(CHAPTER_UNIT_DIR)))
print(_('IMAGES_WILL_BE_SAVED_IN').format(OUTPUT_SPLIT_IMAGES_BASE_DIR))
print(_('MAX_HEIGHT_ALLOWED').format(MAX_IMAGE_HEIGHT))

original_image_path = None
found_extension = None
for ext in SUPPORTED_IMAGE_EXTENSIONS:
    potential_path = os.path.join(CHAPTER_UNIT_DIR, f"{TARGET_IMAGE_BASENAME}{ext}")
    if os.path.exists(potential_path):
        original_image_path = potential_path
        found_extension = ext
        break

if not original_image_path:
    log_error(_('TARGET_FILE_NOT_FOUND').format(TARGET_IMAGE_BASENAME, ', '.join(SUPPORTED_IMAGE_EXTENSIONS)), TARGET_IMAGE_BASENAME, level="ERROR")
else:
    image_base_name = os.path.basename(original_image_path)
    try:
        img = Image.open(original_image_path)
        width, height = img.size
        
        if img.mode != 'L' and img.mode != 'RGB': 
            img = img.convert('L') 

        if height <= MAX_IMAGE_HEIGHT:
            print(_('IMAGE_MANAGEABLE_SIZE').format(image_base_name, width, height))
            img.save(os.path.join(OUTPUT_SPLIT_IMAGES_BASE_DIR, f"{TARGET_IMAGE_BASENAME}.png"))
        else:
            print(_('IMAGE_TOO_LARGE').format(image_base_name, width, height))
            
            segments_saved_count = 0
            for i in range(0, height, MAX_IMAGE_HEIGHT):
                box = (0, i, width, min(i + MAX_IMAGE_HEIGHT, height))
                segment = img.crop(box)
                
                segment_filename = f"{TARGET_IMAGE_BASENAME}_{str(segments_saved_count + 1).zfill(3)}.png"
                segment_path = os.path.join(OUTPUT_SPLIT_IMAGES_BASE_DIR, segment_filename)
                segment.save(segment_path)
                segments_saved_count += 1
                print(_('SAVED_SEGMENT').format(segment_path))
            
            print(_('SPLITTING_FINISHED').format(segments_saved_count, os.path.basename(CHAPTER_UNIT_DIR)))

    except Exception as e:
        log_error(_('ERROR_DURING_PROCESSING').format(e), image_base_name, level="ERROR")

print(_('IMAGE_PREPARATION_FINISHED').format(os.path.basename(CHAPTER_UNIT_DIR)))
print(_('CHECK_LOG_FOR_ERRORS').format(ERROR_LOG_FILE))