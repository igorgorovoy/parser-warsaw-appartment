#!/usr/bin/env python3
"""Check if a specific listing has photos on its detail page"""

import requests
from bs4 import BeautifulSoup

# First, get a listing URL from search results
search_url = "https://www.olx.pl/nieruchomosci/mieszkania/wynajem/warszawa/?search[filter_enum_rooms][0]=three&search[filter_float_price:from]=4000&search[filter_float_price:to]=6000"

print("="*80)
print("GETTING LISTING WITHOUT PHOTO FROM SEARCH")
print("="*80)

response = requests.get(search_url, timeout=30)
soup = BeautifulSoup(response.text, 'html.parser')

cards = soup.find_all('div', {'data-cy': 'l-card'})

# Find a card without photo
test_url = None
test_title = None

for card in cards[5:10]:  # Check cards 6-10
    img_elem = card.find('img', src=True)
    if img_elem:
        img_src = img_elem.get('src', '')
        if 'no_thumbnail' in img_src:
            # This card shows no thumbnail
            link_elem = card.find('a', href=True)
            if link_elem:
                test_url = link_elem['href']
                if not test_url.startswith('http'):
                    test_url = 'https://www.olx.pl' + test_url
                
                title_elem = card.find('h4') or card.find('h6')
                test_title = title_elem.get_text(strip=True) if title_elem else 'No title'
                break

if not test_url:
    print("❌ No listing found with no_thumbnail")
    exit(1)

print(f"Found listing: {test_title}")
print(f"URL: {test_url}")
print()

print("="*80)
print("CHECKING DETAIL PAGE FOR PHOTOS")
print("="*80)

# Now fetch the detail page
response = requests.get(test_url, timeout=30)
soup = BeautifulSoup(response.text, 'html.parser')

# Look for images on detail page
all_imgs = soup.find_all('img')
print(f"Total img tags on detail page: {len(all_imgs)}\n")

# Look for gallery or photo elements
photo_count = 0
for img in all_imgs:
    src = img.get('src', '')
    if 'apollo.olxcdn.com' in src and 'no_thumbnail' not in src:
        photo_count += 1
        if photo_count <= 3:
            print(f"📸 Photo {photo_count}: {src[:100]}...")

if photo_count > 0:
    print(f"\n✅ FOUND {photo_count} PHOTOS on detail page!")
    print("❌ But NO photo in search results (only placeholder)")
else:
    print("\n❌ No photos found even on detail page")

print("="*80)

