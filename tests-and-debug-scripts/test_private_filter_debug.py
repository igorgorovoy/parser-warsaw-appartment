#!/usr/bin/env python3
"""Debug script to check private/business listing detection"""

import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

def test_otodom():
    """Test Otodom private filter"""
    print("="*80)
    print("TESTING OTODOM PRIVATE FILTER")
    print("="*80)
    
    # Build URL
    district = os.getenv('OTODOM_DISTRICT', 'wola')
    rooms = os.getenv('ROOMS', 'three')
    price_from = os.getenv('PRICE_FROM', '4000')
    price_to = os.getenv('PRICE_TO', '6000')
    
    # Map rooms
    rooms_map = {'one': '1', 'two': '2', 'three': '3', 'four': '4'}
    rooms_num = rooms_map.get(rooms, '3')
    
    url = f"https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie/mazowieckie/warszawa/{district}?limit=36&roomsNumber=%5B{rooms_num}%5D&priceMax={price_to}&priceMin={price_from}&by=DEFAULT&direction=DESC&viewType=listing"
    
    print(f"\nURL: {url}\n")
    
    response = requests.get(url, timeout=30)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    listing_links = soup.find_all('a', {'data-cy': 'listing-item-link'})
    print(f"Found {len(listing_links)} listings\n")
    
    for i, link in enumerate(listing_links[:5], 1):
        print(f"\n{'='*60}")
        print(f"Listing {i}")
        print('='*60)
        
        # Get parent
        parent = link.find_parent('article') or link.find_parent('div', class_=lambda x: x and 'listing' in str(x).lower())
        
        if parent:
            parent_text = parent.get_text(separator=' | ', strip=True)
            
            # Check for private indicators
            is_private_1 = 'prywatne' in parent_text.lower()
            is_private_2 = 'oferta prywatna' in parent_text.lower()
            is_private_3 = 'biuro' in parent_text.lower()  # opposite - business
            is_private_4 = 'agencja' in parent_text.lower()  # opposite - business
            
            print(f"Contains 'prywatne': {is_private_1}")
            print(f"Contains 'oferta prywatna': {is_private_2}")
            print(f"Contains 'biuro': {is_private_3}")
            print(f"Contains 'agencja': {is_private_4}")
            
            # Show relevant text snippet
            text_lower = parent_text.lower()
            for keyword in ['prywatne', 'biuro', 'agencja', 'deweloper']:
                if keyword in text_lower:
                    idx = text_lower.index(keyword)
                    snippet = parent_text[max(0, idx-30):min(len(parent_text), idx+50)]
                    print(f"\nSnippet with '{keyword}': ...{snippet}...")
            
            # Show title
            title_elem = link.find('p', {'data-cy': 'listing-item-title'})
            if title_elem:
                print(f"\nTitle: {title_elem.get_text(strip=True)[:60]}")

def test_olx():
    """Test OLX URL with private filter"""
    print("\n\n")
    print("="*80)
    print("TESTING OLX PRIVATE FILTER")
    print("="*80)
    
    district_name = os.getenv('DISTRICT_NAME', 'wola')
    base_url = f"https://www.olx.pl/nieruchomosci/mieszkania/wynajem/warszawa/q-{district_name}/"
    
    params = [
        f"search[filter_enum_rooms][0]=three",
        f"search[filter_float_price:from]=4000",
        f"search[filter_float_price:to]=6000",
        f"search[private_business]=private",  # This should filter to private only
    ]
    
    url = base_url + '?' + '&'.join(params)
    print(f"\nURL: {url}\n")
    print(f"Private filter parameter: search[private_business]=private")
    
    response = requests.get(url, timeout=30)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    cards = soup.find_all('div', {'data-cy': 'l-card'})
    print(f"\nFound {len(cards)} listings on OLX")
    
    # Check if we can detect business vs private in the HTML
    for i, card in enumerate(cards[:3], 1):
        print(f"\n{'='*60}")
        print(f"OLX Listing {i}")
        print('='*60)
        
        card_text = card.get_text(separator=' | ', strip=True)
        
        # Look for business indicators
        has_pro = 'PRO' in card_text or 'pro' in card_text.lower()
        has_business = 'biuro' in card_text.lower() or 'agencja' in card_text.lower()
        
        print(f"Has 'PRO': {has_pro}")
        print(f"Has business keywords: {has_business}")
        
        # Get title
        title_elem = card.find('h4') or card.find('h6')
        if title_elem:
            print(f"Title: {title_elem.get_text(strip=True)[:60]}")

if __name__ == '__main__':
    test_otodom()
    test_olx()

