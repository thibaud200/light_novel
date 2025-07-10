import os
import subprocess
import sys
import datetime
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import json
import config

# --- Chemins des fichiers de log globaux ---
#ORCHESTRATOR_LOG_FILE_PATH = 'D:\\novel\\orchestrator_log.log'
#GLOBAL_ERROR_LOG_FILE_PATH = 'D:\\novel\\global_errors.log'
#PROGRESS_LOG_FILE_PATH = 'D:\\novel\\processed_chapters.progress'
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
    log_message = f"[{timestamp}] [CHAPITRE: {os.path.basename(chapter_unit_path)}] [SCRIPT: {script_name}] ERREUR: {message}\nDetails: {error_details}\n"
    os.makedirs(os.path.dirname(GLOBAL_ERROR_LOG_FILE_PATH), exist_ok=True)
    with open(GLOBAL_ERROR_LOG_FILE_PATH, 'a', encoding='utf-8') as f:
        f.write(log_message + '\n')
    print(f"[GLOBAL_ERROR] {log_message.strip()}")

# --- Fonction pour charger les derniers chapitres traités / livres complets ---
def load_last_processed_chapters():
    if os.path.exists(PROGRESS_LOG_FILE_PATH):
        try:
            with open(PROGRESS_LOG_FILE_PATH, 'r', encoding='utf-8') as f:
                # Stocke un dict {book_name: chapter_path ou True pour complet}
                return json.load(f)
        except json.JSONDecodeError:
            log_orchestrator_message(f"AVERTISSEMENT: Le fichier de progression '{os.path.basename(PROGRESS_LOG_FILE_PATH)}' est corrompu ou vide. Reprise à zéro pour tous les livres.", "WARNING")
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
        log_orchestrator_message(f"ERREUR CRITIQUE: Échec de la sauvegarde du fichier de progression '{os.path.basename(PROGRESS_LOG_FILE_PATH)}': {e}", "CRITICAL")


sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from extract_cbz import extract_cbz_content

# --- Configuration GLOBALE de l'Orchestrateur ---
#GLOBAL_BOOKS_ROOT_DIR = 'D:\\novel'
#SCRIPTS_DIR = 'D:\\novel'
GLOBAL_BOOKS_ROOT_DIR = config.GLOBAL_BOOKS_ROOT_DIR
SCRIPTS_DIR = config.SCRIPTS_DIR

#PROCESSED_IMAGES_SUBFOLDER_NAME = 'images_processed'
#OUTPUT_TEXT_SUBFOLDER_NAME = 'sortieTXT'
#OUTPUT_CLEANED_TEXT_SUBFOLDER_NAME = 'sortieTXT_cleaned'
#FINAL_COLLECTED_TEXTS_SUBFOLDER_NAME = 'final_texts'

#EXCLUDE_DIR_NAMES = {"traiter", "script", "backup", "temp", "sortie","scripts", "a traiter", "__pycache__"} 

