#!/usr/bin/env python3
"""
Test if photo extraction works for the specific Otodom listing
"""

import requests
from bs4 import BeautifulSoup

# The listing user mentioned
test_url = "https://www.otodom.pl/pl/oferta/apartament-kolejowa-19-dzielnica-metro-ID4qero"

def test_photo_extraction():
    """Test photo extraction using the new logic"""
    
    print("🧪 TESTING OTODOM PHOTO EXTRACTION")
    print("="*80)
    print(f"URL: {test_url}")
    print("="*80)
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        print("\n📥 Fetching detail page...")
        response = requests.get(test_url, headers=headers, timeout=10)
        response.raise_for_status()
        print(f"✅ Status: {response.status_code}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Simulate the logic from base_parser.py
        is_otodom = 'otodom.pl' in test_url
        print(f"\n🔍 Detected as: {'Otodom' if is_otodom else 'OLX'}")
        
        # Check <picture> elements first (as in base_parser.py)
        print(f"\n1️⃣ Checking <picture> elements...")
        pictures = soup.find_all('picture')
        print(f"   Found {len(pictures)} <picture> elements")
        
        photo_found = None
        
        if is_otodom and pictures:
            for i, pic in enumerate(pictures[:5], 1):
                imgs = pic.find_all('img')
                for img in imgs:
                    src = img.get('src', '')
                    if src:
                        has_apollo = 'apollo.olxcdn.com' in src
                        is_long = len(src) > 100
                        is_svg = src.endswith('.svg')
                        has_icon = 'icon' in src.lower()
                        
                        print(f"\n   Picture {i}:")
                        print(f"      URL length: {len(src)}")
                        print(f"      Has apollo.olxcdn.com: {has_apollo}")
                        print(f"      Length > 100: {is_long}")
                        print(f"      Is SVG: {is_svg}")
                        print(f"      Has 'icon': {has_icon}")
                        
                        # Check if matches our logic
                        if has_apollo and is_long and not is_svg and not has_icon:
                            photo_found = src
                            print(f"      ✅ MATCH! This would be selected")
                            print(f"\n🎯 SELECTED PHOTO:")
                            print(f"   {src[:120]}...")
                            break
                
                if photo_found:
                    break
        
        if not photo_found:
            print(f"\n❌ No photo found in <picture> elements")
            
            # Fallback: regular <img> elements
            print(f"\n2️⃣ Checking regular <img> elements (fallback)...")
            all_imgs = soup.find_all('img')
            print(f"   Found {len(all_imgs)} <img> elements")
            
            for i, img in enumerate(all_imgs[:10], 1):
                src = img.get('src', '')
                if src and src.startswith('http'):
                    has_apollo = 'apollo.olxcdn.com' in src
                    is_long = len(src) > 100
                    is_svg = src.endswith('.svg')
                    has_icon = 'icon' in src.lower()
                    
                    if has_apollo and is_long and not is_svg and not has_icon:
                        photo_found = src
                        print(f"\n   IMG {i}: MATCH!")
                        print(f"      {src[:120]}...")
                        print(f"      🎯 SELECTED (fallback)")
                        break
        
        print(f"\n{'='*80}")
        print(f"RESULT:")
        print(f"{'='*80}")
        
        if photo_found:
            print(f"✅ PHOTO FOUND!")
            print(f"   Full URL: {photo_found[:150]}...")
            print(f"\n💡 This photo would be sent to Slack")
        else:
            print(f"❌ NO PHOTO FOUND")
            print(f"💡 Parser logic might need adjustment")
        
        print(f"{'='*80}")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_photo_extraction()

