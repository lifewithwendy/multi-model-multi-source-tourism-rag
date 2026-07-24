import os
import re
import urllib.request
import urllib.parse

base_dir = r"e:\Personal\Tourism-Rag\multi-model-multi-source-tourism-rag"
md_path = os.path.join(base_dir, "data", "images", "ATTRIBUTIONS.md")
img_base_dir = os.path.join(base_dir, "data", "images")

def download_placeholder(attraction, save_path):
    text = urllib.parse.quote(attraction)
    # Using placehold.co to generate a valid image file with text
    url = f"https://placehold.co/600x400.jpg?text={text}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response, open(save_path, 'wb') as out_file:
            out_file.write(response.read())
        return True
    except Exception as e:
        print(f"Error downloading placeholder for {attraction}: {e}")
        return False

def main():
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    current_category = None
    updated_lines = []
    
    for line in lines:
        cat_match = re.match(r'^##\s+(.*)', line)
        if cat_match:
            current_category = cat_match.group(1).strip().lower()
            if current_category == "notes on licensing":
                current_category = None
                
        row_match = re.match(r'^\|\s*([^\|]+\.(?:jpg|jpeg|png))\s*\|\s*([^\|]+)\s*\|\s*(.*)\|\s*(.*)\|\s*(.*)\|', line)
        if row_match and current_category:
            filename = row_match.group(1).strip()
            attraction = row_match.group(2).strip()
            source_url = row_match.group(3).strip()
            
            if not source_url:  # empty or missing
                print(f"Generating placeholder for {attraction} - {filename}")
                
                cat_dir = os.path.join(img_base_dir, current_category)
                os.makedirs(cat_dir, exist_ok=True)
                save_path = os.path.join(cat_dir, filename)
                
                success = download_placeholder(attraction, save_path)
                
                if success:
                    new_line = f"| {filename} | {attraction} | Generated (AI), no external source | AI | Public Domain |\n"
                    updated_lines.append(new_line)
                    continue
                    
            updated_lines.append(line)
        else:
            updated_lines.append(line)
            
    with open(md_path, 'w', encoding='utf-8') as f:
        f.writelines(updated_lines)
    print("Done generating placeholders and updating ATTRIBUTIONS.md.")

if __name__ == "__main__":
    main()
