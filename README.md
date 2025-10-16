# 🏠 Multi-site parser for searching the apartment in Warsaw

---

![The mechanical apartment hunter](dfeee9ba-1358-4b09-8df5-081f6d7c9c6b.png)


Automatic parser for apartment rental listings on **OLX.pl** and **Otodom.pl** with Slack notifications.

## 📋 Table of Contents

- [🏠 Multi-site parser for searching the apartment in Warsaw](#-multi-site-parser-for-searching-the-apartment-in-warsaw)
  - [📋 Table of Contents](#-table-of-contents)
  - [Features](#features)
  - [⚠️ Important: Parser differences](#️-important-parser-differences)
    - [OLX parser](#olx-parser)
    - [Otodom parser](#otodom-parser)
  - [Installation](#installation)
    - [1. Clone the repository or download files](#1-clone-the-repository-or-download-files)
    - [2. Install dependencies](#2-install-dependencies)
    - [3. Configure slack webhook](#3-configure-slack-webhook)
    - [4. Configure environment variables](#4-configure-environment-variables)
  - [Usage](#usage)
    - [Quick start (recommended)](#quick-start-recommended)
    - [Single run (manual)](#single-run-manual)
    - [Loop mode](#loop-mode)
  - [Search Parameters](#search-parameters)
    - [Configuring parameters](#configuring-parameters)
  - [Files](#files)
  - [🔍 How uniqueness check works](#-how-uniqueness-check-works)
  - [Logging](#logging)
  - [Automation](#automation)
    - [Cron (Linux/Mac)](#cron-linuxmac)
    - [Task Scheduler (Windows)](#task-scheduler-windows)
    - [Docker (optional)](#docker-optional)
  - [🐛 Troubleshooting](#-troubleshooting)
    - ["SLACK\_WEBHOOK\_URL not set"](#slack_webhook_url-not-set)
    - ["No listings found on page"](#no-listings-found-on-page)
    - [Parser doesn't find new listings](#parser-doesnt-find-new-listings)
    - [Parser shows "No title" or missing data](#parser-shows-no-title-or-missing-data)
  - [⚠️ Important Notes](#️-important-notes)
  - [📧 Support](#-support)
  - [Architecture](#architecture)
    - [High-Level Architecture](#high-level-architecture)
    - [Agent Workflow](#agent-workflow)
    - [Parser Components](#parser-components)
      - [1. **BaseParser** (Abstract Base Class)](#1-baseparser-abstract-base-class)
      - [2. **OLXParser** (OLX Implementation)](#2-olxparser-olx-implementation)
      - [3. **OtodomParser** (Otodom Implementation)](#3-otodomparser-otodom-implementation)
      - [4. **MultiParser** (Orchestrator)](#4-multiparser-orchestrator)
    - [Database Schema](#database-schema)
    - [Slack Message Format](#slack-message-format)
    - [Data Flow](#data-flow)
  - [License](#license)


## Features

- ✅ **Multi-site support**: Parse both OLX.pl and Otodom.pl simultaneously
- ✅ **Uniqueness check**: Doesn't send duplicate listings
- ✅ **Slack integration**: Real-time notifications via Webhook
- ✅ **Beautiful formatting**: Well-structured messages in Slack with source tags and photos
- ✅ **Photo display**: First image from each listing shown in Slack messages
- ✅ **Flexible configuration**: Enable/disable individual parsers
- ✅ **Two operation modes**: Single run or continuous monitoring
- ✅ **Rate limiting**: Built-in delays to reduce server load
- ✅ **SQLite database**: Reliable storage with per-source tracking
- ✅ **Detailed logging**: Full history of all actions

## ⚠️ Important: Parser differences

### OLX parser
✅ **Full filtering support**:
- District ✅
- Number of rooms ✅
- Price range ✅
- Furniture ✅
- Pets allowed ✅
- Private listings only ✅
- Floors ❌ (not supported by OLX API)

### Otodom parser
⚠️ **Limited URL filtering**:
- District ✅
- Number of rooms ✅
- Price range ✅
- Area (m²) ✅
- Furniture ❌ (URL filter not available)
- Pets allowed ❌ (URL filter not available)
- Private listings only ⚠️ (filtered client-side by checking "prywatne" text)

**Result**: Otodom will send MORE listings than OLX because URL filters for furniture and pets are not available. Private listings are filtered client-side (by checking for "prywatne" text in listing), which means ALL listings are downloaded but only private ones are processed. By default, Otodom is **disabled**. Enable it in `.env` if you want more results.

##  Installation

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

### 3. Configure slack webhook

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
- `DISTRICT_NAME` - district name (lowercase, e.g., wola, srodmiescie, mokotow)
- `FLOORS` - floors comma-separated (1,2,3,4,5,6,7,8,9) - ⚠️ NOT supported by OLX API
- `FURNITURE` - furnished (yes/no)
- `PETS` - pets allowed (Tak/Nie)
- `ROOMS` - number of rooms (one/two/three/four)
- `PRICE_FROM` - price from (PLN)
- `PRICE_TO` - price to (PLN)
- `LISTING_TYPE` - type (private/business)

**Example `.env` file:**

```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

DISTRICT_NAME=wola
FURNITURE=yes
PETS=Tak
ROOMS=three
PRICE_FROM=4000
PRICE_TO=6000
LISTING_TYPE=private

RUN_MODE=once
CHECK_INTERVAL=300
```

##  Usage

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

##  Search Parameters

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
# District (lowercase name, found in OLX URL: /warszawa/q-DISTRICT_NAME/)
DISTRICT_NAME=wola

# Common districts: wola, srodmiescie, mokotow, praga-polnoc, praga-poludnie, bielany

# Other parameters
FURNITURE=yes        # yes/no
PETS=Tak            # Tak/Nie
ROOMS=three         # one/two/three/four
PRICE_FROM=4000
PRICE_TO=6000
LISTING_TYPE=private  # private/business
```

The URL is automatically built from these parameters at runtime.

##  Files

- `multi_parser.py` - main script that runs all parsers
- `olx_parser.py` - OLX.pl parser
- `otodom_parser.py` - Otodom.pl parser
- `base_parser.py` - base class with shared functionality
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
rm listings.db seen_listings.json
```

**Note:** If you upgraded from an older version and get database errors, delete the old database to create a new one with the correct structure.

To view statistics, use the included script:

```bash
python3 db_stats.py
```

Or query the database directly:

```bash
sqlite3 listings.db "SELECT COUNT(*) FROM seen_listings"
sqlite3 listings.db "SELECT * FROM seen_listings ORDER BY first_seen DESC LIMIT 5"
```

##  Logging

The parser logs all actions with timestamps. Logging levels:

- `INFO` - normal operation (found listings, sent messages)
- `WARNING` - warnings (no listings found)
- `ERROR` - errors (network issues, parsing problems, etc.)

##  Automation

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
2. Delete `listings.db` for testing
3. Make sure there are new listings on OLX matching your criteria

### Parser shows "No title" or missing data

OLX may have changed their HTML structure. Run the test script to check selectors:

```bash
venv/bin/python3 test_parser.py
```

This will show which selectors work and save HTML samples for debugging.

### "403 Forbidden" error on Otodom (especially from servers)

**Problem:** Otodom blocks requests from servers or non-Polish IP addresses.

**Symptoms:**
```
ERROR - Error requesting Otodom: 403 Client Error: Forbidden
```

**Solutions:**

1. **Test your connection first:**
   ```bash
   python3 test_proxy.py
   ```
   This will check if your IP is blocked and test proxy connections.

2. **Use a proxy server (recommended for servers):**
   - Add to `.env` file:
     ```bash
     PROXY_URL=http://your-proxy:port
     # or with authentication:
     PROXY_URL=http://username:password@proxy-server:port
     ```
   - The parser will automatically use it for Otodom requests.

3. **Where to get a proxy:**
   - **Free (for testing):** [free-proxy-list.net](https://free-proxy-list.net/) - filter by Poland
   - **Paid (reliable):** Webshare.io (from $2.99/month), Smartproxy, Bright Data

4. **Alternative: Use VPN with Polish IP** on your server

**Note:** Works locally but not on server? This is normal - Otodom often blocks datacenter IPs.

📚 **Detailed guide:** See [SERVER_SETUP.md](SERVER_SETUP.md) for complete troubleshooting.

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

##  Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    WARSAW APARTMENT PARSER                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                   │
│  │   multi_parser  │    │   base_parser   │                   │
│  │   (Orchestrator)│────│   (Base Class)  │                   │
│  └─────────────────┘    └─────────────────┘                   │
│           │                       ▲                            │
│           │                       │                            │
│  ┌────────▼────────┐    ┌────────▼────────┐                   │
│  │   olx_parser    │    │  otodom_parser  │                   │
│  │   (OLX.pl)      │    │  (Otodom.pl)    │                   │
│  └─────────────────┘    └─────────────────┘                   │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                        DATA LAYER                              │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                   │
│  │   SQLite DB     │    │   Slack API     │                   │
│  │  (Uniqueness)   │    │  (Notifications)│                   │
│  └─────────────────┘    └─────────────────┘                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Agent Workflow

```mermaid
graph TD
    A[🚀 Start multi_parser.py] --> B[📖 Load .env configuration]
    B --> C{🔍 Check enabled parsers}
    
    C -->|OLX enabled| D[🏠 Initialize OLX Parser]
    C -->|Otodom enabled| E[🏢 Initialize Otodom Parser]
    
    D --> F[🌐 Fetch OLX listings]
    E --> G[🌐 Fetch Otodom listings]
    
    F --> H[🔍 Filter by district]
    G --> I[🔍 Filter by district & private]
    
    H --> J[📸 Extract photos]
    I --> K[📸 Extract photos]
    
    J --> L[💾 Check uniqueness in DB]
    K --> L
    
    L -->|New listing| M[📤 Send to Slack]
    L -->|Already seen| N[⏭️ Skip]
    
    M --> O[💾 Save to database]
    N --> P{🔄 Loop mode?}
    O --> P
    
    P -->|Yes| Q[⏰ Wait 1 minute]
    P -->|No| R[✅ Finish]
    Q --> C
    
    style A fill:#e1f5fe
    style M fill:#c8e6c9
    style R fill:#ffcdd2
```

###  Parser Components

#### 1. **BaseParser** (Abstract Base Class)
**Location:** `base_parser.py`

**Responsibilities:**
- Database initialization and management
- Slack webhook integration
- Rate limiting (1 minute intervals)
- Photo extraction from detail pages
- Uniqueness checking
- Common utility methods

**Key Methods:**
```python
- _init_database()           # SQLite schema setup
- _save_listing()           # Store listing with uniqueness check
- send_to_slack()           # Send formatted message to Slack
- _fetch_photo_from_detail_page()  # Extract first image
- _extract_date_from_location()    # Parse dates from location strings
```

#### 2. **OLXParser** (OLX Implementation)
**Location:** `olx_parser.py`

**Features:**
- ✅ URL-based filtering (district, price, rooms, furniture, pets)
- ✅ Client-side district filtering for accuracy
- ✅ Handles lazy-loaded images
- ✅ Extracts dates from location strings
- ✅ Filters out "extended search" results

**Search URL Structure:**
```
https://www.olx.pl/nieruchomosci/mieszkania/wynajem/warszawa/q-wola/
?search[filter_float_price:from]=4000
&search[filter_float_price:to]=8000
&search[filter_enum_rooms][0]=three
&search[filter_enum_furnished][0]=yes
&search[filter_enum_pets][0]=yes
&search[private_business]=private
```

#### 3. **OtodomParser** (Otodom Implementation)
**Location:** `otodom_parser.py`

**Features:**
- ✅ JSON-based data extraction from `__NEXT_DATA__`
- ✅ Client-side filtering (district, private listings)
- ✅ Multi-page support (3 pages = 108 listings)
- ✅ Date extraction from JSON timestamps
- ✅ Fallback selectors for HTML parsing

**Search URL Structure:**
```
https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie/mazowieckie/warszawa
?priceMin=4000
&priceMax=8000
&roomsNumber=%5B3%5D
&areaMin=60
&areaMax=90
&page=1
```

#### 4. **MultiParser** (Orchestrator)
**Location:** `multi_parser.py`

**Responsibilities:**
- Configuration management from `.env`
- Parser initialization and coordination
- URL building for each platform
- Search criteria logging
- Main execution loop

###  Database Schema

```sql
CREATE TABLE seen_listings (
    id TEXT PRIMARY KEY,
    title TEXT,
    price TEXT,
    location TEXT,
    url TEXT,
    source TEXT,           -- 'OLX' or 'Otodom'
    image_url TEXT,        -- First photo URL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

###  Slack Message Format

```json
{
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "🏠 New Listing [Source]: Title"
      }
    },
    {
      "type": "section",
      "fields": [
        {"type": "mrkdwn", "text": "*Price:* 5000 zł"},
        {"type": "mrkdwn", "text": "*Location:* Wola, Warszawa - 15 października 2025"},
        {"type": "mrkdwn", "text": "*Link:* <URL|View Listing>"}
      ]
    },
    {
      "type": "image",
      "image_url": "https://...",
      "alt_text": "Listing photo"
    }
  ]
}
```

###  Data Flow

1. **Configuration** → Load from `.env`
2. **URL Building** → Platform-specific search URLs
3. **Data Fetching** → HTTP requests with rate limiting
4. **Parsing** → HTML/JSON extraction
5. **Filtering** → Client-side criteria matching
6. **Uniqueness Check** → SQLite database lookup
7. **Photo Extraction** → Additional HTTP request if needed
8. **Slack Notification** → Formatted message delivery
9. **Storage** → Save to database for future uniqueness checks

##  License

This project is created for personal use. Use at your own discretion.

