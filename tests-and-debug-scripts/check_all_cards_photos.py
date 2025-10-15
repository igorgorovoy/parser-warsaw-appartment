#!/usr/bin/env python3
"""Check all cards for photos"""

import requests
from bs4 import BeautifulSoup

base_search_url = "https://www.olx.pl/nieruchomosci/mieszkania/wynajem/warszawa/?search[filter_enum_rooms][0]=three&search[filter_float_price:from]=4000&search[filter_float_price:to]=6000"

print("="*80)
print("CHECKING ALL CARDS FOR PHOTOS")
print("="*80)

response = requests.get(base_search_url, timeout=30)
soup = BeautifulSoup(response.text, 'html.parser')

cards = soup.find_all('div', {'data-cy': 'l-card'})
print(f"Found {len(cards)} total cards\n")

cards_with_photo = 0
cards_without_photo = 0

for i, card in enumerate(cards, 1):
    # Title
    title_elem = card.find('h4') or card.find('h6')
    title = title_elem.get_text(strip=True) if title_elem else 'No title'
    
    # Check for image
    img_elem = card.find('img', src=True)
    
    if img_elem:
        img_src = img_elem.get('src', '')
        if img_src and img_src.startswith('http'):
            cards_with_photo += 1
            if i <= 5:  # Show first 5
                print(f"✅ {i}. {title[:60]}")
                print(f"   Photo: {img_src[:80]}...")
        else:
            cards_without_photo += 1
            print(f"⚠️  {i}. {title[:60]}")
            print(f"   Has img but no valid src: {img_src[:50]}")
    else:
        cards_without_photo += 1
        print(f"❌ {i}. {title[:60]}")
        print(f"   NO IMG ELEMENT")

print()
print("="*80)
print(f"SUMMARY:")
print(f"  Cards with photo:    {cards_with_photo}")
print(f"  Cards without photo: {cards_without_photo}")
print(f"  Total:               {len(cards)}")
print("="*80)

