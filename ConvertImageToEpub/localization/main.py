import locale
import importlib

def get_preferred_language():
    """Détecte la langue préférée de l'utilisateur."""
    try:
        lang, _ = locale.getdefaultlocale()
        if lang:
            return lang.split('_')[0].lower()
    except (ValueError, locale.Error):
        pass
    
    # Langue par défaut si la détection échoue
    return 'en'

def get_translator():
    """Charge les chaînes de caractères localisées et retourne une fonction de traduction."""
    lang = get_preferred_language()
    
    try:
        # Tente d'importer le module de la langue détectée en utilisant le nom de fichier correct
        module = importlib.import_module(f".locales.{lang}.{lang}_messages", package="localization")
    except (ImportError, KeyError):
        # Si la langue n'est pas disponible, charge le module par défaut (anglais)
        print(f"Attention : La langue '{lang}' n'est pas supportée. Utilisation de la langue par défaut 'en'.")
        module = importlib.import_module(".locales.en.en_messages", package="localization")

    def _(key):
        return getattr(module, key, key)
    
    return _