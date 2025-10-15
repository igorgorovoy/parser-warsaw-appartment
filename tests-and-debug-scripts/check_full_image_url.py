#!/usr/bin/env python3
"""Check full image URL from Otodom"""

import requests
from bs4 import BeautifulSoup

url = "https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie/mazowieckie/warszawa/warszawa/warszawa/srodmiescie?roomsNumber=%5B3%5D&priceMin=4000&priceMax=6000"

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}

response = requests.get(url, headers=headers, timeout=30)
soup = BeautifulSoup(response.text, 'html.parser')

# Find first listing
listing_links = soup.find_all('a', {'data-cy': 'listing-item-link'})

if listing_links:
    link = listing_links[0]
    parent = link.find_parent('article')
    
    if parent:
        img_elem = parent.find('img', src=True)
        
        if img_elem:
            print("="*80)
            print("FULL IMAGE URL:")
            print("="*80)
            img_src = img_elem.get('src', '')
            print(f"Length: {len(img_src)} characters")
            print(f"Full URL:\n{img_src}")
            print("="*80)
            
            # Check if URL starts with http
            if img_src.startswith('http'):
                print("✅ Valid HTTP URL")
            else:
                print("❌ NOT a valid HTTP URL")
                print(f"Starts with: {img_src[:50]}")

