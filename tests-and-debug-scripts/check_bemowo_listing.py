#!/usr/bin/env python3
"""Check specific listing from Bemowo"""

import requests
from bs4 import BeautifulSoup

url = "https://www.olx.pl/d/oferta/3-pokoje-stare-bemowo-bezposrednio-CID3-ID17zlpa.html"

print("="*80)
print("Checking listing from Bemowo")
print("="*80)
print(f"URL: {url}\n")

try:
    response = requests.get(url, timeout=30)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Get title
    title_elem = soup.find('h1')
    if title_elem:
        title = title_elem.get_text(strip=True)
        print(f"Title: {title}")
    
    # Get location
    location_elem = soup.find('p', {'data-testid': 'ad-posted-at'}) or soup.find('a', href=lambda x: x and 'warszawa' in str(x).lower())
    if location_elem:
        print(f"Location element: {location_elem.get_text(strip=True)}")
    
    # Get all text and check for "wola" mentions
    full_text = soup.get_text().lower()
    
    print(f"\nSearching for 'wola' in listing text...")
    if 'wola' in full_text:
        print("✅ Found 'wola' in text!")
        
        # Find context around "wola"
        import re
        matches = re.finditer(r'.{0,50}wola.{0,50}', full_text)
        print("\nContexts where 'wola' appears:")
        for i, match in enumerate(list(matches)[:5], 1):
            context = match.group(0).strip()
            print(f"  {i}. ...{context}...")
    else:
        print("❌ 'wola' NOT found in text")
    
    # Check description
    desc_elem = soup.find('div', {'data-cy': 'ad_description'})
    if desc_elem:
        desc = desc_elem.get_text(strip=True)
        print(f"\nDescription excerpt: {desc[:200]}...")
        if 'wola' in desc.lower():
            print("⚠️  'wola' is mentioned in description!")
    
    print("\n" + "="*80)
    print("CONCLUSION:")
    print("="*80)
    if 'wola' in full_text:
        print("This listing appears in /q-wola/ search because it mentions")
        print("'wola' in the text, even though it's in Bemowo district.")
        print("\n⚠️  /q-wola/ is a TEXT SEARCH, not a district filter!")
    else:
        print("This listing should NOT appear in /q-wola/ search.")
        print("It might be an OLX bug or outdated index.")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

