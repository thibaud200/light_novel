import subprocess
import sys
import importlib.util
import argparse
from collections import defaultdict

def check_and_install_dependencies():
    """
    Vérifie si les dépendances nécessaires sont installées et les installe si ce n'est pas le cas.
    """
    required_packages = {
        "ebooklib": "EbookLib", # format: {module_name: package_name_for_pip}
        "lxml": "lxml"          # lxml is an EbookLib dependancy
    }

    print("Checking and installing dependancies if needed...")

    for module_name, package_name in required_packages.items():
        if importlib.util.find_spec(module_name) is None:
            print(f"The dependancy '{package_name}' ({module_name}) was not found. Installation en progress...")
            try:
                # Execute pip for package install
                subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
                print(f"'{package_name}' installed with success.")
            except subprocess.CalledProcessError as e:
                print(f"ERREUR : Impossible to install '{package_name}'. Check manual install with 'pip install {package_name}'.")
                print(f"Error details : {e}")
                sys.exit(1)
        else:
            print(f"The dependancy '{package_name}' ({module_name}) is already installed.")
