import os
import re
import json
import shutil
import subprocess
from pathlib import Path

# === CONFIGURATION ===
GLOBAL_BOOKS_ROOT_DIR = r"D:\\novel\\scripts"
CALIBRE_LIBRARY_PATH = r"C:\\Users\\thibs\\Bibliothèque calibre"
CALIBREDB_PATH = r"C:\\Program Files\\Calibre2\\calibredb.exe"
EBOOK_CONVERT_PATH = r"C:\\Program Files\\Calibre2\\ebook-convert.exe"
EBOOK_META_PATH = r"C:\\Program Files\\Calibre2\\ebook-meta.exe"
GLOBAL_EPUB_OUTPUT_DIR = os.path.join(GLOBAL_BOOKS_ROOT_DIR, "sortie")

FINAL_TEXTS_SUBFOLDER_NAME = "final_texts"
EXCLUDE_BOOK_FOLDERS = {"traiter", "script", "backup", "temp", "__pycache__"}
LOG_FILE = os.path.join(GLOBAL_BOOKS_ROOT_DIR, "calibre_automation.log")
PROGRESS_FILE = os.path.join(GLOBAL_BOOKS_ROOT_DIR, "calibre_processed_books.progress")

# === LOGGING ===
def log(msg, level="INFO"):
    line = f"[{level}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

# === UTILITAIRES ===
def natsort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'([0-9]+)', s)]

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_progress(progress):
    temp = PROGRESS_FILE + ".tmp"
    with open(temp, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2)
    shutil.move(temp, PROGRESS_FILE)

# === COMMANDS ===
def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = (result.stdout.strip() + "\n" + result.stderr.strip()).strip()
        return output
    except subprocess.CalledProcessError as e:
        log(f"Erreur commande: {' '.join(cmd)}", level="ERROR")
        if e.stderr:
            log(f"stderr:\n{e.stderr.strip()}", level="ERROR")
        if e.stdout:
            log(f"stdout:\n{e.stdout.strip()}", level="DEBUG")
        return None

def convert_txt_to_epub(txt_path, epub_path):
    output = run_cmd([EBOOK_CONVERT_PATH, txt_path, epub_path, "--output-profile", "tablet"])
    if output is None:
        log(f"Conversion échouée pour {txt_path}", level="ERROR")
        return False
    log(f"Conversion réussie pour {txt_path}", level="DEBUG")
    return True

def set_epub_metadata(epub_path, title, author, series, index):
    return run_cmd([
        EBOOK_META_PATH, epub_path,
        "--title", title,
        "--authors", author,
        "--series", series,
        "--index", str(index)
    ])

def add_to_calibre(epub_path):
    return run_cmd([
        CALIBREDB_PATH, "add", epub_path,
        "--library-path", CALIBRE_LIBRARY_PATH
    ])

def export_from_calibre(book_id, export_dir):
    os.makedirs(export_dir, exist_ok=True)
    return run_cmd([
        CALIBREDB_PATH, "export", str(book_id),
        "--to-dir", export_dir,
        "--library-path", CALIBRE_LIBRARY_PATH
    ])

def remove_from_calibre(book_id):
    return run_cmd([
        CALIBREDB_PATH, "remove", str(book_id),
        "--library-path", CALIBRE_LIBRARY_PATH
    ])

def extract_book_id(output):
    patterns = [
        r"ID:\s*(\d+)",
        r"Ajout des identifiants de livres\s*:\s*(\d+)",
        r"Ajouter les ids de livre(?:\xa0| )*:\s*(\d+)",
        r"Added book ids:\s*\[(\d+)\]"
    ]
    for pattern in patterns:
        match = re.search(pattern, output)
        if match:
            return match.group(1)
    return None

