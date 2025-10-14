# 🎉 Multi-Site Parser - Ready to Use!

## ✅ What's Been Created

### **Dual-Site Apartment Parser**
- 🟦 **OLX.pl** parser - finds apartments on OLX (full filtering)
- 🟩 **Otodom.pl** parser - finds apartments on Otodom (limited filtering)
- Both can run simultaneously and send results to same Slack channel

### ⚠️ **Important Limitation**
Otodom API does NOT support filtering by:
- Furniture (furnished/unfurnished)
- Pets allowed
- Listing type (private/agency)

**This means Otodom will show MORE results** than OLX for same search criteria.
**Recommendation**: Use OLX for precise filtering, enable Otodom only if you want additional results.

### **Key Features**
- ✅ Works with both sites at once
- ✅ Each listing tagged with source ([OLX] or [Otodom])
- ✅ No duplicates - SQLite database tracks all seen listings
- ✅ Rate limiting - 60 seconds between requests per site
- ✅ Detailed logging - full history of all actions
- ✅ Flexible configuration - enable/disable each parser

## 📝 Configuration

Edit `.env` file:

```bash
# Required
SLACK_WEBHOOK_URL=your_webhook_url_here

# Enable/disable parsers
ENABLE_OLX=true
ENABLE_OTODOM=true

# Search parameters (shared)
PRICE_FROM=4000
PRICE_TO=6000
ROOMS=three

# OLX specific
DISTRICT_ID=359
FLOORS=1,2,3,4,5,6,7,8,9
FURNITURE=yes
PETS=Tak
LISTING_TYPE=private

# Otodom specific
OTODOM_DISTRICT=srodmiescie
AREA_FROM=60
AREA_TO=90

# Operation mode
RUN_MODE=once    # or 'loop' for continuous monitoring
CHECK_INTERVAL=300  # seconds (5 minutes)
```

## 🚀 How to Run

### Quick Start
```bash
./run.sh
```

### Manual Run
```bash
venv/bin/python3 multi_parser.py
```

### Run Only OLX
Set in `.env`: `ENABLE_OTODOM=false`

### Run Only Otodom  
Set in `.env`: `ENABLE_OLX=false`

### Continuous Monitoring
Set in `.env`: `RUN_MODE=loop`

## 📊 What You'll Get in Slack

```
🏠 New listing [OLX]: Mieszkanie 3-pokojowe Śródmieście
Price: 4 500 zł
Location: Warszawa, Śródmieście
[View listing button]
Source: OLX | ID: ID123456
─────────────────────

🏠 New listing [Otodom]: Nowoczesne Mieszkanie Centrum
Price: 4900 zł  
Location: Śródmieście, Warszawa
[View listing button]
Source: Otodom | ID: OTODOM_ID4yAgO
```

## 📁 Project Structure

```
parser-warsaw-appartment/
├── multi_parser.py      # Main script (runs both parsers)
├── olx_parser.py        # OLX.pl parser
├── otodom_parser.py     # Otodom.pl parser  
├── base_parser.py       # Shared functionality
├── listings.db          # SQLite database
├── .env                 # Your configuration
├── run.sh              # Quick launch script
└── test_*.py           # Testing tools
```

## 🔧 Utilities

### View Statistics
```bash
venv/bin/python3 db_stats.py
```

### Test OLX Selectors
```bash
venv/bin/python3 test_parser.py
```

### Test Otodom Parser
```bash
venv/bin/python3 test_otodom_parser.py
```

### Send Test Message
```bash
venv/bin/python3 send_test_message.py
```

## 🎯 Next Steps

1. ✅ Configure `.env` with your Slack webhook
2. ✅ Adjust search parameters to your needs
3. ✅ Run `./run.sh` to start
4. ✅ Check your Slack channel for listings
5. ✅ Optionally set `RUN_MODE=loop` for automation

## 💡 Tips

- **First run**: Will find many listings (all existing ones)
- **Subsequent runs**: Only new listings since last run
- **Reset history**: `rm listings.db` to start fresh
- **Rate limits**: Parser waits 60s between site requests
- **Cron job**: Add to crontab for automatic checks
- **Statistics**: Shows breakdown by source (OLX vs Otodom)

## 🐛 Troubleshooting

### Database errors after upgrade:
```bash
venv/bin/python3 migrate_database.py  # Migrate old database
# OR
rm listings.db seen_listings.json     # Start fresh
```

### Otodom shows "No title":
Old Otodom entries in database need to be re-parsed:
```bash
venv/bin/python3 clean_otodom.py      # Remove old Otodom entries
```

### Check if selectors still work:
```bash
venv/bin/python3 test_parser.py           # for OLX
venv/bin/python3 test_otodom_parser.py    # for Otodom
```

---

**Everything is ready to use! Just configure `.env` and run `./run.sh`** 🚀

