import os
import time
import json
from flask import Flask, render_template, request, jsonify
from PIL import Image
import io

# Try to import CLIP dependencies
try:
    import torch
    from transformers import CLIPProcessor, CLIPModel
    CLIP_AVAILABLE = True
except ImportError:
    CLIP_AVAILABLE = False
    print("Warning: Torch or Transformers not found. Falling back to mock analysis.")

app = Flask(__name__)

# --- Configuration ---
MODEL_ID = "openai/clip-vit-base-patch32"
device = "cpu" # Default to CPU for broader compatibility

# Global model variables
model = None
processor = None

def load_model():
    global model, processor, device
    if CLIP_AVAILABLE and model is None:
        print("Loading CLIP model...")
        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model = CLIPModel.from_pretrained(MODEL_ID).to(device)
            processor = CLIPProcessor.from_pretrained(MODEL_ID)
            print(f"CLIP model loaded on {device}.")
        except Exception as e:
            print(f"Failed to load CLIP model: {e}")

# --- Data & Prompts ---

# Prompts provided by user
CLIP_PROMPTS = {
    "nucleus": "a labeled biology textbook diagram of a cell nucleus, showing nucleolus and nuclear membrane",
    "mitochondria": "a biology textbook diagram of a mitochondrion, bean-shaped organelle that produces ATP",
    "ribosomes": "a biology textbook diagram showing ribosomes, small dots involved in protein synthesis",
    "endoplasmic_reticulum": "a labeled diagram of the endoplasmic reticulum in a cell, showing rough and smooth ER",
    "golgi_apparatus": "a biology textbook diagram of the Golgi apparatus, flattened membrane sacs that modify and package proteins",
    "lysosome": "a labeled diagram of a lysosome, a small spherical organelle responsible for waste digestion",
    "chloroplast": "a biology textbook diagram of a chloroplast, green organelle responsible for photosynthesis",
    "cell_membrane": "a labeled diagram of the cell membrane, thin flexible layer controlling movement of substances",
    "cell_wall": "a biology textbook diagram of the cell wall, rigid outer layer providing support and protection"
}

# Database for detailed info
ORGANELLE_DB = {
    "mitochondria": {
        "name": "Mitochondria",
        "structure": "Double membrane-bound organelle with inner folds called cristae.",
        "function": "Produces energy (ATP) through cellular respiration. Known as the powerhouse of the cell.",
        "diseases": "Mitochondrial diseases can affect energy production (e.g., Leigh syndrome).",
        "fun_fact": "Mitochondria have their own DNA, separate from the nucleus!"
    },
    "nucleus": {
        "name": "Nucleus",
        "structure": "Double membrane-bound organelle containing chromatin and nucleolus. Has nuclear pores.",
        "function": "Stores genetic material (DNA) and coordinates cell activities like growth and reproduction.",
        "diseases": "Progeria, genetic disorders linked to chromosomal mutations.",
        "fun_fact": "The nucleus is often the largest organelle in animal cells."
    },
    "chloroplast": {
        "name": "Chloroplast",
        "structure": "Contains chlorophyll and thylakoids stacked into grana.",
        "function": "Conducts photosynthesis to produce food (glucose) for the plant using sunlight.",
        "diseases": "Chlorosis (yellowing of leaves due to lack of chlorophyll).",
        "fun_fact": "Chloroplasts are thought to have originated from cyanobacteria."
    },
    "ribosomes": {
        "name": "Ribosomes",
        "structure": "Small particles consisting of RNA and associated proteins, found in cytoplasm or on rough ER.",
        "function": "The site of protein synthesis (translation).",
        "diseases": "Ribosomopathies (e.g., Diamond-Blackfan anemia).",
        "fun_fact": "Ribosomes are found in both prokaryotic and eukaryotic cells."
    },
    "endoplasmic_reticulum": {
        "name": "Endoplasmic Reticulum (ER)",
        "structure": "Network of membranous tubules and sacs. Rough ER has ribosomes; Smooth ER does not.",
        "function": "Rough ER: Protein synthesis and folding. Smooth ER: Lipid synthesis and detoxification.",
        "diseases": "ER stress is linked to neurodegenerative diseases like Alzheimer's.",
        "fun_fact": "The ER membrane is continuous with the nuclear envelope."
    },
    "golgi_apparatus": {
        "name": "Golgi Apparatus",
        "structure": "Stack of flattened membrane-bound sacs called cisternae.",
        "function": "Modifies, sorts, and packages proteins and lipids for secretion or delivery to other organelles.",
        "diseases": "Achondrogenesis (skeletal disorder).",
        "fun_fact": "Named after Camillo Golgi, who discovered it in 1898."
    },
    "lysosome": {
        "name": "Lysosome",
        "structure": "Spherical vesicle containing hydrolytic enzymes.",
        "function": "Digests waste materials, cellular debris, and foreign invaders.",
        "diseases": "Lysosomal storage diseases (e.g., Tay-Sachs disease).",
        "fun_fact": "Lysosomes act as the waste disposal system of the cell."
    },
    "cell_membrane": {
        "name": "Cell Membrane",
        "structure": "Phospholipid bilayer with embedded proteins and cholesterol.",
        "function": "Controls movement of substances in and out of the cell; provides protection.",
        "diseases": "Cystic fibrosis (defect in transport protein).",
        "fun_fact": "The fluid mosaic model describes its flexible nature."
    },
    "cell_wall": {
        "name": "Cell Wall",
        "structure": "Rigid outer layer made of cellulose (in plants), chitin (in fungi), or peptidoglycan (in bacteria).",
        "function": "Provides structural support, protection, and prevents over-expansion.",
        "diseases": "N/A (Primarily structural in plants/bacteria).",
        "fun_fact": "Animal cells do not have cell walls, which allows them to be more flexible."
    }
}

