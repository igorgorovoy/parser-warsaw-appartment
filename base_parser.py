#!/usr/bin/env python3
"""
Base parser class with common functionality
"""

import sqlite3
import time
import requests
import logging
from typing import Dict, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseParser(ABC):
    """Base parser with common functionality for all listing parsers"""
    
    def __init__(self, slack_webhook_url: str, db_file: str = 'listings.db'):
        self.slack_webhook_url = slack_webhook_url
        self.db_file = db_file
        self._init_database()
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Minimum interval between requests (60 seconds = 1 minute)
        self.request_interval = 60
        self.last_request_time = 0
    
    @abstractmethod
    def get_source_name(self) -> str:
        """Return name of the listing source (e.g., 'OLX', 'Otodom')"""
        pass
    
    @abstractmethod
    def fetch_listings(self) -> list:
        """Fetch listings from the source website"""
        pass
    
    def _init_database(self):
        """Initialize SQLite database for storing seen listings"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS seen_listings (
                    id TEXT PRIMARY KEY,
                    source TEXT,
                    title TEXT,
                    price TEXT,
                    location TEXT,
                    url TEXT,
                    image_url TEXT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sent_to_slack INTEGER DEFAULT 0
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_listing_id ON seen_listings(id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_source ON seen_listings(source)
            ''')
            
            conn.commit()
            conn.close()
            logger.info(f"💾 Database initialized successfully for {self.get_source_name()}")
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
                INSERT OR REPLACE INTO seen_listings (id, source, title, price, location, url, image_url, sent_to_slack)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            ''', (
                listing.get('id'),
                listing.get('source', self.get_source_name()),
                listing.get('title', ''),
                listing.get('price', ''),
                listing.get('location', ''),
                listing.get('url', ''),
                listing.get('image_url', '')
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error saving listing to database: {e}")
    
    def _fetch_photo_from_detail_page(self, listing_url: str) -> Optional[str]:
        """Fetch first photo from listing detail page"""
        try:
            logger.debug(f"Fetching photo from detail page: {listing_url[:80]}...")
            
            # Add small delay to avoid overwhelming the server
            import time
            time.sleep(0.5)
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            response = requests.get(listing_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find images
            for img in soup.find_all('img'):
                src = img.get('src', '')
                # Look for actual photos (not placeholders)
                if 'apollo.olxcdn.com' in src and 'no_thumbnail' not in src:
                    logger.debug(f"Found photo on detail page: {src[:80]}...")
                    return src
            
            logger.debug("No photos found on detail page")
            return None
            
        except Exception as e:
            logger.warning(f"Error fetching photo from detail page: {e}")
            return None
    
    def send_to_slack(self, listing: Dict):
        """Send listing to Slack"""
        try:
            source = listing.get('source', self.get_source_name())
            
            # Build blocks
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🏠 New listing [{source}]: {listing.get('title', 'No title')}"
                    }
                }
            ]
            
            # Add image if available
            image_url = listing.get('image_url')
            if image_url:
                logger.debug(f"Adding image to Slack message: {image_url[:80]}...")
                blocks.append({
                    "type": "image",
                    "image_url": image_url,
                    "alt_text": listing.get('title', 'Apartment image')
                })
            else:
                logger.warning(f"No image_url in listing data for: {listing.get('title', 'Unknown')}")
            
            # Add listing details
            blocks.extend([
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
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"Source: *{source}* | ID: `{listing.get('id', 'unknown')}`"
                        }
                    ]
                },
                {
                    "type": "divider"
                }
            ])
            
            message = {"blocks": blocks}
            
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
            listing['source'] = self.get_source_name()
            
            if listing_id and not self._is_listing_seen(listing_id):
                # Log detailed information about new listing
                logger.info("=" * 80)
                logger.info(f"🆕 NEW LISTING FOUND [{self.get_source_name()}]:")
                logger.info(f"   Title:    {listing.get('title', 'N/A')}")
                logger.info(f"   Price:    {listing.get('price', 'N/A')}")
                logger.info(f"   Location: {listing.get('location', 'N/A')}")
                logger.info(f"   URL:      {listing.get('url', 'N/A')}")
                logger.info(f"   ID:       {listing_id}")
                
                # Try to get image_url from detail page if not present
                if not listing.get('image_url'):
                    logger.info(f"   ⚠️  No image in search results, fetching from detail page...")
                    detail_photo = self._fetch_photo_from_detail_page(listing.get('url'))
                    if detail_photo:
                        listing['image_url'] = detail_photo
                        logger.info(f"   ✅ Fetched photo from detail page")
                
                if listing.get('image_url'):
                    logger.info(f"   📸 Image: {listing.get('image_url', 'N/A')[:80]}...")
                else:
                    logger.warning(f"   ⚠️  No image found (checked detail page too)")
                logger.info("=" * 80)
                
                self.send_to_slack(listing)
                self._save_listing(listing)
                new_count += 1
                # Small delay between sends
                time.sleep(1)
        
        if new_count > 0:
            logger.info(f"✅ Processed {new_count} new listing(s) from {self.get_source_name()}")
        else:
            logger.info(f"ℹ️  No new listings found on {self.get_source_name()}")
        
        return new_count
    
    def get_statistics(self):
        """Get statistics from database for this source"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            source = self.get_source_name()
            
            cursor.execute('SELECT COUNT(*) FROM seen_listings WHERE source = ?', (source,))
            total = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM seen_listings WHERE source = ? AND sent_to_slack = 1', (source,))
            sent = cursor.fetchone()[0]
            
            cursor.execute('SELECT MIN(first_seen), MAX(first_seen) FROM seen_listings WHERE source = ?', (source,))
            first_date, last_date = cursor.fetchone()
            
            conn.close()
            
            logger.info("-" * 80)
            logger.info(f"📊 DATABASE STATISTICS [{source}]:")
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
    
    def _wait_before_request(self):
        """Wait before making request if needed (rate limiting)"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.request_interval:
            wait_time = self.request_interval - time_since_last_request
            logger.info(f"⏳ Waiting {wait_time:.1f} seconds before next request to reduce load...")
            time.sleep(wait_time)
        
        self.last_request_time = time.time()

