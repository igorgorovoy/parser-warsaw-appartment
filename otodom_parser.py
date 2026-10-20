#!/usr/bin/env python3
"""
Otodom.pl parser for apartment and house listings.

Reads listings from the Next.js JSON (__NEXT_DATA__) embedded in search pages,
runs several searches (flats/houses, Warsaw/suburbs) and annotates every new
listing with the nearest school bus stop (coordinates from the detail page).
"""

import json
import os
import random
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional

import requests
from bs4 import BeautifulSoup

from base_parser import BaseParser
from bus_stops import nearest_stop, distance_m, SCHOOL

logger = logging.getLogger(__name__)

POLISH_MONTHS = {
    1: 'stycznia', 2: 'lutego', 3: 'marca', 4: 'kwietnia',
    5: 'maja', 6: 'czerwca', 7: 'lipca', 8: 'sierpnia',
    9: 'września', 10: 'października', 11: 'listopada', 12: 'grudnia'
}

ROOMS_LABEL = {
    'ONE': 1, 'TWO': 2, 'THREE': 3, 'FOUR': 4, 'FIVE': 5,
    'SIX': 6, 'SEVEN': 7, 'EIGHT': 8, 'NINE': 9, 'TEN': 10, 'MORE': '10+'
}

ESTATE_LABEL = {'FLAT': 'Квартира', 'HOUSE': 'Будинок'}


def normalize(text: str) -> str:
    """Lowercase and strip Polish diacritics"""
    table = str.maketrans('ąćęłńóśźż', 'acelnoszz')
    return text.lower().translate(table)


