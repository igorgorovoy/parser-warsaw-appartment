# 🗺️ Multi-District Search Guide

## Overview

The parser now supports searching in **multiple districts simultaneously**. This is useful when you want to find apartments within walking/commuting distance of specific locations (work, metro stations, etc.).

## Configuration

### For OLX

In your `.env` file, set `DISTRICT_NAME` with comma-separated districts:

```bash
# Single district
DISTRICT_NAME=wola

# Multiple districts
DISTRICT_NAME=wola,srodmiescie,mokotow
```

### For Otodom

Similarly, set `OTODOM_DISTRICT`:

```bash
# Single district
OTODOM_DISTRICT=wola

# Multiple districts  
OTODOM_DISTRICT=wola,srodmiescie,mokotow
```

## District Names (Polish)

Common Warsaw districts you can use:

| English Name | Polish Name (use in config) |
|--------------|----------------------------|
| City Center | `srodmiescie` |
| Wola | `wola` |
| Mokotów | `mokotow` |
| Praga North | `praga-polnoc` |
| Praga South | `praga-poludnie` |
| Żoliborz | `zoliborz` |
| Ursynów | `ursynow` |
| Bielany | `bielany` |
| Bemowo | `bemowo` |
| Targówek | `targowek` |
| Ochota | `ochota` |
| Wilanów | `wilanow` |

## Example: Commute-Based Search

If you work at two locations:

### Example 1: Wilanow Office
**Key transit stops:**
- Miasteczko Wilanów
- Natolin Płn. 22
- Płaskowickiej

**Nearby districts:** Wilanów (Mokotów), Ursynów

**Configuration:**
```bash
DISTRICT_NAME=mokotow,ursynow
OTODOM_DISTRICT=mokotow,ursynow
```

### Example 2: Arcadia Office
**Key transit stops:**
- Metro Młociny (Bemowo)
- Metro Świętokrzyska (Śródmieście)
- Rondo ONZ (Wola/Śródmieście)
- Domaniewska (Mokotów)

**Nearby districts:** Wola, Śródmieście, Mokotów, Bemowo

**Configuration:**
```bash
DISTRICT_NAME=wola,srodmiescie,mokotow,bemowo
OTODOM_DISTRICT=wola,srodmiescie,mokotow,bemowo
```

### Example 3: Both Offices (Wide Search)
**Configuration:**
```bash
DISTRICT_NAME=wola,srodmiescie,mokotow,ursynow,bemowo
OTODOM_DISTRICT=wola,srodmiescie,mokotow,ursynow,bemowo
```

## How It Works

1. **Parser searches** using the first district name in OLX URL (e.g., `/q-wola/`)
2. **Client-side filtering** checks each listing's location field
3. **Only listings** from specified districts are saved and sent to Slack
4. **You see the address** in Slack - you manually verify the actual commute time

## Tips

- ✅ **Start with 2-3 districts** - too many districts = too many listings
- ✅ **Check the address** in Slack messages - verify it's actually convenient
- ✅ **Use Google Maps** to check real commute times (15-20 min is typical)
- ✅ **Adjust as needed** - add/remove districts based on results
- ❌ **Don't use all Warsaw districts** - you'll get overwhelmed with listings

## Limitations

- Parser **cannot calculate** actual commute times
- Parser **cannot check** public transport routes
- You must **manually verify** each address works for your commute
- Some listings may have **incomplete addresses** (street name only)

## Recommended Workflow

1. Start with districts you know are convenient
2. Review addresses in Slack messages
3. Add/remove districts based on results
4. Delete database (`rm listings.db`) after changing districts
5. Re-run parser to get fresh results

## Need Help?

If you're unsure which districts to use:
1. Check your commute on Google Maps
2. Note which districts the route passes through
3. Add those districts to your configuration

