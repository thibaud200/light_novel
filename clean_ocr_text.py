import os
import re
import datetime
import argparse

parser = argparse.ArgumentParser(description="Script pour nettoyer le texte OCR d'UNE SEULE unité de chapitre.")
parser.add_argument('--chapter_unit', type=str, required=True,
                    help='Chemin du répertoire de l\'unité de chapitre (ex: C:\\novel\\MonLivre\\Chapter 01 ou C:\\novel\\MonLivre\\MonArchive_unzipped).')
args = parser.parse_args()
CHAPTER_UNIT_DIR = args.chapter_unit

OUTPUT_TEXT_SUBFOLDER_NAME = 'sortieTXT'
INPUT_TEXT_DIR = os.path.join(CHAPTER_UNIT_DIR, OUTPUT_TEXT_SUBFOLDER_NAME)

OUTPUT_CLEANED_TEXT_SUBFOLDER_NAME = 'sortieTXT_cleaned'
OUTPUT_CLEANED_TEXT_DIR = os.path.join(CHAPTER_UNIT_DIR, OUTPUT_CLEANED_TEXT_SUBFOLDER_NAME)

ERROR_LOG_FILE = os.path.join(CHAPTER_UNIT_DIR, 'clean_errors.log') 

def log_error(message, filename="N/A"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] [UNITÉ_CHAPITRE: {os.path.basename(CHAPTER_UNIT_DIR)}] [FICHIER: {filename}] ERREUR: {message}"
    
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
    print(f"Dossier de sortie pour textes nettoyés créé : {OUTPUT_CLEANED_TEXT_DIR}\n")

if os.path.exists(ERROR_LOG_FILE):
    os.remove(ERROR_LOG_FILE)
    print(f"Fichier de log '{ERROR_LOG_FILE}' précédent supprimé.\n")

print(f"Démarrage du post-traitement du texte pour l'unité : {os.path.basename(CHAPTER_UNIT_DIR)}")
print(f"Les fichiers nettoyés seront sauvegardés dans : {OUTPUT_CLEANED_TEXT_DIR}\n")

if not os.path.exists(INPUT_TEXT_DIR):
    log_error(f"Le dossier de textes OCR '{OUTPUT_TEXT_SUBFOLDER_NAME}' n'a pas été trouvé dans l'unité de chapitre.", "N/A")
else:
    for filename in os.listdir(INPUT_TEXT_DIR):
        if not filename.lower().endswith('.txt'):
            print(f"  ATTENTION : '{filename}' n'est pas un fichier .txt et sera ignoré.")
            continue
        
        input_filepath = os.path.join(INPUT_TEXT_DIR, filename)
        output_filepath = os.path.join(OUTPUT_CLEANED_TEXT_DIR, filename)

        print(f"Traitement du fichier : {filename}")

        try:
            with open(input_filepath, 'r', encoding='utf-8') as f:
                raw_text = f.read()
            
            cleaned_text = clean_text(raw_text)

            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write(cleaned_text)
            
            print(f"  Nettoyage réussi : '{filename}' -> '{os.path.basename(output_filepath)}'")

        except Exception as e:
            log_error(f"Erreur lors du nettoyage de '{filename}' : {e}", filename)

print(f"\n--- Post-traitement du texte pour '{os.path.basename(CHAPTER_UNIT_DIR)}' terminé ---")
print(f"Vérifiez le fichier '{ERROR_LOG_FILE}' pour les erreurs.")