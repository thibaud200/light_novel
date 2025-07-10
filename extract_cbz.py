import os
import zipfile
import shutil
import datetime

def extract_cbz_content(cbz_file_path, output_parent_dir_for_extraction):
    cbz_name_base = os.path.splitext(os.path.basename(cbz_file_path))[0]
    output_chapter_dir = os.path.join(output_parent_dir_for_extraction, f"{cbz_name_base}_unzipped")

    if os.path.exists(output_chapter_dir):
        print(f"  Dossier d'extraction '{output_chapter_dir}' existe déjà. Suppression du contenu existant pour réextraction.")
        shutil.rmtree(output_chapter_dir)
        
    os.makedirs(output_chapter_dir, exist_ok=True)

    print(f"  Extraction de '{os.path.basename(cbz_file_path)}' vers '{output_chapter_dir}'...")
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
                        print(f"    Renommé '{os.path.basename(first_img_path)}' en '1.png' pour la compatibilité.")
        
        print(f"  Extraction de '{os.path.basename(cbz_file_path)}' terminée.")
        return output_chapter_dir
    
    except zipfile.BadZipFile:
        # log_error_cbz n'est pas définie ici pour le mode standalone, mais l'orchestrateur gère le log
        print(f"[ERROR CBZ EXTRACT] {os.path.basename(cbz_file_path)}: Le fichier CBZ est corrompu ou invalide.")
        return None
    except Exception as e:
        print(f"[ERROR CBZ EXTRACT] {os.path.basename(cbz_file_path)}: Erreur inattendue lors de l'extraction : {e}")
        return None

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extrait le contenu d'un fichier CBZ.")
    parser.add_argument('--cbz_file', type=str, required=True,
                        help='Chemin du fichier CBZ à extraire.')
    parser.add_argument('--output_parent_dir', type=str, required=True,
                        help='Répertoire parent où extraire le contenu (le dossier du livre).')
    args = parser.parse_args()

    def log_error_cbz(message, cbz_file):
        print(f"[ERROR CBZ EXTRACT] {cbz_file}: {message}")

    extracted_path = extract_cbz_content(args.cbz_file, args.output_parent_dir)
    if extracted_path:
        print(f"\nContenu extrait dans : {extracted_path}")
    else:
        print("\nÉchec de l'extraction du CBZ.")