#MAX_CONCURRENT_CHAPTER_UNITS = 4

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
    log_orchestrator_message(f"--- Exécution de {script_name} pour '{os.path.basename(chapter_unit_path_arg)}' ---", level="INFO")
    try:
        command = [sys.executable, script_path, '--chapter_unit', chapter_unit_path_arg]
        
        result = subprocess.run(command,
                                capture_output=True,
                                text=True,
                                check=True)
        
        if result.stdout:
            log_orchestrator_message(f"  Sortie de {script_name}:\n{result.stdout.strip()}", "DEBUG")
        if result.stderr:
            log_orchestrator_message(f"  Erreur/Avertissement de {script_name}:\n{result.stderr.strip()}", "WARNING")

        log_orchestrator_message(f"--- {script_name} terminé avec succès. ---", level="INFO")
        return True
    except subprocess.CalledProcessError as e:
        error_details = f"Code de sortie : {e.returncode}\nSTDERR : {e.stderr.strip() if e.stderr else 'Aucune'}\nSTDOUT : {e.stdout.strip() if e.stdout else 'Aucune'}"
        log_orchestrator_message(f"!!! ERREUR : {script_name} a échoué pour '{os.path.basename(chapter_unit_path_arg)}' !!!", "ERROR")
        log_global_error(f"Échec de l'exécution du script.", chapter_unit_path_arg, script_name, error_details)
        return False
    except FileNotFoundError:
        error_details = f"Le fichier du script {script_name} n'a pas été trouvé. Vérifiez le chemin SCRIPTS_DIR."
        log_orchestrator_message(f"!!! ERREUR CRITIQUE : {script_name} introuvable !!!", "CRITICAL")
        log_global_error(error_details, chapter_unit_path_arg, script_name)
        return False
    except Exception as e:
        error_details = f"Erreur inattendue : {e}"
        log_orchestrator_message(f"!!! ERREUR INATTENDUE lors de l'exécution de {script_name}: {e} !!!", "CRITICAL")
        log_global_error(error_details, chapter_unit_path_arg, script_name)
        return False

# --- Fonction pour nettoyer les dossiers intermédiaires ---
def cleanup_intermediate_folders(chapter_unit_path, folders_to_clean_names):
    log_orchestrator_message(f"  Nettoyage des fichiers intermédiaires pour '{os.path.basename(chapter_unit_path)}'...", level="INFO")
    for folder_name in folders_to_clean_names:
        folder_path = os.path.join(chapter_unit_path, folder_name)
        if os.path.exists(folder_path):
            try:
                shutil.rmtree(folder_path)
                log_orchestrator_message(f"    Dossier supprimé : {os.path.basename(folder_path)}", level="INFO")
            except Exception as e:
                log_orchestrator_message(f"    ERREUR lors de la suppression de {os.path.basename(folder_path)}: {e}", "ERROR")
        else:
            log_orchestrator_message(f"    Dossier '{os.path.basename(folder_path)}' non trouvé, pas de nettoyage nécessaire.", level="INFO")
    log_orchestrator_message(f"  Nettoyage terminé pour '{os.path.basename(chapter_unit_path)}'.", level="INFO")

# --- Fonction : Collecter les fichiers TXT finaux pour un livre ---
def collect_final_texts(book_root_dir, chapter_units_list):
    log_orchestrator_message(f"--- Début de la collecte des fichiers TXT finaux pour le livre : {os.path.basename(book_root_dir)} ---", level="INFO")
    
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
                        log_orchestrator_message(f"    Copié '{txt_file_name}' de '{os.path.basename(chapter_unit_path)}' vers le dossier final.", level="INFO")
                        collected_count += 1
                    except Exception as e:
                        log_orchestrator_message(f"    ERREUR lors de la copie de '{txt_file_name}': {e}", "ERROR")
                        log_global_error(f"Échec de la copie du fichier TXT nettoyé.", chapter_unit_path, "collect_final_texts", str(e))
            
        else:
            log_orchestrator_message(f"    Dossier '{os.path.basename(cleaned_txt_source_dir)}' non trouvé pour '{os.path.basename(chapter_unit_path)}'.", "WARNING")

    log_orchestrator_message(f"--- Collecte de {collected_count} fichiers TXT finaux terminée pour le livre : {os.path.basename(book_root_dir)} ---", level="INFO")

