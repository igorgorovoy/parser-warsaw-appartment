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
import sqlite3

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
        self.db_file = 'listings.db'
        self._init_database()
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Minimum interval between requests to OLX (60 seconds = 1 minute)
        self.request_interval = 60
        self.last_request_time = 0
    
    def _init_database(self):
        """Initialize SQLite database for storing seen listings"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Create table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS seen_listings (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    price TEXT,
                    location TEXT,
                    url TEXT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sent_to_slack INTEGER DEFAULT 0
                )
            ''')
            
            # Create index for faster lookups
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_listing_id ON seen_listings(id)
            ''')
            
            conn.commit()
            conn.close()
            logger.info("💾 Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def _is_listing_seen(self, listing_id: str) -> bool:
        """Check if listing has been seen before"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM seen_listings WHERE id = ?', (listing_id,))
            result = cursor.fetchone()
            conn.close()
            return result is not None
        except Exception as e:
            logger.error(f"Error checking listing: {e}")
            return False
    
    def _save_listing(self, listing: Dict):
        """Save listing to database"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO seen_listings (id, title, price, location, url, sent_to_slack)
                VALUES (?, ?, ?, ?, ?, 1)
            ''', (
                listing.get('id'),
                listing.get('title', ''),
                listing.get('price', ''),
                listing.get('location', ''),
                listing.get('url', '')
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error saving listing to database: {e}")
    
    def fetch_listings(self) -> List[Dict]:
        """Fetch list of listings from OLX"""
        try:
            # Wait before making request if needed (1 minute interval)
            current_time = time.time()
            time_since_last_request = current_time - self.last_request_time
            
            if time_since_last_request < self.request_interval:
                wait_time = self.request_interval - time_since_last_request
                logger.info(f"⏳ Waiting {wait_time:.1f} seconds before next request to reduce load on OLX...")
                time.sleep(wait_time)
            
            logger.info("🌐 Fetching listings from OLX...")
            response = requests.get(self.search_url, headers=self.headers, timeout=30)
            self.last_request_time = time.time()
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            listings = []
            
            # OLX uses div with data-cy="l-card"
            cards = soup.find_all('div', {'data-cy': 'l-card'})
            
            if not cards:
                logger.warning("⚠️  No listings found on page")
                logger.debug("Trying alternative selectors...")
                
                # Try alternative card selector
                cards = soup.find_all('div', class_=lambda x: x and 'offer' in x.lower())
                if not cards:
                    logger.warning("⚠️  Still no listings found with alternative selectors")
                    # Save HTML for debugging
                    with open('debug_page.html', 'w', encoding='utf-8') as f:
                        f.write(soup.prettify())
                    logger.info("💾 Saved page HTML to debug_page.html for inspection")
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
            
            logger.info(f"📋 Found {len(listings)} listing(s) on page")
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
        
        # Listing ID and URL
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
        
        # Debug logging if title is missing
        if not listing.get('title'):
            logger.warning(f"⚠️  Could not find title for listing ID: {listing.get('id', 'unknown')}")
            logger.debug(f"Card HTML structure: {card.prettify()[:500]}")
        
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
            logger.info(f"✉️  Listing sent to Slack successfully")
            
        except Exception as e:
            logger.error(f"Error sending to Slack: {e}")
    
    def process_new_listings(self):
        """Main method for processing new listings"""
        listings = self.fetch_listings()
        new_count = 0
        
        for listing in listings:
            listing_id = listing.get('id')
            if listing_id and not self._is_listing_seen(listing_id):
                # Log detailed information about new listing
                logger.info("=" * 80)
                logger.info(f"🆕 NEW LISTING FOUND:")
                logger.info(f"   Title:    {listing.get('title', 'N/A')}")
                logger.info(f"   Price:    {listing.get('price', 'N/A')}")
                logger.info(f"   Location: {listing.get('location', 'N/A')}")
                logger.info(f"   URL:      {listing.get('url', 'N/A')}")
                logger.info(f"   ID:       {listing_id}")
                logger.info("=" * 80)
                
                self.send_to_slack(listing)
                self._save_listing(listing)
                new_count += 1
                # Small delay between sends
                time.sleep(1)
        
        if new_count > 0:
            logger.info(f"✅ Processed {new_count} new listing(s)")
        else:
            logger.info("ℹ️  No new listings found")
        
        return new_count
    
    def get_statistics(self):
        """Get statistics from database"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM seen_listings')
            total = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM seen_listings WHERE sent_to_slack = 1')
            sent = cursor.fetchone()[0]
            
            # Get date of first and last listing
            cursor.execute('SELECT MIN(first_seen), MAX(first_seen) FROM seen_listings')
            first_date, last_date = cursor.fetchone()
            
            conn.close()
            
            logger.info("-" * 80)
            logger.info(f"📊 DATABASE STATISTICS:")
            logger.info(f"   Total listings stored: {total}")
            logger.info(f"   Sent to Slack:         {sent}")
            if first_date:
                logger.info(f"   First listing:         {first_date}")
            if last_date:
                logger.info(f"   Last listing:          {last_date}")
            logger.info("-" * 80)
            
            return {'total': total, 'sent': sent}
        except Exception as e:
            logger.error(f"❌ Error getting statistics: {e}")
            return {'total': 0, 'sent': 0}


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
    
    logger.info(f"🔗 Built search URL with {len(params)} parameters")
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

