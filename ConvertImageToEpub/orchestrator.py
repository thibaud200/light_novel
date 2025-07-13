import os
import subprocess
import sys
import datetime
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import json
import config

# Importation du module de localisation
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from localization.main import get_translator
_ = get_translator()

# --- Chemins des fichiers de log globaux ---
ORCHESTRATOR_LOG_FILE_PATH = config.ORCHESTRATOR_LOG_FILE_PATH
GLOBAL_ERROR_LOG_FILE_PATH = config.GLOBAL_ERROR_LOG_FILE_PATH
PROGRESS_LOG_FILE_PATH = config.PROGRESS_LOG_FILE_PATH 

# --- Fonction pour journaliser les messages de l'orchestrateur ---
def log_orchestrator_message(message, level="INFO"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] [{level}] {message}"
    os.makedirs(os.path.dirname(ORCHESTRATOR_LOG_FILE_PATH), exist_ok=True)
    with open(ORCHESTRATOR_LOG_FILE_PATH, 'a', encoding='utf-8') as f:
        f.write(log_message + '\n')
    print(log_message)

# --- Fonction pour journaliser les erreurs dans le fichier d'erreurs global ---
def log_global_error(message, chapter_unit_path="N/A", script_name="N/A", error_details=""):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] [{_('CHAPITRE')}: {os.path.basename(chapter_unit_path)}] [{_('SCRIPT')}: {script_name}] {_('ERREUR')}: {message}\n{_('Details')}: {error_details}\n"
    os.makedirs(os.path.dirname(GLOBAL_ERROR_LOG_FILE_PATH), exist_ok=True)
    with open(GLOBAL_ERROR_LOG_FILE_PATH, 'a', encoding='utf-8') as f:
        f.write(log_message + '\n')
    print(f"[{_('GLOBAL_ERROR')}] {log_message.strip()}")

# --- Fonction pour charger les derniers chapitres traités / livres complets ---
def load_last_processed_chapters():
    if os.path.exists(PROGRESS_LOG_FILE_PATH):
        try:
            with open(PROGRESS_LOG_FILE_PATH, 'r', encoding='utf-8') as f:
                # Stocke un dict {book_name: chapter_path ou True pour complet}
                return json.load(f)
        except json.JSONDecodeError:
            log_orchestrator_message(_('PROGRESS_FILE_CORRUPTED').format(os.path.basename(PROGRESS_LOG_FILE_PATH)), "WARNING")
            return {}
    return {}

# --- Fonction pour sauvegarder le dernier chapitre traité / état complet d'un livre ---
def save_last_processed_chapters(last_processed_chapters_map):
    temp_path = PROGRESS_LOG_FILE_PATH + ".tmp"
    try:
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(last_processed_chapters_map, f, indent=4)
        shutil.move(temp_path, PROGRESS_LOG_FILE_PATH)
    except Exception as e:
        log_orchestrator_message(_('CRITICAL_ERROR_SAVE_PROGRESS').format(os.path.basename(PROGRESS_LOG_FILE_PATH), e), "CRITICAL")


sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from extract_cbz import extract_cbz_content

# --- Configuration GLOBALE de l'Orchestrateur ---
GLOBAL_BOOKS_ROOT_DIR = config.GLOBAL_BOOKS_ROOT_DIR
SCRIPTS_DIR = config.SCRIPTS_DIR

PROCESSED_IMAGES_SUBFOLDER_NAME = config.PROCESSED_IMAGES_SUBFOLDER_NAME
OUTPUT_TEXT_SUBFOLDER_NAME = config.OUTPUT_TEXT_SUBFOLDER_NAME
OUTPUT_CLEANED_TEXT_SUBFOLDER_NAME = config.OUTPUT_CLEANED_TEXT_SUBFOLDER_NAME
FINAL_COLLECTED_TEXTS_SUBFOLDER_NAME = config.FINAL_COLLECTED_TEXTS_SUBFOLDER_NAME
EXCLUDE_DIR_NAMES = config.EXCLUDE_DIR_NAMES

MAX_CONCURRENT_CHAPTER_UNITS = config.MAX_CONCURRENT_CHAPTER_UNITS 

