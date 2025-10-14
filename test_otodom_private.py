#!/usr/bin/env python3
"""Test Otodom private listings filter"""

import requests
from bs4 import BeautifulSoup

def test_url(url, description):
    """Test a URL and show what listings are found"""
    print(f"\n{'='*80}")
    print(f"{description}")
    print(f"URL: {url}")
    print('='*80)
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Save HTML for inspection
        with open('debug_otodom_search.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        
        # Find listing cards
        cards = soup.find_all('article', {'data-cy': 'listing-item'})
        if not cards:
            cards = soup.find_all('div', class_=lambda x: x and 'listing' in str(x).lower())
        
        print(f"Found {len(cards)} listings")
        
        if cards:
            for i, card in enumerate(cards[:5], 1):
                # Get link
                link = card.find('a', href=True)
                url = link['href'] if link else 'No link'
                
                # Get all text
                text = card.get_text(separator=' ', strip=True)
                
                # Check for private indicators
                is_private = 'prywatne' in text.lower() or 'oferta prywatna' in text.lower()
                private_mark = "✅ PRIVATE" if is_private else "❌ BUSINESS"
                
                print(f"\n  {i}. {private_mark}")
                print(f"     URL: {url[:80]}...")
                if len(text) > 200:
                    print(f"     Text: {text[:200]}...")
        else:
            print("⚠️  No cards found. Checking HTML structure...")
            # Look for any listing elements
            all_articles = soup.find_all('article')
            print(f"Found {len(all_articles)} <article> tags")
            
            all_divs_with_data = soup.find_all('div', attrs={'data-cy': True})
            print(f"Found {len(all_divs_with_data)} <div> tags with data-cy")
            
    except Exception as e:
        print(f"❌ Error: {e}")

# Base URL for 3-room apartments in Warsaw
base_url = "https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie/mazowieckie/warszawa/warszawa/warszawa"

# Test different filters
print("\n" + "="*80)
print("TESTING OTODOM PRIVATE LISTING FILTERS")
print("="*80)

# Test 1: No filter
test_url(
    f"{base_url}?roomsNumber=%5B3%5D&priceMin=4000&priceMax=6000",
    "TEST 1: Basic filters (3 rooms, price 4000-6000) - NO private filter"
)

# Test 2: Try ownerTypeSingleUser
test_url(
    f"{base_url}?roomsNumber=%5B3%5D&priceMin=4000&priceMax=6000&ownerTypeSingleUser=true",
    "TEST 2: + ownerTypeSingleUser=true"
)

# Test 3: Try by-owner
test_url(
    f"{base_url}?roomsNumber=%5B3%5D&priceMin=4000&priceMax=6000&by-owner=true",
    "TEST 3: + by-owner=true"
)

# Test 4: Try userType
test_url(
    f"{base_url}?roomsNumber=%5B3%5D&priceMin=4000&priceMax=6000&userType=private",
    "TEST 4: + userType=private"
)

# Test 5: Check the actual listing URL provided
print("\n" + "="*80)
print("CHECKING THE PROVIDED LISTING")
print("="*80)

listing_url = "https://www.otodom.pl/pl/oferta/wynajme-3-pokojowe-jasne-mieszkanie-siekierki-ID4yA0z"
response = requests.get(listing_url, timeout=30)
soup = BeautifulSoup(response.text, 'html.parser')

# Save for inspection
with open('debug_otodom_listing.html', 'w', encoding='utf-8') as f:
    f.write(soup.prettify())

# Look for private/business indicators
text = soup.get_text()
if 'prywatne' in text.lower():
    print("✅ Found 'prywatne' in listing page")
if 'oferta prywatna' in text.lower():
    print("✅ Found 'oferta prywatna' in listing page")
if 'agencja' in text.lower():
    print("❌ Found 'agencja' in listing page")

# Look for user type in structured data
scripts = soup.find_all('script', type='application/ld+json')
for script in scripts:
    if 'private' in script.string.lower() if script.string else '':
        print(f"✅ Found 'private' in JSON-LD: {script.string[:200]}...")

print("\n✅ HTML files saved: debug_otodom_search.html, debug_otodom_listing.html")

