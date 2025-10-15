#!/usr/bin/env python3
"""Test how OLX filters by district"""

import requests
from bs4 import BeautifulSoup

# Test different approaches to filter by district
test_configs = [
    ("Using /q-wola/ (search query)", "https://www.olx.pl/nieruchomosci/mieszkania/wynajem/warszawa/q-wola/?search[filter_enum_rooms][0]=three&search[filter_float_price:from]=4000&search[filter_float_price:to]=6000&search[private_business]=private"),
    
    ("Using /wola/ subdirectory", "https://www.olx.pl/nieruchomosci/mieszkania/wynajem/warszawa/wola/?search[filter_enum_rooms][0]=three&search[filter_float_price:from]=4000&search[filter_float_price:to]=6000&search[private_business]=private"),
    
    ("Using search[district_id] parameter", "https://www.olx.pl/nieruchomosci/mieszkania/wynajem/warszawa/?search[district_id]=373&search[filter_enum_rooms][0]=three&search[filter_float_price:from]=4000&search[filter_float_price:to]=6000&search[private_business]=private"),
]

print("="*80)
print("Testing OLX district filtering methods")
print("="*80)

for name, url in test_configs:
    print(f"\n{name}")
    print("-" * 60)
    print(f"URL: {url[:100]}...")
    
    try:
        response = requests.get(url, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            cards = soup.find_all('div', {'data-cy': 'l-card'})
            
            print(f"Found {len(cards)} listings")
            
            if cards:
                print("\nFirst 5 locations:")
                for i, card in enumerate(cards[:5], 1):
                    location_elem = card.find('p', {'data-testid': 'location-date'})
                    if location_elem:
                        location = location_elem.get_text(strip=True)
                        # Extract just the district part
                        parts = location.split(',')
                        if len(parts) >= 2:
                            district = parts[1].strip().split(' - ')[0]
                            print(f"  {i}. {district}")
                        else:
                            print(f"  {i}. {location}")
                    
                    # Check title for district name
                    title_elem = card.find('h4') or card.find('h6')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        # Check if "Wola" is in title
                        if 'wola' in title.lower() or 'bemowo' in title.lower():
                            print(f"      Title contains: {title[:60]}")
        else:
            print(f"❌ Failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "="*80)
print("Which method correctly filters to only Wola district?")
print("="*80)