SPLIT_SCRIPT = os.path.join(SCRIPTS_DIR, 'split_large_images.py')
OCR_SCRIPT = os.path.join(SCRIPTS_DIR, 'OCR.py')
CLEAN_SCRIPT = os.path.join(SCRIPTS_DIR, 'clean_ocr_text.py')

# --- Clé de tri naturel ---
def natsort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

# --- Fonction pour exécuter un script enfant (SILENCIEUSE) ---
def run_child_script(script_path, chapter_unit_path_arg):
    script_name = os.path.basename(script_path)
    log_orchestrator_message(_('EXECUTING_SCRIPT').format(script_name, os.path.basename(chapter_unit_path_arg)), level="INFO")
    try:
        command = [sys.executable, script_path, '--chapter_unit', chapter_unit_path_arg]
        
        result = subprocess.run(command,
                                capture_output=True,
                                text=True,
                                check=True)
        
        if result.stdout:
            log_orchestrator_message(_('SCRIPT_OUTPUT').format(script_name, result.stdout.strip()), "DEBUG")
        if result.stderr:
            log_orchestrator_message(_('SCRIPT_WARNING').format(script_name, result.stderr.strip()), "WARNING")

        log_orchestrator_message(_('SCRIPT_SUCCESS').format(script_name), level="INFO")
        return True
    except subprocess.CalledProcessError as e:
        error_details = f"{_('Exit code')} : {e.returncode}\n{_('STDERR')} : {e.stderr.strip() if e.stderr else _('None')}\n{_('STDOUT')} : {e.stdout.strip() if e.stdout else _('None')}"
        log_orchestrator_message(_('SCRIPT_FAILED').format(script_name, os.path.basename(chapter_unit_path_arg)), "ERROR")
        log_global_error(_('SCRIPT_EXECUTION_FAILED'), chapter_unit_path_arg, script_name, error_details)
        return False
    except FileNotFoundError:
        error_details = _('SCRIPT_FILE_NOT_FOUND').format(script_name)
        log_orchestrator_message(_('SCRIPT_NOT_FOUND').format(script_name), "CRITICAL")
        log_global_error(error_details, chapter_unit_path_arg, script_name)
        return False
    except Exception as e:
        error_details = _('UNEXPECTED_ERROR_DETAILS').format(e)
        log_orchestrator_message(_('UNEXPECTED_ERROR').format(script_name, e), "CRITICAL")
        log_global_error(error_details, chapter_unit_path_arg, script_name)
        return False

# --- Fonction pour nettoyer les dossiers intermédiaires ---
def cleanup_intermediate_folders(chapter_unit_path, folders_to_clean_names):
    log_orchestrator_message(_('CLEANING_INTERMEDIATE_FILES').format(os.path.basename(chapter_unit_path)), level="INFO")
    for folder_name in folders_to_clean_names:
        folder_path = os.path.join(chapter_unit_path, folder_name)
        if os.path.exists(folder_path):
            try:
                shutil.rmtree(folder_path)
                log_orchestrator_message(_('FOLDER_DELETED').format(os.path.basename(folder_path)), level="INFO")
            except Exception as e:
                log_orchestrator_message(_('ERROR_DELETING_FOLDER').format(os.path.basename(folder_path), e), "ERROR")
        else:
            log_orchestrator_message(_('FOLDER_NOT_FOUND').format(os.path.basename(folder_path)), level="INFO")
    log_orchestrator_message(_('CLEANUP_FINISHED_FOR').format(os.path.basename(chapter_unit_path)), level="INFO")

