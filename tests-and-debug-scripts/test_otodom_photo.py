#!/usr/bin/env python3
"""
Test script to debug Otodom photo extraction
"""

import os
import sys
import requests
from bs4 import BeautifulSoup

# Test URLs from Slack screenshot
test_urls = [
    "https://www.otodom.pl/pl/oferta/wyjatkowy-apartament-al-ujazdowskie-16-ID4yv8T",
    "https://www.otodom.pl/pl/oferta/2-pokoje-okrag-balkon-garaz-ID4ywIy",
]

def test_photo_extraction(url):
    """Test photo extraction from Otodom listing"""
    print(f"\n{'='*80}")
    print(f"Testing: {url}")
    print('='*80)
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        # Fetch search results page first (simulate parser behavior)
        print("\n1️⃣ SIMULATING SEARCH RESULTS PAGE:")
        print("   (In real parser, this is where we first try to get photo)")
        
        # Fetch detail page
        print("\n2️⃣ FETCHING DETAIL PAGE:")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        print(f"   ✅ Status: {response.status_code}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try different methods to find images
        print("\n3️⃣ SEARCHING FOR IMAGES:")
        
        all_imgs = soup.find_all('img')
        print(f"   Found {len(all_imgs)} total <img> tags")
        
        # Method 1: Look for otodom/otocdn URLs
        print("\n   📸 Images with otodom/otocdn domains:")
        otodom_imgs = []
        for i, img in enumerate(all_imgs[:20], 1):  # Check first 20
            src = img.get('src', '')
            if 'otodom.pl' in src or 'otocdn.net' in src:
                # Skip icons and placeholders
                if 'icon' not in src and 'logo' not in src and 'placeholder' not in src:
                    print(f"      [{i}] {src[:100]}...")
                    otodom_imgs.append(src)
        
        # Method 2: Look for specific data attributes
        print("\n   🔍 Images with data-cy='listing-item-image-source':")
        cy_imgs = soup.find_all('img', {'data-cy': 'listing-item-image-source'})
        for img in cy_imgs:
            print(f"      {img.get('src', 'NO SRC')[:100]}...")
        
        # Method 3: Look for gallery/carousel
        print("\n   🖼️  Images in gallery/carousel:")
        gallery = soup.find_all(['div', 'section'], class_=lambda x: x and ('gallery' in x.lower() or 'carousel' in x.lower() or 'image' in x.lower()))
        for g in gallery[:5]:
            imgs = g.find_all('img')
            for img in imgs[:3]:
                src = img.get('src', '')
                if src and src.startswith('http'):
                    print(f"      {src[:100]}...")
        
        # Method 4: Look for picture elements
        print("\n   🎨 <picture> elements:")
        pictures = soup.find_all('picture')
        for pic in pictures[:5]:
            imgs = pic.find_all('img')
            sources = pic.find_all('source')
            for img in imgs:
                print(f"      IMG: {img.get('src', 'NO SRC')[:100]}...")
            for source in sources:
                print(f"      SOURCE: {source.get('srcset', 'NO SRCSET')[:100]}...")
        
        # Show result
        print("\n4️⃣ RESULT:")
        if otodom_imgs:
            print(f"   ✅ Found {len(otodom_imgs)} potential photo(s)")
            print(f"   🎯 BEST CHOICE: {otodom_imgs[0]}")
        else:
            print("   ❌ No photos found with current logic")
            print("   💡 Try expanding search criteria")
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")

def main():
    print("🧪 OTODOM PHOTO EXTRACTION TEST")
    print("="*80)
    
    for url in test_urls:
        test_photo_extraction(url)
    
    print(f"\n{'='*80}")
    print("✅ TEST COMPLETE")
    print("="*80)

if __name__ == '__main__':
    main()

