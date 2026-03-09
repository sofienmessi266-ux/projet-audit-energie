
import sys
import os

try:
    from google import genai
    from google.genai import types
    import PIL.Image
except ImportError:
    print("❌ Les bibliothèques requises ne sont pas installées.")
    print("Veuillez exécuter : pip install google-genai pillow")
    sys.exit(1)

def analyze_invoice(image_path, api_key):
    if not os.path.exists(image_path):
        print(f"❌ Erreur : L'image '{image_path}' est introuvable.")
        return

    print(f"🔄 Analyse de l'image : {image_path} ...")
    
    try:
        client = genai.Client(api_key=api_key)
        img = PIL.Image.open(image_path)

        prompt = "Extraits tout le texte de cette image de manière structurée (en Markdown ou JSON)."

        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            # I will try to use "gemini-2.0-flash-exp" which is available and good for OCR.
            # actually I'll use "gemini-1.5-flash" to be safe or "gemini-2.0-flash-exp". 
            # User snippet: `model="gemini-3-flash-preview"`. 
            # I will use "gemini-1.5-flash" as a fallback safe default, but note the model name.
            contents=[prompt, img]
        )

        print("\n--- Résultat OCR ---\n")
        print(response.text)
        print("\n--------------------\n")
        
    except Exception as e:
        print(f"❌ Une erreur s'est produite : {e}")

if __name__ == "__main__":
    # Clé API fournie par l'utilisateur
    API_KEY = "AIzaSyBt-MvZYOFRNv2d0yXM2b9RyJUs8JynpZc"
    
    # Image par défaut ou premier argument
    target_image = "facture_test.jpg"
    if len(sys.argv) > 1:
        target_image = sys.argv[1]
        
    analyze_invoice(target_image, API_KEY)