# --- Fonction : Collecter les fichiers TXT finaux pour un livre ---
def collect_final_texts(book_root_dir, chapter_units_list):
    log_orchestrator_message(_('START_COLLECTING_FINAL_TXT').format(os.path.basename(book_root_dir)), level="INFO")
    
    final_output_book_dir = os.path.join(book_root_dir, FINAL_COLLECTED_TEXTS_SUBFOLDER_NAME)
    os.makedirs(final_output_book_dir, exist_ok=True)

    collected_count = 0
    for chapter_unit_path in sorted(chapter_units_list, key=natsort_key):
        cleaned_txt_source_dir = os.path.join(chapter_unit_path, OUTPUT_CLEANED_TEXT_SUBFOLDER_NAME)
        
        if os.path.exists(cleaned_txt_source_dir):
            for txt_file_name in sorted(os.listdir(cleaned_txt_source_dir), key=natsort_key):
                if txt_file_name.lower().endswith('.txt'):
                    source_file_path = os.path.join(cleaned_txt_source_dir, txt_file_name)
                    destination_file_path = os.path.join(final_output_book_dir, txt_file_name)
                    
                    try:
                        shutil.copy2(source_file_path, destination_file_path)
                        log_orchestrator_message(_('COPIED_TO_FINAL_FOLDER').format(txt_file_name, os.path.basename(chapter_unit_path)), level="INFO")
                        collected_count += 1
                    except Exception as e:
                        log_orchestrator_message(_('ERROR_COPYING_FILE').format(txt_file_name, e), "ERROR")
                        log_global_error(_('FAILED_TO_COPY_CLEANED_TXT'), chapter_unit_path, "collect_final_texts", str(e))
            
        else:
            log_orchestrator_message(_('CLEANED_TXT_FOLDER_NOT_FOUND').format(os.path.basename(cleaned_txt_source_dir), os.path.basename(chapter_unit_path)), "WARNING")

    log_orchestrator_message(_('FINAL_TXT_COLLECTION_FINISHED').format(collected_count, os.path.basename(book_root_dir)), level="INFO")