# --- Fonction pour traiter une seule unité de chapitre de manière séquentielle ---
#def _process_single_chapter_unit(chapter_unit_path, book_folder_name, last_processed_chapters_map):
#    message_prefix = f"[Chapitre '{os.path.basename(chapter_unit_path)}' pour '{book_folder_name}']"
#    log_orchestrator_message(f"{message_prefix} Début du traitement.", "INFO")
#
#    split_success = run_child_script(SPLIT_SCRIPT, chapter_unit_path)
#    if not split_success:
#        return f"{message_prefix} Arrêt suite à l'échec de la division des images."
#
#    ocr_success = run_child_script(OCR_SCRIPT, chapter_unit_path)
#    if not ocr_success:
#        return f"{message_prefix} Arrêt suite à l'échec de l'OCR."
#    
#    cleanup_intermediate_folders(chapter_unit_path, [PROCESSED_IMAGES_SUBFOLDER_NAME])
#
#    clean_success = run_child_script(CLEAN_SCRIPT, chapter_unit_path)
#    if not clean_success:
#        return f"{message_prefix} Arrêt suite à l'échec du nettoyage du texte."
#
#    # Mettre à jour le fichier de progression pour ce livre
#    last_processed_chapters_map[book_folder_name] = chapter_unit_path
#    save_last_processed_chapters(last_processed_chapters_map)
#
#    return f"{message_prefix} Traitement de l'unité de chapitre terminé."
def _process_single_chapter_unit(chapter_unit_path, book_folder_name, last_processed_chapters_map):
    message_prefix = f"[Chapitre '{os.path.basename(chapter_unit_path)}' pour '{book_folder_name}']"
    log_orchestrator_message(f"{message_prefix} Début du traitement.", "INFO")

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
        log_orchestrator_message(f"{message_prefix} Fichier(s) TXT final(aux) déjà présent(s) dans '{FINAL_COLLECTED_TEXTS_SUBFOLDER_NAME}'. Saut du traitement complet.", "INFO")
        # Mettre à jour le fichier de progression pour ce livre si ce chapitre est traité
        last_processed_chapters_map[book_folder_name] = chapter_unit_path
        save_last_processed_chapters(last_processed_chapters_map)
        return f"{message_prefix} Traitement de l'unité de chapitre ignoré (fichier final déjà présent)."

    # 2. Vérifier dans sortieTXT_cleaned
    cleaned_txt_dir = os.path.join(chapter_unit_path, OUTPUT_CLEANED_TEXT_SUBFOLDER_NAME)
    if has_txt_files(cleaned_txt_dir):
        log_orchestrator_message(f"{message_prefix} Fichier(s) nettoyé(s) déjà présent(s) dans '{OUTPUT_CLEANED_TEXT_SUBFOLDER_NAME}'. Saut du traitement complet.", "INFO")
        # Mettre à jour le fichier de progression pour ce livre si ce chapitre est traité
        last_processed_chapters_map[book_folder_name] = chapter_unit_path
        save_last_processed_chapters(last_processed_chapters_map)
        return f"{message_prefix} Traitement de l'unité de chapitre ignoré (fichier nettoyé déjà présent)."

    # 3. Vérifier dans sortieTXT
    output_txt_dir = os.path.join(chapter_unit_path, OUTPUT_TEXT_SUBFOLDER_NAME)
    if has_txt_files(output_txt_dir):
        log_orchestrator_message(f"{message_prefix} Fichier(s) OCR brut(s) déjà présent(s) dans '{OUTPUT_TEXT_SUBFOLDER_NAME}'. Reprise à partir de l'étape de nettoyage.", "INFO")
        clean_success = run_child_script(CLEAN_SCRIPT, chapter_unit_path)
        if not clean_success:
            return f"{message_prefix} Arrêt suite à l'échec du nettoyage du texte."
        # Après un nettoyage réussi, on nettoie les dossiers intermédiaires (ici sortieTXT)
        cleanup_intermediate_folders(chapter_unit_path, [OUTPUT_TEXT_SUBFOLDER_NAME])
        # Puis on met à jour le progrès
        last_processed_chapters_map[book_folder_name] = chapter_unit_path
        save_last_processed_chapters(last_processed_chapters_map)
        return f"{message_prefix} Traitement de l'unité de chapitre terminé (reprise du nettoyage)."

    ### FIN DE LA NOUVELLE LOGIQUE DE VÉRIFICATION ###

    # Si aucun fichier final n'est trouvé, procéder au traitement complet (split -> ocr -> clean)
    log_orchestrator_message(f"{message_prefix} Aucun fichier de sortie trouvé. Démarrage du traitement complet.", "INFO")

    split_success = run_child_script(SPLIT_SCRIPT, chapter_unit_path)
    if not split_success:
        return f"{message_prefix} Arrêt suite à l'échec de la division des images."

    ocr_success = run_child_script(OCR_SCRIPT, chapter_unit_path)
    if not ocr_success:
        return f"{message_prefix} Arrêt suite à l'échec de l'OCR."
    
    # Nettoyage des images traitées après OCR, car elles ne sont plus nécessaires
    cleanup_intermediate_folders(chapter_unit_path, [PROCESSED_IMAGES_SUBFOLDER_NAME])

    clean_success = run_child_script(CLEAN_SCRIPT, chapter_unit_path)
    if not clean_success:
        return f"{message_prefix} Arrêt suite à l'échec du nettoyage du texte."

    # Nettoyage des fichiers OCR bruts après nettoyage
    cleanup_intermediate_folders(chapter_unit_path, [OUTPUT_TEXT_SUBFOLDER_NAME])

    # Mettre à jour le fichier de progression pour ce livre
    last_processed_chapters_map[book_folder_name] = chapter_unit_path
    save_last_processed_chapters(last_processed_chapters_map)

    return f"{message_prefix} Traitement de l'unité de chapitre terminé."

