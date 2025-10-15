#!/usr/bin/env python3
"""
Otodom.pl parser for apartment listings
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging
import re
import os
from base_parser import BaseParser

logger = logging.getLogger(__name__)


class OtodomParser(BaseParser):
    """Parser for Otodom.pl"""
    
    def __init__(self, search_url: str, slack_webhook_url: str):
        super().__init__(slack_webhook_url)
        self.search_url = search_url
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    
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
            
            # Otodom uses data-cy="listing-item-link" for listing links
            listing_links = soup.find_all('a', {'data-cy': 'listing-item-link'})
            
            if not listing_links:
                logger.warning("⚠️  No listings found on Otodom page")
                # Save HTML for debugging
                with open('debug_otodom_page.html', 'w', encoding='utf-8') as f:
                    f.write(soup.prettify())
                logger.info("💾 Saved page HTML to debug_otodom_page.html for inspection")
                return []
            
            logger.info(f"📋 Found {len(listing_links)} listing(s) on Otodom page")
            
            # Check if we need to filter for private listings
            listing_type = os.getenv('LISTING_TYPE', 'private')
            filter_private = listing_type == 'private'
            
            listings = []
            for link in listing_links:
                try:
                    listing = self._parse_listing_link(link, filter_private)
                    if listing:
                        listings.append(listing)
                except Exception as e:
                    logger.error(f"❌ Error parsing link: {e}")
                    continue
            
            if filter_private and len(listings) < len(listing_links):
                logger.info(f"🔍 Filtered to {len(listings)} private listing(s) (from {len(listing_links)} total)")
            else:
                logger.info(f"✅ Successfully parsed {len(listings)} listing(s)")
            
            return listings
            
        except requests.RequestException as e:
            logger.error(f"Error requesting Otodom: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []
    
    def _parse_listing_link(self, link, filter_private: bool = False) -> Optional[Dict]:
        """Parse individual listing link from Otodom"""
        listing = {}
        
        # Get URL
        url = link.get('href', '')
        if not url:
            return None
        
        if not url.startswith('http'):
            url = 'https://www.otodom.pl' + url
        
        listing['url'] = url
        
        # Extract ID from URL (e.g., ID4yA0z from /pl/oferta/...-ID4yA0z)
        id_match = re.search(r'-ID([a-zA-Z0-9]+)$', url)
        if id_match:
            listing['id'] = f"OTODOM_{id_match.group(1)}"
        else:
            listing['id'] = f"OTODOM_{url.split('/')[-1]}"
        
        # Get title from title element inside link
        title_elem = link.find('p', {'data-cy': 'listing-item-title'})
        if title_elem:
            listing['title'] = title_elem.get_text(strip=True)
        else:
            # Fallback: extract from URL
            url_parts = url.split('/')
            if len(url_parts) > 3:
                slug = url_parts[-1]
                title_slug = re.sub(r'-ID[a-zA-Z0-9]+$', '', slug)
                listing['title'] = title_slug.replace('-', ' ').title()
            else:
                listing['title'] = 'Otodom Listing'
        
        # Get parent element to find price, location, image, and private/business indicator
        parent = link.find_parent('article') or link.find_parent('div', class_=lambda x: x and 'listing' in str(x).lower())
        
        if parent:
            parent_text = parent.get_text(separator=' ', strip=True)
            
            # Check if private listing
            is_private = 'prywatne' in parent_text.lower() or 'oferta prywatna' in parent_text.lower()
            
            # Filter if needed
            if filter_private and not is_private:
                logger.debug(f"⏭️  Skipping non-private listing: {listing.get('title', 'Unknown')}")
                return None
            
            # Extract price
            price_match = re.search(r'(\d[\d\s]*\d+|\d+)\s*zł', parent_text)
            if price_match:
                price_str = price_match.group(1).replace(' ', '')
                listing['price'] = f"{price_str} zł"
            else:
                listing['price'] = 'N/A'
            
            # Extract location
            location_match = re.search(r'(?:ul\.\s+)?([A-ZŁŚĆŻŹ][a-ząćęłńóśźż\s]+(?:,\s*[A-ZŁŚĆŻŹ][a-ząćęłńóśźż\s]+)*)', parent_text)
            if location_match:
                location = location_match.group(1).strip()
                if len(location) > 50:
                    location = location[:50] + '...'
                listing['location'] = location
            else:
                listing['location'] = 'Warszawa'
            
            # Extract image
            img_elem = parent.find('img', src=True)
            if img_elem:
                img_src = img_elem.get('src', '')
                logger.debug(f"Found img element for {listing.get('id')}: src length={len(img_src)}")
                if img_src and img_src.startswith('http'):
                    listing['image_url'] = img_src
                    logger.debug(f"Set image_url from src: {img_src[:80]}...")
                else:
                    # Try srcset for better quality
                    srcset = img_elem.get('srcset', '')
                    if srcset:
                        # srcset format: "url1 1x, url2 2x"
                        urls = [part.strip().split()[0] for part in srcset.split(',') if part.strip()]
                        if urls:
                            # Take the last one (usually highest quality)
                            listing['image_url'] = urls[-1]
                            logger.debug(f"Set image_url from srcset: {urls[-1][:80]}...")
                # Also try data-cy="listing-item-image-source" for Otodom
                if not listing.get('image_url'):
                    img_with_cy = parent.find('img', {'data-cy': 'listing-item-image-source'})
                    if img_with_cy and img_with_cy.get('src'):
                        listing['image_url'] = img_with_cy.get('src')
                        logger.debug(f"Set image_url from data-cy: {listing['image_url'][:80]}...")
            else:
                logger.debug(f"No img element found in parent for {listing.get('id')}")
        else:
            listing['price'] = 'N/A'
            listing['location'] = 'Warszawa'
        
        # Debug logging if data is missing
        if not listing.get('title') or listing['title'] == 'Otodom Listing':
            logger.warning(f"⚠️  Could not extract proper title for: {listing.get('id')}")
            logger.debug(f"URL: {url}")
        
        return listing if listing.get('id') else None
