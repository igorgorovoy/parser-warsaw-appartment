#!/usr/bin/env python3
"""Test different district filter formats for OLX"""

import requests
from bs4 import BeautifulSoup
import time

# Test different URL formats
test_urls = [
    # Current format
    ("search[district_id]=373", "https://www.olx.pl/nieruchomosci/mieszkania/wynajem/warszawa/?search[district_id]=373&search[filter_enum_rooms][0]=three"),
    
    # Try filter_enum format
    ("filter_enum_district", "https://www.olx.pl/nieruchomosci/mieszkania/wynajem/warszawa/?search[filter_enum_district][0]=373&search[filter_enum_rooms][0]=three"),
    
    # Try without search[] prefix
    ("district_id", "https://www.olx.pl/nieruchomosci/mieszkania/wynajem/warszawa/?district_id=373&search[filter_enum_rooms][0]=three"),
    
    # Try subdirectory approach (district name in URL)
    ("URL subdirectory", "https://www.olx.pl/nieruchomosci/mieszkania/wynajem/warszawa/q-wola/?search[filter_enum_rooms][0]=three"),
]

def test_url(name, url):
    print(f"\n{'='*80}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print('='*80)
    
    try:
        response = requests.get(url, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        cards = soup.find_all('div', {'data-cy': 'l-card'})
        print(f"Found {len(cards)} listings")
        
        if cards:
            print("\nFirst 5 locations:")
            for i, card in enumerate(cards[:5], 1):
                location_elem = card.find('p', {'data-testid': 'location-date'})
                if location_elem:
                    location = location_elem.get_text(strip=True)
                    # Extract district from location
                    parts = location.split(' - ')
                    if len(parts) > 0:
                        district_info = parts[0]
                        print(f"  {i}. {district_info}")
        
        time.sleep(1)  # Be nice to the server
        
    except Exception as e:
        print(f"Error: {e}")

print("Testing different district filter formats for OLX")
print("Looking for Wola district (ID: 373)")

for name, url in test_urls:
    test_url(name, url)

print("\n" + "="*80)
print("CONCLUSION:")
print("="*80)
print("Check which format returns only listings from Wola district")

