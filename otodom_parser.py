#!/usr/bin/env python3
"""
Otodom.pl parser for apartment listings
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging
import re
import os
from base_parser import BaseParser

logger = logging.getLogger(__name__)


class OtodomParser(BaseParser):
    """Parser for Otodom.pl"""
    
    def __init__(self, search_url: str, slack_webhook_url: str):
        super().__init__(slack_webhook_url)
        self.search_url = search_url
        # Створюємо сесію для збереження cookies між запитами
        self.session = requests.Session()
        
        # Налаштування проксі, якщо вказано в змінних оточення
        proxy_url = os.getenv('PROXY_URL')  # Формат: http://user:pass@host:port або http://host:port
        if proxy_url:
            self.session.proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            logger.info(f"🔐 Використання проксі-сервера: {proxy_url.split('@')[-1] if '@' in proxy_url else proxy_url}")
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.otodom.pl/'
        }
        self._initialized = False
    
    def get_source_name(self) -> str:
        """Return source name"""
        return "Otodom"
    
    def _init_session(self):
        """Ініціалізувати сесію відвідавши головну сторінку для отримання cookies"""
        if self._initialized:
            return
        
        try:
            logger.debug("🔐 Ініціалізація сесії з Otodom (отримання cookies)...")
            # Спочатку відвідуємо головну сторінку
            home_headers = self.headers.copy()
            home_headers['Sec-Fetch-Site'] = 'none'
            home_headers.pop('Referer', None)
            
            response = self.session.get('https://www.otodom.pl/', headers=home_headers, timeout=30)
            response.raise_for_status()
            
            logger.debug(f"✅ Сесія ініціалізована, отримано cookies: {len(self.session.cookies)} шт.")
            self._initialized = True
            
            # Невелика затримка після ініціалізації
            import time
            time.sleep(2)
            
        except requests.exceptions.ProxyError as e:
            logger.warning(f"⚠️  Проксі не працює: {e}")
            logger.info("🔄 Спроба без проксі...")
            # Вимикаємо проксі і пробуємо ще раз
            self.session.proxies.clear()
            try:
                response = self.session.get('https://www.otodom.pl/', headers=home_headers, timeout=30)
                response.raise_for_status()
                logger.info(f"✅ З'єднання без проксі успішне! Отримано cookies: {len(self.session.cookies)} шт.")
                self._initialized = True
                import time
                time.sleep(2)
            except Exception as inner_e:
                logger.warning(f"⚠️  Не вдалося ініціалізувати сесію навіть без проксі: {inner_e}")
                self._initialized = True
        except Exception as e:
            logger.warning(f"⚠️  Не вдалося ініціалізувати сесію: {e}")
            # Продовжуємо роботу навіть якщо не вдалося отримати cookies
            self._initialized = True
    
    def fetch_listings(self) -> List[Dict]:
        """Fetch list of listings from Otodom"""
        try:
            # Ініціалізуємо сесію перед першим запитом
            self._init_session()
            
            self._wait_before_request()
            
            logger.info("🌐 Fetching listings from Otodom...")
            # Використовуємо сесію замість прямого requests.get
            try:
                response = self.session.get(self.search_url, headers=self.headers, timeout=30)
                response.raise_for_status()
                logger.debug("⏸️  Otodom request completed, processing results...")
            except requests.exceptions.ProxyError as e:
                logger.warning(f"⚠️  Проксі не працює під час запиту: {e}")
                logger.info("🔄 Повторна спроба без проксі...")
                # Вимикаємо проксі і пробуємо ще раз
                self.session.proxies.clear()
                response = self.session.get(self.search_url, headers=self.headers, timeout=30)
                response.raise_for_status()
                logger.info("✅ Запит без проксі успішний!")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract date information from JSON data (Otodom uses Next.js with JSON)
            dates_map = {}
            script_tags = soup.find_all('script', {'id': '__NEXT_DATA__'})
            if script_tags:
                try:
                    import json
                    from datetime import datetime
                    json_data = json.loads(script_tags[0].string)
                    
                    # Navigate to listings in JSON
                    if 'props' in json_data and 'pageProps' in json_data['props']:
                        data = json_data['props']['pageProps'].get('data', {})
                        search_ads = data.get('searchAds', {})
                        items = search_ads.get('items', [])
                        
                        # Build a map of listing ID to date
                        polish_months = {
                            1: 'stycznia', 2: 'lutego', 3: 'marca', 4: 'kwietnia',
                            5: 'maja', 6: 'czerwca', 7: 'lipca', 8: 'sierpnia',
                            9: 'września', 10: 'października', 11: 'listopada', 12: 'grudnia'
                        }
                        
                        for item in items:
                            listing_id = f"ID{item.get('slug', '').split('-ID')[-1]}" if 'ID' in item.get('slug', '') else None
                            date_created = item.get('dateCreated', '')
                            
                            if listing_id and date_created:
                                try:
                                    dt = datetime.strptime(date_created, '%Y-%m-%d %H:%M:%S')
                                    polish_date = f"{dt.day} {polish_months[dt.month]} {dt.year}"
                                    dates_map[listing_id] = polish_date
                                except:
                                    pass
                        
                        logger.debug(f"Extracted dates for {len(dates_map)} listings from JSON")
                except Exception as e:
                    logger.debug(f"Could not extract dates from JSON: {e}")
            
            # Otodom changed their selector - try multiple approaches
            listing_links = soup.find_all('a', {'data-cy': 'listing-item-link'})
            
            # Fallback: if no links found with data-cy, try href-based search
            if not listing_links:
                listing_links = soup.find_all('a', href=lambda x: x and '/pl/oferta/' in x)
                logger.debug(f"Using fallback selector, found {len(listing_links)} links")
            
            if not listing_links:
                logger.warning("⚠️  No listings found on Otodom page")
                # Save HTML for debugging
                with open('debug_otodom_page.html', 'w', encoding='utf-8') as f:
                    f.write(soup.prettify())
                logger.info("💾 Saved page HTML to debug_otodom_page.html for inspection")
                return []
            
            logger.info(f"📋 Found {len(listing_links)} listing(s) on Otodom page")
            
            # Check if we need to filter for private listings
            listing_type = os.getenv('LISTING_TYPE', 'private')
            filter_private = False  # ВИМКНЕНО - фільтр працює неправильно
            
            # Build district and price maps from JSON for accurate filtering
            districts_map = {}
            prices_map = {}
            if script_tags:
                try:
                    json_data = json.loads(script_tags[0].string)
                    if 'props' in json_data and 'pageProps' in json_data['props']:
                        data = json_data['props']['pageProps'].get('data', {})
                        search_ads = data.get('searchAds', {})
                        items = search_ads.get('items', [])
                        
                        for item in items:
                            # Extract district and price from JSON (more accurate than text parsing)
                            listing_id = f"ID{item.get('slug', '').split('-ID')[-1]}" if 'ID' in item.get('slug', '') else None
                            if listing_id:
                                location = item.get('location', {})
                                reverse_geo = location.get('reverseGeocoding', {})
                                locations = reverse_geo.get('locations', [])
                                
                                # Find district level location
                                district = next((loc['name'] for loc in locations if loc.get('locationLevel') == 'district'), None)
                                if district:
                                    districts_map[listing_id] = district
                                
                                # Extract price from JSON
                                price_info = item.get('price', {})
                                if price_info:
                                    price_value = price_info.get('value', '')
                                    if price_value:
                                        prices_map[listing_id] = price_value
                                        logger.debug(f"💰 Price from JSON for {listing_id}: {price_value}")
                        
                        logger.debug(f"Extracted districts for {len(districts_map)} listings from JSON")
                        logger.debug(f"Extracted prices for {len(prices_map)} listings from JSON")
                except Exception as e:
                    logger.debug(f"Could not extract districts/prices from JSON: {e}")
            
            # Log which districts we're analyzing
            district_name = os.getenv('OTODOM_DISTRICT', 'wola')
            expected_districts = [d.strip() for d in district_name.split(',') if d.strip()]
            logger.info(f"🔍 Analyzing districts: {', '.join(expected_districts)}")
            
            listings = []
            for i, link in enumerate(listing_links[:5], 1):  # Тільки перші 5 для дебагу
                try:
                    logger.info(f"🔍 Parsing link {i}/5...")
                    
                    # Get listing ID from link to fetch price from JSON
                    href = link.get('href', '')
                    listing_id = f"ID{href.split('-ID')[-1]}" if '-ID' in href else None
                    json_price = prices_map.get(listing_id) if listing_id else None
                    
                    # Try to get price from search results HTML (parent element)
                    search_price = None
                    try:
                        parent = link.find_parent('article') or link.find_parent('div', class_=lambda x: x and 'listing' in str(x).lower())
                        if parent:
                            parent_text = parent.get_text(separator=' ', strip=True)
                            # Look for pattern like "4500 zł + czynsz: 1100 zł/miesiąc"
                            price_match = re.search(r'(\d{3,5})\s*zł\s*\+\s*czynsz', parent_text)
                            if price_match:
                                search_price = price_match.group(1)
                                logger.debug(f"💰 Price from search HTML: {search_price} zł")
                    except Exception as e:
                        logger.debug(f"Could not extract price from search HTML: {e}")
                    
                    listing = self._parse_listing_link(link, filter_private, json_price, search_price)
                    if listing:
                        logger.info(f"✅ Parsed listing {i}: {listing.get('title', 'No title')[:50]}...")
                        
                        # Add date from JSON if available
                        # Use _short_id (ID...) to match with dates_map keys
                        short_id = listing.get('_short_id')
                        if short_id and short_id in dates_map:
                            date_str = dates_map[short_id]
                            # Append date to location (like OLX does)
                            current_location = listing.get('location', 'Warszawa')
                            listing['location'] = f"{current_location} - {date_str}"
                            logger.debug(f"Added date to {short_id}: {date_str}")
                        
                        # Filter by district using JSON data (more accurate)
                        if short_id and short_id in districts_map:
                            district_from_json = districts_map[short_id]
                            logger.info(f"📍 District from JSON: {district_from_json}")
                            
                            # Skip non-Warsaw districts (but Ursynów, Wola, etc. are Warsaw districts)
                            # Only skip if it's clearly not Warsaw (like Kraków, Gdańsk, etc.)
                            non_warsaw_cities = ['kraków', 'krakow', 'gdańsk', 'gdansk', 'wrocław', 'wroclaw', 'poznań', 'poznan']
                            if any(city in district_from_json.lower() for city in non_warsaw_cities):
                                logger.info(f"⏭️  Skipping listing from '{district_from_json}' (not Warsaw city)")
                                continue
                            
                            districts_str = os.getenv('OTODOM_DISTRICT', '')
                            if districts_str:
                                expected_districts = [d.strip() for d in districts_str.split(',') if d.strip()]
                                logger.info(f"🎯 Looking for districts: {expected_districts}")
                                # Normalize Polish characters for comparison
                                district_normalized = district_from_json.lower()
                                district_normalized = district_normalized.replace('ą', 'a').replace('ć', 'c').replace('ę', 'e').replace('ł', 'l').replace('ń', 'n').replace('ó', 'o').replace('ś', 's').replace('ź', 'z').replace('ż', 'z')
                                
                                match_found = any(district.lower() in district_normalized for district in expected_districts)
                                if not match_found:
                                    districts_display = ', '.join(expected_districts)
                                    logger.info(f"⏭️  Skipping listing from '{district_from_json}' (looking for: {districts_display})")
                                    continue
                                else:
                                    logger.info(f"✅ District match found: {district_from_json}")
                        
                        # Remove temporary _short_id before saving
                        if '_short_id' in listing:
                            del listing['_short_id']
                        
                        listings.append(listing)
                        logger.info(f"✅ Added listing to results: {listing.get('title', 'No title')[:50]}...")
                    else:
                        logger.info(f"❌ Failed to parse listing {i}")
                except Exception as e:
                    logger.error(f"❌ Error parsing link {i}: {e}")
                    continue
            
            # Log district analysis summary
            district_summary = {}
            for listing in listings:
                location = listing.get('location', '')
                if 'Wola' in location:
                    district_summary['Wola'] = district_summary.get('Wola', 0) + 1
                elif 'Ursynów' in location:
                    district_summary['Ursynów'] = district_summary.get('Ursynów', 0) + 1
                elif 'Kabaty' in location:
                    district_summary['Kabaty'] = district_summary.get('Kabaty', 0) + 1
                elif 'Natolin' in location:
                    district_summary['Natolin'] = district_summary.get('Natolin', 0) + 1
                elif 'Imielin' in location:
                    district_summary['Imielin'] = district_summary.get('Imielin', 0) + 1
                elif 'Stokłosy' in location:
                    district_summary['Stokłosy'] = district_summary.get('Stokłosy', 0) + 1
            
            if district_summary:
                summary_str = ', '.join([f"{district}: {count}" for district, count in district_summary.items()])
                logger.info(f"📊 District analysis: {summary_str}")
            
            if filter_private and len(listings) < len(listing_links):
                logger.info(f"🔍 Filtered to {len(listings)} private listing(s) (from {len(listing_links)} total)")
            else:
                logger.info(f"✅ Successfully parsed {len(listings)} listing(s)")
            
            return listings
            
        except requests.RequestException as e:
            logger.error(f"Error requesting Otodom: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []
    
    def _parse_listing_link(self, link, filter_private: bool = False, json_price: str = None, search_price: str = None) -> Optional[Dict]:
        """Parse individual listing link from Otodom"""
        listing = {}
        
        # Get URL
        url = link.get('href', '')
        if not url:
            return None
        
        if not url.startswith('http'):
            url = 'https://www.otodom.pl' + url
        
        listing['url'] = url
        
        # Extract ID from URL (e.g., ID4yA0z from /pl/oferta/...-ID4yA0z)
        id_match = re.search(r'-ID([a-zA-Z0-9]+)$', url)
        if id_match:
            short_id = id_match.group(1)
            listing['id'] = f"OTODOM_{short_id}"
            listing['_short_id'] = f"ID{short_id}"  # For matching with dates_map
        else:
            listing['id'] = f"OTODOM_{url.split('/')[-1]}"
            listing['_short_id'] = None
        
        # Get title from title element inside link
        title_elem = link.find('p', {'data-cy': 'listing-item-title'})
        if title_elem:
            listing['title'] = title_elem.get_text(strip=True)
        else:
            # Fallback: extract from URL
            url_parts = url.split('/')
            if len(url_parts) > 3:
                slug = url_parts[-1]
                title_slug = re.sub(r'-ID[a-zA-Z0-9]+$', '', slug)
                listing['title'] = title_slug.replace('-', ' ').title()
            else:
                listing['title'] = 'Otodom Listing'
        
        # CRITICAL: Check if private listing by fetching the actual listing page
        # The search results page doesn't contain reliable advertiser type info
        if filter_private:
            try:
                self._wait_before_request()
                response = self.session.get(url, headers=self.headers, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract advertiser type from JSON data
                script_tags = soup.find_all('script', {'id': '__NEXT_DATA__'})
                if script_tags:
                    import json
                    json_data = json.loads(script_tags[0].string)
                    
                    if 'props' in json_data and 'pageProps' in json_data['props']:
                        ad = json_data['props']['pageProps'].get('ad', {})
                        advertiser_type = ad.get('advertiserType', '').lower()
                        advert_type = ad.get('advertType', '').lower()
                        
                        # Filter out business/agency listings
                        if advertiser_type in ['business', 'agency', 'developer', 'professional'] or \
                           advert_type in ['agency', 'developer', 'professional', 'business']:
                            logger.debug(f"⏭️  Skipping {advertiser_type}/{advert_type} listing: {listing.get('title', 'Unknown')}")
                            return None
                        
                        logger.debug(f"✅ Private listing confirmed: {advertiser_type}/{advert_type}")
                
            except Exception as e:
                logger.warning(f"⚠️  Could not check advertiser type for {url}: {e}")
                # If we can't check, skip it to be safe when filtering is enabled
                return None
        
        # Get parent element to find price, location, image
        parent = link.find_parent('article') or link.find_parent('div', class_=lambda x: x and 'listing' in str(x).lower())
        
        if parent:
            parent_text = parent.get_text(separator=' ', strip=True)
            parent_text_lower = parent_text.lower()
            
            # Check for property-specific keywords based on search type
            property_type = os.getenv('PROPERTY_TYPE', 'apartments')
            
            if property_type == 'houses':
                is_relevant_property = ('dom' in parent_text_lower or 
                                      'house' in parent_text_lower or
                                      'wynajem' in parent_text_lower or
                                      'domy' in parent_text_lower)
            else:
                is_relevant_property = ('mieszkanie' in parent_text_lower or 
                                       'apartment' in parent_text_lower or
                                       'wynajem' in parent_text_lower or
                                       'pokój' in parent_text_lower)
            
            # Skip if not relevant property type
            if not is_relevant_property:
                logger.debug(f"⏭️  Skipping non-{property_type} listing: {listing.get('title', 'Unknown')} (relevant: {is_relevant_property})")
                return None
            
            # Extract price - prioritize search price, then JSON price, then HTML
            if search_price:
                listing['price'] = f"{search_price} zł/miesiąc"
                logger.debug(f"💰 Price from search HTML: {search_price} zł")
            elif json_price:
                listing['price'] = f"{json_price} zł/miesiąc"
                logger.debug(f"💰 Price from JSON: {json_price} zł")
            else:
                # Extract price from HTML - look for main rental price first
                # Pattern: "4500 zł/miesiąc" or "4500 zł/mies" 
                main_price_match = re.search(r'(\d[\d\s]*\d+|\d+)\s*zł\s*/\s*mies', parent_text)
                if main_price_match:
                    price_str = main_price_match.group(1).replace(' ', '')
                    listing['price'] = f"{price_str} zł/miesiąc"
                    logger.debug(f"💰 Price from /mies pattern: {price_str} zł")
                else:
                    # Look for pattern like "4500 zł + czynsz: 1100 zł/miesiąc"
                    main_price_pattern = re.search(r'(\d{3,5})\s*zł\s*\+\s*czynsz', parent_text)
                    if main_price_pattern:
                        price_str = main_price_pattern.group(1)
                        listing['price'] = f"{price_str} zł/miesiąc"
                        logger.debug(f"💰 Price from +czynsz pattern: {price_str} zł")
                    else:
                        # Fallback: look for any price but EXCLUDE czynsz
                        # Use better regex that doesn't capture page numbers
                        all_prices = re.findall(r'\b(\d{3,5})\s*zł\b', parent_text)
                        logger.debug(f"💰 All prices found: {all_prices}")
                        
                        if all_prices:
                            # Find czynsz pattern to exclude it
                            czynsz_match = re.search(r'czynsz[:\s]*(\d{3,5})\s*zł', parent_text, re.IGNORECASE)
                            if czynsz_match:
                                czynsz_value = czynsz_match.group(1)
                                logger.debug(f"💰 Czynsz value: {czynsz_value}")
                                # Find the first price that's NOT czynsz
                                for price_str in all_prices:
                                    if price_str != czynsz_value:
                                        listing['price'] = f"{price_str} zł/miesiąc"
                                        logger.debug(f"💰 Selected price (not czynsz): {price_str} zł")
                                        break
                                else:
                                    listing['price'] = 'N/A'
                                    logger.debug(f"💰 No non-czynsz price found")
                            else:
                                # No czynsz found, take the first price
                                listing['price'] = f"{all_prices[0]} zł/miesiąc"
                                logger.debug(f"💰 First price (no czynsz): {all_prices[0]} zł")
                        else:
                            listing['price'] = 'N/A'
                            logger.debug(f"💰 No prices found in text")
            
            # Extract czynsz (service charge) separately
            czynsz_match = re.search(r'czynsz[:\s]*(\d[\d\s]*\d+|\d+)\s*zł', parent_text, re.IGNORECASE)
            if czynsz_match:
                czynsz_str = czynsz_match.group(1).replace(' ', '')
                listing['czynsz'] = f"{czynsz_str} zł/miesiąc"
            else:
                listing['czynsz'] = None
            
            # Extract location - look for district name in text
            # Otodom format: "..., District, Warszawa, mazowieckie"
            # Try to find known districts in text
            districts_to_check = ['wola', 'śródmieście', 'mokotów', 'praga', 'żoliborz', 'ochota', 'ursynów', 'bielany', 'targówek', 'bemowo', 'włochy', 'ursus', 'wilanów', 'wawer', 'wesoła', 'rembertów', 'białołęka']
            location_found = None
            parent_text_lower = parent_text.lower()
            
            for district in districts_to_check:
                if district in parent_text_lower:
                    # Found district, try to extract fuller location around it
                    # Look for pattern: "district, Warszawa"
                    pattern = rf'([^,]*{district}[^,]*),\s*warszawa'
                    match = re.search(pattern, parent_text_lower, re.IGNORECASE)
                    if match:
                        location_found = match.group(1).strip().title()
                        break
            
            if location_found:
                listing['location'] = location_found + ', Warszawa'
            else:
                # Fallback: try original regex
                location_match = re.search(r'ul\.\s+([^,]+),\s*([A-ZŁŚĆŻŹ][a-ząćęłńóśźż\s]+),\s*([A-ZŁŚĆŻŹ][a-ząćęłńóśźż\s]+)', parent_text)
                if location_match:
                    street = location_match.group(1).strip()
                    district = location_match.group(2).strip()
                    city = location_match.group(3).strip()
                    listing['location'] = f"{district}, {city}"
                else:
                    listing['location'] = 'Warszawa'
            
            # Note: District filtering is now done at fetch_listings level using JSON data
            # This is more accurate than text parsing
            
            # Extract image
            img_elem = parent.find('img', src=True)
            if img_elem:
                img_src = img_elem.get('src', '')
                logger.debug(f"Found img element for {listing.get('id')}: src length={len(img_src)}")
                if img_src and img_src.startswith('http'):
                    listing['image_url'] = img_src
                    logger.debug(f"Set image_url from src: {img_src[:80]}...")
                else:
                    # Try srcset for better quality
                    srcset = img_elem.get('srcset', '')
                    if srcset:
                        # srcset format: "url1 1x, url2 2x"
                        urls = [part.strip().split()[0] for part in srcset.split(',') if part.strip()]
                        if urls:
                            # Take the last one (usually highest quality)
                            listing['image_url'] = urls[-1]
                            logger.debug(f"Set image_url from srcset: {urls[-1][:80]}...")
                # Also try data-cy="listing-item-image-source" for Otodom
                if not listing.get('image_url'):
                    img_with_cy = parent.find('img', {'data-cy': 'listing-item-image-source'})
                    if img_with_cy and img_with_cy.get('src'):
                        listing['image_url'] = img_with_cy.get('src')
                        logger.debug(f"Set image_url from data-cy: {listing['image_url'][:80]}...")
            else:
                logger.debug(f"No img element found in parent for {listing.get('id')}")
        else:
            listing['price'] = 'N/A'
            listing['location'] = 'Warszawa'
        
        # Debug logging if data is missing
        if not listing.get('title') or listing['title'] == 'Otodom Listing':
            logger.warning(f"⚠️  Could not extract proper title for: {listing.get('id')}")
            logger.debug(f"URL: {url}")
        
        return listing if listing.get('id') else None
