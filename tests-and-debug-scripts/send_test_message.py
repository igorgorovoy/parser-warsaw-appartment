#!/usr/bin/env python3
"""
Send test message to Slack to verify integration
"""

import os
import requests
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

def send_test_message():
    """Send a test listing message to Slack"""
    
    slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    
    if not slack_webhook_url:
        print("❌ SLACK_WEBHOOK_URL not found in .env file!")
        print("Please add your Slack Webhook URL to the .env file.")
        return False
    
    # Check if it's the example URL
    if 'YOUR/WEBHOOK/URL' in slack_webhook_url:
        print("❌ Please replace the example Slack Webhook URL in .env file with your actual webhook URL")
        print("Get it from: https://api.slack.com/messaging/webhooks")
        return False
    
    # Test listing data
    test_listing = {
        'title': '🧪 TEST: Mieszkanie 3-pokojowe Śródmieście, 65m², umeblowane',
        'price': '4 500 zł',
        'location': f'Warszawa, Śródmieście - Test {datetime.now().strftime("%H:%M")}',
        'url': 'https://www.olx.pl/d/oferta/test-message-ID999999.html',
        'id': 'TEST999999'
    }
    
    # Build Slack message
    message = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🏠 New listing: {test_listing.get('title', 'No title')}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Price:*\n{test_listing.get('price', 'Not specified')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Location:*\n{test_listing.get('location', 'Not specified')}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"<{test_listing.get('url', '#')}|View listing>"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "✅ *This is a test message from OLX Parser* - Integration is working correctly!"
                    }
                ]
            },
            {
                "type": "divider"
            }
        ]
    }
    
    print("=" * 80)
    print("📤 SENDING TEST MESSAGE TO SLACK")
    print("=" * 80)
    print(f"Webhook URL: {slack_webhook_url[:50]}...")
    print(f"Message: {test_listing['title']}")
    print()
    
    try:
        response = requests.post(
            slack_webhook_url,
            json=message,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        response.raise_for_status()
        
        print("✅ SUCCESS!")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        print()
        print("=" * 80)
        print("🎉 Test message sent successfully!")
        print("📱 Check your Slack channel to see the message")
        print("=" * 80)
        return True
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        print(f"Response: {e.response.text if e.response else 'No response'}")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Could not connect to Slack")
        print("Check your internet connection")
        return False
    except requests.exceptions.Timeout:
        print("❌ Timeout Error: Request took too long")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False


if __name__ == '__main__':
    send_test_message()