# === Main TREATEMENT ===
def process_book(book_path):
    book_name = os.path.basename(book_path)
    log(f"\n--- Traitement du livre: {book_name} ---")

    progress = load_progress()
    book_progress = progress.get(book_name)

    if book_progress is True:
        log(f"Livre déjà marqué comme traité : {book_name}", level="INFO")
        return

    done_epubs = set()
    failed_epubs = set()

    if isinstance(book_progress, dict):
        done_epubs = set(book_progress.get("success", []))
        failed_epubs = set(book_progress.get("fail", []))

    final_texts = os.path.join(book_path, FINAL_TEXTS_SUBFOLDER_NAME)
    exports = os.path.join(GLOBAL_EPUB_OUTPUT_DIR, book_name)
    os.makedirs(exports, exist_ok=True)

    if not os.path.exists(final_texts):
        log(f"Aucun dossier final_texts pour {book_name}", level="WARNING")
        return

    total, success, skipped = 0, 0, 0
    failures = []

    for fname in sorted(os.listdir(final_texts), key=natsort_key):
        if not fname.lower().endswith(".txt"):
            continue

        chapter_path = os.path.join(final_texts, fname)
        chapter_num_match = re.search(r"(\d+)", fname)
        if not chapter_num_match:
            log(f"Nom de fichier invalide: {fname}", level="WARNING")
            continue

        chapter_index = int(chapter_num_match.group(1))
        new_title = f"{book_name} - Chapter {chapter_index:04d}"
        epub_name = new_title + ".epub"
        epub_path = os.path.join(exports, epub_name)

        if epub_name in done_epubs:
            skipped += 1
            continue

        log(f"Traitement chapitre: {fname} → {epub_name}")
        total += 1
        temp_epub = os.path.join(book_path, f"temp_{chapter_index:04d}.epub")

        try:
            if not convert_txt_to_epub(chapter_path, temp_epub):
                raise Exception("Conversion échouée")

            set_epub_metadata(temp_epub, new_title, "A definir", book_name, chapter_index)

            add_output = add_to_calibre(temp_epub)
            log(f"Sortie brute calibredb add:\n{add_output}", level="DEBUG")
            book_id = extract_book_id(add_output) if add_output else None

            if not book_id:
                match = re.search(r"(\d+)", add_output or "")
                if match:
                    book_id = match.group(1)
                    log(f"✔️ ID récupéré en brut : {book_id}", level="INFO")
                else:
                    log("⚠️ ID non détecté, ajout probablement réussi mais pas exporté", level="WARNING")
                    raise Exception("ID Calibre non détecté")

            final_epub_path = os.path.join(exports, epub_name)
            shutil.copy(temp_epub, final_epub_path)
            remove_from_calibre(book_id)

            success += 1
            done_epubs.add(epub_name)

            # immediate save after success
            progress[book_name] = {
                "success": sorted(done_epubs),
                "fail": sorted(failed_epubs),
                "complete": False  # pas encore fini le livre
            }
            save_progress(progress)

        except Exception as e:
            log(f"Erreur sur le chapitre {epub_name} : {e}", level="ERROR")
            failures.append(epub_name)
            failed_epubs.add(epub_name)
        finally:
            if os.path.exists(temp_epub):
                os.remove(temp_epub)

    # Marque comme complet si pas d’échecs
    progress[book_name] = {
        "success": sorted(done_epubs),
        "fail": sorted(failed_epubs),
        "complete": len(failed_epubs) == 0
    }
    save_progress(progress)

    if progress[book_name]["complete"]:
        log(f"✅ Livre complet traité et marqué comme terminé : {book_name}")
    else:
        log(f"💾 Progression partielle sauvegardée : {len(done_epubs)} chapitres OK, {len(failed_epubs)} échecs")

    log(f"Livre: {book_name} | Total: {total} | Succès: {success} | Ignorés: {skipped} | Échecs: {len(failures)}")
    if failures:
        log(f"Chapitres échoués: {', '.join(failures)}", level="WARNING")
    log(f"--- Fin du traitement du livre: {book_name} ---")

# === EXECUTION ===
if __name__ == "__main__":
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

    progress = load_progress()
    books = [f for f in os.listdir(GLOBAL_BOOKS_ROOT_DIR)
             if os.path.isdir(os.path.join(GLOBAL_BOOKS_ROOT_DIR, f))
             and f.lower() not in EXCLUDE_BOOK_FOLDERS
             and progress.get(f) is not True]

    books = sorted(books, key=natsort_key)

    for book in books:
        process_book(os.path.join(GLOBAL_BOOKS_ROOT_DIR, book))

    log("\n--- Traitement EPUB terminé ---")
