import os
import sys

source_file = "ml_predictor_component.py"
target_file = r"pages\1_⚡_Electricite.py"

try:
    with open(source_file, "r", encoding="utf-8") as f_in:
        content = f_in.read()
        
    with open(target_file, "a", encoding="utf-8") as f_out:
        f_out.write("\n\n")
        f_out.write(content)
        f_out.write("\n")
        
    print(f"✅ Appended {len(content)} characters from {source_file} to {target_file}")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
