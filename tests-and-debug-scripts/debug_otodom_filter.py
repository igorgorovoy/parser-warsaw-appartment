#!/usr/bin/env python3
"""
Debug Otodom filtering logic
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
    print(f"📋 Found {len(listing_links)} listing links")
    
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
    
    # Find Wola listings in JSON
    wola_in_json = [k for k, v in districts_map.items() if 'wola' in v.lower()]
    print(f"🏠 Wola listings in JSON: {len(wola_in_json)}")
    print(f"   IDs: {wola_in_json}")
    
    # Check which Wola listings have corresponding HTML links
    wola_with_html = []
    wola_without_html = []
    
    for wola_id in wola_in_json:
        found_links = [link for link in listing_links if wola_id in link.get('href', '')]
        if found_links:
            wola_with_html.append(wola_id)
        else:
            wola_without_html.append(wola_id)
    
    print(f"\n✅ Wola listings with HTML links: {len(wola_with_html)}")
    print(f"   {wola_with_html}")
    
    print(f"\n❌ Wola listings WITHOUT HTML links: {len(wola_without_html)}")
    print(f"   {wola_without_html}")
    
    if wola_without_html:
        print(f"\n💡 Проблема: JSON містить Wola listings, але HTML не містить відповідних links!")
        print(f"   Це означає що Otodom показує різні результати в JSON і HTML")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
