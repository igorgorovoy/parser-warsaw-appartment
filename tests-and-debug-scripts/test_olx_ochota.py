#!/usr/bin/env python3
"""
Debug why OLX Ochota listing passed the filter
"""

import requests
from bs4 import BeautifulSoup

# The specific listing URL from Slack
test_url = "https://www.olx.pl/d/oferta/do-wynajecia-3-pokojowe-mieszkanie-warszawa-ochota-ul-jankowska-5-CID3-IDchWy.html"

print(f"🔍 Checking OLX listing: {test_url}\n")

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}

try:
    response = requests.get(test_url, headers=headers, timeout=10)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Check if it has extended_search in URL
    if 'reason=extended_search' in test_url:
        print("❌ URL contains 'reason=extended_search'")
    else:
        print("✅ URL does NOT contain 'reason=extended_search'")
    
    # Find location in page
    location_elem = soup.find('p', {'data-testid': 'ad-location'})
    if location_elem:
        location = location_elem.get_text(strip=True)
        print(f"\n📍 Location on page: {location}")
        
        if 'ochota' in location.lower():
            print("❌ Contains 'Ochota'")
        if 'wola' in location.lower():
            print("✅ Contains 'Wola'")
    
    # Check if it's from search results page
    print(f"\n💡 This listing might be:")
    print(f"   - Direct link (not from search results)")
    print(f"   - Or search results changed after we parsed")
    
except Exception as e:
    print(f"❌ ERROR: {e}")

