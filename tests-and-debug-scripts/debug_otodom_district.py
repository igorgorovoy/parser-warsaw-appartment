#!/usr/bin/env python3
"""
Debug why Otodom district filtering doesn't work
"""

import os
import sys
import requests
from bs4 import BeautifulSoup
import json
from dotenv import load_dotenv

load_dotenv()

search_url = "https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie/mazowieckie/warszawa?priceMin=4000&priceMax=8000&roomsNumber=%5B3%5D"

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}

try:
    print("🔍 Checking Otodom district data in JSON...")
    response = requests.get(search_url, headers=headers, timeout=10)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Check JSON data for district information
    script_tags = soup.find_all('script', {'id': '__NEXT_DATA__'})
    if script_tags:
        json_data = json.loads(script_tags[0].string)
        
        # Navigate to listings
        if 'props' in json_data and 'pageProps' in json_data['props']:
            data = json_data['props']['pageProps'].get('data', {})
            search_ads = data.get('searchAds', {})
            items = search_ads.get('items', [])
            
            print(f"\n📋 Found {len(items)} listings in JSON")
            print(f"\n🔍 Checking first 5 listings for district info:")
            
            for i, item in enumerate(items[:5], 1):
                print(f"\n{i}. {item.get('title', 'No title')[:50]}...")
                print(f"   ID: {item.get('id')}")
                
                # Check location data
                location = item.get('location', {})
                if location:
                    reverse_geo = location.get('reverseGeocoding', {})
                    locations = reverse_geo.get('locations', [])
                    
                    print(f"   Location hierarchy:")
                    for loc in locations:
                        level = loc.get('locationLevel')
                        name = loc.get('name')
                        print(f"      - {level}: {name}")
                    
                    # Find district
                    district = next((loc['name'] for loc in locations if loc.get('locationLevel') == 'district'), None)
                    print(f"   ✅ District from JSON: {district}")
                    
                    # Check if it's Wola
                    if district and 'wola' in district.lower():
                        print(f"      ✅ MATCHES Wola!")
                    else:
                        print(f"      ❌ NOT Wola (it's {district})")
                
                # Check is_private
                is_private = item.get('isPrivateOwner', False)
                print(f"   Private: {is_private}")
    
    print(f"\n{'='*80}")
    print(f"💡 CONCLUSION:")
    print(f"   JSON has accurate district data in location.reverseGeocoding.locations")
    print(f"   We should use JSON district instead of text parsing!")
    print(f"{'='*80}")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

