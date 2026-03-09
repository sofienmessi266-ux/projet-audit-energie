@echo off
echo Installation de PyInstaller...
pip install pyinstaller

echo.
echo ==========================================
echo Creation de l'executable en cours...
echo Cela peut prendre plusieurs minutes.
echo ==========================================
echo.

REM Commande PyInstaller avec les parametres necessaires pour Streamlit
pyinstaller --onefile ^
--collect-all streamlit ^
--collect-all google.genai ^
--add-data "app.py;." ^
--add-data "database.py;." ^
--add-data "pages;pages" ^
--hidden-import pandas ^
--hidden-import plotly ^
--hidden-import scikit-learn ^
--name "Audit_Energetique" ^
run_app.py

echo.
echo ==========================================
echo TERMINE !
echo L'application se trouve dans le dossier "dist"
echo Vous pouvez copier le fichier "Audit_Energetique.exe"
echo et "audit_energetique.db" pour le donner a quelqu'un!
echo ==========================================
pause
