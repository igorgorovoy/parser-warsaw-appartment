#!/usr/bin/env python3
"""
Database statistics viewer for OLX Parser
Shows information about stored listings
"""

import sqlite3
import sys
from datetime import datetime

DB_FILE = 'listings.db'


def get_statistics():
    """Get and display database statistics"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Total listings
        cursor.execute('SELECT COUNT(*) FROM seen_listings')
        total = cursor.fetchone()[0]
        
        # Sent to Slack
        cursor.execute('SELECT COUNT(*) FROM seen_listings WHERE sent_to_slack = 1')
        sent = cursor.fetchone()[0]
        
        # First and last seen
        cursor.execute('SELECT MIN(first_seen), MAX(first_seen) FROM seen_listings')
        first, last = cursor.fetchone()
        
        print("=" * 60)
        print("📊 OLX Parser Database Statistics")
        print("=" * 60)
        print(f"Total listings stored:    {total}")
        print(f"Sent to Slack:            {sent}")
        print(f"First listing seen:       {first}")
        print(f"Last listing seen:        {last}")
        print("=" * 60)
        
        # Recent listings
        cursor.execute('''
            SELECT title, price, location, first_seen 
            FROM seen_listings 
            ORDER BY first_seen DESC 
            LIMIT 10
        ''')
        
        recent = cursor.fetchall()
        if recent:
            print("\n📋 Last 10 listings:")
            print("-" * 60)
            for idx, (title, price, location, seen) in enumerate(recent, 1):
                print(f"{idx}. {title[:40]}")
                print(f"   Price: {price} | Location: {location}")
                print(f"   Seen: {seen}")
                print()
        
        conn.close()
        
    except sqlite3.OperationalError:
        print("❌ Database file not found or not accessible.")
        print(f"Make sure '{DB_FILE}' exists in the current directory.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    get_statistics()

