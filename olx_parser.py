#!/usr/bin/env python3
"""
OLX Parser for searching apartments in Warsaw
Parses listings and sends new ones to Slack
"""

import os
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict
import logging
from dotenv import load_dotenv
from base_parser import BaseParser

# Load variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OLXParser(BaseParser):
    """Parser for OLX.pl"""
    
    def __init__(self, search_url: str, slack_webhook_url: str):
        super().__init__(slack_webhook_url)
        self.search_url = search_url
    
    def get_source_name(self) -> str:
        """Return source name"""
        return "OLX"
    
    def fetch_listings(self) -> List[Dict]:
        """Fetch list of listings from OLX for all districts"""
        try:
            self._wait_before_request()
            
            logger.info("🌐 Fetching listings from OLX...")
            
            # Get all district URLs
            urls = build_search_urls()
            all_listings = []
            
            for i, url in enumerate(urls, 1):
                district = url.split('/q-')[1].split('/')[0] if '/q-' in url else 'unknown'
                logger.info(f"🔍 Checking district {i}/{len(urls)}: {district}")
                
                try:
                    response = requests.get(url, headers=self.headers, timeout=30)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # OLX uses div with data-cy="l-card"
                    cards = soup.find_all('div', {'data-cy': 'l-card'})
                    
                    if not cards:
                        logger.debug(f"⚠️  No listings found for district: {district}")
                        continue
                    
                    logger.debug(f"📋 Found {len(cards)} cards for district: {district}")
                    
                    # Get district filter for client-side filtering (supports multiple districts)
                    district_filter = os.getenv('DISTRICT_NAME', '')
                    # Support multiple districts separated by comma: "wola,srodmiescie,mokotow"
                    districts = [d.strip() for d in district_filter.split(',') if d.strip()] if district_filter else []
                    
                    district_listings = []
                    for card in cards:
                        try:
                            listing = self._parse_listing_card(card, filter_districts=districts)
                            if listing:
                                district_listings.append(listing)
                            else:
                                logger.debug("Skipped card (no ID or filtered out)")
                        except Exception as e:
                            logger.error(f"❌ Error parsing card: {e}")
                            continue
                    
                    if districts:
                        total_cards = len(cards)
                        filtered_count = len(district_listings)
                        if filtered_count < total_cards:
                            districts_str = ', '.join([d.capitalize() for d in districts])
                            logger.debug(f"🔍 Filtered to {filtered_count} listing(s) in {districts_str} (from {total_cards} total)")
                    
                    logger.debug(f"📋 Found {len(district_listings)} listing(s) for district: {district}")
                    all_listings.extend(district_listings)
                    
                    # Delay between requests to avoid overwhelming the server
                    if i < len(urls):
                        import random
                        delay = random.uniform(2, 5)  # Random delay between 2-5 seconds
                        logger.debug(f"⏸️  Waiting {delay:.1f} seconds before next district...")
                        time.sleep(delay)
                        
                except Exception as e:
                    logger.error(f"❌ Error fetching district {district}: {e}")
                    continue
            
            logger.info(f"📋 Found {len(all_listings)} total listing(s) from all districts")
            return all_listings
            
        except requests.RequestException as e:
            logger.error(f"Error requesting OLX: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []
    
    def _parse_listing_card(self, card, filter_districts: list = None) -> Dict:
        """Parse individual listing card with optional district filtering (supports multiple districts)"""
        listing = {}
        
        # Listing ID and URL
        link_elem = card.find('a', href=True)
        if link_elem and 'href' in link_elem.attrs:
            url = link_elem['href']
            if not url.startswith('http'):
                url = 'https://www.olx.pl' + url
            
            # Skip listings with extended search (from other districts)
            # OLX adds listings from other districts when results are low
            if 'reason=extended_search' in url:
                logger.debug(f"⏭️  Skipping extended search listing (from other district): {url[:80]}...")
                return None
            
            listing['url'] = url
            
            # Extract ID from URL
            parts = url.split('-')
            if parts:
                listing['id'] = parts[-1].replace('.html', '').split('#')[0]
        
        # Title - try multiple selectors (h4 is primary on OLX as of 2025-10)
        title_elem = card.find('h4')
        if not title_elem:
            # Try alternative selectors
            title_elem = card.find('h6')
        if not title_elem:
            title_elem = card.find('a', {'data-cy': 'listing-ad-title'})
        if not title_elem:
            # Try any heading with class containing 'title'
            title_elem = card.find(['h3', 'h5'], class_=lambda x: x and 'title' in x.lower())
        
        if title_elem:
            listing['title'] = title_elem.get_text(strip=True)
        else:
            # Try to get text from the link
            if link_elem:
                title_text = link_elem.get_text(strip=True)
                if title_text and len(title_text) > 5:
                    listing['title'] = title_text
        
        # Price - try multiple selectors
        price_elem = card.find('p', {'data-testid': 'ad-price'})
        if not price_elem:
            price_elem = card.find('span', class_=lambda x: x and 'price' in x.lower())
        if not price_elem:
            price_elem = card.find('p', class_=lambda x: x and 'price' in x.lower())
        
        if price_elem:
            listing['price'] = price_elem.get_text(strip=True)
        
        # Location - try multiple selectors
        location_elem = card.find('p', {'data-testid': 'location-date'})
        if not location_elem:
            location_elem = card.find('span', class_=lambda x: x and 'location' in x.lower())
        if not location_elem:
            location_elem = card.find('p', class_=lambda x: x and 'location' in x.lower())
        
        if location_elem:
            listing['location'] = location_elem.get_text(strip=True)
            
            # Filter by districts if specified (client-side filtering, supports multiple districts)
            if filter_districts:
                location_lower = listing['location'].lower()
                
                # First check if it's Warsaw (basic city filter)
                if 'warszawa' not in location_lower and 'warsaw' not in location_lower:
                    logger.debug(f"⏭️  Skipping listing from '{listing['location']}' (not Warsaw)")
                    return None
                
                # Extract district from "Warszawa, District - Date" format
                if ',' in location_lower:
                    parts = location_lower.split(',')
                    if len(parts) >= 2:
                        district_part = parts[1].strip().split(' - ')[0]
                        # Check if the district matches any of the allowed districts (case-insensitive)
                        match_found = any(district.lower() in district_part for district in filter_districts)
                        if not match_found:
                            districts_str = ', '.join(filter_districts)
                            logger.debug(f"⏭️  Skipping listing from '{district_part}' (looking for: {districts_str})")
                            return None
        
        # Image - try to find first image
        img_elem = card.find('img', src=True)
        if img_elem:
            img_src = img_elem.get('src', '')
            # OLX images can be in srcset or src
            if img_src and img_src.startswith('http'):
                listing['image_url'] = img_src
            else:
                # Try srcset for better quality
                srcset = img_elem.get('srcset', '')
                if srcset:
                    # srcset format: "url1 150w, url2 300w, ..."
                    # Take the first URL (already decent quality)
                    urls = [part.strip().split()[0] for part in srcset.split(',') if part.strip()]
                    if urls:
                        listing['image_url'] = urls[0]
        
        # Debug logging if title is missing
        if not listing.get('title'):
            logger.warning(f"⚠️  Could not find title for listing ID: {listing.get('id', 'unknown')}")
            logger.debug(f"Card HTML structure: {card.prettify()[:500]}")
        
        return listing if listing.get('id') else None


def build_search_urls() -> List[str]:
    """Build search URLs for all districts"""
    
    # Get all districts
    district_name = os.getenv('DISTRICT_NAME', 'wola')
    districts = [d.strip() for d in district_name.split(',') if d.strip()]
    
    urls = []
    for district in districts:
        base_url = f"https://www.olx.pl/nieruchomosci/mieszkania/wynajem/warszawa/q-{district}/"
        
        params = []
        
        # NOTE: Floor filter is NOT supported by OLX API - it breaks the URL and causes random results
        # Keeping the env var for documentation but not using it in the URL
        # floors = os.getenv('FLOORS', '1,2,3,4,5,6,7,8,9')
        
        # Furnished
        furniture = os.getenv('FURNITURE', 'yes')
        if furniture:
            params.append(f"search[filter_enum_furniture][0]={furniture}")
        
        # Pets allowed
        pets = os.getenv('PETS', 'Tak')
        if pets:
            params.append(f"search[filter_enum_pets][0]={pets}")
        
        # Number of rooms (one, two, three, four)
        rooms = os.getenv('ROOMS', 'three')
        if rooms:
            params.append(f"search[filter_enum_rooms][0]={rooms}")
        
        # Price from
        price_from = os.getenv('PRICE_FROM', '4000')
        if price_from:
            params.append(f"search[filter_float_price:from]={price_from}")
        
        # Price to
        price_to = os.getenv('PRICE_TO', '6000')
        if price_to:
            params.append(f"search[filter_float_price:to]={price_to}")
        
        # Listing type (private or business)
        listing_type = os.getenv('LISTING_TYPE', 'private')
        if listing_type:
            params.append(f"search[private_business]={listing_type}")
        
        # Build URL
        if params:
            search_url = base_url + '?' + '&'.join(params)
        else:
            search_url = base_url
        
        urls.append(search_url)
    
    return urls


def build_search_url() -> str:
    """Build search URL from configuration parameters (legacy function for compatibility)"""
    
    # District - use only the first district in URL path for proper filtering
    # Multiple districts are handled by client-side filtering
    district_name = os.getenv('DISTRICT_NAME', 'wola')  # Default: Wola
    # Take only the first district for URL
    first_district = district_name.split(',')[0].strip()
    base_url = f"https://www.olx.pl/nieruchomosci/mieszkania/wynajem/warszawa/q-{first_district}/"
    
    params = []
    
    # NOTE: Floor filter is NOT supported by OLX API - it breaks the URL and causes random results
    # Keeping the env var for documentation but not using it in the URL
    # floors = os.getenv('FLOORS', '1,2,3,4,5,6,7,8,9')
    
    # Furnished
    furniture = os.getenv('FURNITURE', 'yes')
    if furniture:
        params.append(f"search[filter_enum_furniture][0]={furniture}")
    
    # Pets allowed
    pets = os.getenv('PETS', 'Tak')
    if pets:
        params.append(f"search[filter_enum_pets][0]={pets}")
    
    # Number of rooms (one, two, three, four)
    rooms = os.getenv('ROOMS', 'three')
    if rooms:
        params.append(f"search[filter_enum_rooms][0]={rooms}")
    
    # Price from
    price_from = os.getenv('PRICE_FROM', '4000')
    if price_from:
        params.append(f"search[filter_float_price:from]={price_from}")
    
    # Price to
    price_to = os.getenv('PRICE_TO', '6000')
    if price_to:
        params.append(f"search[filter_float_price:to]={price_to}")
    
    # Listing type (private or business)
    listing_type = os.getenv('LISTING_TYPE', 'private')
    if listing_type:
        params.append(f"search[private_business]={listing_type}")
    
    # Build URL
    if params:
        search_url = base_url + '?' + '&'.join(params)
    else:
        search_url = base_url
    
    # Log search criteria
    logger.info("=" * 80)
    logger.info("🔍 OLX SEARCH CRITERIA:")
    
    # Show all districts for filtering
    all_districts = [d.strip().capitalize() for d in district_name.split(',') if d.strip()]
    if len(all_districts) > 1:
        logger.info(f"   Districts:    {', '.join(all_districts)} (filtered client-side)")
        logger.info(f"   URL district: {first_district.capitalize()} (first district only)")
    else:
        logger.info(f"   District:     {first_district.capitalize()}")
    
    logger.info(f"   Rooms:        {os.getenv('ROOMS', 'three')}")
    logger.info(f"   Price:        {os.getenv('PRICE_FROM', '4000')} - {os.getenv('PRICE_TO', '6000')} PLN")
    logger.info(f"   Furniture:    {os.getenv('FURNITURE', 'yes')}")
    logger.info(f"   Pets:         {os.getenv('PETS', 'Tak')}")
    logger.info(f"   Listing type: {os.getenv('LISTING_TYPE', 'private')}")
    logger.info(f"   ⚠️  Note: Floor filter not supported by OLX API")
    logger.info("=" * 80)
    logger.debug(f"Full URL: {search_url}")
    return search_url


def main():
    """Main function"""
    
    # Slack Webhook URL
    SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')
    
    # Check required parameters
    if not SLACK_WEBHOOK_URL:
        logger.error("SLACK_WEBHOOK_URL not set!")
        logger.error("Create .env file and add: SLACK_WEBHOOK_URL='https://hooks.slack.com/services/YOUR/WEBHOOK/URL'")
        return
    
    # Build URL from parameters
    SEARCH_URL = build_search_url()
    
    parser = OLXParser(SEARCH_URL, SLACK_WEBHOOK_URL)
    
    # Operation mode: single run or loop
    run_mode = os.getenv('RUN_MODE', 'once')  # 'once' or 'loop'
    
    if run_mode == 'loop':
        check_interval = int(os.getenv('CHECK_INTERVAL', '300'))  # Default 5 minutes
        logger.info("=" * 80)
        logger.info(f"🔄 Running in LOOP mode")
        logger.info(f"   Check interval:  {check_interval} seconds ({check_interval//60} minutes)")
        logger.info(f"   Request delay:   60 seconds (1 minute)")
        logger.info(f"   Press Ctrl+C to stop")
        logger.info("=" * 80)
        
        try:
            iteration = 0
            while True:
                iteration += 1
                logger.info(f"\n{'='*80}")
                logger.info(f"🔍 ITERATION #{iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info("=" * 80)
                
                parser.process_new_listings()
                parser.get_statistics()
                
                logger.info(f"\n⏸️  Waiting {check_interval} seconds until next check...")
                time.sleep(check_interval)
        except KeyboardInterrupt:
            logger.info("\n" + "=" * 80)
            logger.info("🛑 Stopping parser...")
            logger.info("=" * 80)
            parser.get_statistics()
    else:
        logger.info("=" * 80)
        logger.info(f"▶️  Running in SINGLE CHECK mode")
        logger.info(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)
        parser.process_new_listings()
        parser.get_statistics()


if __name__ == '__main__':
    main()

