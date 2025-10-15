#!/usr/bin/env python3
"""
Check if Otodom has date information in listing cards
"""

import requests
from bs4 import BeautifulSoup
import json
import re

search_url = "https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie/mazowieckie/warszawa?priceMin=4000&priceMax=8000&roomsNumber=%5B3%5D"

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}

try:
    print("🔍 Checking Otodom for date information...")
    response = requests.get(search_url, headers=headers, timeout=10)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Check JSON data
    script_tags = soup.find_all('script', {'id': '__NEXT_DATA__'})
    if script_tags:
        print(f"\n📋 Found JSON data, checking first listing...")
        for script in script_tags:
            try:
                json_data = json.loads(script.string)
                
                # Navigate to listings
                if 'props' in json_data and 'pageProps' in json_data['props']:
                    data = json_data['props']['pageProps'].get('data', {})
                    search_ads = data.get('searchAds', {})
                    items = search_ads.get('items', [])
                    
                    if items:
                        first_listing = items[0]
                        print(f"\n✅ First listing data:")
                        print(f"   ID: {first_listing.get('id', 'N/A')}")
                        print(f"   Title: {first_listing.get('title', 'N/A')[:50]}...")
                        print(f"   dateCreated: {first_listing.get('dateCreated', 'N/A')}")
                        print(f"   createdAtFirst: {first_listing.get('createdAtFirst', 'N/A')}")
                        print(f"   pushedUpAt: {first_listing.get('pushedUpAt', 'N/A')}")
                        
                        # Try to parse date
                        date_created = first_listing.get('dateCreated', '')
                        if date_created:
                            print(f"\n📅 Date format: {date_created}")
                            # Try to convert to readable format
                            from datetime import datetime
                            try:
                                dt = datetime.strptime(date_created, '%Y-%m-%d %H:%M:%S')
                                polish_months = {
                                    1: 'stycznia', 2: 'lutego', 3: 'marca', 4: 'kwietnia',
                                    5: 'maja', 6: 'czerwca', 7: 'lipca', 8: 'sierpnia',
                                    9: 'września', 10: 'października', 11: 'listopada', 12: 'grudnia'
                                }
                                polish_date = f"{dt.day} {polish_months[dt.month]} {dt.year}"
                                print(f"   Polish format: {polish_date}")
                            except:
                                pass
                        
                        break
                    else:
                        print("   ❌ No items found in JSON")
                
            except Exception as e:
                print(f"   ❌ Error parsing JSON: {e}")
    
    # Also check text content
    print(f"\n🔍 Checking text content...")
    links = soup.find_all('a', href=lambda x: x and '/oferta/' in str(x))
    if links:
        first_link = links[0]
        parent = first_link.find_parent('article') or first_link.find_parent('div')
        if parent:
            text = parent.get_text(separator=' ', strip=True)
            print(f"\n📝 First listing text (first 300 chars):")
            print(f"   {text[:300]}...")
            
            # Look for date patterns
            date_patterns = [
                r'\d{1,2}\s+\w+\s+\d{4}',  # "15 października 2025"
                r'\d{4}-\d{2}-\d{2}',       # "2025-10-15"
            ]
            
            for pattern in date_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    print(f"\n   ✅ Found date pattern: {matches}")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

