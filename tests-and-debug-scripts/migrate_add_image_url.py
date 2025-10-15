#!/usr/bin/env python3
"""
Add image_url column to existing database
"""

import sqlite3
import os

DB_FILE = 'listings.db'

def migrate():
    """Add image_url column to database"""
    
    if not os.path.exists(DB_FILE):
        print("✅ No database found - will be created with correct structure on first run")
        return
    
    print("🔄 Checking database structure...")
    
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Check if image_url column exists
        cursor.execute("PRAGMA table_info(seen_listings)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'image_url' in columns:
            print("✅ Database already has image_url column")
            conn.close()
            return
        
        print("⚠️  Adding image_url column...")
        
        # Add image_url column
        cursor.execute("ALTER TABLE seen_listings ADD COLUMN image_url TEXT")
        
        conn.commit()
        conn.close()
        
        print("✅ Added image_url column successfully!")
        print("🎉 Migration completed! Photos will now be stored.")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("=" * 80)
    print("DATABASE MIGRATION: ADD IMAGE_URL COLUMN")
    print("=" * 80)
    print()
    migrate()
    print()
    print("=" * 80)