def _process_single_chapter_unit(chapter_unit_path, book_folder_name, last_processed_chapters_map):
    message_prefix = f"[{_('CHAPITRE')}: '{os.path.basename(chapter_unit_path)}' {_('pour')} '{book_folder_name}']"
    log_orchestrator_message(_('PROCESSING_STARTED').format(message_prefix), "INFO")

    ### DÉBUT DE LA NOUVELLE LOGIQUE DE VÉRIFICATION ###
    chapter_name = os.path.basename(chapter_unit_path)
    book_final_texts_dir = os.path.join(os.path.dirname(chapter_unit_path), FINAL_COLLECTED_TEXTS_SUBFOLDER_NAME) # Utilisez FINAL_COLLECTED_TEXTS_SUBFOLDER_NAME

    # Fonction utilitaire pour vérifier la présence d'un fichier .txt dans un répertoire
    def has_txt_files(directory):
        if os.path.exists(directory):
            return any(f.lower().endswith('.txt') for f in os.listdir(directory))
        return False

    # 1. Vérifier dans le répertoire final_texts (le plus prioritaire)
    # On doit chercher un fichier qui contient le nom du chapitre dans le nom du fichier texte final.
    final_text_found = False
    if os.path.exists(book_final_texts_dir):
        # Pour le nommage des fichiers dans final_texts, ils sont formatés comme "Chapter_XXXX_Titre.txt"
        # Donc nous allons chercher un fichier qui contient le nom de votre dossier de chapitre
        # Assumons que le nom du chapitre dans le dossier est "Chapter 1" ou "Chapter 001_title"
        # Et le fichier final dans final_texts est "Chapter 001_title_some_stuff.txt"
        
        # Simplifions le nom du chapitre pour la recherche (enlever _unzipped si c'est le cas)
        search_chapter_name = chapter_name.replace('_unzipped', '').lower()
        search_chapter_name = search_chapter_name.replace('chapter', '').strip().replace(' ', '_').replace('-', '_')
        search_chapter_name = re.sub(r'[^a-z0-9_]', '', search_chapter_name) # Nettoyage pour la recherche

        for f_name in os.listdir(book_final_texts_dir):
            if f_name.lower().endswith('.txt'):
                # Nettoyer le nom du fichier final de manière similaire
                cleaned_f_name = f_name.replace('_unzipped', '').lower()
                cleaned_f_name = cleaned_f_name.replace('chapter', '').strip().replace(' ', '_').replace('-', '_')
                cleaned_f_name = re.sub(r'[^a-z0-9_]', '', cleaned_f_name)

                if search_chapter_name in cleaned_f_name: # Vérifie si le nom simplifié du chapitre est dans le nom du fichier final
                    final_text_found = True
                    break
    
    if final_text_found:
        log_orchestrator_message(_('FINAL_TXT_FOUND').format(message_prefix, FINAL_COLLECTED_TEXTS_SUBFOLDER_NAME), "INFO")
        # Mettre à jour le fichier de progression pour ce livre si ce chapitre est traité
        last_processed_chapters_map[book_folder_name] = chapter_unit_path
        save_last_processed_chapters(last_processed_chapters_map)
        return _('PROCESSING_SKIPPED_FINAL').format(message_prefix)

    # 2. Vérifier dans sortieTXT_cleaned
    cleaned_txt_dir = os.path.join(chapter_unit_path, OUTPUT_CLEANED_TEXT_SUBFOLDER_NAME)
    if has_txt_files(cleaned_txt_dir):
        log_orchestrator_message(_('CLEANED_FILES_FOUND').format(message_prefix, OUTPUT_CLEANED_TEXT_SUBFOLDER_NAME), "INFO")
        # Mettre à jour le fichier de progression pour ce livre si ce chapitre est traité
        last_processed_chapters_map[book_folder_name] = chapter_unit_path
        save_last_processed_chapters(last_processed_chapters_map)
        return _('PROCESSING_SKIPPED_CLEANED').format(message_prefix)

    # 3. Vérifier dans sortieTXT
    output_txt_dir = os.path.join(chapter_unit_path, OUTPUT_TEXT_SUBFOLDER_NAME)
    if has_txt_files(output_txt_dir):
        log_orchestrator_message(_('RAW_OCR_FOUND_RESUME').format(message_prefix, OUTPUT_TEXT_SUBFOLDER_NAME), "INFO")
        clean_success = run_child_script(CLEAN_SCRIPT, chapter_unit_path)
        if not clean_success:
            return _('STOP_CLEAN_FAIL').format(message_prefix)
        # Après un nettoyage réussi, on nettoie les dossiers intermédiaires (ici sortieTXT)
        cleanup_intermediate_folders(chapter_unit_path, [OUTPUT_TEXT_SUBFOLDER_NAME])
        # Puis on met à jour le progrès
        last_processed_chapters_map[book_folder_name] = chapter_unit_path
        save_last_processed_chapters(last_processed_chapters_map)
        return _('PROCESSING_RESUMED_CLEANING').format(message_prefix)

    ### FIN DE LA NOUVELLE LOGIQUE DE VÉRIFICATION ###

    # Si aucun fichier final n'est trouvé, procéder au traitement complet (split -> ocr -> clean)
    log_orchestrator_message(_('NO_OUTPUT_FOUND').format(message_prefix), "INFO")

    split_success = run_child_script(SPLIT_SCRIPT, chapter_unit_path)
    if not split_success:
        return _('STOP_SPLIT_FAIL').format(message_prefix)

    ocr_success = run_child_script(OCR_SCRIPT, chapter_unit_path)
    if not ocr_success:
        return _('STOP_OCR_FAIL').format(message_prefix)
    
    # Nettoyage des images traitées après OCR, car elles ne sont plus nécessaires
    cleanup_intermediate_folders(chapter_unit_path, [PROCESSED_IMAGES_SUBFOLDER_NAME])

    clean_success = run_child_script(CLEAN_SCRIPT, chapter_unit_path)
    if not clean_success:
        return _('STOP_CLEAN_FAIL').format(message_prefix)

    # Nettoyage des fichiers OCR bruts après nettoyage
    cleanup_intermediate_folders(chapter_unit_path, [OUTPUT_TEXT_SUBFOLDER_NAME])

    # Mettre à jour le fichier de progression pour ce livre
    last_processed_chapters_map[book_folder_name] = chapter_unit_path
    save_last_processed_chapters(last_processed_chapters_map)

    return _('PROCESSING_FINISHED').format(message_prefix)

# --- Processus principal ---
log_orchestrator_message(_('ORCHESTRATOR_START'), level="INFO")
log_orchestrator_message(_('GLOBAL_BOOKS_ROOT_DIR_MSG').format(GLOBAL_BOOKS_ROOT_DIR), level="INFO")
log_orchestrator_message(_('MAX_CONCURRENT_CHAPTER_UNITS_MSG').format(MAX_CONCURRENT_CHAPTER_UNITS), level="INFO")