class OtodomParser(BaseParser):
    """Parser for Otodom.pl"""

    def __init__(self, searches: List[Dict], slack_webhook_url: str):
        """
        searches: list of {'name': str, 'url': str, 'filter_districts': bool,
                           'all_warsaw': bool (optional), 'bus_limit': int (optional)}
        filter_districts=False lets non-Warsaw listings through,
        all_warsaw=True skips the OTODOM_DISTRICT check for Warsaw listings,
        bus_limit overrides the bus stop distance limit (0 = only show the distance).
        """
        super().__init__(slack_webhook_url)
        self.searches = searches
        self.session = requests.Session()

        proxy_url = os.getenv('PROXY_URL')  # Format: http://user:pass@host:port or http://host:port
        if proxy_url:
            self.session.proxies = {'http': proxy_url, 'https': proxy_url}
            logger.info(f"🔐 Using proxy: {proxy_url.split('@')[-1]}")

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://www.otodom.pl/',
        }
        self._initialized = False

        self.max_pages = int(os.getenv('OTODOM_MAX_PAGES', '3'))
        self.districts = [normalize(d.strip()) for d in os.getenv('OTODOM_DISTRICT', '').split(',') if d.strip()]
        self.bus_max_city = int(os.getenv('BUS_MAX_DISTANCE_M', '1500'))
        self.bus_max_suburb = int(os.getenv('SUBURB_BUS_MAX_DISTANCE_M', '5000'))
        # Suburb listings within this distance of the school pass regardless of bus stops
        self.school_max = int(os.getenv('SCHOOL_MAX_DISTANCE_M', '12000'))
        # isPrivateOwner from search JSON: listing published by the owner, not an agency
        self.private_only = os.getenv('LISTING_TYPE', 'private') == 'private'

    def get_source_name(self) -> str:
        """Return source name"""
        return "Otodom"

    def _init_session(self):
        """Visit the home page once to get cookies"""
        if self._initialized:
            return
        try:
            self.session.get('https://www.otodom.pl/', headers=self.headers, timeout=30)
        except requests.exceptions.ProxyError as e:
            logger.warning(f"⚠️  Proxy failed, continuing without it: {e}")
            self.session.proxies.clear()
        except Exception as e:
            logger.warning(f"⚠️  Could not initialize session: {e}")
        self._initialized = True

    def _get_next_data(self, url: str) -> Optional[Dict]:
        """Download a page and return its __NEXT_DATA__ JSON"""
        response = self.session.get(url, headers=self.headers, timeout=30)
        response.raise_for_status()
        script = BeautifulSoup(response.content, 'html.parser').find('script', {'id': '__NEXT_DATA__'})
        if not script or not script.string:
            return None
        return json.loads(script.string)

    def _fetch_search_items(self, url: str) -> List[Dict]:
        """Fetch up to max_pages of search results"""
        items = []
        for page in range(1, self.max_pages + 1):
            page_url = f"{url}&page={page}" if page > 1 else url
            data = self._get_next_data(page_url)
            search_ads = (data or {}).get('props', {}).get('pageProps', {}).get('data', {}).get('searchAds') or {}
            page_items = search_ads.get('items', [])
            items.extend(page_items)

            total_pages = (search_ads.get('pagination') or {}).get('totalPages', 1)
            if page >= total_pages or not page_items:
                break
            time.sleep(random.uniform(2, 4))
        return items

    def _fetch_coordinates(self, url: str) -> Optional[Dict]:
        """Get listing coordinates from its detail page"""
        try:
            time.sleep(random.uniform(1, 2))
            data = self._get_next_data(url)
            location = (data or {}).get('props', {}).get('pageProps', {}).get('ad', {}).get('location', {})
            coords = location.get('coordinates') or {}
            if coords.get('latitude') is None:
                return None
            return {
                'lat': coords['latitude'],
                'lon': coords['longitude'],
                # radius > 0 means the owner hid the exact address
                'approx': bool((location.get('mapDetails') or {}).get('radius')),
            }
        except Exception as e:
            logger.warning(f"⚠️  Could not get coordinates for {url}: {e}")
            return None

    def _location_parts(self, item: Dict) -> Dict:
        """Extract city, district and sub-area from reverse geocoding"""
        parts = {}
        for loc in (item.get('location') or {}).get('reverseGeocoding', {}).get('locations', []):
            parts[loc.get('locationLevel')] = loc.get('name')
        street = ((item.get('location') or {}).get('address') or {}).get('street') or {}
        parts['street'] = street.get('name')
        return parts

    @staticmethod
    def _is_warsaw(parts: Dict) -> bool:
        return parts.get('city_or_village') == 'Warszawa'

    def _district_allowed(self, parts: Dict, search: Dict) -> bool:
        """Warsaw listings must be in one of OTODOM_DISTRICT (unless all_warsaw); suburbs pass if the search allows them"""
        if not self._is_warsaw(parts):
            return not search.get('filter_districts', True)
        if search.get('all_warsaw') or not self.districts:
            return True
        names = normalize(' '.join(filter(None, [parts.get('district'), parts.get('residential')])))
        return any(d in names for d in self.districts)

    def _item_to_listing(self, item: Dict, search_name: str) -> Dict:
        """Convert Otodom JSON item to listing dict"""
        parts = self._location_parts(item)
        place = [parts.get('street'), parts.get('residential'), parts.get('district'),
                 parts.get('city_or_village') or parts.get('city'), parts.get('commune')]
        seen = []
        for p in place:
            if p and p not in seen:
                seen.append(p)
        location = ', '.join(seen)

        created = item.get('dateCreated', '')
        try:
            dt = datetime.strptime(created, '%Y-%m-%d %H:%M:%S')
            location += f" - {dt.day} {POLISH_MONTHS[dt.month]} {dt.year}"
        except ValueError:
            pass

        price = (item.get('totalPrice') or item.get('rentPrice') or {}).get('value')
        images = item.get('images') or []
        image_url = (images[0].get('large') or images[0].get('medium')) if images else None

        details = [
            ESTATE_LABEL.get(item.get('estate'), item.get('estate') or ''),
            f"{ROOMS_LABEL.get(item.get('roomsNumber'), item.get('roomsNumber'))} кімн." if item.get('roomsNumber') else None,
            f"{item.get('areaInSquareMeters')} м²" if item.get('areaInSquareMeters') else None,
            f"ділянка {item.get('terrainAreaInSquareMeters')} м²" if item.get('terrainAreaInSquareMeters') else None,
            'приватне' if item.get('isPrivateOwner') else 'агенція/забудовник',
        ]

        return {
            'id': f"OTODOM_{item.get('slug', '').split('-ID')[-1]}" if '-ID' in item.get('slug', '') else f"OTODOM_{item.get('id')}",
            'title': item.get('title', 'Otodom listing'),
            'price': f"{int(price)} zł/miesiąc" if price else 'N/A',
            'location': location or 'Warszawa',
            'url': f"https://www.otodom.pl/pl/oferta/{item.get('slug')}",
            'image_url': image_url,
            'details': ' · '.join(d for d in details if d),
            '_search': search_name,
        }

    def fetch_listings(self) -> List[Dict]:
        """Fetch listings from all configured searches"""
        self._init_session()
        self._wait_before_request()

        listings = []
        seen_ids = set()
        for search in self.searches:
            logger.info(f"🌐 Otodom search: {search['name']}")
            try:
                items = self._fetch_search_items(search['url'])
            except requests.RequestException as e:
                logger.error(f"❌ Error requesting Otodom ({search['name']}): {e}")
                continue
            logger.info(f"📋 {len(items)} listing(s) in search results")

            kept = skipped_district = skipped_bus = skipped_agency = 0
            for item in items:
                try:
                    if item.get('hidePrice'):
                        continue
                    # Year-round living only: skip summer cottages
                    if 'letnisk' in normalize(item.get('title', '')):
                        continue
                    if self.private_only and not item.get('isPrivateOwner'):
                        skipped_agency += 1
                        continue
                    parts = self._location_parts(item)
                    if not self._district_allowed(parts, search):
                        skipped_district += 1
                        continue

                    listing = self._item_to_listing(item, search['name'])
                    if listing['id'] in seen_ids or self._is_listing_seen(listing['id']):
                        continue
                    seen_ids.add(listing['id'])

                    # Bus stop distance (one detail request per NEW listing only)
                    coords = self._fetch_coordinates(listing['url'])
                    if coords:
                        route, stop, meters = nearest_stop(coords['lat'], coords['lon'])
                        limit = self.bus_max_city if self._is_warsaw(parts) else self.bus_max_suburb
                        if 'bus_limit' in search:
                            limit = search['bus_limit']
                        approx = ' (адреса приблизна)' if coords['approx'] else ''
                        listing['bus'] = f"🚌 {stop} ({route}) — {meters} м по прямій{approx}"
                        school_m = round(distance_m(coords['lat'], coords['lon'], SCHOOL[1], SCHOOL[2]))
                        listing['school'] = f"🏫 школа ({SCHOOL[0]}) — {school_m} м по прямій{approx}"
                        near_school = not self._is_warsaw(parts) and self.school_max and school_m <= self.school_max
                        if limit and meters > limit and not near_school:
                            logger.info(f"⏭️  {listing['title'][:50]} — {meters} m to {stop}, "
                                        f"{school_m} m to school, over {limit} m")
                            self._save_filtered(listing)
                            skipped_bus += 1
                            continue
                    else:
                        listing['bus'] = '🚌 відстань невідома (немає координат)'

                    listings.append(listing)
                    kept += 1
                except Exception as e:
                    logger.error(f"❌ Error processing listing: {e}")

            logger.info(f"✅ {search['name']}: {kept} new, skipped {skipped_agency} agency, "
                        f"{skipped_district} by district, {skipped_bus} by bus distance")
            time.sleep(random.uniform(2, 4))

        return listings
