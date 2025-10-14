#!/usr/bin/env python3
"""
OLX Parser for searching apartments in Warsaw
Parses listings and sends new ones to Slack
"""

import os
import json
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Set
import logging
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OLXParser:
    """Parser for OLX.pl"""
    
    def __init__(self, search_url: str, slack_webhook_url: str):
        self.search_url = search_url
        self.slack_webhook_url = slack_webhook_url
        self.seen_ids_file = 'seen_listings.json'
        self.seen_ids = self._load_seen_ids()
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def _load_seen_ids(self) -> Set[str]:
        """Load IDs of previously seen listings"""
        if os.path.exists(self.seen_ids_file):
            try:
                with open(self.seen_ids_file, 'r') as f:
                    return set(json.load(f))
            except Exception as e:
                logger.error(f"Error loading seen_ids: {e}")
                return set()
        return set()
    
    def _save_seen_ids(self):
        """Save IDs of seen listings"""
        try:
            with open(self.seen_ids_file, 'w') as f:
                json.dump(list(self.seen_ids), f)
        except Exception as e:
            logger.error(f"Error saving seen_ids: {e}")
    
    def fetch_listings(self) -> List[Dict]:
        """Fetch list of listings from OLX"""
        try:
            logger.info("Fetching listings from OLX...")
            response = requests.get(self.search_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            listings = []
            
            # OLX uses div with data-cy="l-card"
            cards = soup.find_all('div', {'data-cy': 'l-card'})
            
            if not cards:
                logger.warning("No listings found on page")
                return []
            
            for card in cards:
                try:
                    listing = self._parse_listing_card(card)
                    if listing:
                        listings.append(listing)
                except Exception as e:
                    logger.error(f"Error parsing card: {e}")
                    continue
            
            logger.info(f"Found {len(listings)} listings")
            return listings
            
        except requests.RequestException as e:
            logger.error(f"Error requesting OLX: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []
    
    def _parse_listing_card(self, card) -> Dict:
        """Parse individual listing card"""
        listing = {}
        
        # Listing ID
        link_elem = card.find('a', href=True)
        if link_elem and 'href' in link_elem.attrs:
            url = link_elem['href']
            if not url.startswith('http'):
                url = 'https://www.olx.pl' + url
            listing['url'] = url
            
            # Extract ID from URL
            parts = url.split('-')
            if parts:
                listing['id'] = parts[-1].replace('.html', '').split('#')[0]
        
        # Title
        title_elem = card.find('h6')
        if title_elem:
            listing['title'] = title_elem.get_text(strip=True)
        
        # Price
        price_elem = card.find('p', {'data-testid': 'ad-price'})
        if price_elem:
            listing['price'] = price_elem.get_text(strip=True)
        
        # Location
        location_elem = card.find('p', {'data-testid': 'location-date'})
        if location_elem:
            listing['location'] = location_elem.get_text(strip=True)
        
        return listing if listing.get('id') else None
    
    def send_to_slack(self, listing: Dict):
        """Send listing to Slack"""
        try:
            message = {
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"🏠 New listing: {listing.get('title', 'No title')}"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Price:*\n{listing.get('price', 'Not specified')}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Location:*\n{listing.get('location', 'Not specified')}"
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"<{listing.get('url', '#')}|View listing>"
                        }
                    },
                    {
                        "type": "divider"
                    }
                ]
            }
            
            response = requests.post(
                self.slack_webhook_url,
                json=message,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            logger.info(f"Listing sent to Slack: {listing.get('title', 'N/A')}")
            
        except Exception as e:
            logger.error(f"Error sending to Slack: {e}")
    
    def process_new_listings(self):
        """Main method for processing new listings"""
        listings = self.fetch_listings()
        new_count = 0
        
        for listing in listings:
            listing_id = listing.get('id')
            if listing_id and listing_id not in self.seen_ids:
                logger.info(f"Found new listing: {listing.get('title', 'N/A')}")
                self.send_to_slack(listing)
                self.seen_ids.add(listing_id)
                new_count += 1
                # Small delay between sends
                time.sleep(1)
        
        if new_count > 0:
            self._save_seen_ids()
            logger.info(f"Processed {new_count} new listings")
        else:
            logger.info("No new listings found")
        
        return new_count


def build_search_url() -> str:
    """Build search URL from configuration parameters"""
    base_url = "https://www.olx.pl/nieruchomosci/mieszkania/wynajem/warszawa/"
    
    params = []
    
    # District
    district_id = os.getenv('DISTRICT_ID', '359')  # Default Śródmieście
    if district_id:
        params.append(f"search[district_id]={district_id}")
    
    # Floors (1-9, excluding ground floor)
    floors = os.getenv('FLOORS', '1,2,3,4,5,6,7,8,9').split(',')
    for i, floor in enumerate(floors):
        if floor.strip():
            params.append(f"search[filter_enum_floor_select][{i}]=floor_{floor.strip()}")
    
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
    
    logger.info(f"Built search URL: {search_url}")
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
        logger.info(f"Running in loop mode. Checking every {check_interval} seconds")
        logger.info("Press Ctrl+C to stop")
        
        try:
            while True:
                parser.process_new_listings()
                logger.info(f"Waiting {check_interval} seconds until next check...")
                time.sleep(check_interval)
        except KeyboardInterrupt:
            logger.info("Stopping parser...")
    else:
        logger.info("Running in single check mode")
        parser.process_new_listings()


if __name__ == '__main__':
    main()