# Nettoyer les logs précédents au démarrage
if os.path.exists(ORCHESTRATOR_LOG_FILE_PATH):
    os.remove(ORCHESTRATOR_LOG_FILE_PATH)
if os.path.exists(GLOBAL_ERROR_LOG_FILE_PATH):
    os.remove(GLOBAL_ERROR_LOG_FILE_PATH)
if os.path.exists(PROGRESS_LOG_FILE_PATH + ".tmp"):
    os.remove(PROGRESS_LOG_FILE_PATH + ".tmp")
# Ne pas supprimer PROGRESS_LOG_FILE_PATH ici, car on le charge en premier.

# Charger les derniers chapitres traités
last_processed_chapters_by_book = load_last_processed_chapters()
if last_processed_chapters_by_book:
    log_orchestrator_message(_('LOADING_RESUME_POINTS').format(len(last_processed_chapters_by_book)), "INFO")
    for book_name, progress_status in last_processed_chapters_by_book.items():
        if progress_status is True:
            log_orchestrator_message(_('BOOK_MARKED_AS_PROCESSED').format(book_name), "INFO")
        else:
            log_orchestrator_message(_('LAST_PROCESSED_CHAPTER').format(book_name, os.path.basename(progress_status)), "INFO")
else:
    log_orchestrator_message(_('NO_RESUME_POINT_FOUND'), "INFO")


all_futures = []
book_chapter_units_map = {}

