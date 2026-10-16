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
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
        
        # Minimum interval between requests (90 seconds = 1.5 minutes)
        self.request_interval = 90
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

    def _save_filtered(self, listing: Dict):
        """Remember a listing that was filtered out (sent_to_slack = 0) so it isn't re-checked"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO seen_listings (id, source, title, price, location, url, image_url, sent_to_slack)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0)
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
            logger.error(f"Error saving filtered listing to database: {e}")

    def _fetch_photo_from_detail_page(self, listing_url: str) -> Optional[str]:
        """Fetch first photo from listing detail page"""
        try:
            logger.debug(f"Fetching photo from detail page: {listing_url[:80]}...")
            
            # Add small delay to avoid overwhelming the server
            import time
            time.sleep(0.5)
            
            # Use the same headers as main requests for consistency
            response = requests.get(listing_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Detect source based on URL
            is_otodom = 'otodom.pl' in listing_url
            
            # Otodom uses OLX CDN for photos, so check <picture> elements first
            if is_otodom:
                # Look for <picture> elements (Otodom's gallery)
                pictures = soup.find_all('picture')
                for pic in pictures:
                    imgs = pic.find_all('img')
                    for img in imgs:
                        src = img.get('src', '')
                        # Otodom stores photos on OLX CDN (apollo.olxcdn.com)
                        # Photos have long base64-encoded URLs
                        if 'apollo.olxcdn.com' in src and len(src) > 100:
                            # Skip SVG, icons, logos
                            if not src.endswith('.svg') and 'icon' not in src.lower() and 'logo' not in src.lower():
                                logger.debug(f"Found Otodom photo in <picture>: {src[:80]}...")
                                return src
            
            # Fallback: Find images
            for img in soup.find_all('img'):
                src = img.get('src', '')
                
                if is_otodom:
                    # Otodom: also try apollo CDN (fallback)
                    # Photos have long base64-encoded URLs
                    if 'apollo.olxcdn.com' in src and len(src) > 100:
                        if not src.endswith('.svg') and 'icon' not in src.lower() and 'logo' not in src.lower():
                            logger.debug(f"Found Otodom photo on detail page: {src[:80]}...")
                            return src
                else:
                    # OLX: look for actual photos (not placeholders)
                    if 'apollo.olxcdn.com' in src and 'no_thumbnail' not in src:
                        logger.debug(f"Found OLX photo on detail page: {src[:80]}...")
                        return src
            
            logger.debug("No photos found on detail page")
            return None
            
        except Exception as e:
            logger.warning(f"Error fetching photo from detail page: {e}")
            return None
    
    def send_to_slack(self, listing: Dict):
        """Send listing to Slack"""
        try:
            # Double-check that we haven't sent this listing before
            listing_id = listing.get('id')
            if listing_id and self._is_listing_seen(listing_id):
                logger.warning(f"⚠️  Listing {listing_id} already sent to Slack, skipping...")
                return
            
            source = listing.get('source', self.get_source_name())
            
            # Extract date from location for display
            import re
            location = listing.get('location', '')
            date_display = ""
            date_match = re.search(r'(\d{1,2}\s+\w+\s+\d{4})', location)
            if date_match:
                date_display = f" • {date_match.group(1)}"
            
            # Build blocks
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🏠 New listing [{source}]{date_display}: {listing.get('title', 'No title')}"[:150]
                    }
                }
            ]
            
            # Add listing details FIRST
            price_text = listing.get('price', 'Not specified')
            czynsz = listing.get('czynsz')
            if czynsz:
                price_text += f"\n*Czynsz:* {czynsz}"
            
            blocks.extend([
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Price:*\n{price_text}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Location:*\n{listing.get('location', 'Not specified')}"
                        }
                    ]
                }
            ])

            extra = '\n'.join(filter(None, [listing.get('details'), listing.get('bus')]))
            if extra:
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": extra}
                })

            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"<{listing.get('url', '#')}|View listing>"
                }
            })
            
            # Add image AFTER details (Slack displays it better this way)
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
            
            # Add context and divider at the end
            blocks.extend([
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
            if not response.ok:
                # Raise so the caller doesn't mark the listing as sent
                raise RuntimeError(f"Slack {response.status_code}: {response.text}")
            logger.info(f"✉️  Listing sent to Slack successfully")

        except Exception as e:
            logger.error(f"Error sending to Slack: {e}")
            raise
    
    def _extract_date_from_location(self, location: str) -> str:
        """Extract date from location string for sorting"""
        import re
        from datetime import datetime
        
        # Try to extract date from "Warszawa, District - DD month YYYY" format
        date_match = re.search(r'(\d{1,2})\s+(stycznia|lutego|marca|kwietnia|maja|czerwca|lipca|sierpnia|września|października|listopada|grudnia)\s+(\d{4})', location.lower())
        if date_match:
            day = date_match.group(1)
            month_pl = date_match.group(2)
            year = date_match.group(3)
            
            # Polish month names to numbers
            months = {
                'stycznia': '01', 'lutego': '02', 'marca': '03', 'kwietnia': '04',
                'maja': '05', 'czerwca': '06', 'lipca': '07', 'sierpnia': '08',
                'września': '09', 'października': '10', 'listopada': '11', 'grudnia': '12'
            }
            
            month_num = months.get(month_pl, '01')
            try:
                # Return YYYY-MM-DD for easy sorting
                return f"{year}-{month_num}-{day.zfill(2)}"
            except:
                pass
        
        # If can't parse, return today's date (newest)
        return datetime.now().strftime('%Y-%m-%d')
    
    def process_new_listings(self):
        """Main method for processing new listings"""
        listings = self.fetch_listings()
        
        # Sort listings by date (newest first) for better organization
        if listings:
            logger.debug("Sorting listings by date...")
            for listing in listings:
                listing['_sort_date'] = self._extract_date_from_location(listing.get('location', ''))
            
            # Sort by date descending (newest first)
            listings.sort(key=lambda x: x.get('_sort_date', ''), reverse=True)
            logger.debug(f"Sorted {len(listings)} listings by date")
        
        new_count = 0
        new_listings = []
        
        # Collect new listings first
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
                
                # Collect new listing instead of sending immediately
                new_listings.append(listing)
                new_count += 1
        
        # Send in REVERSE order so newest appear at TOP in Slack
        if new_listings:
            logger.info(f"📤 Sending {len(new_listings)} new listings in reverse order (newest at top)...")
            for listing in reversed(new_listings):
                try:
                    self.send_to_slack(listing)
                    # Only save to database AFTER successful Slack send
                    self._save_listing(listing)
                    logger.debug(f"✅ Successfully sent and saved: {listing.get('id')}")
                except Exception as e:
                    logger.error(f"❌ Failed to send listing {listing.get('id')}: {e}")
                    # Don't save to database if Slack send failed
                    continue
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

