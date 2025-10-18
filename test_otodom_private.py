#!/usr/bin/env python3
"""
Тест фільтрації приватних оголошень на Otodom
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()

# Ensure private filter is enabled
os.environ['LISTING_TYPE'] = 'private'

from multi_parser import build_otodom_url
from otodom_parser import OtodomParser

def main():
    logger.info("="*80)
    logger.info("🧪 ТЕСТ: Фільтрація приватних оголошень на Otodom")
    logger.info("="*80)
    
    # Build URL
    search_url = build_otodom_url()
    
    # Get webhook from env
    webhook = os.getenv('SLACK_WEBHOOK_URL', '')
    
    # Create parser
    parser = OtodomParser(search_url, webhook)
    
    # Fetch listings
    logger.info("\n🔍 Починаємо пошук приватних оголошень...")
    listings = parser.fetch_listings()
    
    # Results
    logger.info("\n" + "="*80)
    logger.info("📊 РЕЗУЛЬТАТИ:")
    logger.info("="*80)
    logger.info(f"✅ Знайдено ПРИВАТНИХ оголошень: {len(listings)}")
    
    if listings:
        logger.info("\n📋 Список знайдених оголошень:")
        for i, listing in enumerate(listings, 1):
            logger.info(f"\n{i}. {listing.get('title', 'No title')}")
            logger.info(f"   💰 {listing.get('price', 'N/A')}")
            logger.info(f"   📍 {listing.get('location', 'N/A')}")
            logger.info(f"   🔗 {listing.get('url', 'N/A')}")
    else:
        logger.info("\n⚠️  Приватних оголошень не знайдено у вказаних районах")
    
    logger.info("\n" + "="*80)

if __name__ == "__main__":
    main()