with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_CHAPTER_UNITS) as executor:
    # 1. Phase de Détection et Soumission des Tâches
    for book_folder_name in sorted(os.listdir(GLOBAL_BOOKS_ROOT_DIR), key=natsort_key):
        book_folder_path = os.path.join(GLOBAL_BOOKS_ROOT_DIR, book_folder_name)

        if not os.path.isdir(book_folder_path):
            log_orchestrator_message(_('IGNORED_NON_DIRECTORY').format(book_folder_name), "INFO")
            continue

        if book_folder_name.lower() in EXCLUDE_DIR_NAMES:
            log_orchestrator_message(_('IGNORED_EXCLUDED_DIR').format(book_folder_name), "INFO")
            continue

        # --- NOUVELLE LOGIQUE : Sauter le livre entier si marqué comme COMPLET ---
        if last_processed_chapters_by_book.get(book_folder_name) is True:
            log_orchestrator_message(f"\n========================================================", level="INFO")
            log_orchestrator_message(_('BOOK_MARKED_AS_PROCESSED_SKIP').format(book_folder_name), "INFO")
            log_orchestrator_message(f"========================================================", level="INFO")
            chapter_units_for_this_book_temp = []
            for item_in_book_folder_name in sorted(os.listdir(book_folder_path), key=natsort_key):
                item_in_book_folder_path = os.path.join(book_folder_path, item_in_book_folder_name)
                if os.path.isdir(item_in_book_folder_path) and item_in_book_folder_name.lower() not in EXCLUDE_DIR_NAMES.union({
                    PROCESSED_IMAGES_SUBFOLDER_NAME.lower(), OUTPUT_TEXT_SUBFOLDER_NAME.lower(), 
                    OUTPUT_CLEANED_TEXT_SUBFOLDER_NAME.lower(), FINAL_COLLECTED_TEXTS_SUBFOLDER_NAME.lower(),
                    '__pycache__'}):
                    chapter_units_for_this_book_temp.append(item_in_book_folder_path)
                elif item_in_book_folder_name.lower().endswith('.cbz'):
                     chapter_units_for_this_book_temp.append(item_in_book_folder_path)
            book_chapter_units_map[book_folder_path] = chapter_units_for_this_book_temp
            continue

        log_orchestrator_message(f"\n========================================================", level="INFO")
        log_orchestrator_message(_('START_DETECTION_BOOK').format(book_folder_name), level="INFO")
        log_orchestrator_message(_('BOOK_FOLDER_PATH').format(book_folder_path), level="INFO")
        log_orchestrator_message(f"========================================================", level="INFO")

        chapter_units_for_this_book = []

        for item_in_book_folder_name in sorted(os.listdir(book_folder_path), key=natsort_key):
            item_in_book_folder_path = os.path.join(book_folder_path, item_in_book_folder_name)

            all_excluded_items = {
                PROCESSED_IMAGES_SUBFOLDER_NAME.lower(),
                OUTPUT_TEXT_SUBFOLDER_NAME.lower(),
                OUTPUT_CLEANED_TEXT_SUBFOLDER_NAME.lower(),
                FINAL_COLLECTED_TEXTS_SUBFOLDER_NAME.lower()
            }.union(EXCLUDE_DIR_NAMES)

            if item_in_book_folder_name.lower() in all_excluded_items:
                log_orchestrator_message(_('IGNORED_SYSTEM_SUBFOLDER').format(item_in_book_folder_name), "INFO")
                continue
            
            if not os.path.isdir(item_in_book_folder_path) and not item_in_book_folder_name.lower().endswith('.cbz'):
                log_orchestrator_message(_('IGNORED_NON_CBZ_FILE').format(item_in_book_folder_name), "INFO")
                continue
            
            if os.path.isdir(item_in_book_folder_path):
                chapter_units_for_this_book.append(item_in_book_folder_path)
            
            elif os.path.isfile(item_in_book_folder_path) and item_in_book_folder_name.lower().endswith('.cbz'):
                log_orchestrator_message(_('CBZ_DETECTED').format(item_in_book_folder_name), "INFO")
                extracted_chapter_unit_path = extract_cbz_content(item_in_book_folder_path, book_folder_path)
                if extracted_chapter_unit_path:
                    chapter_units_for_this_book.append(extracted_chapter_unit_path)
                    log_orchestrator_message(_('CBZ_EXTRACTED').format(item_in_book_folder_name), "INFO")
                else:
                    log_orchestrator_message(_('CBZ_EXTRACTION_FAILED').format(item_in_book_folder_name), "ERROR")
            
        chapter_units_for_this_book.sort(key=natsort_key)

        if not chapter_units_for_this_book:
            log_orchestrator_message(_('NO_CHAPTER_UNIT_FOUND').format(book_folder_name), "WARNING")
            continue

        book_chapter_units_map[book_folder_path] = chapter_units_for_this_book
        
        # --- LOGIQUE DE REPRISE : Filtrer les chapitres déjà traités pour ce livre ---
        chapters_to_submit_for_book = []
        last_processed_status_for_book = last_processed_chapters_by_book.get(book_folder_name)

        if last_processed_status_for_book is True:
            log_orchestrator_message(_('DOUBLE_CHECK_PROCESSED').format(book_folder_name), "INFO")
            chapters_to_submit_for_book = []
        elif last_processed_status_for_book:
            log_orchestrator_message(_('RESUME_POINT_DETECTED').format(book_folder_name, os.path.basename(last_processed_status_for_book)), "INFO")
            found_last_processed = False
            for chapter_path in chapter_units_for_this_book:
                if found_last_processed:
                    chapters_to_submit_for_book.append(chapter_path)
                elif chapter_path == last_processed_status_for_book:
                    found_last_processed = True
                    log_orchestrator_message(_('RESUMING_AFTER_CHAPTER').format(os.path.basename(chapter_path)), "INFO")
                else:
                    log_orchestrator_message(_('IGNORED_ALREADY_PROCESSED').format(os.path.basename(chapter_path)), "DEBUG")
            
            if not found_last_processed and chapters_to_submit_for_book:
                log_orchestrator_message(_('RESUME_POINT_NOT_FOUND').format(os.path.basename(last_processed_status_for_book), book_folder_name), "WARNING")
            elif not found_last_processed and not chapters_to_submit_for_book:
                 log_orchestrator_message(_('RESUME_POINT_NOT_FOUND_NO_MORE').format(os.path.basename(last_processed_status_for_book)), "WARNING")

        else:
            chapters_to_submit_for_book = chapter_units_for_this_book


        if not chapters_to_submit_for_book:
            log_orchestrator_message(_('ALL_CHAPTERS_ALREADY_PROCESSED').format(book_folder_name), "INFO")
        else:
            log_orchestrator_message(_('SUBMITTING_CHAPTERS').format(len(chapters_to_submit_for_book), book_folder_name), "INFO")
            for chapter_unit_path in chapters_to_submit_for_book:
                future = executor.submit(_process_single_chapter_unit, chapter_unit_path, book_folder_name, last_processed_chapters_by_book)
                all_futures.append(future)

    log_orchestrator_message(_('ALL_TASKS_SUBMITTED'), "INFO")
    for future in as_completed(all_futures):
        result_message = future.result()
        log_orchestrator_message(result_message, "INFO")

