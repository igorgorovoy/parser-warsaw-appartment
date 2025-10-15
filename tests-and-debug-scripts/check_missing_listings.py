#!/usr/bin/env python3
"""
Check why some listings from the screenshot are missing
"""

import os
import sys
import requests
from bs4 import BeautifulSoup
import json
import re
from dotenv import load_dotenv

load_dotenv()

search_url = "https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie/mazowieckie/warszawa?priceMin=4000&priceMax=8000&roomsNumber=%5B3%5D&areaMin=60&areaMax=90"

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}

try:
    response = requests.get(search_url, headers=headers, timeout=10)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find all listing links
    listing_links = soup.find_all('a', href=lambda x: x and '/pl/oferta/' in x)
    
    # Extract districts from JSON
    districts_map = {}
    script_tags = soup.find_all('script', {'id': '__NEXT_DATA__'})
    if script_tags:
        json_data = json.loads(script_tags[0].string)
        if 'props' in json_data and 'pageProps' in json_data['props']:
            data = json_data['props']['pageProps'].get('data', {})
            search_ads = data.get('searchAds', {})
            items = search_ads.get('items', [])
            
            for item in items:
                listing_id = f"ID{item.get('slug', '').split('-ID')[-1]}" if 'ID' in item.get('slug', '') else None
                if listing_id:
                    location = item.get('location', {})
                    reverse_geo = location.get('reverseGeocoding', {})
                    locations = reverse_geo.get('locations', [])
                    
                    district = next((loc['name'] for loc in locations if loc.get('locationLevel') == 'district'), None)
                    if district:
                        districts_map[listing_id] = district
    
    # Listings from screenshot that should be found
    expected_listings = [
        "Trzy duże niezależne pokoje",  # ID4bq16 ✅
        "Apartament Kolejowa, 19 Dzielnica",  # ID4qero ✅
        "Komfortowe mieszkanie przy Rondzie",  # ID4yxJV ✅
        "Mieszkanie 83 m2 ul. Piaskowa 4",  # ❓
        "Nowe-Piękne-3-Pokoje 2 Garaże",  # ❓
        "Wynajmę komfortowy apartament",  # ❓
        "Nowoczesne 3-pokojowe mieszkanie"  # ❓
    ]
    
    print(f"🔍 Checking {len(expected_listings)} listings from screenshot:")
    
    found_count = 0
    missing_count = 0
    
    for i, expected_title in enumerate(expected_listings, 1):
        print(f"\n{i}. Looking for: '{expected_title}'")
        
        # Find links that might match this title
        matching_links = []
        for link in listing_links:
            url = link.get('href', '')
            if not url.startswith('http'):
                url = 'https://www.otodom.pl' + url
            
            # Extract ID from URL
            id_match = re.search(r'-ID([a-zA-Z0-9]+)$', url)
            if id_match:
                short_id = f"ID{id_match.group(1)}"
                
                # Get parent element
                parent = link.find_parent('article') or link.find_parent('div', class_=lambda x: x and 'listing' in str(x).lower())
                if not parent:
                    parent = link.parent
                
                if parent:
                    parent_text = parent.get_text(separator=' ', strip=True)
                    
                    # Check if title matches
                    if expected_title.lower() in parent_text.lower():
                        # Check if private
                        is_private = ('prywatne' in parent_text.lower() or 
                                     'oferta prywatna' in parent_text.lower())
                        
                        # Check district
                        district = districts_map.get(short_id, 'Unknown')
                        is_wola = 'wola' in district.lower() if district else False
                        
                        matching_links.append({
                            'id': short_id,
                            'url': url,
                            'private': is_private,
                            'district': district,
                            'is_wola': is_wola,
                            'text_snippet': parent_text[:100] + '...'
                        })
        
        if matching_links:
            found_count += 1
            print(f"   ✅ Found {len(matching_links)} matching link(s):")
            for link_info in matching_links:
                print(f"      ID: {link_info['id']}")
                print(f"      Private: {link_info['private']}")
                print(f"      District: {link_info['district']}")
                print(f"      Wola: {link_info['is_wola']}")
                print(f"      URL: {link_info['url'][:60]}...")
        else:
            missing_count += 1
            print(f"   ❌ NOT FOUND!")
    
    print(f"\n{'='*80}")
    print(f"📊 SUMMARY:")
    print(f"   Found: {found_count}/{len(expected_listings)} listings")
    print(f"   Missing: {missing_count} listings")
    print(f"{'='*80}")

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
