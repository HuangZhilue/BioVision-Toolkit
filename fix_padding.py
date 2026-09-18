import glob
import re

files = glob.glob('*.html')
for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    # We need to remove:
    # padding-left: 80px !important; /* Make room for the floating bar */
    # from the body block in the css
    
    # Simple replace
    new_content = re.sub(r'\s*padding-left:\s*80px\s*!important;\s*/\*.*?\*/', '', content)
    
    with open(file, 'w', encoding='utf-8') as f:
        f.write(new_content)

print('Done replacing padding-left in ' + ', '.join(files))
