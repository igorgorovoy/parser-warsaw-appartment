#!/usr/bin/env python3
"""
Check if missing Wola listings are private or not
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
    
    # Find Wola listings in JSON
    wola_in_json = [k for k, v in districts_map.items() if 'wola' in v.lower()]
    
    print(f"🏠 Checking {len(wola_in_json)} Wola listings for private status:")
    
    for wola_id in wola_in_json:
        # Find corresponding HTML link
        found_links = [link for link in listing_links if wola_id in link.get('href', '')]
        
        if found_links:
            link = found_links[0]
            
            # Use the same logic as the parser
            parent = link.find_parent('article') or link.find_parent('div', class_=lambda x: x and 'listing' in str(x).lower())
            
            # Fallback to direct parent
            if not parent:
                parent = link.parent
            
            print(f"\n{wola_id}:")
            print(f"   Link: {link.get('href', '')[:60]}...")
            print(f"   Parent tag: {parent.name if parent else 'None'}")
            
            # Get parent text
            if parent:
                parent_text = parent.get_text(separator=' ', strip=True)
                print(f"   Parent text: '{parent_text[:200]}...'")
                
                # Check if private - use same logic as parser
                is_private = ('prywatne' in parent_text.lower() or 
                             'oferta prywatna' in parent_text.lower())
                
                print(f"   Private: {is_private}")
                
                # Check for any private-related words
                private_words = ['prywatne', 'prywatna', 'prywatny', 'prywatnych', 'oferta prywatna']
                found_words = [word for word in private_words if word in parent_text.lower()]
                print(f"   Private words found: {found_words}")
                
                if not is_private:
                    print(f"   ❌ NOT PRIVATE - Would be filtered out!")
                else:
                    print(f"   ✅ Private - Would pass filter")
            else:
                print(f"   ❌ No parent found!")
                
                # Check if private - look for various private indicators
                is_private = ('prywatne' in parent_text.lower() or 
                             'prywatna' in parent_text.lower() or
                             'oferta prywatna' in parent_text.lower())
                
                print(f"\n{wola_id}:")
                print(f"   Private: {is_private}")
                print(f"   Full text: {parent_text}")
                
                # Check for any private-related words
                private_words = ['prywatne', 'prywatna', 'prywatny', 'prywatnych', 'oferta prywatna']
                found_words = [word for word in private_words if word in parent_text.lower()]
                print(f"   Private words found: {found_words}")
                
                if not is_private:
                    print(f"   ❌ NOT PRIVATE - Would be filtered out!")
                else:
                    print(f"   ✅ Private - Would pass filter")
        else:
            print(f"\n{wola_id}: No HTML link found")

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