# --- Processus principal ---
log_orchestrator_message("--- Démarrage de l'Orchestrateur de traitement de livres (PARALLELISE) ---", level="INFO")
log_orchestrator_message(f"Répertoire global des livres : {GLOBAL_BOOKS_ROOT_DIR}", level="INFO")
log_orchestrator_message(f"Unités de chapitre traitées en parallèle : {MAX_CONCURRENT_CHAPTER_UNITS}", level="INFO")


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
    log_orchestrator_message(f"Chargement des points de reprise pour {len(last_processed_chapters_by_book)} livres.", "INFO")
    for book_name, progress_status in last_processed_chapters_by_book.items():
        if progress_status is True:
            log_orchestrator_message(f"  Livre '{book_name}': Marqué comme ENTIÈREMENT TRAITÉ.", "INFO")
        else:
            log_orchestrator_message(f"  Livre '{book_name}': Dernier chapitre traité '{os.path.basename(progress_status)}'", "INFO")
else:
    log_orchestrator_message("Aucun point de reprise trouvé. Démarrage complet du traitement.", "INFO")


all_futures = []
book_chapter_units_map = {}

with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_CHAPTER_UNITS) as executor:
    # 1. Phase de Détection et Soumission des Tâches
    for book_folder_name in sorted(os.listdir(GLOBAL_BOOKS_ROOT_DIR), key=natsort_key):
        book_folder_path = os.path.join(GLOBAL_BOOKS_ROOT_DIR, book_folder_name)

        if not os.path.isdir(book_folder_path):
            log_orchestrator_message(f"IGNORÉ (élément racine non-répertoire) : '{book_folder_name}'.", "INFO")
            continue

        if book_folder_name.lower() in EXCLUDE_DIR_NAMES:
            log_orchestrator_message(f"IGNORÉ : Le répertoire '{book_folder_name}' est exclu par nom.", "INFO")
            continue

        # --- NOUVELLE LOGIQUE : Sauter le livre entier si marqué comme COMPLET ---
        if last_processed_chapters_by_book.get(book_folder_name) is True:
            log_orchestrator_message(f"\n========================================================", level="INFO")
            log_orchestrator_message(f"Livre '{book_folder_name}' marqué comme ENTIÈREMENT TRAITÉ. IGNORE LE PARCOURS DES CHAPITRES.", "INFO")
            log_orchestrator_message(f"========================================================", level="INFO")
            # Ajout du livre à book_chapter_units_map pour la phase de post-traitement (collecte et nettoyage)
            # si tous les chapitres étaient déjà complets. On doit lui fournir la liste complète des chapitres
            # pour qu'il puisse faire le nettoyage final même s'ils n'ont pas été traités dans cette session.
            # Pour cela, il faut qu'on liste les chapitres une fois pour cette situation.
            chapter_units_for_this_book_temp = []
            for item_in_book_folder_name in sorted(os.listdir(book_folder_path), key=natsort_key):
                item_in_book_folder_path = os.path.join(book_folder_path, item_in_book_folder_name)
                if os.path.isdir(item_in_book_folder_path) and item_in_book_folder_name.lower() not in EXCLUDE_DIR_NAMES.union({
                    PROCESSED_IMAGES_SUBFOLDER_NAME.lower(), OUTPUT_TEXT_SUBFOLDER_NAME.lower(), 
                    OUTPUT_CLEANED_TEXT_SUBFOLDER_NAME.lower(), FINAL_COLLECTED_TEXTS_SUBFOLDER_NAME.lower(),
                    '__pycache__'}):
                    chapter_units_for_this_book_temp.append(item_in_book_folder_path)
                elif item_in_book_folder_name.lower().endswith('.cbz'): # Les CBZ sont aussi des unités de chapitre
                     chapter_units_for_this_book_temp.append(item_in_book_folder_path) # Leur extraction sera sautée par le run_child_script si le CBZ a déjà été traité.
            book_chapter_units_map[book_folder_path] = chapter_units_for_this_book_temp # Important pour le post-traitement
            continue # Passe au livre suivant

        log_orchestrator_message(f"\n========================================================", level="INFO")
        log_orchestrator_message(f"Début de la détection pour le livre/dossier : {book_folder_name}", level="INFO")
        log_orchestrator_message(f"Chemin du dossier du livre : {book_folder_path}", level="INFO")
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
                log_orchestrator_message(f"  IGNORÉ (sous-dossier de système ou exclu) : '{item_in_book_folder_name}'", "INFO")
                continue
            
            if not os.path.isdir(item_in_book_folder_path) and not item_in_book_folder_name.lower().endswith('.cbz'):
                log_orchestrator_message(f"  IGNORÉ (fichier non CBZ dans dossier livre) : '{item_in_book_folder_name}'", "INFO")
                continue
            
            if os.path.isdir(item_in_book_folder_path):
                chapter_units_for_this_book.append(item_in_book_folder_path)
            
            elif os.path.isfile(item_in_book_folder_path) and item_in_book_folder_name.lower().endswith('.cbz'):
                log_orchestrator_message(f"  Détecté un fichier CBZ dans le dossier livre : '{item_in_book_folder_name}'. Tentative d'extraction...", "INFO")
                extracted_chapter_unit_path = extract_cbz_content(item_in_book_folder_path, book_folder_path)
                if extracted_chapter_unit_path:
                    chapter_units_for_this_book.append(extracted_chapter_unit_path)
                    log_orchestrator_message(f"  CBZ '{item_in_book_folder_name}' extrait et son dossier ajouté à la liste de traitement.", "INFO")
                else:
                    log_orchestrator_message(f"  ÉCHEC d'extraction du CBZ '{item_in_book_folder_name}'. Ce chapitre sera ignoré.", "ERROR")
            
        chapter_units_for_this_book.sort(key=natsort_key)

        if not chapter_units_for_this_book:
            log_orchestrator_message(f"AUCUNE unité de chapitre (dossier ou CBZ) trouvée pour le livre : '{book_folder_name}'.", "WARNING")
            continue

        book_chapter_units_map[book_folder_path] = chapter_units_for_this_book
        
        # --- LOGIQUE DE REPRISE : Filtrer les chapitres déjà traités pour ce livre ---
        chapters_to_submit_for_book = []
        last_processed_status_for_book = last_processed_chapters_by_book.get(book_folder_name) # Peut être un chemin ou True

        if last_processed_status_for_book is True: # Ce cas ne devrait plus être atteint ici, mais en sécurité
            log_orchestrator_message(f"  Livre '{book_folder_name}' est déjà marqué comme ENTIÈREMENT TRAITÉ. (Double vérification).", "INFO")
            chapters_to_submit_for_book = [] # Aucun chapitre à soumettre
        elif last_processed_status_for_book: # C'est un chemin de dernier chapitre traité
            log_orchestrator_message(f"  Point de reprise détecté pour '{book_folder_name}': '{os.path.basename(last_processed_status_for_book)}'.", "INFO")
            found_last_processed = False
            for chapter_path in chapter_units_for_this_book:
                if found_last_processed:
                    chapters_to_submit_for_book.append(chapter_path)
                elif chapter_path == last_processed_status_for_book:
                    found_last_processed = True
                    log_orchestrator_message(f"    Reprise APRES le chapitre '{os.path.basename(chapter_path)}'.", "INFO")
                else:
                    log_orchestrator_message(f"    IGNORÉ (déjà traité) : '{os.path.basename(chapter_path)}'.", "DEBUG")
            
            if not found_last_processed and chapters_to_submit_for_book: 
                # Cas où le dernier chapitre n'est plus trouvé MAIS il y a des chapitres à soumettre
                # Cela signifie que le point de reprise est corrompu ou le chapitre a été déplacé
                log_orchestrator_message(f"AVERTISSEMENT : Le dernier chapitre traité '{os.path.basename(last_processed_status_for_book)}' n'a pas été trouvé dans la liste actuelle des chapitres de '{book_folder_name}'. Reprise à partir du premier chapitre non traité (si existant).", "WARNING")
                # Pas besoin de remettre chapter_units_for_this_book entier, car chapters_to_submit_for_book contient déjà la suite
            elif not found_last_processed and not chapters_to_submit_for_book:
                 # Cas où le dernier chapitre n'est plus trouvé ET il n'y a plus de chapitres après.
                 # Cela peut arriver si le livre est considéré comme fini mais n'avait pas le flag True.
                 log_orchestrator_message(f"AVERTISSEMENT : Point de reprise '{os.path.basename(last_processed_status_for_book)}' non trouvé et plus de chapitres à traiter. Livre potentiellement incomplet.", "WARNING")

        else: # Aucun point de reprise, traiter tout le livre
            chapters_to_submit_for_book = chapter_units_for_this_book


        if not chapters_to_submit_for_book:
            log_orchestrator_message(f"  Tous les chapitres de '{book_folder_name}' ont déjà été traités ou aucun nouveau chapitre à soumettre.", "INFO")
        else:
            log_orchestrator_message(f"Soumission de {len(chapters_to_submit_for_book)} unités de chapitre pour '{book_folder_name}' au pool de traitement...", "INFO")
            for chapter_unit_path in chapters_to_submit_for_book:
                future = executor.submit(_process_single_chapter_unit, chapter_unit_path, book_folder_name, last_processed_chapters_by_book)
                all_futures.append(future)

    log_orchestrator_message("\n--- Toutes les tâches de traitement de chapitre soumises. Attente de la complétion... ---", "INFO")
    for future in as_completed(all_futures):
        result_message = future.result()
        log_orchestrator_message(result_message, "INFO")

