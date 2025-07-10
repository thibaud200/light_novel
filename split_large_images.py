import os
from PIL import Image
import datetime
import argparse
import config

parser = argparse.ArgumentParser(description="Script pour diviser les grandes images en segments gérables pour l'OCR d'UNE SEULE unité de chapitre.")
parser.add_argument('--chapter_unit', type=str, required=True,
                    help='Chemin du répertoire de l\'unité de chapitre (ex: C:\\novel\\MonLivre\\Chapter 01 ou C:\\novel\\MonLivre\\MonArchive_unzipped).')
args = parser.parse_args()
CHAPTER_UNIT_DIR = args.chapter_unit

#PROCESSED_IMAGES_SUBFOLDER_NAME = 'images_processed'
PROCESSED_IMAGES_SUBFOLDER_NAME = config.PROCESSED_IMAGES_SUBFOLDER_NAME
OUTPUT_SPLIT_IMAGES_BASE_DIR = os.path.join(CHAPTER_UNIT_DIR, PROCESSED_IMAGES_SUBFOLDER_NAME)

#MAX_IMAGE_HEIGHT = 10000 # Vous avez confirmé que 10000 fonctionne pour vous.
MAX_IMAGE_HEIGHT = config.MAX_IMAGE_HEIGHT
# NOUVEAU : Extensions d'image cibles pour l'entrée
TARGET_IMAGE_BASENAME = '1' # Nous allons chercher '1.png', '1.jpg', etc.
SUPPORTED_IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.tiff', '.tif') # Ajouter d'autres extensions si besoin

ERROR_LOG_FILE = os.path.join(CHAPTER_UNIT_DIR, 'split_errors.log') 

def log_error(message, image_name="N/A", level="ERROR"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] [UNITÉ_CHAPITRE: {os.path.basename(CHAPTER_UNIT_DIR)}] [IMAGE: {image_name}] {level}: {message}"
    
    with open(ERROR_LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_message + '\n')
    print(f"  {log_message}")

if not os.path.exists(OUTPUT_SPLIT_IMAGES_BASE_DIR):
    os.makedirs(OUTPUT_SPLIT_IMAGES_BASE_DIR)
    print(f"Dossier de sortie pour images divisées créé : {OUTPUT_SPLIT_IMAGES_BASE_DIR}\n")

if os.path.exists(ERROR_LOG_FILE):
    os.remove(ERROR_LOG_FILE)
    print(f"Fichier de log '{ERROR_LOG_FILE}' précédent supprimé.\n")

print(f"Démarrage de la division/préparation de l'unité : {os.path.basename(CHAPTER_UNIT_DIR)}")
print(f"Les images divisées seront sauvegardées dans : {OUTPUT_SPLIT_IMAGES_BASE_DIR}")
print(f"Hauteur maximale autorisée : {MAX_IMAGE_HEIGHT} pixels\n")


# NOUVEAU : Logique pour trouver l'image cible (1.png, 1.jpg, etc.)
original_image_path = None
found_extension = None # Pour stocker l'extension trouvée
for ext in SUPPORTED_IMAGE_EXTENSIONS:
    potential_path = os.path.join(CHAPTER_UNIT_DIR, f"{TARGET_IMAGE_BASENAME}{ext}")
    if os.path.exists(potential_path):
        original_image_path = potential_path
        found_extension = ext # Enregistre l'extension trouvée
        break

if not original_image_path:
    log_error(f"Le fichier cible '{TARGET_IMAGE_BASENAME}.*' avec une extension supportée n'a pas été trouvé dans l'unité de chapitre. Extensions cherchées : {', '.join(SUPPORTED_IMAGE_EXTENSIONS)}", TARGET_IMAGE_BASENAME, level="ERROR")
else:
    image_base_name = os.path.basename(original_image_path)
    try:
        img = Image.open(original_image_path)
        width, height = img.size

        # --- POINT D'AJOUT POUR LE PRÉ-TRAITEMENT DE L'IMAGE (OPTIONNEL) ---
        # Vos images sont déjà en N&B pur, donc ces étapes ne sont pas strictement nécessaires
        # pour la binarisation ou le contraste. Cependant, elles sont utiles pour s'assurer
        # d'un format interne optimal pour PIL et Tesseract, ou pour des images futures.
        
        # Convertir en niveaux de gris si ce n'est pas déjà un mode 'L' (Luminance/Grayscale) ou 'RGB'
        # Tesseract préfère le N&B ou les niveaux de gris pour l'OCR de texte.
        if img.mode != 'L' and img.mode != 'RGB': 
            img = img.convert('L') 
        # Si vous vouliez forcer la binarisation (déjà N&B pour vous):
        # img = img.point(lambda p: 255 if p > 128 else 0) 
        # --- FIN DU POINT D'AJOUT ---

        if height <= MAX_IMAGE_HEIGHT:
            print(f"  Image '{image_base_name}' est de taille gérable ({width}x{height}). Copie sans division.")
            # NOUVEAU : Sauvegarder toujours en PNG pour une consistance optimale avant l'OCR.
            img.save(os.path.join(OUTPUT_SPLIT_IMAGES_BASE_DIR, f"{TARGET_IMAGE_BASENAME}.png"))
        else:
            print(f"  Image '{image_base_name}' est trop grande ({width}x{height}). Division en segments...")
            
            segments_saved_count = 0
            for i in range(0, height, MAX_IMAGE_HEIGHT):
                box = (0, i, width, min(i + MAX_IMAGE_HEIGHT, height))
                segment = img.crop(box)
                
                # Toujours sauvegarder en PNG pour la cohérence et la qualité sans perte
                segment_filename = f"{TARGET_IMAGE_BASENAME}_{str(segments_saved_count + 1).zfill(3)}.png"
                segment_path = os.path.join(OUTPUT_SPLIT_IMAGES_BASE_DIR, segment_filename)
                segment.save(segment_path)
                segments_saved_count += 1
                print(f"    Sauvegardé : {segment_path}")
            
            print(f"  Division terminée : {segments_saved_count} segments créés pour '{os.path.basename(CHAPTER_UNIT_DIR)}'.")

    except Exception as e:
        log_error(f"Erreur lors du traitement : {e}", image_base_name, level="ERROR")

print(f"\n--- Processus de préparation des images pour '{os.path.basename(CHAPTER_UNIT_DIR)}' terminé ---")
print(f"Vérifiez le fichier '{ERROR_LOG_FILE}' pour les erreurs.")