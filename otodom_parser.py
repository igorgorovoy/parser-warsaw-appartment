#!/usr/bin/env python3
"""
Otodom.pl parser for apartment listings
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import logging
from base_parser import BaseParser

logger = logging.getLogger(__name__)


class OtodomParser(BaseParser):
    """Parser for Otodom.pl"""
    
    def __init__(self, search_url: str, slack_webhook_url: str):
        super().__init__(slack_webhook_url)
        self.search_url = search_url
    
    def get_source_name(self) -> str:
        """Return source name"""
        return "Otodom"
    
    def fetch_listings(self) -> List[Dict]:
        """Fetch list of listings from Otodom"""
        try:
            self._wait_before_request()
            
            logger.info("🌐 Fetching listings from Otodom...")
            response = requests.get(self.search_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            listings = []
            
            # Otodom uses article tags or div with specific classes
            # Try multiple selectors
            cards = soup.find_all('article', {'data-cy': 'listing-item'})
            
            if not cards:
                # Try alternative selectors
                cards = soup.find_all('div', class_=lambda x: x and 'listing' in x.lower())
            
            if not cards:
                logger.warning("⚠️  No listings found on Otodom page")
                logger.debug("Trying more alternative selectors...")
                
                # Try finding by data attributes
                cards = soup.find_all('article')
                if not cards:
                    # Save HTML for debugging
                    with open('debug_otodom_page.html', 'w', encoding='utf-8') as f:
                        f.write(soup.prettify())
                    logger.info("💾 Saved page HTML to debug_otodom_page.html for inspection")
                    return []
            
            for card in cards:
                try:
                    listing = self._parse_listing_card(card)
                    if listing:
                        listings.append(listing)
                    else:
                        logger.debug("Skipped card without ID")
                except Exception as e:
                    logger.error(f"❌ Error parsing card: {e}")
                    continue
            
            logger.info(f"📋 Found {len(listings)} listing(s) on Otodom page")
            return listings
            
        except requests.RequestException as e:
            logger.error(f"Error requesting Otodom: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []
    
    def _parse_listing_card(self, card) -> Dict:
        """Parse individual listing card from Otodom"""
        listing = {}
        
        # Listing ID and URL
        link_elem = card.find('a', href=True)
        if link_elem and 'href' in link_elem.attrs:
            url = link_elem['href']
            if not url.startswith('http'):
                url = 'https://www.otodom.pl' + url
            listing['url'] = url
            
            # Extract ID from URL or data attribute
            if 'ID' in url:
                parts = url.split('ID')
                if len(parts) > 1:
                    listing['id'] = 'OTODOM_ID' + parts[-1].split('.')[0].split('/')[0].split('?')[0]
            else:
                # Try to get ID from data attribute
                listing_id = card.get('id') or card.get('data-id') or card.get('data-item-id')
                if listing_id:
                    listing['id'] = f'OTODOM_{listing_id}'
        
        # Title - try multiple selectors
        title_elem = card.find('h3')
        if not title_elem:
            title_elem = card.find('h2')
        if not title_elem:
            title_elem = card.find('h4')
        if not title_elem:
            # Try finding by aria-label or data-cy
            title_elem = card.find(['div', 'span'], {'data-cy': 'listing-item-title'})
        
        if title_elem:
            listing['title'] = title_elem.get_text(strip=True)
        else:
            # Try to get text from the link
            if link_elem:
                title_text = link_elem.get('aria-label', '')
                if not title_text:
                    title_text = link_elem.get_text(strip=True)
                if title_text and len(title_text) > 5:
                    listing['title'] = title_text
        
        # Price - try multiple selectors
        price_elem = card.find('span', class_=lambda x: x and 'price' in x.lower())
        if not price_elem:
            price_elem = card.find('div', class_=lambda x: x and 'price' in x.lower())
        if not price_elem:
            price_elem = card.find(['span', 'div'], {'data-cy': 'listing-item-price'})
        
        if price_elem:
            listing['price'] = price_elem.get_text(strip=True)
        
        # Location - try multiple selectors
        location_elem = card.find('span', class_=lambda x: x and 'location' in x.lower())
        if not location_elem:
            location_elem = card.find('div', class_=lambda x: x and 'location' in x.lower())
        if not location_elem:
            location_elem = card.find(['span', 'div', 'p'], {'data-cy': 'listing-item-location'})
        
        if location_elem:
            listing['location'] = location_elem.get_text(strip=True)
        
        # Debug logging if title is missing
        if not listing.get('title'):
            logger.warning(f"⚠️  Could not find title for Otodom listing ID: {listing.get('id', 'unknown')}")
            logger.debug(f"Card HTML structure: {card.prettify()[:500]}")
        
        return listing if listing.get('id') else None

