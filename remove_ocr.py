import sys

file_path = r"pages\1_⚡_Electricite.py"

try:
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Block 1: Imports
        if "try:" in line and "from google import genai" in lines[i+1]:
            # Skip until except block ends
            new_lines.append("HAS_OCR_LIBS = False\n")
            while i < len(lines) and "HAS_OCR_LIBS = False" not in lines[i]:
                i += 1
            i += 1 # skip that line too
            continue
            
        # Block 2: Section OCR UI
        if "st.markdown(\"### 📷 Scanner une facture (OCR)\")" in line:
            # Add dummy helper instead
            new_lines.append("    # --- Section OCR (Désétactivée) ---\n")
            new_lines.append("    if 'ocr_data' not in st.session_state:\n")
            new_lines.append("        st.session_state.ocr_data = {}\n")
            new_lines.append("\n")
            new_lines.append("    def get_ocr_val(key, default):\n")
            new_lines.append("        return default\n\n")
            
            # Skip until the end of the OCR try/except block
            while i < len(lines) and "st.error(f\"Erreur lors de l'analyse OCR: {e}\")" not in lines[i]:
                i += 1
            i += 1 # skip the error line
            continue
            
        new_lines.append(line)
        i += 1

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
        
    print("✅ Sections OCR commentées/supprimées avec succès.")
except Exception as e:
    print(f"❌ Erreur: {e}")
    sys.exit(1)
