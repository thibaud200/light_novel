import os
import zipfile
import shutil
import datetime
import sys

# Importation du module de localisation
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from localization.main import get_translator
_ = get_translator()

def extract_cbz_content(cbz_file_path, output_parent_dir_for_extraction):
    cbz_name_base = os.path.splitext(os.path.basename(cbz_file_path))[0]
    output_chapter_dir = os.path.join(output_parent_dir_for_extraction, f"{cbz_name_base}_unzipped")

    if os.path.exists(output_chapter_dir):
        print(_('EXTRACTION_FOLDER_EXISTS').format(output_chapter_dir))
        shutil.rmtree(output_chapter_dir)
        
    os.makedirs(output_chapter_dir, exist_ok=True)

    print(_('EXTRACTING_CBZ').format(os.path.basename(cbz_file_path), output_chapter_dir))
    try:
        with zipfile.ZipFile(cbz_file_path, 'r') as zip_ref:
            extracted_files = []
            for member in zip_ref.namelist():
                if member.endswith('/'):
                    continue
                
                if os.path.basename(member).lower() in ('.ds_store', 'thumbs.db'):
                    continue

                dest_path = os.path.join(output_chapter_dir, os.path.basename(member))
                
                with zip_ref.open(member, 'r') as source:
                    with open(dest_path, "wb") as target:
                        shutil.copyfileobj(source, target)
                extracted_files.append(dest_path)

            main_image_found = False
            for f in extracted_files:
                if os.path.basename(f).lower() == '1.png':
                    main_image_found = True
                    break
            
            if not main_image_found and extracted_files:
                img_files = [f for f in extracted_files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                img_files.sort()
                if img_files:
                    first_img_path = img_files[0]
                    target_1_png_path = os.path.join(output_chapter_dir, '1.png')
                    if os.path.abspath(first_img_path) != os.path.abspath(target_1_png_path):
                        os.rename(first_img_path, target_1_png_path)
                        print(_('RENAMED_FOR_COMPATIBILITY').format(os.path.basename(first_img_path)))
        
        print(_('EXTRACTION_FINISHED').format(os.path.basename(cbz_file_path)))
        return output_chapter_dir
    
    except zipfile.BadZipFile:
        print(f"[{_('ERROR CBZ EXTRACT')}] {os.path.basename(cbz_file_path)}: {_('CBZ_CORRUPTED')}")
        return None
    except Exception as e:
        print(f"[{_('ERROR CBZ EXTRACT')}] {os.path.basename(cbz_file_path)}: {_('UNEXPECTED_EXTRACTION_ERROR').format(e)}")
        return None

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=_('CBZ_FILE_HELP'))
    parser.add_argument('--cbz_file', type=str, required=True,
                        help=_('CBZ_FILE_HELP'))
    parser.add_argument('--output_parent_dir', type=str, required=True,
                        help=_('OUTPUT_PARENT_DIR_HELP'))
    args = parser.parse_args()

    def log_error_cbz(message, cbz_file):
        print(f"[{_('ERROR CBZ EXTRACT')}] {cbz_file}: {message}")

    extracted_path = extract_cbz_content(args.cbz_file, args.output_parent_dir)
    if extracted_path:
        print(_('CONTENT_EXTRACTED_TO').format(extracted_path))
    else:
        print(_('EXTRACTION_FAILED'))