import tkinter as tk
from tkinter import filedialog, messagebox
import os
import sys
import subprocess
import importlib
import locale

# Obtenez le chemin du répertoire du script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Remontez d'un niveau pour atteindre la racine du projet
project_root = os.path.join(script_dir, os.path.pardir)

# Ajoutez la racine du projet au chemin de recherche des modules de Python
sys.path.append(project_root)

# L'importation de 'config' est maintenant possible
import config

# Détermine la langue préférée de l'utilisateur
system_locale = locale.getlocale()
user_lang = system_locale[0][:2] if system_locale and system_locale[0] else 'en'

# Importe le module de messages de la bonne langue.
# Le chemin d'importation est relatif au répertoire de l'interface.
try:
    messages_module = importlib.import_module(f"localization.locales.{user_lang}.gui_{user_lang}_messages")
    strings = messages_module.GUI_MESSAGES
except (ImportError, FileNotFoundError):
    try:
        messages_module = importlib.import_module("localization.locales.en.gui_en_messages")
        strings = messages_module.GUI_MESSAGES
    except (ImportError, FileNotFoundError):
        messagebox.showerror("Erreur critique", "Le fichier de langue par défaut (anglais) est introuvable. L'application ne peut pas démarrer.")
        exit()

def create_ui():
    """Crée l'interface utilisateur et gère les événements."""
    window = tk.Tk()
    window.title(strings["WINDOW_TITLE"])

    # Fonction pour sauvegarder la configuration
    def save_config():
        try:
            values = {
                '-ORCHESTRATOR_LOG_FILE_PATH-': path_var_1.get(),
                '-GLOBAL_ERROR_LOG_FILE_PATH-': path_var_2.get(),
                '-PROGRESS_LOG_FILE_PATH-': path_var_3.get(),
                '-GLOBAL_BOOKS_ROOT_DIR-': path_var_4.get(),
                '-SCRIPTS_DIR-': path_var_5.get(),
                '-OCR_LANGUAGE-': ocr_lang_var.get(),
                '-MAX_IMAGE_HEIGHT-': max_height_var.get(),
                '-EXCLUDE_DIR_NAMES-': exclude_dirs_var.get(),
                '-MAX_CONCURRENT_CHAPTER_UNITS-': max_units_var.get()
            }
            
            # Utilisation du chemin absolu pour écrire dans le fichier config.py
            config_path = os.path.join(project_root, 'config.py')
            with open(config_path, 'w') as f:
                f.write(f"# config.py\n\n")
                f.write(f"# --- Global path for the files of the Orchestrator ---\n")
                f.write(f"ORCHESTRATOR_LOG_FILE_PATH = '{values['-ORCHESTRATOR_LOG_FILE_PATH-'].replace('\\', '\\\\')}'\n")
                f.write(f"GLOBAL_ERROR_LOG_FILE_PATH = '{values['-GLOBAL_ERROR_LOG_FILE_PATH-'].replace('\\', '\\\\')}'\n")
                f.write(f"PROGRESS_LOG_FILE_PATH = '{values['-PROGRESS_LOG_FILE_PATH-'].replace('\\', '\\\\')}'\n")
                f.write(f"GLOBAL_BOOKS_ROOT_DIR = '{values['-GLOBAL_BOOKS_ROOT_DIR-'].replace('\\', '\\\\')}'\n")
                f.write(f"SCRIPTS_DIR = '{values['-SCRIPTS_DIR-'].replace('\\', '\\\\')}'\n\n")
                f.write(f"# --- Paramèters for the OCR and the treatement for the image ---\n")
                f.write(f"OCR_LANGUAGE = '{values['-OCR_LANGUAGE-']}'\n")
                f.write(f"MAX_IMAGE_HEIGHT = {int(values['-MAX_IMAGE_HEIGHT-'])}\n\n")
                f.write(f"# --- Name of the subdirectories (shouldn't be modified) ---\n")
                f.write(f"PROCESSED_IMAGES_SUBFOLDER_NAME = '{config.PROCESSED_IMAGES_SUBFOLDER_NAME}'\n")
                f.write(f"OUTPUT_TEXT_SUBFOLDER_NAME = '{config.OUTPUT_TEXT_SUBFOLDER_NAME}'\n")
                f.write(f"OUTPUT_CLEANED_TEXT_SUBFOLDER_NAME = '{config.OUTPUT_CLEANED_TEXT_SUBFOLDER_NAME}'\n")
                f.write(f"# --- Name of the final subdirectory for the text files ---\n")
                f.write(f"FINAL_COLLECTED_TEXTS_SUBFOLDER_NAME = '{config.FINAL_COLLECTED_TEXTS_SUBFOLDER_NAME}'\n\n")
                f.write(f"# --- exclusion folder List---\n")
                excluded_dirs = str(set(item.strip() for item in values['-EXCLUDE_DIR_NAMES-'].split(',')))
                f.write(f"EXCLUDE_DIR_NAMES = {excluded_dirs}\n\n")
                f.write(f"# --- Paramèters parallel treatement  ---\n")
                f.write(f"MAX_CONCURRENT_CHAPTER_UNITS = {int(values['-MAX_CONCURRENT_CHAPTER_UNITS-'])}\n")
            
            messagebox.showinfo(strings["SUCCESS"], strings["SAVE_SUCCESS_MESSAGE"])

        except ValueError:
            messagebox.showerror(strings["ERROR"], strings["FORMAT_ERROR_MESSAGE"])
        except Exception as e:
            messagebox.showerror(strings["ERROR"], strings["GENERAL_ERROR"] + str(e))

    # Fonction pour lancer le script
    def launch_script():
        script_path = os.path.join(values['-SCRIPTS_DIR-'], 'orchestrator.py')
        if not os.path.exists(script_path):
            messagebox.showerror(strings["LAUNCH_ERROR"], strings["SCRIPT_NOT_FOUND_ERROR"] + f" {script_path}")
        else:
            try:
                subprocess.Popen(['python', script_path])
                window.destroy()
            except Exception as e:
                messagebox.showerror(strings["LAUNCH_ERROR"], strings["SCRIPT_LAUNCH_ERROR"] + str(e))

    # Variables pour stocker les valeurs
    path_var_1 = tk.StringVar(value=config.ORCHESTRATOR_LOG_FILE_PATH)
    path_var_2 = tk.StringVar(value=config.GLOBAL_ERROR_LOG_FILE_PATH)
    path_var_3 = tk.StringVar(value=config.PROGRESS_LOG_FILE_PATH)
    path_var_4 = tk.StringVar(value=config.GLOBAL_BOOKS_ROOT_DIR)
    path_var_5 = tk.StringVar(value=config.SCRIPTS_DIR)
    ocr_lang_var = tk.StringVar(value=config.OCR_LANGUAGE)
    max_height_var = tk.StringVar(value=config.MAX_IMAGE_HEIGHT)
    exclude_dirs_var = tk.StringVar(value=", ".join(config.EXCLUDE_DIR_NAMES))
    max_units_var = tk.StringVar(value=config.MAX_CONCURRENT_CHAPTER_UNITS)

    # Création et positionnement des widgets
    row_idx = 0
    # Section Chemins d'accès
    tk.Label(window, text=strings["WINDOW_TITLE"]).grid(row=row_idx, columnspan=3, sticky='w')
    
    row_idx += 1
    tk.Label(window, text=strings["ORCHESTRATOR_LOG_FILE_PATH"]).grid(row=row_idx, column=0, sticky='w')
    tk.Entry(window, textvariable=path_var_1, width=50).grid(row=row_idx, column=1)
    tk.Button(window, text=strings["BROWSE_BUTTON"], command=lambda: path_var_1.set(filedialog.askopenfilename())).grid(row=row_idx, column=2)

    row_idx += 1
    tk.Label(window, text=strings["GLOBAL_ERROR_LOG_FILE_PATH"]).grid(row=row_idx, column=0, sticky='w')
    tk.Entry(window, textvariable=path_var_2, width=50).grid(row=row_idx, column=1)
    tk.Button(window, text=strings["BROWSE_BUTTON"], command=lambda: path_var_2.set(filedialog.askopenfilename())).grid(row=row_idx, column=2)

    row_idx += 1
    tk.Label(window, text=strings["PROGRESS_LOG_FILE_PATH"]).grid(row=row_idx, column=0, sticky='w')
    tk.Entry(window, textvariable=path_var_3, width=50).grid(row=row_idx, column=1)
    tk.Button(window, text=strings["BROWSE_BUTTON"], command=lambda: path_var_3.set(filedialog.askopenfilename())).grid(row=row_idx, column=2)

    row_idx += 1
    tk.Label(window, text=strings["GLOBAL_BOOKS_ROOT_DIR"]).grid(row=row_idx, column=0, sticky='w')
    tk.Entry(window, textvariable=path_var_4, width=50).grid(row=row_idx, column=1)
    tk.Button(window, text=strings["BROWSE_BUTTON"], command=lambda: path_var_4.set(filedialog.askdirectory())).grid(row=row_idx, column=2)
    
    row_idx += 1
    tk.Label(window, text=strings["SCRIPTS_DIR"]).grid(row=row_idx, column=0, sticky='w')
    tk.Entry(window, textvariable=path_var_5, width=50).grid(row=row_idx, column=1)
    tk.Button(window, text=strings["BROWSE_BUTTON"], command=lambda: path_var_5.set(filedialog.askdirectory())).grid(row=row_idx, column=2)

    row_idx += 1
    tk.Label(window, text="").grid(row=row_idx, column=0)

    # Section Paramètres OCR
    row_idx += 1
    tk.Label(window, text=strings["OCR_LANGUAGE"]).grid(row=row_idx, column=0, sticky='w')
    tk.Entry(window, textvariable=ocr_lang_var, width=50).grid(row=row_idx, column=1)

    row_idx += 1
    tk.Label(window, text=strings["MAX_IMAGE_HEIGHT"]).grid(row=row_idx, column=0, sticky='w')
    tk.Entry(window, textvariable=max_height_var, width=50).grid(row=row_idx, column=1)

    row_idx += 1
    tk.Label(window, text="").grid(row=row_idx, column=0)

    # Section Paramètres de traitement
    row_idx += 1
    tk.Label(window, text=strings["EXCLUDE_DIRS"]).grid(row=row_idx, column=0, sticky='w')
    tk.Entry(window, textvariable=exclude_dirs_var, width=50).grid(row=row_idx, column=1)

    row_idx += 1
    tk.Label(window, text=strings["MAX_CONCURRENT_CHAPTER_UNITS"]).grid(row=row_idx, column=0, sticky='w')
    tk.Entry(window, textvariable=max_units_var, width=50).grid(row=row_idx, column=1)

    row_idx += 1
    tk.Label(window, text="").grid(row=row_idx, column=0)

    # Boutons d'action
    button_frame = tk.Frame(window)
    tk.Button(button_frame, text=strings["SAVE_BUTTON"], command=save_config).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text=strings["LAUNCH_BUTTON"], command=launch_script).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text=strings["QUIT_BUTTON"], command=window.destroy).pack(side=tk.LEFT, padx=5)
    button_frame.grid(row=row_idx, columnspan=3, pady=10)

    window.mainloop()

if __name__ == "__main__":
    create_ui()