#!/usr/bin/env python3
"""
Debug script to see WHY Otodom filters out all listings
"""

import os
import sys
import requests
from bs4 import BeautifulSoup
import re
from dotenv import load_dotenv

# Load environment
load_dotenv()

def test_otodom_filtering():
    """Test Otodom filtering logic"""
    
    print("🔍 DEBUGGING OTODOM FILTERING")
    print("="*80)
    
    # Build URL
    base_url = "https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie/mazowieckie/warszawa"
    
    params = []
    
    # Price range
    price_from = os.getenv('PRICE_FROM', '4000')
    price_to = os.getenv('PRICE_TO', '6000')
    params.append(f"priceMin={price_from}")
    params.append(f"priceMax={price_to}")
    
    # Rooms
    rooms = os.getenv('ROOMS', 'three')
    rooms_map = {'three': '3'}
    if rooms in rooms_map:
        params.append(f"roomsNumber=%5B{rooms_map[rooms]}%5D")
    
    search_url = base_url + '?' + '&'.join(params) if params else base_url
    
    print(f"\n📍 URL: {search_url}")
    print(f"\n🔧 FILTERS:")
    print(f"   OTODOM_DISTRICT: {os.getenv('OTODOM_DISTRICT', 'NOT SET')}")
    print(f"   LISTING_TYPE: {os.getenv('LISTING_TYPE', 'NOT SET')}")
    
    # Fetch page
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    try:
        print(f"\n📥 Fetching page...")
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find listing links
        links = soup.find_all('a', href=lambda x: x and '/oferta/' in x)
        
        print(f"\n📋 Found {len(links)} total links")
        
        # Filter unique listings
        unique_urls = set()
        for link in links:
            href = link.get('href', '')
            if href.startswith('http'):
                url = href
            else:
                url = 'https://www.otodom.pl' + href
            
            if '/oferta/' in url and url not in unique_urls:
                unique_urls.add(url)
        
        print(f"📋 Found {len(unique_urls)} unique listings")
        
        # Test filtering on first 5
        print(f"\n🧪 TESTING FIRST 5 LISTINGS:")
        print("="*80)
        
        for i, url in enumerate(list(unique_urls)[:5], 1):
            print(f"\n{i}. {url}")
            
            # Find the parent card
            link_elem = soup.find('a', href=lambda x: x and url.split('/')[-1] in str(x))
            if not link_elem:
                print("   ❌ Link not found in soup")
                continue
            
            parent = link_elem.find_parent(['article', 'div'])
            if not parent:
                print("   ❌ Parent not found")
                continue
            
            parent_text = parent.get_text(separator=' ', strip=True)
            
            # Check private
            is_private = 'prywatne' in parent_text.lower() or 'oferta prywatna' in parent_text.lower()
            print(f"   🏷️  Private: {is_private}")
            print(f"      Text sample: {parent_text[:200]}...")
            
            # Extract location
            location_match = re.search(r'(?:ul\.\s+)?([A-ZŁŚĆŻŹ][a-ząćęłńóśźż\s]+(?:,\s*[A-ZŁŚĆŻŹ][a-ząćęłńóśźż\s]+)*)', parent_text)
            location = location_match.group(1).strip() if location_match else 'Unknown'
            print(f"   📍 Location: {location}")
            
            # Check district filter
            districts_str = os.getenv('OTODOM_DISTRICT', '')
            if districts_str:
                expected_districts = [d.strip() for d in districts_str.split(',') if d.strip()]
                location_lower = location.lower()
                match_found = any(district.lower() in location_lower for district in expected_districts)
                print(f"   🗺️  District match: {match_found} (looking for: {expected_districts})")
            
            # Would it pass filters?
            filter_private = os.getenv('LISTING_TYPE', 'private') == 'private'
            
            passes = True
            reasons = []
            
            if filter_private and not is_private:
                passes = False
                reasons.append("Not private")
            
            if districts_str:
                expected_districts = [d.strip() for d in districts_str.split(',') if d.strip()]
                location_lower = location.lower()
                match_found = any(district.lower() in location_lower for district in expected_districts)
                if not match_found:
                    passes = False
                    reasons.append(f"Wrong district (not in {expected_districts})")
            
            if passes:
                print(f"   ✅ WOULD PASS FILTERS")
            else:
                print(f"   ❌ WOULD BE FILTERED OUT: {', '.join(reasons)}")
        
        print(f"\n{'='*80}")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_otodom_filtering()

