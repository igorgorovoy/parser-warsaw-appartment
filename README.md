# 🏠 OLX Parser for Warsaw Apartments

Automatic parser for apartment rental listings on OLX.pl with Slack notifications.

## 📋 Features

- ✅ Parse listings from OLX.pl based on your criteria
- ✅ Uniqueness check (doesn't send duplicate listings)
- ✅ Slack integration via Webhook
- ✅ Beautiful message formatting in Slack
- ✅ Two operation modes: single run or continuous monitoring
- ✅ Logging of all actions

## 🔧 Installation

### 1. Clone the repository or download files

```bash
cd parser-warsaw-appartment
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

or use virtualenv (recommended):

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Slack Webhook

1. Go to https://api.slack.com/messaging/webhooks
2. Create a new Incoming Webhook for your workspace
3. Choose a channel where messages will be sent
4. Copy the Webhook URL

### 4. Configure environment variables

Copy the `env.example` file to `.env`:

```bash
cp env.example .env
```

Edit `.env` and configure:

**Required:**
- `SLACK_WEBHOOK_URL` - your Slack Webhook URL

**Search parameters (all have default values):**
- `DISTRICT_ID` - district ID (359 = Śródmieście)
- `FLOORS` - floors comma-separated (1,2,3,4,5,6,7,8,9)
- `FURNITURE` - furnished (yes/no)
- `PETS` - pets allowed (Tak/Nie)
- `ROOMS` - number of rooms (one/two/three/four)
- `PRICE_FROM` - price from (PLN)
- `PRICE_TO` - price to (PLN)
- `LISTING_TYPE` - type (private/business)

**Example `.env` file:**

```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

DISTRICT_ID=359
FLOORS=1,2,3,4,5
FURNITURE=yes
PETS=Tak
ROOMS=three
PRICE_FROM=4000
PRICE_TO=6000
LISTING_TYPE=private

RUN_MODE=once
CHECK_INTERVAL=300
```

## 🚀 Usage

### Quick start (recommended)

Use the ready-made script:

```bash
./run.sh
```

The script automatically activates the virtual environment and runs the parser.

### Single run (manual)

Check listings once:

```bash
source venv/bin/activate
python3 parser.py
```

### Loop mode

Continuous checking every 5 minutes:

```bash
export RUN_MODE=loop
export CHECK_INTERVAL=300
python3 parser.py
```

Or set these parameters in the `.env` file.

## ⚙️ Search Parameters

By default, the parser searches for apartments with these parameters:

- **District**: Śródmieście (district 359)
- **Floors**: 1-9 (excluding ground floor)
- **Furnished**: Yes
- **Pets**: Allowed
- **Number of rooms**: 3
- **Price**: 4000-6000 PLN
- **Type**: Private listings only

### Configuring parameters

All parameters are configured in the `.env` file:

```bash
# District (ID can be found in the URL on OLX)
DISTRICT_ID=359

# Floors (comma-separated)
FLOORS=1,2,3,4,5,6,7,8,9

# Other parameters
FURNITURE=yes        # yes/no
PETS=Tak            # Tak/Nie
ROOMS=three         # one/two/three/four
PRICE_FROM=4000
PRICE_TO=6000
LISTING_TYPE=private  # private/business
```

The URL is automatically built from these parameters at runtime.

## 📁 Files

- `parser.py` - main parser script
- `requirements.txt` - Python dependencies
- `listings.db` - SQLite database storing seen listings (automatically created)
- `.env` - configuration file (create from `env.example`)
- `run.sh` - convenient launch script

## 🔍 How uniqueness check works

The parser uses an SQLite database (`listings.db`) to store all seen listings with their details (title, price, location, URL, timestamp). On each run, it checks if a listing ID already exists in the database before sending it to Slack.

**Benefits of database approach:**
- More reliable than JSON files
- Stores complete listing information
- Tracks when listings were first seen
- Prevents duplicate notifications

To reset the history and get all listings again, delete the database:

```bash
rm listings.db
```

To view statistics, use the included script:

```bash
python3 db_stats.py
```

Or query the database directly:

```bash
sqlite3 listings.db "SELECT COUNT(*) FROM seen_listings"
sqlite3 listings.db "SELECT * FROM seen_listings ORDER BY first_seen DESC LIMIT 5"
```

## 📝 Logging

The parser logs all actions with timestamps. Logging levels:

- `INFO` - normal operation (found listings, sent messages)
- `WARNING` - warnings (no listings found)
- `ERROR` - errors (network issues, parsing problems, etc.)

## 🔄 Automation

### Cron (Linux/Mac)

To run the parser every 30 minutes, add to crontab:

```bash
crontab -e
```

Add line:

```
*/30 * * * * cd /path/to/parser-warsaw-appartment && ./run.sh >> parser.log 2>&1
```

### Task Scheduler (Windows)

Create a new task in Task Scheduler that runs the script at the desired interval.

### Docker (optional)

You can create a Docker container for isolation:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY parser.py .
COPY .env .
CMD ["python", "parser.py"]
```

## 🐛 Troubleshooting

### "SLACK_WEBHOOK_URL not set"

Make sure you have set the environment variable or created the `.env` file.

### "No listings found on page"

OLX may have changed the HTML structure. You may need to update selectors in the `_parse_listing_card` function.

### Parser doesn't find new listings

1. Check if the search URL is correct
2. Delete `seen_listings.json` for testing
3. Make sure there are new listings on OLX matching your criteria

## ⚠️ Important Notes

- **Ethics**: Use the parser responsibly. Don't create excessive load on OLX servers.
- **Built-in Protection**: Parser automatically waits at least 60 seconds (1 minute) between requests to OLX to reduce server load.
- **OLX Rules**: Familiarize yourself with OLX Terms of Service before use.
- **Request Frequency**: Recommended interval is at least 5 minutes between checks.
- **User-Agent**: The parser uses a standard browser User-Agent.
- **Database**: All listings are stored in SQLite database for reliable duplicate prevention.

## 📧 Support

If you encounter issues:
1. Check the logs
2. Make sure all dependencies are installed
3. Verify that Slack Webhook is working

## 📄 License

This project is created for personal use. Use at your own discretion.

