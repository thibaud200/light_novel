import subprocess
import sys
import os
import shutil
from urllib.parse import urlparse
import time
import re

# --- Script Configuration ---
url_file = "link_novels.txt"
error_report_file = "errors_rapport.txt"
root_dir="C:\\novel"

# --- Nom du fichier journal pour cette exécution ---
# Le nom du fichier journal sera unique pour chaque exécution du script
log_file = "log_scrapper.log"

# Le chemin vers l'exécutable de lightnovel-crawler
lnc_executable = shutil.which("lightnovel-crawler")
if lnc_executable is None:
    print("Erreur: L'exécutable 'lightnovel-crawler' n'a pas été trouvé.")
    print("Veuillez vous assurer que votre environnement virtuel est activé.")
    sys.exit(1)

urls_to_process = []
try:
    with open(url_file, 'r') as f:
        urls_to_process = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    print(f"Erreur: Le fichier '{url_file}' est introuvable.")
    sys.exit(1)

if not urls_to_process:
    print("Le fichier ne contient aucune URL.")
    sys.exit(0)

print(f"Lancement de lightnovel-crawler pour {len(urls_to_process)} romans...")
print("Le statut de chaque roman sera vérifié via le journal.")

# Boucler sur chaque URL
for url in urls_to_process:
    print(f"\n--- Traitement de l'URL : {url} ---")
    
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            # Extraction du nom du roman pour le chemin de sortie
            parsed_url = urlparse(url)
            novel_name = os.path.splitext(os.path.basename(parsed_url.path.rstrip('/')))[0]
            output_path = os.path.join(root_dir, novel_name)
            
            # Construire la commande
            command = [
                lnc_executable,
                '--suppress',
                #'-ll',
                '--log-file', log_file,       # Utilisation du nom de fichier correct
                '--output', output_path,
                '--format', 'epub',
                '--all',
                '--source', url,
                '--multi'
            ]
            
            subprocess.run(command, check=True)
            
            # --- Vérification de la réussite via le fichier journal ---
            success = False
            with open(log_file, 'r') as f:
                log_content = f.read()
                match = re.search(r'Chapters:\s+\d+%\|.*\|\s+(\d+)/(\d+)', log_content)
                if match:
                    downloaded_count = int(match.group(1))
                    total_count = int(match.group(2))
                    if downloaded_count == total_count:
                        success = True
            
            if success:
                print(f"Traitement de l'URL {url} réussi à 100%.")
                break
            else:
                print(f"Traitement de l'URL {url} incomplet. Réessai...")
                if attempt == max_retries - 1:
                    raise subprocess.CalledProcessError(1, command)

        except subprocess.CalledProcessError as e:
            print(f"Tentative {attempt + 1}/{max_retries} : Le traitement de l'URL {url} a échoué.")
            if attempt < max_retries - 1:
                print("Attente de 10 secondes avant de réessayer...")
                time.sleep(10)
            else:
                print(f"Échec après {max_retries} tentatives. Passage au roman suivant.")
                with open(error_report_file, 'a') as f:
                    f.write(f"{url}\n")
        
        except Exception as e:
            print(f"Une erreur inattendue s'est produite pour l'URL {url}: {e}")
            with open(error_report_file, 'a') as f:
                f.write(f"{url}\n")
            break

print("\n--- Processus de traitement terminé. ---")
print(f"Les liens en erreur ont été enregistrés dans '{error_report_file}'.")