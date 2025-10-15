#!/usr/bin/env python3
"""Check listing from Slack that had no photo"""

import requests
from bs4 import BeautifulSoup

# From your Slack screenshot - listing without photo
# "Apartament 3-pokoje z balkonem| Bezpośrednio| Przyjazne zwierzętom"
# Let's search for it

search_url = "https://www.olx.pl/d/oferta/apartament-3-pokoje-z-balkonem-bezposrednio-przyjazne-zwierzetom-CID3-ID16fQR7.html"

print("="*80)
print("CHECKING SPECIFIC LISTING FROM SLACK")
print("="*80)
print(f"URL: {search_url}")
print()

try:
    response = requests.get(search_url, timeout=30)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Save for inspection
    with open('debug_listing_detail.html', 'w', encoding='utf-8') as f:
        f.write(soup.prettify())
    
    # Look for images
    all_imgs = soup.find_all('img')
    print(f"Total img tags: {len(all_imgs)}\n")
    
    photo_count = 0
    for img in all_imgs:
        src = img.get('src', '')
        data_src = img.get('data-src', '')
        
        # Check for actual photos
        if 'apollo.olxcdn.com' in src or 'apollo.olxcdn.com' in data_src:
            if 'no_thumbnail' not in src and 'no_thumbnail' not in data_src:
                photo_count += 1
                if photo_count <= 5:
                    actual_src = data_src if data_src else src
                    print(f"📸 Photo {photo_count}: {actual_src[:100]}...")
    
    if photo_count > 0:
        print(f"\n✅ LISTING HAS {photo_count} PHOTOS!")
        print("\n🎯 CONCLUSION:")
        print("   Photos exist on detail page but were NOT in search results!")
        print("   This means OLX doesn't always show photos in search listings.")
    else:
        print("\n❌ No photos found on detail page either")
        print("   This listing genuinely has no photos")
    
    print("\n💾 Saved HTML to: debug_listing_detail.html")
    
except Exception as e:
    print(f"❌ Error: {e}")

print("="*80)

