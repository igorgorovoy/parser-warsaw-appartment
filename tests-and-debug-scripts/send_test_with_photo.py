#!/usr/bin/env python3
"""Send a test message to Slack with photo to verify new format"""

import os
from dotenv import load_dotenv
import requests

load_dotenv()

SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')

if not SLACK_WEBHOOK_URL:
    print("❌ SLACK_WEBHOOK_URL not set!")
    exit(1)

# Test message with photo
test_listing = {
    'source': 'OLX',
    'title': 'Test Listing: Spacious 3-room apartment with balcony',
    'price': '4500 zł',
    'location': 'Śródmieście, Warszawa',
    'url': 'https://www.olx.pl/d/oferta/test-listing-ID123abc',
    'id': 'TEST_123',
    'image_url': 'https://ireland.apollo.olxcdn.com/v1/files/8ojpkzdkdj2u2-PL/image;s=644x461'
}

# Build Slack message with photo
blocks = [
    {
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": f"🏠 New listing [{test_listing['source']}]: {test_listing['title']}"
        }
    }
]

# Add image
if test_listing.get('image_url'):
    blocks.append({
        "type": "image",
        "image_url": test_listing['image_url'],
        "alt_text": test_listing['title']
    })

# Add listing details
blocks.extend([
    {
        "type": "section",
        "fields": [
            {
                "type": "mrkdwn",
                "text": f"*Price:*\n{test_listing['price']}"
            },
            {
                "type": "mrkdwn",
                "text": f"*Location:*\n{test_listing['location']}"
            }
        ]
    },
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"<{test_listing['url']}|View listing>"
        }
    },
    {
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"Source: *{test_listing['source']}* | ID: `{test_listing['id']}`"
            }
        ]
    },
    {
        "type": "divider"
    }
])

message = {"blocks": blocks}

print("📤 Sending test message to Slack...")
print(f"   Title: {test_listing['title']}")
print(f"   Photo: {test_listing['image_url'][:60]}...")

try:
    response = requests.post(
        SLACK_WEBHOOK_URL,
        json=message,
        headers={'Content-Type': 'application/json'}
    )
    response.raise_for_status()
    print("\n✅ Test message sent successfully!")
    print("Check your Slack channel to see the message with photo.")
except Exception as e:
    print(f"\n❌ Error: {e}")

