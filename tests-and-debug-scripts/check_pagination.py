#!/usr/bin/env python3
"""
Check if there's pagination on Otodom results page
"""

import requests
from bs4 import BeautifulSoup

search_url = "https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie/mazowieckie/warszawa?priceMin=4000&priceMax=8000&roomsNumber=%5B3%5D&areaMin=60&areaMax=90"

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}

try:
    response = requests.get(search_url, headers=headers, timeout=10)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    print("🔍 Checking for pagination elements...")
    
    # Look for pagination indicators
    pagination_elements = [
        soup.find_all('a', {'data-cy': 'pagination-next'}),
        soup.find_all('button', {'data-cy': 'pagination-next'}),
        soup.find_all('a', href=lambda x: x and 'page=' in x if x else False),
        soup.find_all('button', text=lambda x: x and 'następna' in x.lower() if x else False),
        soup.find_all('button', text=lambda x: x and 'dalej' in x.lower() if x else False),
        soup.find_all('a', text=lambda x: x and 'następna' in x.lower() if x else False),
        soup.find_all('a', text=lambda x: x and 'dalej' in x.lower() if x else False),
    ]
    
    found_pagination = []
    for elements in pagination_elements:
        found_pagination.extend(elements)
    
    if found_pagination:
        print(f"✅ Found {len(found_pagination)} pagination elements:")
        for elem in found_pagination:
            print(f"   - {elem.name}: {elem.get_text(strip=True)}")
            if elem.get('href'):
                print(f"     href: {elem.get('href')}")
    else:
        print("❌ No pagination elements found")
    
    # Look for page numbers
    page_numbers = soup.find_all('a', text=lambda x: x and x.isdigit() if x else False)
    if page_numbers:
        print(f"📄 Found {len(page_numbers)} page number links:")
        for link in page_numbers:
            print(f"   - Page {link.get_text()}: {link.get('href', '')}")
    
    # Look for "Page X of Y" text
    page_info = soup.find_all(text=lambda x: x and ('strona' in x.lower() or 'page' in x.lower()) if x else False)
    if page_info:
        print(f"📊 Page info found:")
        for info in page_info:
            print(f"   - {info.strip()}")
    
    # Count total listings
    listing_links = soup.find_all('a', href=lambda x: x and '/pl/oferta/' in x)
    print(f"\n📋 Total listings on this page: {len(listing_links)}")

except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
