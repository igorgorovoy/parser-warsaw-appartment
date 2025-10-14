#!/usr/bin/env python3
"""
Multi-site parser - runs OLX and Otodom parsers
"""

import os
import time
from datetime import datetime
import logging
from dotenv import load_dotenv
from olx_parser import OLXParser, build_search_url as build_olx_url
from otodom_parser import OtodomParser

# Load variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def build_otodom_url() -> str:
    """Build Otodom search URL from configuration parameters"""
    # Otodom uses different URL structure
    base_url = "https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie/mazowieckie/warszawa/warszawa/warszawa"
    
    params = []
    
    # District (dzielnica)
    district = os.getenv('OTODOM_DISTRICT', 'srodmiescie')
    if district:
        base_url += f"/{district}"
    
    # Price range
    price_from = os.getenv('PRICE_FROM', '4000')
    price_to = os.getenv('PRICE_TO', '6000')
    if price_from:
        params.append(f"priceMin={price_from}")
    if price_to:
        params.append(f"priceMax={price_to}")
    
    # Area (powierzchnia)
    area_from = os.getenv('AREA_FROM', '60')
    area_to = os.getenv('AREA_TO', '90')
    if area_from:
        params.append(f"areaMin={area_from}")
    if area_to:
        params.append(f"areaMax={area_to}")
    
    # Number of rooms
    rooms = os.getenv('ROOMS', 'three')
    rooms_map = {'one': '1', 'two': '2', 'three': '3', 'four': '4'}
    if rooms in rooms_map:
        params.append(f"roomsNumber=%5B{rooms_map[rooms]}%5D")
    
    # Build URL
    if params:
        search_url = base_url + '?' + '&'.join(params)
    else:
        search_url = base_url
    
    logger.info(f"🔗 Built Otodom URL")
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
    
    # Check which parsers to enable
    enable_olx = os.getenv('ENABLE_OLX', 'true').lower() == 'true'
    enable_otodom = os.getenv('ENABLE_OTODOM', 'true').lower() == 'true'
    
    parsers = []
    
    # Initialize OLX parser
    if enable_olx:
        olx_url = build_olx_url()
        olx_parser = OLXParser(olx_url, SLACK_WEBHOOK_URL)
        parsers.append(('OLX', olx_parser))
        logger.info("✅ OLX parser enabled")
    
    # Initialize Otodom parser
    if enable_otodom:
        otodom_url = build_otodom_url()
        otodom_parser = OtodomParser(otodom_url, SLACK_WEBHOOK_URL)
        parsers.append(('Otodom', otodom_parser))
        logger.info("✅ Otodom parser enabled")
    
    if not parsers:
        logger.error("No parsers enabled! Enable at least one in .env file")
        return
    
    # Operation mode: single run or loop
    run_mode = os.getenv('RUN_MODE', 'once')  # 'once' or 'loop'
    
    if run_mode == 'loop':
        check_interval = int(os.getenv('CHECK_INTERVAL', '300'))  # Default 5 minutes
        logger.info("=" * 80)
        logger.info(f"🔄 Running in LOOP mode")
        logger.info(f"   Active parsers:  {', '.join([name for name, _ in parsers])}")
        logger.info(f"   Check interval:  {check_interval} seconds ({check_interval//60} minutes)")
        logger.info(f"   Request delay:   60 seconds (1 minute) per parser")
        logger.info(f"   Press Ctrl+C to stop")
        logger.info("=" * 80)
        
        try:
            iteration = 0
            while True:
                iteration += 1
                logger.info(f"\n{'='*80}")
                logger.info(f"🔍 ITERATION #{iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info("=" * 80)
                
                # Run each parser
                for name, parser in parsers:
                    logger.info(f"\n▶️  Processing {name}...")
                    parser.process_new_listings()
                    parser.get_statistics()
                
                # Show combined statistics
                show_combined_statistics(parsers)
                
                logger.info(f"\n⏸️  Waiting {check_interval} seconds until next check...")
                time.sleep(check_interval)
        except KeyboardInterrupt:
            logger.info("\n" + "=" * 80)
            logger.info("🛑 Stopping parser...")
            logger.info("=" * 80)
            show_combined_statistics(parsers)
    else:
        logger.info("=" * 80)
        logger.info(f"▶️  Running in SINGLE CHECK mode")
        logger.info(f"   Active parsers: {', '.join([name for name, _ in parsers])}")
        logger.info(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)
        
        for name, parser in parsers:
            logger.info(f"\n▶️  Processing {name}...")
            parser.process_new_listings()
            parser.get_statistics()
        
        show_combined_statistics(parsers)


def show_combined_statistics(parsers):
    """Show combined statistics from all parsers"""
    import sqlite3
    
    try:
        conn = sqlite3.connect('listings.db')
        cursor = conn.cursor()
        
        logger.info("\n" + "=" * 80)
        logger.info("📊 COMBINED STATISTICS (ALL SOURCES)")
        logger.info("=" * 80)
        
        # Total across all sources
        cursor.execute('SELECT COUNT(*) FROM seen_listings')
        total_all = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM seen_listings WHERE sent_to_slack = 1')
        sent_all = cursor.fetchone()[0]
        
        logger.info(f"   Total listings (all sources): {total_all}")
        logger.info(f"   Sent to Slack (all sources):  {sent_all}")
        
        # Per source breakdown
        logger.info("\n   Breakdown by source:")
        for name, _ in parsers:
            cursor.execute('SELECT COUNT(*) FROM seen_listings WHERE source = ?', (name,))
            source_total = cursor.fetchone()[0]
            logger.info(f"     - {name}: {source_total} listings")
        
        conn.close()
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Error getting combined statistics: {e}")


if __name__ == '__main__':
    main()

