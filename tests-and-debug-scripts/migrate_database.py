#!/usr/bin/env python3
"""
Migrate old database to new structure with source column
"""

import sqlite3
import os

DB_FILE = 'listings.db'
BACKUP_FILE = 'listings_backup.db'

def migrate():
    """Migrate database to new structure"""
    
    if not os.path.exists(DB_FILE):
        print("✅ No database found - will be created with correct structure on first run")
        return
    
    print("🔄 Checking database structure...")
    
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Check if source column exists
        cursor.execute("PRAGMA table_info(seen_listings)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'source' in columns:
            print("✅ Database already has correct structure")
            conn.close()
            return
        
        print("⚠️  Old database structure detected")
        print("📦 Creating backup...")
        
        # Backup old database
        import shutil
        shutil.copy2(DB_FILE, BACKUP_FILE)
        print(f"✅ Backup created: {BACKUP_FILE}")
        
        # Get old data
        cursor.execute("SELECT id, title, price, location, url, first_seen, sent_to_slack FROM seen_listings")
        old_data = cursor.fetchall()
        print(f"📊 Found {len(old_data)} existing listings")
        
        conn.close()
        
        # Delete old database
        os.remove(DB_FILE)
        print("🗑️  Removed old database")
        
        # Create new database with correct structure
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE seen_listings (
                id TEXT PRIMARY KEY,
                source TEXT,
                title TEXT,
                price TEXT,
                location TEXT,
                url TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sent_to_slack INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('CREATE INDEX idx_listing_id ON seen_listings(id)')
        cursor.execute('CREATE INDEX idx_source ON seen_listings(source)')
        
        print("✅ Created new database structure")
        
        # Migrate old data (assume all are from OLX if ID format matches)
        migrated = 0
        for row in old_data:
            listing_id, title, price, location, url, first_seen, sent_to_slack = row
            
            # Determine source from ID format
            if listing_id.startswith('OTODOM_'):
                source = 'Otodom'
            else:
                source = 'OLX'
            
            cursor.execute('''
                INSERT INTO seen_listings (id, source, title, price, location, url, first_seen, sent_to_slack)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (listing_id, source, title, price, location, url, first_seen, sent_to_slack))
            migrated += 1
        
        conn.commit()
        conn.close()
        
        print(f"✅ Migrated {migrated} listings to new database")
        print(f"🎉 Migration completed successfully!")
        print(f"\n💾 Backup saved as: {BACKUP_FILE}")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        
        # Restore backup if it exists
        if os.path.exists(BACKUP_FILE) and not os.path.exists(DB_FILE):
            print("🔄 Restoring backup...")
            import shutil
            shutil.copy2(BACKUP_FILE, DB_FILE)
            print("✅ Backup restored")

if __name__ == '__main__':
    print("=" * 80)
    print("DATABASE MIGRATION TOOL")
    print("=" * 80)
    print()
    migrate()
    print()
    print("=" * 80)

