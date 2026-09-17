import json

print("Loading bioclip TreeOfLifeClassifier to extract families locally...")
try:
    import torch
    import os
    os.environ["HF_HOME"] = os.path.join(os.getcwd(), "models")
    os.environ["TORCH_HOME"] = os.path.join(os.getcwd(), "models")
    if os.name == 'nt':
        torch.compile = lambda x, **kwargs: x
    from bioclip import TreeOfLifeClassifier
    classifier = TreeOfLifeClassifier()
except Exception as e:
    print("Error loading bioclip:", e)
    exit(1)

# Build a mapping of sci_name -> family from local model taxonomy
sci_to_family = {}
for cls in classifier.classes:
    sci = cls.get('scientific_name') or cls.get('species') or cls.get('classification')
    family = cls.get('family', 'Unknown')
    if sci:
        sci_to_family[sci] = family

print(f"Built local taxonomy map with {len(sci_to_family)} species.")

# Update china_birds.json
try:
    with open('china_birds.json', 'r', encoding='utf8') as f:
        birds = json.load(f)
except Exception as e:
    print("Error loading china_birds.json:", e)
    exit(1)

matched = 0
for sci_name, data in birds.items():
    if sci_name in sci_to_family:
        data['family'] = sci_to_family[sci_name]
        matched += 1
    else:
        # For birds not in the local model, set to Unknown
        data['family'] = 'Unknown'

with open('china_birds.json', 'w', encoding='utf8') as f:
    json.dump(birds, f, ensure_ascii=False, indent=2)

print(f"Successfully added 'family' to china_birds.json. Matched {matched}/{len(birds)} birds locally.")
