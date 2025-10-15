#!/usr/bin/env python3
"""Check why some listings don't have photos"""

import requests
from bs4 import BeautifulSoup

# IDs from screenshot (без фото)
test_ids = [
    "ID16fQR7",  # Apartament 3-pokoje z balkonem
    "ID17N4xE",  # Mieszkanie 3 pokoje 60m2 Mokotów
]

base_search_url = "https://www.olx.pl/nieruchomosci/mieszkania/wynajem/warszawa/?search[filter_enum_rooms][0]=three&search[filter_float_price:from]=4000&search[filter_float_price:to]=6000"

print("="*80)
print("CHECKING LISTINGS WITHOUT PHOTOS")
print("="*80)

response = requests.get(base_search_url, timeout=30)
soup = BeautifulSoup(response.text, 'html.parser')

cards = soup.find_all('div', {'data-cy': 'l-card'})
print(f"Found {len(cards)} total cards\n")

for card in cards[:20]:  # Check first 20
    # Get link
    link_elem = card.find('a', href=True)
    if not link_elem:
        continue
    
    url = link_elem['href']
    if not url.startswith('http'):
        url = 'https://www.olx.pl' + url
    
    # Extract ID
    listing_id = None
    if 'ID' in url:
        parts = url.split('ID')
        if len(parts) > 1:
            listing_id = 'ID' + parts[-1].split('.')[0].split('/')[0].split('?')[0]
    
    # Check if this is one of the problematic IDs
    if listing_id in test_ids:
        # Title
        title_elem = card.find('h4') or card.find('h6')
        title = title_elem.get_text(strip=True) if title_elem else 'No title'
        
        print(f"Found problematic listing: {listing_id}")
        print(f"Title: {title}")
        print(f"URL: {url}")
        
        # Check for image
        img_elem = card.find('img', src=True)
        if img_elem:
            img_src = img_elem.get('src', '')
            srcset = img_elem.get('srcset', '')
            print(f"✅ HAS IMAGE:")
            print(f"   src: {img_src[:100]}")
            if srcset:
                print(f"   srcset: {srcset[:100]}")
        else:
            print(f"❌ NO IMAGE ELEMENT FOUND")
            # Check all img tags in card
            all_imgs = card.find_all('img')
            print(f"   Total img tags: {len(all_imgs)}")
            for i, img in enumerate(all_imgs, 1):
                print(f"   img {i}: src={img.get('src', 'N/A')[:50]}")
        
        print()

print("="*80)

