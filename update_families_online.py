import json
import torch
import os
import PIL.Image
from torchvision import transforms

os.environ["HF_HOME"] = os.path.join(os.getcwd(), "models")
os.environ["TORCH_HOME"] = os.path.join(os.getcwd(), "models")

if os.name == 'nt':
    torch.compile = lambda x, **kwargs: x

from bioclip import TreeOfLifeClassifier, Rank

print("Loading bioclip model...")
classifier = TreeOfLifeClassifier()

print("Generating dummy image to extract taxonomy...")
temp_path = "dummy.jpg"
img = PIL.Image.new('RGB', (224, 224), color='black')
img.save(temp_path)

print("Running prediction to get taxonomy...")
predictions = classifier.predict(temp_path, rank=Rank.SPECIES, k=15000, min_prob=0.0)

if os.path.exists(temp_path):
    os.remove(temp_path)
    
sci_to_family = {}
for pred in predictions:
    sci = pred.get("scientific_name") or pred.get("species") or pred.get("classification")
    fam = pred.get("family", "Unknown")
    if sci:
        sci_to_family[sci] = fam
        
print(f"Extracted taxonomy for {len(sci_to_family)} species from model.")

try:
    with open('china_birds.json', 'r', encoding='utf8') as f:
        birds = json.load(f)
except:
    birds = {}

matched = 0
for sci_name, data in birds.items():
    if sci_name in sci_to_family:
        data['family'] = sci_to_family[sci_name]
        matched += 1
    else:
        data['family'] = 'Unknown'

with open('china_birds.json', 'w', encoding='utf8') as f:
    json.dump(birds, f, ensure_ascii=False, indent=2)

print(f"Matched {matched}/{len(birds)} birds!")
