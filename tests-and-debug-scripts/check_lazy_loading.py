#!/usr/bin/env python3
"""Check if OLX uses lazy loading for images"""

import requests
from bs4 import BeautifulSoup

url = "https://www.olx.pl/nieruchomosci/mieszkania/wynajem/warszawa/?search[filter_enum_rooms][0]=three&search[filter_float_price:from]=4000&search[filter_float_price:to]=6000"

print("="*80)
print("CHECKING LAZY LOADING ATTRIBUTES")
print("="*80)

response = requests.get(url, timeout=30)
soup = BeautifulSoup(response.text, 'html.parser')

cards = soup.find_all('div', {'data-cy': 'l-card'})
print(f"Found {len(cards)} cards\n")

# Check first card without photo
for i, card in enumerate(cards[5:15], 6):  # Cards 6-15 (without photo according to previous test)
    title_elem = card.find('h4') or card.find('h6')
    title = title_elem.get_text(strip=True) if title_elem else 'No title'
    
    print(f"{i}. {title[:60]}")
    
    # Find all img tags
    imgs = card.find_all('img')
    
    for img in imgs:
        print(f"   IMG element:")
        print(f"      src: {img.get('src', 'N/A')[:80]}")
        print(f"      data-src: {img.get('data-src', 'N/A')[:80]}")
        print(f"      data-srcset: {img.get('data-srcset', 'N/A')[:80]}")
        print(f"      srcset: {img.get('srcset', 'N/A')[:80]}")
        print(f"      loading: {img.get('loading', 'N/A')}")
        
        # Check all data-* attributes
        data_attrs = {k: v for k, v in img.attrs.items() if k.startswith('data-')}
        if data_attrs:
            print(f"      All data-* attributes: {list(data_attrs.keys())}")
    
    print()
    
    if i >= 8:  # Show only 3 examples
        break

print("="*80)

