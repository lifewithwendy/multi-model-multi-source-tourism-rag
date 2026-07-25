import os
import re
import urllib.request
import urllib.parse
import json
import time

base_dir = r"e:\Personal\Tourism-Rag\multi-model-multi-source-tourism-rag"
md_path = os.path.join(base_dir, "data", "images", "ATTRIBUTIONS.md")
img_base_dir = os.path.join(base_dir, "data", "images")

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
WIKIMEDIA_REFERER = 'https://commons.wikimedia.org/'

def search_wikimedia_images(query, count=2):
    time.sleep(2)  # rate limit to avoid 429
    url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrnamespace": 6,
        "gsrsearch": f"{query} Sri Lanka",
        "gsrlimit": max(10, count*3),
        "prop": "imageinfo",
        "iiprop": "url|extmetadata",
        # Ask Commons for a thumbnail URL instead of the original upload URL.
        # Wikimedia recommends thumbnails for automated downloads to reduce rate limiting.
        "iiurlwidth": 1200,
    }
    
    query_string = urllib.parse.urlencode(params)
    full_url = f"{url}?{query_string}"
    
    req = urllib.request.Request(full_url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print(f"HTTP 429 Too Many Requests for {query}. Sleeping 5s...")
            time.sleep(5)
            # Retry once
            try:
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read().decode())
            except Exception as inner_e:
                print(f"Retry failed for {query}: {inner_e}")
                return []
        else:
            print(f"Error fetching data for {query}: {e}")
            return []
    except Exception as e:
        print(f"Error fetching data for {query}: {e}")
        return []
        
    results = []
    if "query" in data and "pages" in data["query"]:
        pages = data["query"]["pages"]
        for page_id, page_data in pages.items():
            if "imageinfo" in page_data:
                info = page_data["imageinfo"][0]
                img_url = info.get("url")
                download_url = info.get("thumburl", img_url)
                
                if not download_url or not download_url.lower().endswith(('.jpg', '.jpeg', '.png')):
                    continue
                    
                extmetadata = info.get("extmetadata", {})
                author = extmetadata.get("Artist", {}).get("value", "Unknown")
                author = re.sub(r'<[^>]+>', '', author).strip()
                author = author.replace('|', '-') # sanitize for markdown table
                
                license_name = extmetadata.get("LicenseShortName", {}).get("value", "Unknown")
                license_name = license_name.replace('|', '-')
                
                desc_url = info.get("descriptionurl", "")
                desc_url = desc_url.replace('|', '%7C')
                
                results.append({
                    "url": download_url,
                    "author": author,
                    "license": license_name,
                    "source_url": desc_url
                })
            if len(results) >= count:
                break
    return results

def download_image(url, save_path, referer=None):
    time.sleep(6) # slower pacing helps avoid Wikimedia robot-policy throttling
    headers = {
        'User-Agent': USER_AGENT,
    }
    if referer:
        headers['Referer'] = referer
    else:
        headers['Referer'] = WIKIMEDIA_REFERER

    req = urllib.request.Request(
        url,
        headers=headers,
    )
    try:
        with urllib.request.urlopen(req) as response, open(save_path, 'wb') as out_file:
            out_file.write(response.read())
        return True
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print(f"HTTP 429 Too Many Requests for {url}. Sleeping 20s...")
            time.sleep(20)
            try:
                with urllib.request.urlopen(req) as response, open(save_path, 'wb') as out_file:
                    out_file.write(response.read())
                return True
            except Exception as inner_e:
                print(f"Retry failed for {url}: {inner_e}")
                return False
        else:
            print(f"Error downloading {url}: {e}")
            return False
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False


def row_needs_download(source_url, author, license_name):
    return not source_url.strip() or not author.strip() or not license_name.strip()

def main():
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    current_category = None
    attraction_cache = {}  # {attraction_name: [img_info1, img_info2]}
    
    updated_lines = []
    
    for line in lines:
        cat_match = re.match(r'^##\s+(.*)', line)
        if cat_match:
            current_category = cat_match.group(1).strip().lower()
            if current_category == "notes on licensing":
                current_category = None
                
        # match table row: | diyaluma_1.jpg | Diyaluma Falls | | | |
        row_match = re.match(r'^\|\s*([^\|]+\.(?:jpg|jpeg|png))\s*\|\s*([^\|]+)\s*\|\s*(.*)\|\s*(.*)\|\s*(.*)\|', line)
        if row_match and current_category:
            filename = row_match.group(1).strip()
            attraction = row_match.group(2).strip()
            
            source_url = row_match.group(3).strip()
            author = row_match.group(4).strip()
            license_name = row_match.group(5).strip()

            if row_needs_download(source_url, author, license_name):
                print(f"Processing {attraction} - {filename}")
                
                if attraction not in attraction_cache:
                    print(f"  Fetching from Wikimedia...")
                    images = search_wikimedia_images(attraction, count=2)
                    while len(images) < 2:
                        images.append({})
                    attraction_cache[attraction] = images
                
                img_info = {}
                if attraction_cache[attraction]:
                    img_info = attraction_cache[attraction].pop(0)
                
                if img_info and 'url' in img_info:
                    cat_dir = os.path.join(img_base_dir, current_category)
                    os.makedirs(cat_dir, exist_ok=True)
                    save_path = os.path.join(cat_dir, filename)
                    already_downloaded = os.path.exists(save_path) and os.path.getsize(save_path) > 0
                    
                    if already_downloaded:
                        print(f"  Skipping existing file {save_path}")
                        success = True
                    else:
                        print(f"  Downloading {img_info['url']} to {save_path}")
                        success = download_image(img_info['url'], save_path, img_info.get('source_url'))
                    
                    if success:
                        new_line = f"| {filename} | {attraction} | {img_info['source_url']} | {img_info['author']} | {img_info['license']} |\n"
                        updated_lines.append(new_line)
                        continue
                        
            updated_lines.append(line)
        else:
            updated_lines.append(line)
            
    with open(md_path, 'w', encoding='utf-8') as f:
        f.writelines(updated_lines)
    print("Done updating ATTRIBUTIONS.md and downloading images.")

if __name__ == "__main__":
    main()
