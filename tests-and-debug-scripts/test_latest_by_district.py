#!/usr/bin/env python3
"""
Тестовий скрипт для перевірки останніх оголошень в кожному районі
Перевіряє OLX для різних районів Варшави
"""

import os
import sys
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv

# Додаємо батьківську директорію до шляху для імпорту
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Завантажуємо змінні оточення
load_dotenv()

# Список основних районів Варшави для тестування
TEST_DISTRICTS = [
    'wola',
    'srodmiescie',
    'mokotow',
    'praga-polnoc',
    'praga-poludnie',
    'zoliborz',
    'ursynow',
    'ochota',
    'bemowo',
    'bielany'
]


def build_district_search_url(district: str) -> str:
    """Побудова URL пошуку для конкретного району"""
    base_url = f"https://www.olx.pl/nieruchomosci/mieszkania/wynajem/warszawa/q-{district}/"
    
    params = []
    
    # Отримуємо параметри з env або використовуємо базові
    furniture = os.getenv('FURNITURE', 'yes')
    if furniture:
        params.append(f"search[filter_enum_furniture][0]={furniture}")
    
    pets = os.getenv('PETS', 'Tak')
    if pets:
        params.append(f"search[filter_enum_pets][0]={pets}")
    
    rooms = os.getenv('ROOMS', 'three')
    if rooms:
        params.append(f"search[filter_enum_rooms][0]={rooms}")
    
    price_from = os.getenv('PRICE_FROM', '4000')
    if price_from:
        params.append(f"search[filter_float_price:from]={price_from}")
    
    price_to = os.getenv('PRICE_TO', '6000')
    if price_to:
        params.append(f"search[filter_float_price:to]={price_to}")
    
    listing_type = os.getenv('LISTING_TYPE', 'private')
    if listing_type:
        params.append(f"search[private_business]={listing_type}")
    
    if params:
        return base_url + '?' + '&'.join(params)
    return base_url


