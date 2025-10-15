#!/usr/bin/env python3
"""
Debug specific Otodom listing to see why it's filtered out
"""

import requests
from bs4 import BeautifulSoup
import re
import json

# The specific listing user mentioned
test_url = "https://www.otodom.pl/pl/oferta/apartament-kolejowa-19-dzielnica-metro-ID4qero"

def check_listing():
    """Check the specific listing"""
    
    print("🔍 DEBUGGING SPECIFIC OTODOM LISTING")
    print("="*80)
    print(f"URL: {test_url}")
    print("="*80)
    
    # First, let's check if this listing appears in search results
    search_url = "https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie/mazowieckie/warszawa?priceMin=4000&priceMax=8000&roomsNumber=%5B3%5D"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    try:
        print("\n1️⃣ CHECKING IF LISTING IS IN SEARCH RESULTS...")
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check if this listing ID is in the page
        listing_id = "ID4qero"
        page_html = str(soup)
        
        if listing_id in page_html:
            print(f"   ✅ Listing {listing_id} FOUND in search results!")
        else:
            print(f"   ❌ Listing {listing_id} NOT in search results")
            print(f"   💡 This might be why parser skipped it")
            return
        
        # Find the link
        link = soup.find('a', href=lambda x: x and listing_id in str(x))
        if not link:
            print(f"   ❌ Could not find link element")
            return
        
        print(f"   ✅ Found link element")
        
        # Get parent
        parent = link.find_parent('article') or link.find_parent('div')
        if not parent:
            print(f"   ❌ Could not find parent element")
            return
        
        print(f"   ✅ Found parent element")
        
        # Get text
        parent_text = parent.get_text(separator=' ', strip=True)
        print(f"\n2️⃣ PARENT TEXT (first 500 chars):")
        print(f"   {parent_text[:500]}...")
        
        # Check for "prywatne"
        has_prywatne = 'prywatne' in parent_text.lower()
        has_oferta_prywatna = 'oferta prywatna' in parent_text.lower()
        
        print(f"\n3️⃣ PRIVATE CHECK:")
        print(f"   'prywatne' in text: {has_prywatne}")
        print(f"   'oferta prywatna' in text: {has_oferta_prywatna}")
        print(f"   IS PRIVATE: {has_prywatne or has_oferta_prywatna}")
        
        if not (has_prywatne or has_oferta_prywatna):
            print(f"\n   ⚠️  TEXT DOESN'T CONTAIN 'PRYWATNE'!")
            print(f"   💡 Searching for alternative indicators...")
            
            # Check in HTML attributes
            parent_html = str(parent)
            if 'prywatne' in parent_html.lower() or 'private' in parent_html.lower():
                print(f"   ✅ Found 'prywatne' in HTML attributes")
            else:
                print(f"   ❌ No 'prywatne' in HTML either")
        
        # Try to extract location
        location_match = re.search(r'(?:ul\.\s+)?([A-ZŁŚĆŻŹ][a-ząćęłńóśźż\s]+(?:,\s*[A-ZŁŚĆŻŹ][a-ząćęłńóśźż\s]+)*)', parent_text)
        if location_match:
            location = location_match.group(1).strip()
            print(f"\n4️⃣ LOCATION:")
            print(f"   Extracted: {location}")
            
            # Check district
            location_lower = location.lower()
            if 'wola' in location_lower:
                print(f"   ✅ Contains 'Wola'")
            else:
                print(f"   ❌ Does NOT contain 'Wola'")
                print(f"   💡 This might be why it's filtered out")
        else:
            print(f"\n4️⃣ LOCATION:")
            print(f"   ❌ Could not extract location")
        
        # Check JSON data in page (Otodom uses React/Next.js with JSON data)
        script_tags = soup.find_all('script', {'id': '__NEXT_DATA__'})
        if script_tags:
            print(f"\n5️⃣ CHECKING JSON DATA:")
            for script in script_tags:
                try:
                    json_data = json.loads(script.string)
                    # Look for our listing in JSON
                    json_str = json.dumps(json_data)
                    if listing_id in json_str:
                        print(f"   ✅ Found listing in JSON data")
                        
                        # Try to find isPrivateOwner field
                        if 'isPrivateOwner' in json_str:
                            # Find the specific listing data
                            import re as re_module
                            pattern = rf'{listing_id}.*?"isPrivateOwner":(true|false)'
                            match = re_module.search(pattern, json_str)
                            if match:
                                is_private_json = match.group(1) == 'true'
                                print(f"   📋 isPrivateOwner in JSON: {is_private_json}")
                                if is_private_json:
                                    print(f"   ✅ JSON confirms it's PRIVATE!")
                                    print(f"   💡 Parser should use JSON data, not text parsing!")
                except Exception as e:
                    print(f"   ⚠️  Could not parse JSON: {e}")
        
        print(f"\n{'='*80}")
        print(f"CONCLUSION:")
        print(f"{'='*80}")
        print(f"The listing IS on the page, but text parsing might not work.")
        print(f"Otodom uses React/JSON data - parser should check JSON instead!")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_listing()

