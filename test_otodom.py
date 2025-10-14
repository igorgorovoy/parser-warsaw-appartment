#!/usr/bin/env python3
"""
Test script to check Otodom page structure and selectors
"""

import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()

def test_otodom_selectors():
    """Test different selectors on actual Otodom page"""
    
    # Build URL from env
    from multi_parser import build_otodom_url
    url = build_otodom_url()
    
    print("=" * 80)
    print("Testing Otodom selectors")
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
        cards = soup.find_all('article', {'data-cy': 'listing-item'})
        print(f"✓ Found {len(cards)} cards with article[data-cy='listing-item']")
        
        if not cards:
            # Try alternatives
            cards = soup.find_all('article')
            print(f"  Alternative: Found {len(cards)} <article> tags")
        
        if not cards:
            cards = soup.find_all('div', class_=lambda x: x and 'listing' in x.lower())
            print(f"  Alternative: Found {len(cards)} divs with 'listing' in class")
        
        if cards:
            print("\nTesting first card:")
            print("-" * 80)
            card = cards[0]
            
            # Test title selectors
            print("\nTitle selectors:")
            h3 = card.find('h3')
            print(f"  h3: {h3.get_text(strip=True) if h3 else 'NOT FOUND'}")
            
            h2 = card.find('h2')
            print(f"  h2: {h2.get_text(strip=True) if h2 else 'NOT FOUND'}")
            
            h4 = card.find('h4')
            print(f"  h4: {h4.get_text(strip=True) if h4 else 'NOT FOUND'}")
            
            title_cy = card.find(['div', 'span'], {'data-cy': 'listing-item-title'})
            print(f"  [data-cy='listing-item-title']: {title_cy.get_text(strip=True) if title_cy else 'NOT FOUND'}")
            
            # Try finding by class with 'title'
            title_class = card.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'span', 'div'], class_=lambda x: x and 'title' in x.lower())
            print(f"  element with 'title' in class: {title_class.get_text(strip=True) if title_class else 'NOT FOUND'}")
            
            # Test link
            link = card.find('a', href=True)
            if link:
                print(f"\n  Link text: {link.get_text(strip=True)[:100]}")
                print(f"  Link aria-label: {link.get('aria-label', 'N/A')[:100]}")
            
            # Test price selectors
            print("\nPrice selectors:")
            price_class = card.find('span', class_=lambda x: x and 'price' in x.lower())
            print(f"  span with 'price' in class: {price_class.get_text(strip=True) if price_class else 'NOT FOUND'}")
            
            price_cy = card.find(['span', 'div'], {'data-cy': 'listing-item-price'})
            print(f"  [data-cy='listing-item-price']: {price_cy.get_text(strip=True) if price_cy else 'NOT FOUND'}")
            
            # Test location selectors
            print("\nLocation selectors:")
            loc_class = card.find('span', class_=lambda x: x and 'location' in x.lower())
            print(f"  span with 'location' in class: {loc_class.get_text(strip=True) if loc_class else 'NOT FOUND'}")
            
            loc_cy = card.find(['span', 'div', 'p'], {'data-cy': 'listing-item-location'})
            print(f"  [data-cy='listing-item-location']: {loc_cy.get_text(strip=True) if loc_cy else 'NOT FOUND'}")
            
            # URL
            print("\nURL:")
            link = card.find('a', href=True)
            print(f"  First link: {link['href'] if link else 'NOT FOUND'}")
            
            # ID
            print(f"\nCard ID: {card.get('id', 'N/A')}")
            print(f"Card data-id: {card.get('data-id', 'N/A')}")
            print(f"Card data-item-id: {card.get('data-item-id', 'N/A')}")
            
            # Save full card HTML for inspection
            print("\n" + "=" * 80)
            print("First card HTML structure (saved to debug_otodom_card.html):")
            with open('debug_otodom_card.html', 'w', encoding='utf-8') as f:
                f.write(card.prettify())
            print("✓ Saved to debug_otodom_card.html")
            
            # Show card classes
            print(f"\nCard classes: {card.get('class', [])}")
            print(f"Card attributes: {card.attrs}")
            
            # Try to find all text in card
            print(f"\nAll text in card (first 500 chars):")
            print(card.get_text(strip=True)[:500])
            
        else:
            print("\n❌ No cards found on page!")
            with open('debug_otodom_full_page.html', 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
            print("Saved full page HTML to debug_otodom_full_page.html")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_otodom_selectors()

