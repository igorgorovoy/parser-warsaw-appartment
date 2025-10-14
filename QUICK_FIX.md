# 🔧 Quick Fix Guide

## Problem: Otodom shows "No title", "Not specified"

### ✅ Solution:
Old Otodom entries in database don't have proper data. Clean and re-parse:

```bash
# Step 1: Clean old Otodom entries
venv/bin/python3 clean_otodom.py

# Step 2: Run parser again
./run.sh
```

**What happens:**
- Old Otodom entries (36) removed from database
- Parser will re-fetch them with correct title, price, location
- New Slack messages will have full information

---

## Problem: Database errors "no such column: source"

### ✅ Solution:
Migrate old database structure:

```bash
# Option 1: Migrate (keeps existing data)
venv/bin/python3 migrate_database.py

# Option 2: Start fresh (loses history)
rm listings.db seen_listings.json
```

---

## Verification

### Test OLX parser:
```bash
venv/bin/python3 test_parser.py
```

### Test Otodom parser:
```bash
venv/bin/python3 test_otodom_parser.py
```

Should show titles like:
```
1. ID: OTODOM_ID4yAgO
   Title: Nowoczesne Mieszkanie Centrum Wysoki Standard
   Price: 4900 zł
   Location: Śródmieście, Warszawa
```

---

## After Fix

Run parser and check Slack - should see:
```
🏠 New listing [Otodom]: Nowoczesne Mieszkanie Centrum Wysoki Standard
Price: 4900 zł
Location: Śródmieście, Warszawa
```

✅ All working!