log_orchestrator_message(_('START_POST_PROCESSING'), "INFO")
for book_folder_path, chapter_units_list in sorted(book_chapter_units_map.items(), key=lambda item: natsort_key(os.path.basename(item[0]))):
    book_folder_name = os.path.basename(book_folder_path)
    
    is_book_marked_as_complete = last_processed_chapters_by_book.get(book_folder_name) is True

    if is_book_marked_as_complete:
        log_orchestrator_message(_('BOOK_IS_PROCESSED').format(book_folder_name), "INFO")
        collect_final_texts(book_folder_path, chapter_units_list)

        for chapter_unit_path_for_cleanup in chapter_units_list:
            cleanup_intermediate_folders(chapter_unit_path_for_cleanup, [OUTPUT_TEXT_SUBFOLDER_NAME, OUTPUT_CLEANED_TEXT_SUBFOLDER_NAME])
            if chapter_unit_path_for_cleanup.endswith('_unzipped'):
                cleanup_intermediate_folders(chapter_unit_path_for_cleanup, ["."])

        log_orchestrator_message(f"\n========================================================", level="INFO")
        log_orchestrator_message(_('BOOK_COMPLETE_PROCESSING_MSG').format(book_folder_name), level="INFO")
        log_orchestrator_message(f"========================================================", level="INFO")
    else:
        all_chapters_processed_in_this_run = True
        for chapter_path in chapter_units_list:
            cleaned_txt_source_dir = os.path.join(chapter_path, OUTPUT_CLEANED_TEXT_SUBFOLDER_NAME)
            if not (os.path.exists(cleaned_txt_source_dir) and any(f.lower().endswith('.txt') for f in os.listdir(cleaned_txt_source_dir))):
                all_chapters_processed_in_this_run = False
                break
        
        if all_chapters_processed_in_this_run:
            log_orchestrator_message(_('BOOK_POST_PROCESSING_STARTED').format(book_folder_name), "INFO")
            collect_final_texts(book_folder_path, chapter_units_list)

            for chapter_unit_path_for_cleanup in chapter_units_list:
                cleanup_intermediate_folders(chapter_unit_path_for_cleanup, [OUTPUT_TEXT_SUBFOLDER_NAME, OUTPUT_CLEANED_TEXT_SUBFOLDER_NAME])
                if chapter_unit_path_for_cleanup.endswith('_unzipped'):
                    cleanup_intermediate_folders(chapter_unit_path_for_cleanup, ["."])

            log_orchestrator_message(f"\n========================================================", level="INFO")
            log_orchestrator_message(_('BOOK_COMPLETE_PROCESSING_MSG').format(book_folder_name), level="INFO")
            log_orchestrator_message(f"========================================================", level="INFO")
            last_processed_chapters_by_book[book_folder_name] = True 
            save_last_processed_chapters(last_processed_chapters_by_book)
        else:
            log_orchestrator_message(_('BOOK_INCOMPLETE_SKIP').format(book_folder_name), "WARNING")


log_orchestrator_message(_('ALL_BOOKS_FINISHED'), level="INFO")
log_orchestrator_message(_('CHECK_LOG_FILES').format(ORCHESTRATOR_LOG_FILE_PATH, ""), level="INFO")
log_orchestrator_message(_('ERRORS_LOGGED').format(GLOBAL_ERROR_LOG_FILE_PATH), "INFO")
log_orchestrator_message(_('RESUME_POINTS_LOGGED').format(PROGRESS_LOG_FILE_PATH), "INFO")