log_orchestrator_message("\n--- Démarrage de la phase de post-traitement des livres ---", "INFO")
for book_folder_path, chapter_units_list in sorted(book_chapter_units_map.items(), key=lambda item: natsort_key(os.path.basename(item[0]))):
    book_folder_name = os.path.basename(book_folder_path)
    
    # Vérifier si le livre a été entièrement traité avant de collecter et nettoyer
    # Logique mise à jour pour utiliser le flag True du fichier de progression
    is_book_marked_as_complete = last_processed_chapters_by_book.get(book_folder_name) is True

    if is_book_marked_as_complete:
        log_orchestrator_message(f"\n--- LIVRE '{book_folder_name}' est marqué comme ENTIÈREMENT TRAITÉ. Post-traitement (collecte/nettoyage) relancé pour assurer la propreté. ---", "INFO")
        # Même si marqué complet, on relance collecte/nettoyage au cas où un nettoyage précédent aurait échoué.
        # On n'a pas besoin de revérifier tous les chapitres car le flag True nous dit que c'est bon.
        collect_final_texts(book_folder_path, chapter_units_list)

        for chapter_unit_path_for_cleanup in chapter_units_list:
            cleanup_intermediate_folders(chapter_unit_path_for_cleanup, [OUTPUT_TEXT_SUBFOLDER_NAME, OUTPUT_CLEANED_TEXT_SUBFOLDER_NAME])
            if chapter_unit_path_for_cleanup.endswith('_unzipped'):
                cleanup_intermediate_folders(chapter_unit_path_for_cleanup, ["."])

        log_orchestrator_message(f"\n========================================================", level="INFO")
        log_orchestrator_message(f"Traitement complet du livre : {book_folder_name}", level="INFO")
        log_orchestrator_message(f"========================================================", level="INFO")
    else:
        # Si le livre n'est PAS marqué comme complet (soit pas du tout, soit a un point de reprise)
        # On vérifie si TOUS les chapitres ont été traités dans cette session
        all_chapters_processed_in_this_run = True
        for chapter_path in chapter_units_list:
            cleaned_txt_source_dir = os.path.join(chapter_path, OUTPUT_CLEANED_TEXT_SUBFOLDER_NAME)
            if not (os.path.exists(cleaned_txt_source_dir) and any(f.lower().endswith('.txt') for f in os.listdir(cleaned_txt_source_dir))):
                all_chapters_processed_in_this_run = False
                break
        
        if all_chapters_processed_in_this_run:
            log_orchestrator_message(f"\n--- LIVRE '{book_folder_name}' : Tous les chapitres traités dans cette session. Phase de post-traitement démarrée. ---", "INFO")
            collect_final_texts(book_folder_path, chapter_units_list)

            for chapter_unit_path_for_cleanup in chapter_units_list:
                cleanup_intermediate_folders(chapter_unit_path_for_cleanup, [OUTPUT_TEXT_SUBFOLDER_NAME, OUTPUT_CLEANED_TEXT_SUBFOLDER_NAME])
                if chapter_unit_path_for_cleanup.endswith('_unzipped'):
                    cleanup_intermediate_folders(chapter_unit_path_for_cleanup, ["."])

            log_orchestrator_message(f"\n========================================================", level="INFO")
            log_orchestrator_message(f"Traitement complet du livre : {book_folder_name}", level="INFO")
            log_orchestrator_message(f"========================================================", level="INFO")
            # MARQUER LE LIVRE COMME COMPLET APRÈS LA COLLECTE ET LE NETTOYAGE FINAL
            last_processed_chapters_by_book[book_folder_name] = True 
            save_last_processed_chapters(last_processed_chapters_by_book) # Sauvegarder l'état complet
        else:
            log_orchestrator_message(f"\n--- LIVRE '{book_folder_name}' INCOMPLET. Phase de post-traitement ignorée. ---", "WARNING")


log_orchestrator_message("\n--- Tous les livres détectés et traités ont été terminés ---", level="INFO")
log_orchestrator_message(f"Vérifiez le fichier de log principal '{ORCHESTRATOR_LOG_FILE_PATH}' et les logs spécifiques dans chaque unité de chapitre.", level="INFO")
log_orchestrator_message(f"Les erreurs sont consignées dans '{GLOBAL_ERROR_LOG_FILE_PATH}'.", "INFO")
log_orchestrator_message(f"Les points de reprise sont dans '{PROGRESS_LOG_FILE_PATH}'.", "INFO")