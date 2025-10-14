#!/usr/bin/env python3
"""
Test Otodom parser with actual parsing logic
"""

import os
from dotenv import load_dotenv
from otodom_parser import OtodomParser
from multi_parser import build_otodom_url

load_dotenv()

def test():
    slack_url = os.getenv('SLACK_WEBHOOK_URL')
    if not slack_url:
        slack_url = 'https://hooks.slack.com/services/TEST'
    
    url = build_otodom_url()
    parser = OtodomParser(url, slack_url)
    
    print("=" * 80)
    print("Testing Otodom Parser")
    print("=" * 80)
    
    listings = parser.fetch_listings()
    
    print(f"\n✅ Found {len(listings)} listings")
    print("\nFirst 5 listings:")
    print("-" * 80)
    
    for i, listing in enumerate(listings[:5], 1):
        print(f"\n{i}. ID: {listing.get('id', 'N/A')}")
        print(f"   Title: {listing.get('title', 'N/A')}")
        print(f"   Price: {listing.get('price', 'N/A')}")
        print(f"   Location: {listing.get('location', 'N/A')}")
        print(f"   URL: {listing.get('url', 'N/A')[:80]}...")

if __name__ == '__main__':
    test()

