import os
import shutil
import datetime

# --- CONFIGURATION (DOIT CORRESPONDRE À orchestrator.py) ---
GLOBAL_BOOKS_ROOT_DIR = 'D:\\novel' # Le répertoire racine de vos livres

# Noms des sous-dossiers intermédiaires à supprimer
PROCESSED_IMAGES_SUBFOLDER_NAME = 'images_processed'
OUTPUT_TEXT_SUBFOLDER_NAME = 'sortieTXT'
OUTPUT_CLEANED_TEXT_SUBFOLDER_NAME = 'sortieTXT_cleaned'

# Noms des dossiers de sortie finaux (À NE PAS SUPPRIMER)
FINAL_COLLECTED_TEXTS_SUBFOLDER_NAME = 'final_texts'

# Noms des répertoires à exclure du traitement (DOIT CORRESPONDRE à EXCLUDE_DIR_NAMES dans orchestrator.py)
EXCLUDE_DIR_NAMES = {"traiter", "script", "backup", "temp"} 

# Optionnel : Mettez True si vous voulez AUSSI supprimer les dossiers "_unzipped"
DELETE_UNZIPPED_FOLDERS = False 

# --- Fichier de log pour ce script de nettoyage ---
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
            log_cleanup_message(f"    Dossier supprimé : {os.path.basename(folder_path)}")
            return True
        except Exception as e:
            log_cleanup_message(f"    ERREUR lors de la suppression de {os.path.basename(folder_path)}: {e}", "ERROR")
            return False
    else:
        log_cleanup_message(f"    Dossier '{os.path.basename(folder_path)}' non trouvé, pas de nettoyage nécessaire.", "INFO")
        return False

def natsort_key(s):
    # Petite fonction pour trier naturellement (si vous l'avez utilisée dans orchestrator)
    import re # Importation locale car elle est petite et spécifique ici
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

# --- Processus principal de nettoyage ---
if __name__ == "__main__":
    log_cleanup_message("--- Démarrage du script de nettoyage ---")
    log_cleanup_message(f"Répertoire racine à nettoyer : {GLOBAL_BOOKS_ROOT_DIR}")
    log_cleanup_message(f"Suppression des dossiers _unzipped activée : {DELETE_UNZIPPED_FOLDERS}")

    if os.path.exists(CLEANUP_LOG_FILE):
        os.remove(CLEANUP_LOG_FILE) # Nettoyer le log précédent

    # Combinaison de tous les dossiers à exclure par nom (y compris final_texts car on ne veut pas le supprimer)
    all_excluded_by_name = EXCLUDE_DIR_NAMES.union({FINAL_COLLECTED_TEXTS_SUBFOLDER_NAME.lower()})

    processed_count = 0
    skipped_count = 0

    for book_folder_name in sorted(os.listdir(GLOBAL_BOOKS_ROOT_DIR), key=natsort_key):
        book_folder_path = os.path.join(GLOBAL_BOOKS_ROOT_DIR, book_folder_name)

        if not os.path.isdir(book_folder_path):
            log_cleanup_message(f"IGNORÉ (élément racine non-répertoire) : '{book_folder_name}'.", "INFO")
            skipped_count += 1
            continue

        if book_folder_name.lower() in all_excluded_by_name:
            log_cleanup_message(f"IGNORÉ (dossier exclu par nom) : '{book_folder_name}'.", "INFO")
            skipped_count += 1
            continue

        log_cleanup_message(f"\n=========================================================")
        log_cleanup_message(f"Nettoyage du livre/dossier : {book_folder_name}")
        log_cleanup_message(f"=========================================================")

        # Nettoyer les sous-dossiers intermédiaires DANS le dossier du livre lui-même (si existants)
        clean_folder(os.path.join(book_folder_path, PROCESSED_IMAGES_SUBFOLDER_NAME))
        clean_folder(os.path.join(book_folder_path, OUTPUT_TEXT_SUBFOLDER_NAME))
        clean_folder(os.path.join(book_folder_path, OUTPUT_CLEANED_TEXT_SUBFOLDER_NAME))

        # Parcourir les sous-dossiers des chapitres dans ce livre (pour les *_unzipped et autres intermédiaires)
        for chapter_item_name in sorted(os.listdir(book_folder_path), key=natsort_key):
            chapter_item_path = os.path.join(book_folder_path, chapter_item_name)

            if not os.path.isdir(chapter_item_path):
                continue # N'opère que sur les dossiers

            # Exclure les dossiers systèmes/finaux du nettoyage au niveau des chapitres
            if chapter_item_name.lower() in all_excluded_by_name:
                log_cleanup_message(f"  IGNORÉ (sous-dossier de système ou exclu) : '{chapter_item_name}'", "INFO")
                continue

            log_cleanup_message(f"  -> Traitement de l'unité de chapitre : {chapter_item_name}")
            
            # Supprimer les dossiers intermédiaires à l'intérieur de l'unité de chapitre
            clean_folder(os.path.join(chapter_item_path, PROCESSED_IMAGES_SUBFOLDER_NAME))
            clean_folder(os.path.join(chapter_item_path, OUTPUT_TEXT_SUBFOLDER_NAME))
            clean_folder(os.path.join(chapter_item_path, OUTPUT_CLEANED_TEXT_SUBFOLDER_NAME))

            # Logique pour supprimer les dossiers _unzipped si l'option est activée
            if DELETE_UNZIPPED_FOLDERS and chapter_item_name.lower().endswith('_unzipped'):
                log_cleanup_message(f"    Suppression du dossier _unzipped : {chapter_item_name}")
                clean_folder(chapter_item_path) # Supprime le dossier _unzipped lui-même
        
        processed_count += 1

    log_cleanup_message("\n--- Nettoyage terminé ! ---")
    log_cleanup_message(f"Total de dossiers de livres traités : {processed_count}")
    log_cleanup_message(f"Total de dossiers de livres ignorés : {skipped_count}")
    log_cleanup_message(f"Vérifiez le fichier '{CLEANUP_LOG_FILE}' pour le détail des opérations.")
