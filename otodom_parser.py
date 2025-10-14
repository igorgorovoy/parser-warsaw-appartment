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
        """Parse individual listing card from Otodom (React-based site)"""
        listing = {}
        
        # Listing ID and URL
        link_elem = card.find('a', href=True)
        if link_elem and 'href' in link_elem.attrs:
            url = link_elem['href']
            if not url.startswith('http'):
                url = 'https://www.otodom.pl' + url
            listing['url'] = url
            
            # Extract ID from URL
            if 'ID' in url:
                parts = url.split('ID')
                if len(parts) > 1:
                    listing['id'] = 'OTODOM_ID' + parts[-1].split('.')[0].split('/')[0].split('?')[0]
            else:
                # Try to get ID from data attribute
                listing_id = card.get('id') or card.get('data-id') or card.get('data-item-id')
                if listing_id:
                    listing['id'] = f'OTODOM_{listing_id}'
            
            # Extract title from URL (Otodom uses SEO-friendly URLs)
            # Example: /pl/oferta/nowoczesne-mieszkanie-centrum-wysoki-standard-ID4yAgO
            url_parts = url.split('/')
            for part in url_parts:
                if 'ID' in part:
                    # Get the part before ID
                    title_part = part.split('-ID')[0]
                    # Convert dashes to spaces and capitalize
                    listing['title'] = title_part.replace('-', ' ').title()
                    break
        
        # Get all text from card for price and location extraction
        card_text = card.get_text(separator='|', strip=True)
        
        # Extract price from text
        # Pattern: "4900 zł" or "4 900 zł"
        import re
        # Look for first occurrence of price (ignore "+ czynsz" parts)
        price_match = re.search(r'(\d[\d\s]{1,10})\s*zł', card_text)
        if price_match:
            # Clean up the price
            price_clean = price_match.group(1).strip()
            listing['price'] = f"{price_clean} zł"
        
        # Extract location from text
        # Pattern: Location names from Warsaw followed by comma
        location_patterns = [
            r'(Śródmieście|Wola|Mokotów|Praga|Żoliborz|Ochota|Ursynów|Bemowo|Bielany|Targówek|Wilanów|Włochy|Białołęka|Rembertów|Wawer|Ursus|Wesola)[,\s]+[^|]*Warszawa',
            r'al\.\s+[^|]+,\s+[^|]+,\s+Warszawa',
            r'ul\.\s+[^|]+,\s+[^|]+,\s+Warszawa'
        ]
        
        for pattern in location_patterns:
            location_match = re.search(pattern, card_text)
            if location_match:
                listing['location'] = location_match.group(0).strip()
                break
        
        # If no location found, try simpler pattern
        if not listing.get('location'):
            # Just find "Warszawa" with surrounding text
            location_match = re.search(r'[^|]{10,50}Warszawa[^|]{0,20}', card_text)
            if location_match:
                listing['location'] = location_match.group(0).strip()
        
        # Fallback: if still no title, use partial card text
        if not listing.get('title') and card_text:
            # Try to extract something meaningful from card text
            text_parts = card_text.split('|')
            for part in text_parts:
                if len(part) > 20 and len(part) < 100 and 'zł' not in part and 'pokoi' not in part:
                    listing['title'] = part.strip()
                    break
        
        # Debug logging if data is missing
        if not listing.get('title'):
            logger.warning(f"⚠️  Could not extract title for Otodom listing ID: {listing.get('id', 'unknown')}")
            logger.debug(f"URL: {listing.get('url', 'N/A')}")
            logger.debug(f"Card text snippet: {card_text[:300]}")
        
        if not listing.get('price'):
            logger.debug(f"⚠️  No price found for {listing.get('id', 'unknown')}")
        
        if not listing.get('location'):
            logger.debug(f"⚠️  No location found for {listing.get('id', 'unknown')}")
        
        return listing if listing.get('id') else None

