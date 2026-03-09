import os
import sys
import streamlit.web.cli as stcli

def resolve_path(path):
    # PyInstaller crée un dossier temporaire dans sys._MEIPASS
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, path)
    return os.path.join(os.path.abspath("."), path)

if __name__ == "__main__":
    # Définir les arguments pour simuler "streamlit run app.py"
    sys.argv = [
        "streamlit",
        "run",
        resolve_path("app.py"),
        "--global.developmentMode=false",
        "--server.headless=true" # Évite d'ouvrir automatiquement le navigateur côté serveur, bien que Streamlit le fasse localement
    ]
    sys.exit(stcli.main())
