#!/usr/bin/env python3
"""
Test script to check OLX page structure and selectors
"""

import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()

def test_selectors():
    """Test different selectors on actual OLX page"""
    
    # Build URL from env
    from olx_parser import build_search_url
    url = build_search_url()
    
    print("=" * 80)
    print("Testing OLX selectors")
    print("=" * 80)
    print(f"URL: {url}\n")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print("Testing card selectors:")
        print("-" * 80)
        
        # Test main selector
        cards = soup.find_all('div', {'data-cy': 'l-card'})
        print(f"✓ Found {len(cards)} cards with data-cy='l-card'")
        
        if not cards:
            # Try alternatives
            cards = soup.find_all('div', class_=lambda x: x and 'offer' in x.lower())
            print(f"  Alternative: Found {len(cards)} cards with 'offer' in class")
        
        if cards:
            print("\nTesting first card:")
            print("-" * 80)
            card = cards[0]
            
            # Test title selectors
            print("\nTitle selectors:")
            h6 = card.find('h6')
            print(f"  h6: {h6.get_text(strip=True) if h6 else 'NOT FOUND'}")
            
            h4 = card.find('h4')
            print(f"  h4: {h4.get_text(strip=True) if h4 else 'NOT FOUND'}")
            
            title_link = card.find('a', {'data-cy': 'listing-ad-title'})
            print(f"  a[data-cy='listing-ad-title']: {title_link.get_text(strip=True) if title_link else 'NOT FOUND'}")
            
            # Test price selectors
            print("\nPrice selectors:")
            price_testid = card.find('p', {'data-testid': 'ad-price'})
            print(f"  p[data-testid='ad-price']: {price_testid.get_text(strip=True) if price_testid else 'NOT FOUND'}")
            
            price_class = card.find('span', class_=lambda x: x and 'price' in x.lower())
            print(f"  span with 'price' in class: {price_class.get_text(strip=True) if price_class else 'NOT FOUND'}")
            
            # Test location selectors
            print("\nLocation selectors:")
            loc_testid = card.find('p', {'data-testid': 'location-date'})
            print(f"  p[data-testid='location-date']: {loc_testid.get_text(strip=True) if loc_testid else 'NOT FOUND'}")
            
            # URL
            print("\nURL:")
            link = card.find('a', href=True)
            print(f"  First link: {link['href'] if link else 'NOT FOUND'}")
            
            # Save full card HTML for inspection
            print("\n" + "=" * 80)
            print("First card HTML structure (saved to debug_card.html):")
            with open('debug_card.html', 'w', encoding='utf-8') as f:
                f.write(card.prettify())
            print("✓ Saved to debug_card.html")
            
            # Show card classes
            print(f"\nCard classes: {card.get('class', [])}")
            print(f"Card attributes: {card.attrs}")
            
        else:
            print("\n❌ No cards found on page!")
            with open('debug_full_page.html', 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
            print("Saved full page HTML to debug_full_page.html")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    test_selectors()

