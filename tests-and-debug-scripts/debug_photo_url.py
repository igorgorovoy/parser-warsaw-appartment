#!/usr/bin/env python3
"""Debug photo URL extraction from OLX"""

import requests
from bs4 import BeautifulSoup

# Test the specific listing from screenshot
url = "https://www.olx.pl/d/oferta/wynajme-mieszkanie-3-pokojowe-plac-szembeka-ID17Pt577"

print("="*80)
print("DEBUGGING PHOTO URL EXTRACTION")
print("="*80)
print(f"URL: {url}")
print()

try:
    response = requests.get(url, timeout=30)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Save for inspection
    with open('debug_listing_page.html', 'w', encoding='utf-8') as f:
        f.write(soup.prettify())
    
    # Try to find images
    print("Looking for images...")
    
    # Method 1: Find all img tags
    images = soup.find_all('img')
    print(f"\nFound {len(images)} img tags")
    
    for i, img in enumerate(images[:5], 1):
        src = img.get('src', '')
        srcset = img.get('srcset', '')
        alt = img.get('alt', '')
        
        if 'apollo.olxcdn.com' in src or 'otocdn' in src:
            print(f"\n{i}. Image found:")
            print(f"   src: {src[:120]}")
            if srcset:
                print(f"   srcset: {srcset[:120]}")
            if alt:
                print(f"   alt: {alt[:60]}")
    
    print("\n" + "="*80)
    print("Saved HTML to debug_listing_page.html")
    print("="*80)
    
except Exception as e:
    print(f"Error: {e}")