# --- Routes ---

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/api/analyze', methods=['POST'])
def analyze_image():
    if 'files' not in request.files:
        return jsonify({"error": "No files part"}), 400
    
    files = request.files.getlist('files')
    results = []
    
    # Ensure model is loaded if available
    if CLIP_AVAILABLE and model is None:
        load_model()

    for file in files:
        filename = file.filename
        
        # Identify organelle
        if CLIP_AVAILABLE and model is not None:
            try:
                # Read image
                image_bytes = file.read()
                image = Image.open(io.BytesIO(image_bytes))
                
                # Prepare text prompts
                labels = list(CLIP_PROMPTS.keys())
                text_prompts = list(CLIP_PROMPTS.values())
                
                # Process inputs
                inputs = processor(
                    text=text_prompts, 
                    images=image, 
                    return_tensors="pt", 
                    padding=True
                ).to(device)
                
                # Inference
                with torch.no_grad():
                    outputs = model(**inputs)
                
                # Calculate probabilities
                logits_per_image = outputs.logits_per_image # this is the image-text similarity score
                probs = logits_per_image.softmax(dim=1) # we can take the softmax to get the label probabilities
                
                # Get top prediction
                score, idx = probs[0].topk(1)
                predicted_key = labels[idx.item()]
                confidence = float(score.item())
                
                # File pointer reset for other uses if needed (though we consumed it)
                file.seek(0)
                
            except Exception as e:
                print(f"Error during CLIP inference: {e}")
                predicted_key = "nucleus" # Fallback
                confidence = 0.0
        else:
            # Mock fallback if libraries are missing
            time.sleep(0.5)
            fname_lower = filename.lower()
            if 'mito' in fname_lower: predicted_key = 'mitochondria'
            elif 'chloro' in fname_lower: predicted_key = 'chloroplast'
            elif 'ribo' in fname_lower: predicted_key = 'ribosomes'
            elif 'er' in fname_lower or 'endoplasmic' in fname_lower: predicted_key = 'endoplasmic_reticulum'
            elif 'golgi' in fname_lower: predicted_key = 'golgi_apparatus'
            elif 'lyso' in fname_lower: predicted_key = 'lysosome'
            elif 'wall' in fname_lower: predicted_key = 'cell_wall'
            elif 'membrane' in fname_lower: predicted_key = 'cell_membrane'
            else: predicted_key = 'nucleus'
            confidence = 0.92

        # Retrieve data
        data = ORGANELLE_DB.get(predicted_key, ORGANELLE_DB['nucleus'])
        
        results.append({
            "filename": filename,
            "detected_text": [data['name'], "Text detection placeholder"], # Placeholder for OCR
            "organelle": data,
            "confidence": round(confidence, 4)
        })

    return jsonify({"results": results})

if __name__ == '__main__':
    # Optional: Preload model on startup
    # if CLIP_AVAILABLE:
    #     load_model()
    app.run(debug=True, port=5000)
