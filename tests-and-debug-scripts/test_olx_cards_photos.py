#!/usr/bin/env python3
"""Test if OLX cards have photos"""

import requests
from bs4 import BeautifulSoup

url = "https://www.olx.pl/nieruchomosci/mieszkania/wynajem/warszawa/?search[filter_enum_rooms][0]=three&search[filter_float_price:from]=4000&search[filter_float_price:to]=6000&search[district_id]=359&search[filter_enum_furniture][0]=yes&search[filter_enum_pets][0]=Tak&search[private_business]=private"

print("="*80)
print("TESTING OLX CARDS FOR PHOTOS")
print("="*80)

response = requests.get(url, timeout=30)
soup = BeautifulSoup(response.text, 'html.parser')

cards = soup.find_all('div', {'data-cy': 'l-card'})
print(f"Found {len(cards)} cards\n")

for i, card in enumerate(cards[:5], 1):
    # Title
    title_elem = card.find('h4') or card.find('h6')
    title = title_elem.get_text(strip=True) if title_elem else 'No title'
    
    # URL
    link_elem = card.find('a', href=True)
    url = link_elem['href'] if link_elem else 'No URL'
    if not url.startswith('http'):
        url = 'https://www.olx.pl' + url
    
    # Image
    img_elem = card.find('img', src=True)
    
    print(f"{i}. {title[:60]}")
    print(f"   URL: {url[:80]}")
    
    if img_elem:
        img_src = img_elem.get('src', '')
        srcset = img_elem.get('srcset', '')
        
        print(f"   ✅ Image found:")
        print(f"      src: {img_src[:100]}")
        if srcset:
            urls = [part.strip().split()[0] for part in srcset.split(',') if part.strip()]
            print(f"      srcset URLs: {len(urls)} variants")
            if urls:
                print(f"      First URL: {urls[0][:100]}")
    else:
        print(f"   ❌ NO IMAGE FOUND")
    
    print()

print("="*80)

