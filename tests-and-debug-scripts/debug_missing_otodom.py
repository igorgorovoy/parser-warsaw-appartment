#!/usr/bin/env python3
"""
Debug why some Otodom listings are missing
"""

import os
import sys
import requests
from bs4 import BeautifulSoup
import json
import re
from dotenv import load_dotenv

load_dotenv()

# Build the same URL as the parser
def build_otodom_url():
    base_url = "https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie/mazowieckie/warszawa"
    params = []
    
    price_from = os.getenv('PRICE_FROM', '4000')
    price_to = os.getenv('PRICE_TO', '8000')
    if price_from:
        params.append(f"priceMin={price_from}")
    if price_to:
        params.append(f"priceMax={price_to}")
    
    rooms = os.getenv('ROOMS', 'three')
    if rooms == 'three':
        params.append("roomsNumber=%5B3%5D")
    
    area_from = os.getenv('AREA_FROM', '60')
    area_to = os.getenv('AREA_TO', '90')
    if area_from:
        params.append(f"areaMin={area_from}")
    if area_to:
        params.append(f"areaMax={area_to}")
    
    if params:
        search_url = f"{base_url}?{'&'.join(params)}"
    else:
        search_url = base_url
    
    return search_url

search_url = build_otodom_url()
print(f"🔍 Checking URL: {search_url}\n")

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}

try:
    response = requests.get(search_url, headers=headers, timeout=10)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find all listing links - try different selectors
    listing_links = soup.find_all('a', {'data-testid': 'listing-item-link'})
    print(f"📋 Found {len(listing_links)} listing links with data-testid='listing-item-link'")
    
    if len(listing_links) == 0:
        # Try alternative selectors
        listing_links = soup.find_all('a', href=lambda x: x and '/pl/oferta/' in x)
        print(f"📋 Found {len(listing_links)} listing links with '/pl/oferta/' in href")
        
        if len(listing_links) == 0:
            # Try any link with 'oferta' in href
            listing_links = soup.find_all('a', href=lambda x: x and 'oferta' in x)
            print(f"📋 Found {len(listing_links)} listing links with 'oferta' in href")
            
            # Save HTML for debugging
            with open('debug_otodom_page.html', 'w', encoding='utf-8') as f:
                f.write(str(soup))
            print("💾 Saved HTML to debug_otodom_page.html")
    
    print(f"📋 Final count: {len(listing_links)} listing links")
    
    # Extract districts from JSON
    districts_map = {}
    script_tags = soup.find_all('script', {'id': '__NEXT_DATA__'})
    if script_tags:
        try:
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
                
                print(f"📊 Extracted districts for {len(districts_map)} listings from JSON")
                
                # Show all districts found
                districts_found = set(districts_map.values())
                print(f"📍 Districts found in JSON: {sorted(districts_found)}")
                
                wola_listings = [k for k, v in districts_map.items() if 'wola' in v.lower()]
                print(f"🏠 Wola listings in JSON: {len(wola_listings)}")
                if wola_listings:
                    print(f"   IDs: {wola_listings[:5]}")  # Show first 5
        except Exception as e:
            print(f"❌ Could not extract districts from JSON: {e}")
    
    print(f"\n🔍 Analyzing each listing:")
    
    wola_count = 0
    other_districts = 0
    private_count = 0
    total_processed = 0
    
    for i, link in enumerate(listing_links[:10], 1):  # Check first 10
        url = link.get('href', '')
        if not url.startswith('http'):
            url = 'https://www.otodom.pl' + url
        
        # Extract ID from URL
        id_match = re.search(r'-ID([a-zA-Z0-9]+)$', url)
        if id_match:
            short_id = f"ID{id_match.group(1)}"
        else:
            short_id = None
        
        # Get parent element for text analysis
        parent = link.parent
        if parent:
            parent_text = parent.get_text()
            
            # Check if private
            is_private = 'prywatne' in parent_text.lower() or 'prywatna' in parent_text.lower()
            if is_private:
                private_count += 1
            
            # Check district from JSON
            district_from_json = districts_map.get(short_id) if short_id else None
            
            print(f"\n{i}. {url.split('/')[-1][:30]}...")
            print(f"   ID: {short_id}")
            print(f"   Private: {is_private}")
            print(f"   District (JSON): {district_from_json}")
            
            if district_from_json:
                if 'wola' in district_from_json.lower():
                    wola_count += 1
                    print(f"   ✅ WOLA - Would be included")
                else:
                    other_districts += 1
                    print(f"   ❌ {district_from_json} - Would be filtered out")
            else:
                print(f"   ❓ No district data - Would be filtered out")
            
            total_processed += 1
    
    print(f"\n{'='*80}")
    print(f"📊 SUMMARY:")
    print(f"   Total listings processed: {total_processed}")
    print(f"   Private listings: {private_count}")
    print(f"   Wola listings: {wola_count}")
    print(f"   Other districts: {other_districts}")
    print(f"   Expected to pass filters: {wola_count}")
    print(f"{'='*80}")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
