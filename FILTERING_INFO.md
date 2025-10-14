# 🔍 Filtering Comparison: OLX vs Otodom

## Problem: Why Otodom shows different results?

You configured search for:
- ✅ 3 rooms
- ✅ Furnished (yes)
- ✅ Pets allowed (Tak)
- ✅ Private listings only
- ✅ Price: 4000-6000 PLN
- ✅ District: Śródmieście

### OLX Results
Shows ONLY apartments matching **ALL** criteria above.

### Otodom Results  
Shows apartments matching **ONLY SOME** criteria:
- ✅ 3 rooms
- ✅ Price: 4000-6000 PLN
- ✅ District: Śródmieście
- ✅ Area: 60-90 m²
- ❌ Furniture: **ALL** (furnished AND unfurnished)
- ❌ Pets: **ALL** (allowed AND not allowed)
- ❌ Listing type: **ALL** (private AND agencies)

## Why?

**Otodom website doesn't provide URL parameters for these filters.**

When you search on Otodom.pl website, these filters work through JavaScript after page loads. But when we use direct URL (which parser does), these filters are not available.

## Solution

### Option 1: Use only OLX (Recommended)
```bash
# In .env file:
ENABLE_OLX=true
ENABLE_OTODOM=false
```

### Option 2: Accept more results from Otodom
Enable Otodom but understand you'll get extra listings that might not match all criteria:
```bash
# In .env file:
ENABLE_OLX=true
ENABLE_OTODOM=true
```

You can manually check Otodom listings in Slack and skip ones that don't match your needs.

### Option 3: Client-side filtering (Future enhancement)
We could add filtering AFTER parsing - check listing description for keywords like "umeblowane" (furnished), "zwierzęta" (pets), etc. But this would be unreliable because:
- Not all listings have these details in description
- Different wording used by different posters
- Would require fetching full listing page (slower)

## Recommendation

🎯 **For precise results**: Use `ENABLE_OTODOM=false`

🎯 **For maximum coverage**: Use `ENABLE_OTODOM=true` but expect more listings

The choice is yours! 🚀

