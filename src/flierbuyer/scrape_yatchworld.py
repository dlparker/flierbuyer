import requests
import re
from hashlib import md5  # For boat_id
from bs4 import BeautifulSoup

def scrape_yachtworld(model_query):
    url = f"https://www.yachtworld.com/boats-for-sale/make-corsair/model-{model_query}/"
    resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(resp.text, 'html.parser')
    listings = []
    for item in soup.find_all('div', class_='listing-item'):  # Adjust selector
        title = item.find('h3').text.strip()
        if re.search(r'F27|F28', title) and re.search(r'\d{4}', title):  # Filter
            year = int(re.search(r'(\d{4})', title).group(1))
            price_str = item.find('span', class_='price').text.strip('$').replace(',', '')
            price = float(price_str) if price_str.isdigit() else None
            url = item.find('a')['href']
            location = item.find('span', class_='location').text.strip()
            # Scrape detail page for features...
            detail_resp = requests.get(f"https://www.yachtworld.com{url}")
            detail_soup = BeautifulSoup(detail_resp.text, 'html.parser')
            desc = detail_soup.find('div', class_='description').text.lower()
            trailer = 'trailer' in desc
            has_head = 'head' in desc
            features = {'mods': [m for m in ['popup', 'modified'] if m in desc]}  # Expand
            
            boat_id = md5((url + str(year)).encode()).hexdigest()[:8]
            listings.append({
                'boat_id': boat_id, 'url': url, 'model': 'F27' if 'f27' in model_query else 'F28',
                'year': year, 'location': location, 'price': price,
                'trailer': trailer, 'has_head': has_head, 'features': json.dumps(features)
            })
    return listings

# Usage: new_listings = scrape_yachtworld('f-27')