def fetch_listings_for_district(district: str) -> dict:
    """Отримання оголошень для конкретного району"""
    url = build_district_search_url(district)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0'
    }
    
    result = {
        'district': district,
        'url': url,
        'listings_count': 0,
        'listings': [],
        'error': None
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        cards = soup.find_all('div', {'data-cy': 'l-card'})
        
        result['listings_count'] = len(cards)
        
        # Парсимо перші 3 оголошення для демонстрації
        for i, card in enumerate(cards[:3], 1):
            listing = parse_listing_card(card)
            if listing:
                listing['position'] = i
                result['listings'].append(listing)
        
    except requests.RequestException as e:
        result['error'] = f"Помилка запиту: {e}"
    except Exception as e:
        result['error'] = f"Несподівана помилка: {e}"
    
    return result


def parse_listing_card(card) -> dict:
    """Парсинг картки оголошення"""
    listing = {}
    
    # URL та ID
    link_elem = card.find('a', href=True)
    if link_elem and 'href' in link_elem.attrs:
        url = link_elem['href']
        if not url.startswith('http'):
            url = 'https://www.olx.pl' + url
        
        # Пропускаємо extended search
        if 'reason=extended_search' in url:
            return None
        
        listing['url'] = url
        
        # Витягуємо ID з URL
        parts = url.split('-')
        if parts:
            listing['id'] = parts[-1].replace('.html', '').split('#')[0]
    
    # Заголовок
    title_elem = card.find('h4')
    if not title_elem:
        title_elem = card.find('h6')
    if not title_elem:
        title_elem = card.find('a', {'data-cy': 'listing-ad-title'})
    
    if title_elem:
        listing['title'] = title_elem.get_text(strip=True)
    
    # Ціна
    price_elem = card.find('p', {'data-testid': 'ad-price'})
    if not price_elem:
        price_elem = card.find('span', class_=lambda x: x and 'price' in x.lower())
    
    if price_elem:
        listing['price'] = price_elem.get_text(strip=True)
    
    # Локація
    location_elem = card.find('p', {'data-testid': 'location-date'})
    if not location_elem:
        location_elem = card.find('span', class_=lambda x: x and 'location' in x.lower())
    
    if location_elem:
        listing['location'] = location_elem.get_text(strip=True)
    
    return listing if listing.get('id') else None


def print_district_results(result: dict):
    """Виведення результатів для району"""
    district = result['district'].upper()
    
    print(f"\n{'='*80}")
    print(f"🏘️  РАЙОН: {district}")
    print(f"{'='*80}")
    
    if result['error']:
        print(f"❌ Помилка: {result['error']}")
        return
    
    print(f"📊 Знайдено оголошень: {result['listings_count']}")
    
    if result['listings_count'] == 0:
        print("ℹ️  Оголошень не знайдено")
        return
    
    print(f"\n📋 Перші {min(3, len(result['listings']))} оголошення:")
    print("-" * 80)
    
    for listing in result['listings']:
        print(f"\n{listing['position']}. {listing.get('title', 'Без назви')}")
        print(f"   💰 Ціна:     {listing.get('price', 'Не вказано')}")
        print(f"   📍 Локація:  {listing.get('location', 'Не вказано')}")
        print(f"   🔗 URL:      {listing.get('url', '')[:70]}...")
        print(f"   🆔 ID:       {listing.get('id', 'Невідомо')}")


def main():
    """Головна функція"""
    print("="*80)
    print("🧪 ТЕСТУВАННЯ ОСТАННІХ ОГОЛОШЕНЬ ПО РАЙОНАХ")
    print("="*80)
    print(f"⏰ Час запуску: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Виводимо параметри пошуку
    print("\n📋 Параметри пошуку:")
    print(f"   Кімнати:        {os.getenv('ROOMS', 'three')}")
    print(f"   Ціна:           {os.getenv('PRICE_FROM', '4000')} - {os.getenv('PRICE_TO', '6000')} PLN")
    print(f"   Меблі:          {os.getenv('FURNITURE', 'yes')}")
    print(f"   Тварини:        {os.getenv('PETS', 'Tak')}")
    print(f"   Тип оголошення: {os.getenv('LISTING_TYPE', 'private')}")
    
    print(f"\n🗺️  Райони для перевірки: {', '.join([d.capitalize() for d in TEST_DISTRICTS])}")
    
    # Збираємо статистику
    total_listings = 0
    districts_with_listings = []
    districts_without_listings = []
    districts_with_errors = []
    
    # Перевіряємо кожен район
    for i, district in enumerate(TEST_DISTRICTS, 1):
        print(f"\n\n{'#'*80}")
        print(f"🔍 Перевірка {i}/{len(TEST_DISTRICTS)}")
        print(f"{'#'*80}")
        
        result = fetch_listings_for_district(district)
        print_district_results(result)
        
        # Оновлюємо статистику
        if result['error']:
            districts_with_errors.append(district)
        elif result['listings_count'] > 0:
            districts_with_listings.append((district, result['listings_count']))
            total_listings += result['listings_count']
        else:
            districts_without_listings.append(district)
        
        # Затримка між запитами
        if i < len(TEST_DISTRICTS):
            delay = 3
            print(f"\n⏸️  Затримка {delay} секунд перед наступним запитом...")
            time.sleep(delay)
    
    # Виводимо підсумкову статистику
    print("\n\n" + "="*80)
    print("📊 ПІДСУМКОВА СТАТИСТИКА")
    print("="*80)
    print(f"📍 Перевірено районів: {len(TEST_DISTRICTS)}")
    print(f"📋 Загальна кількість оголошень: {total_listings}")
    
    if districts_with_listings:
        print(f"\n✅ Райони з оголошеннями ({len(districts_with_listings)}):")
        for district, count in sorted(districts_with_listings, key=lambda x: x[1], reverse=True):
            print(f"   • {district.capitalize():20} - {count:3} оголошень")
    
    if districts_without_listings:
        print(f"\n⚠️  Райони без оголошень ({len(districts_without_listings)}):")
        for district in districts_without_listings:
            print(f"   • {district.capitalize()}")
    
    if districts_with_errors:
        print(f"\n❌ Райони з помилками ({len(districts_with_errors)}):")
        for district in districts_with_errors:
            print(f"   • {district.capitalize()}")
    
    print("\n" + "="*80)
    print("🏁 ТЕСТУВАННЯ ЗАВЕРШЕНО")
    print("="*80)
    print(f"⏰ Час завершення: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Перервано користувачем")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Критична помилка: {e}")
        sys.exit(1)

