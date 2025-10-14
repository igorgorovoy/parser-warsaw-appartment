#!/usr/bin/env python3
"""Analyze Otodom HTML structure to find private listing filter"""

from bs4 import BeautifulSoup

# Read the saved HTML
with open('debug_otodom_search.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Find all listing links
links = soup.find_all('a', {'data-cy': 'listing-item-link'})
print(f"Found {len(links)} listing links\n")

# Analyze first 10 listings
for i, link in enumerate(links[:10], 1):
    href = link.get('href', '')
    title_elem = link.find('p', {'data-cy': 'listing-item-title'})
    title = title_elem.get_text(strip=True) if title_elem else 'No title'
    
    # Get the parent article/div
    parent = link.find_parent('article') or link.find_parent('div', class_=lambda x: x and 'listing' in str(x).lower())
    
    # Look for private/business indicators in parent
    if parent:
        parent_text = parent.get_text(separator=' ')
        
        # Check for indicators
        is_private = 'prywatne' in parent_text.lower() or 'oferta prywatna' in parent_text.lower()
        is_business = 'agencja' in parent_text.lower() or 'deweloper' in parent_text.lower()
        
        status = "✅ PRIVATE" if is_private else ("❌ BUSINESS" if is_business else "❓ UNKNOWN")
        
        print(f"{i}. {status}")
        print(f"   Title: {title[:60]}")
        print(f"   URL: {href}")
        
        # Look for any badge/tag elements
        badges = parent.find_all(class_=lambda x: x and ('badge' in str(x).lower() or 'tag' in str(x).lower()))
        if badges:
            print(f"   Badges: {[b.get_text(strip=True) for b in badges]}")
        print()

# Now check if there's a URL parameter that works
print("\n" + "="*80)
print("CHECKING OTODOM WEBSITE DIRECTLY FOR PRIVATE FILTER")
print("="*80)
print("\nLet's manually check the Otodom website filters:")
print("1. Go to: https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie/mazowieckie/warszawa")
print("2. Select '3 pokoje' in filters")
print("3. Look for 'Typ ogłoszeniodawcy' or 'Private owner' filter")
print("4. Enable it and check the URL")
print("\nURL format should be something like:")
print("  - ownerTypeSingleUser=true")
print("  - advertiserType=private")
print("  - userType=PRIVATE")

