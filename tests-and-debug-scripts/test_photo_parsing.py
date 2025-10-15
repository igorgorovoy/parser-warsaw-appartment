#!/usr/bin/env python3
"""Test photo parsing for both OLX and Otodom"""

import requests
from bs4 import BeautifulSoup

# Test OLX
print("="*80)
print("TESTING OLX PHOTO PARSING")
print("="*80)

olx_url = "https://www.olx.pl/nieruchomosci/mieszkania/wynajem/warszawa/?search[filter_enum_rooms][0]=three"
response = requests.get(olx_url, timeout=30)
soup = BeautifulSoup(response.text, 'html.parser')

olx_cards = soup.find_all('div', {'data-cy': 'l-card'})
print(f"Found {len(olx_cards)} OLX cards\n")

for i, card in enumerate(olx_cards[:3], 1):
    title_elem = card.find('h4') or card.find('h6')
    title = title_elem.get_text(strip=True) if title_elem else 'No title'
    
    # Find image
    img_elem = card.find('img', src=True)
    if img_elem:
        img_src = img_elem.get('src', '')
        srcset = img_elem.get('srcset', '')
        print(f"{i}. {title[:50]}")
        print(f"   src: {img_src[:100]}")
        if srcset:
            print(f"   srcset: {srcset[:100]}")
    else:
        print(f"{i}. {title[:50]} - NO IMAGE")
    print()

# Test Otodom
print("\n" + "="*80)
print("TESTING OTODOM PHOTO PARSING")
print("="*80)

otodom_url = "https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie/mazowieckie/warszawa/warszawa/warszawa?roomsNumber=%5B3%5D"
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
response = requests.get(otodom_url, headers=headers, timeout=30)
soup = BeautifulSoup(response.text, 'html.parser')

otodom_links = soup.find_all('a', {'data-cy': 'listing-item-link'})
print(f"Found {len(otodom_links)} Otodom listings\n")

for i, link in enumerate(otodom_links[:3], 1):
    title_elem = link.find('p', {'data-cy': 'listing-item-title'})
    title = title_elem.get_text(strip=True) if title_elem else 'No title'
    
    # Find image in parent
    parent = link.find_parent('article')
    if parent:
        img_elem = parent.find('img', src=True)
        if img_elem:
            img_src = img_elem.get('src', '')
            srcset = img_elem.get('srcset', '')
            data_cy = img_elem.get('data-cy', '')
            print(f"{i}. {title[:50]}")
            print(f"   src: {img_src[:100]}")
            if srcset:
                print(f"   srcset: {srcset[:100]}")
            if data_cy:
                print(f"   data-cy: {data_cy}")
        else:
            print(f"{i}. {title[:50]} - NO IMAGE")
    else:
        print(f"{i}. {title[:50]} - NO PARENT")
    print()

print("\n" + "="*80)
print("✅ Test complete!")
print("="*80)

