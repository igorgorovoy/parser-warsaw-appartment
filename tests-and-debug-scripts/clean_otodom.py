#!/usr/bin/env python3
"""
Clean Otodom listings from database to re-parse them with correct data
"""

import sqlite3
import os

DB_FILE = 'listings.db'

def clean_otodom():
    """Remove all Otodom listings from database"""
    
    if not os.path.exists(DB_FILE):
        print("✅ No database found")
        return
    
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Count Otodom listings
        cursor.execute("SELECT COUNT(*) FROM seen_listings WHERE source = 'Otodom' OR id LIKE 'OTODOM_%'")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("✅ No Otodom listings in database")
            conn.close()
            return
        
        print(f"📊 Found {count} Otodom listings in database")
        print("🗑️  Removing Otodom listings...")
        
        # Delete Otodom listings
        cursor.execute("DELETE FROM seen_listings WHERE source = 'Otodom' OR id LIKE 'OTODOM_%'")
        deleted = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        print(f"✅ Removed {deleted} Otodom listings")
        print("🎉 Database cleaned! Otodom listings will be re-parsed on next run.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("=" * 80)
    print("CLEAN OTODOM LISTINGS")
    print("=" * 80)
    print()
    clean_otodom()
    print()
    print("=" * 80)

