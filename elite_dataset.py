import requests
import os
import time
import re
import logging
import datetime
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
from PIL.ExifTags import TAGS

# --- 1. LOGGING AND ERROR TRACKING ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[logging.FileHandler("multi_source.log"), logging.StreamHandler()]
)

HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

# --- 2. HISTORY AND EXIF VERIFICATION TOOLS ---
def fix_metadata(filepath, year, month):
    """Synchronizes file date to history."""
    try:
        past_date = datetime.datetime(year, month, 1, 12, 0, 0)
        ts = past_date.timestamp()
        os.utime(filepath, (ts, ts))
    except: pass

def validate_image(filepath, target_year):
    """Checks EXIF year discrepancy."""
    try:
        with Image.open(filepath) as img:
            exif = img._getexif()
            if exif:
                for tag, value in exif.items():
                    if TAGS.get(tag) == "DateTimeOriginal":
                        if int(value.split(':')[0]) != target_year:
                            return False
        return os.path.getsize(filepath) > 20000 # Exclude files smaller than 20 KB
    except: return True

# --- 3. SOURCE FUNCTIONS ---
def get_wiki_links(y, m_name, limit):
    links = []
    try:
        url = "https://commons.wikimedia.org/w/api.php"
        q = f"action=query&format=json&list=search&srsearch=\"{m_name} {y}\"&srlimit={limit}&srnamespace=6"
        data = requests.get(f"{url}?{q}", headers=HEADERS).json()
        for item in data.get('query', {}).get('search', []):
            img_res = requests.get(url, params={"action":"query", "format":"json", "prop":"imageinfo", "titles":item['title'], "iiprop":"url"}, headers=HEADERS).json()
            p = img_res.get('query', {}).get('pages', {})
            for pid in p:
                u = p[pid].get('imageinfo', [{}])[0].get('url')
                if u: links.append(u)
    except: pass
    return links

def get_bing_links(y, m_name, limit):
    try:
        res = requests.get(f"https://www.bing.com/images/search?q={m_name}+{y}+photography", headers=HEADERS)
        return re.findall(r'murl&quot;:&quot;(http.*?)&quot;', res.text)[:limit]
    except: return []

# --- 4. DOWNLOAD TASK ---
def download_unit(url, folder, filename, year, month):
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200 and 'image' in res.headers.get('Content-Type', ''):
            path = os.path.join(folder, filename)
            with open(path, 'wb') as f: f.write(res.content)
            if validate_image(path, year):
                fix_metadata(path, year, month)
                return True
            if os.path.exists(path): os.remove(path)
    except: pass
    return False

# --- 5. MAIN MOTOR ---
def start_pipeline(year, month_name, month_idx):
    path = f"datasets/{year}/{month_name}"
    os.makedirs(path, exist_ok=True)
    
    # GATTE LINKS from both sources
    wiki_links = get_wiki_links(year, month_name, 60)
    bing_links = get_bing_links(year, month_name, 60)
    all_links = list(set(wiki_links + bing_links)) # Clean the repeaters
    
    count = 0
    with ThreadPoolExecutor(max_workers=10) as executor:
        tasks = [executor.submit(download_unit, u, path, f"img_{i}.jpg", year, month_idx) for i, u in enumerate(all_links)]
        for t in tasks:
            if t.result(): count += 1
            if count >= 100: break
    
    logging.info(f"{month_name} {year}: {count}/100 Photo downloaded (Hybrid Source).")

# --- RUN ---
months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
for year in range(2010, 2026):
    for i, month in enumerate(months):
        start_pipeline(year, month, i + 1)