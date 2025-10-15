#!/usr/bin/env python3
"""Test Otodom parser with real request"""

import os
from dotenv import load_dotenv
from otodom_parser import OtodomParser, build_otodom_url

load_dotenv()

print("="*80)
print("TESTING OTODOM PARSER")
print("="*80)

# Build URL
search_url = build_otodom_url()
slack_webhook = os.getenv('SLACK_WEBHOOK_URL')

print(f"\nSearch URL: {search_url}\n")

# Create parser
parser = OtodomParser(search_url, slack_webhook)

# Fetch listings
print("Fetching listings...")
listings = parser.fetch_listings()

print(f"\n{'='*80}")
print(f"RESULTS: Found {len(listings)} listings")
print('='*80)

if listings:
    print("\nFirst 5 listings:")
    for i, listing in enumerate(listings[:5], 1):
        print(f"\n{i}. {listing.get('title', 'No title')[:60]}")
        print(f"   Price: {listing.get('price', 'N/A')}")
        print(f"   Location: {listing.get('location', 'N/A')[:50]}")
        print(f"   URL: {listing.get('url', '')[:80]}...")
else:
    print("\n⚠️  No listings found!")
    print("\nPossible reasons:")
    print("1. Otodom changed their HTML structure")
    print("2. The URL parameters are incorrect")
    print("3. There are no matching listings")
    print("\nCheck debug_otodom_page.html if it was created")

