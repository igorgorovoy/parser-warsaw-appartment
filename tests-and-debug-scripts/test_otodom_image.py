#!/usr/bin/env python3
"""Test Otodom image extraction"""

import requests
from bs4 import BeautifulSoup

url = "https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie/mazowieckie/warszawa/warszawa/warszawa/srodmiescie?roomsNumber=%5B3%5D&priceMin=4000&priceMax=6000"

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}

print("="*80)
print("TESTING OTODOM IMAGE EXTRACTION")
print("="*80)

response = requests.get(url, headers=headers, timeout=30)
soup = BeautifulSoup(response.text, 'html.parser')

# Find listing links
listing_links = soup.find_all('a', {'data-cy': 'listing-item-link'})
print(f"Found {len(listing_links)} listings\n")

for i, link in enumerate(listing_links[:5], 1):
    # Title
    title_elem = link.find('p', {'data-cy': 'listing-item-title'})
    title = title_elem.get_text(strip=True) if title_elem else 'No title'
    
    # Get parent
    parent = link.find_parent('article')
    
    print(f"{i}. {title[:60]}")
    
    if parent:
        # Look for image
        img_elem = parent.find('img', src=True)
        
        if img_elem:
            img_src = img_elem.get('src', '')
            srcset = img_elem.get('srcset', '')
            data_cy = img_elem.get('data-cy', '')
            
            print(f"   ✅ Image found:")
            print(f"      src: {img_src[:100]}")
            if srcset:
                urls = [part.strip().split()[0] for part in srcset.split(',') if part.strip()]
                print(f"      srcset: {len(urls)} variants")
            if data_cy:
                print(f"      data-cy: {data_cy}")
        else:
            print(f"   ❌ NO IMAGE in parent")
    else:
        print(f"   ❌ NO PARENT ARTICLE")
    
    print()

print("="*80)

