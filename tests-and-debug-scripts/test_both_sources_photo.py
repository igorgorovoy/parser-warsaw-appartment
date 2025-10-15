#!/usr/bin/env python3
"""
Test to verify photo extraction logic for BOTH OLX and Otodom
"""

import requests
from bs4 import BeautifulSoup

# Test URLs
olx_url = "https://www.olx.pl/d/oferta/3-pokoje-70mkw-centrum-wawy-po-remoncie-od-pazdziernika-CID3-ID17uxKh.html"
otodom_url = "https://www.otodom.pl/pl/oferta/wyjatkowy-apartament-al-ujazdowskie-16-ID4yv8T"

def test_source(url, source_name):
    """Test photo extraction for a source"""
    print(f"\n{'='*80}")
    print(f"🧪 TESTING {source_name}")
    print('='*80)
    print(f"URL: {url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        is_otodom = 'otodom.pl' in url
        
        print(f"\n📋 Source detection: {'Otodom' if is_otodom else 'OLX'}")
        
        # Check <picture> elements
        pictures = soup.find_all('picture')
        print(f"\n🖼️  Found {len(pictures)} <picture> elements")
        
        if pictures and is_otodom:
            print(f"   Testing Otodom logic (<picture> first):")
            for i, pic in enumerate(pictures[:3], 1):
                imgs = pic.find_all('img')
                for img in imgs:
                    src = img.get('src', '')
                    if src:
                        has_apollo = 'apollo.olxcdn.com' in src
                        has_ecosystem = 'ECOSYSTEM' in src
                        is_svg = src.endswith('.svg')
                        has_icon = 'icon' in src.lower()
                        
                        print(f"\n   Picture {i}:")
                        print(f"      URL: {src[:100]}...")
                        print(f"      ✓ apollo.olxcdn.com: {has_apollo}")
                        print(f"      ✓ ECOSYSTEM: {has_ecosystem}")
                        print(f"      ✗ .svg: {is_svg}")
                        print(f"      ✗ icon: {has_icon}")
                        
                        if has_apollo and has_ecosystem and not is_svg and not has_icon:
                            print(f"      ✅ MATCH! This would be selected")
                            print(f"\n🎯 SELECTED FOR {source_name}: {src}")
                            return src
        
        # Check regular <img> elements
        all_imgs = soup.find_all('img')
        print(f"\n🖼️  Found {len(all_imgs)} total <img> elements")
        
        print(f"   Testing {'Otodom' if is_otodom else 'OLX'} logic (fallback/main):")
        for i, img in enumerate(all_imgs[:10], 1):
            src = img.get('src', '')
            if src and src.startswith('http'):
                has_apollo = 'apollo.olxcdn.com' in src
                has_ecosystem = 'ECOSYSTEM' in src
                is_svg = src.endswith('.svg')
                has_icon = 'icon' in src.lower()
                has_no_thumb = 'no_thumbnail' in src
                
                if is_otodom:
                    # Otodom logic
                    if has_apollo and has_ecosystem and not is_svg and not has_icon:
                        print(f"\n   IMG {i}: MATCH!")
                        print(f"      {src[:100]}...")
                        print(f"      🎯 SELECTED FOR Otodom (fallback)")
                        return src
                else:
                    # OLX logic
                    if has_apollo and not has_no_thumb:
                        print(f"\n   IMG {i}: MATCH!")
                        print(f"      {src[:100]}...")
                        print(f"      🎯 SELECTED FOR OLX")
                        return src
        
        print(f"\n❌ No photo found with current logic")
        return None
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return None

def main():
    print("🔍 TESTING PHOTO EXTRACTION LOGIC FOR BOTH SOURCES")
    print("="*80)
    
    olx_photo = test_source(olx_url, "OLX")
    otodom_photo = test_source(otodom_url, "OTODOM")
    
    print(f"\n{'='*80}")
    print("📊 SUMMARY")
    print('='*80)
    print(f"\n✅ OLX photo found: {bool(olx_photo)}")
    if olx_photo:
        print(f"   {olx_photo[:120]}...")
        if 'ECOSYSTEM' in olx_photo:
            print(f"   ⚠️  WARNING: OLX photo contains 'ECOSYSTEM' - might conflict with Otodom!")
    
    print(f"\n✅ Otodom photo found: {bool(otodom_photo)}")
    if otodom_photo:
        print(f"   {otodom_photo[:120]}...")
    
    print(f"\n{'='*80}")
    if olx_photo and otodom_photo:
        print("✅ LOGIC IS CORRECT - both sources work!")
    else:
        print("❌ LOGIC HAS ISSUES - check the code!")
    print('='*80)

if __name__ == '__main__':
    main()

