#!/usr/bin/env python3
"""
Тестовий скрипт для перевірки конкретних районів з .env файлу
"""

import os
import sys
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv

# Додаємо батьківську директорію до шляху
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Завантажуємо змінні оточення
load_dotenv()


def build_district_search_url(district: str) -> str:
    """Побудова URL пошуку для конкретного району"""
    base_url = f"https://www.olx.pl/nieruchomosci/mieszkania/wynajem/warszawa/q-{district}/"
    
    params = []
    
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


def test_district(district: str) -> dict:
    """Тестування одного району"""
    url = build_district_search_url(district)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7',
        'DNT': '1',
        'Connection': 'keep-alive',
    }
    
    result = {
        'district': district,
        'url': url,
        'status': 'unknown',
        'count': 0,
        'error': None
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        cards = soup.find_all('div', {'data-cy': 'l-card'})
        
        result['count'] = len(cards)
        result['status'] = 'success'
        
        # Витягуємо перше оголошення для перевірки
        if cards:
            first_card = cards[0]
            location_elem = first_card.find('p', {'data-testid': 'location-date'})
            if location_elem:
                result['sample_location'] = location_elem.get_text(strip=True)
        
    except requests.RequestException as e:
        result['status'] = 'error'
        result['error'] = str(e)
    except Exception as e:
        result['status'] = 'error'
        result['error'] = str(e)
    
    return result


def main():
    """Головна функція"""
    print("="*80)
    print("🧪 ТЕСТУВАННЯ РАЙОНІВ З .ENV ФАЙЛУ")
    print("="*80)
    print(f"⏰ Час запуску: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Отримуємо райони з .env
    district_name = os.getenv('DISTRICT_NAME', '')
    
    if not district_name:
        print("\n❌ ПОМИЛКА: DISTRICT_NAME не встановлено в .env файлі!")
        return
    
    districts = [d.strip() for d in district_name.split(',') if d.strip()]
    
    print(f"\n📍 Райони для перевірки ({len(districts)}):")
    for d in districts:
        print(f"   • {d}")
    
    # Параметри пошуку
    print("\n📋 Параметри пошуку:")
    print(f"   Кімнати:        {os.getenv('ROOMS', 'three')}")
    print(f"   Ціна:           {os.getenv('PRICE_FROM', '4000')} - {os.getenv('PRICE_TO', '6000')} PLN")
    print(f"   Меблі:          {os.getenv('FURNITURE', 'yes')}")
    print(f"   Тварини:        {os.getenv('PETS', 'Tak')}")
    print(f"   Тип оголошення: {os.getenv('LISTING_TYPE', 'private')}")
    
    # Тестуємо кожен район
    results = []
    
    for i, district in enumerate(districts, 1):
        print(f"\n{'='*80}")
        print(f"🔍 Перевірка {i}/{len(districts)}: {district.upper()}")
        print(f"{'='*80}")
        
        result = test_district(district)
        results.append(result)
        
        if result['status'] == 'success':
            print(f"✅ Район '{district}' працює!")
            print(f"📊 Знайдено оголошень: {result['count']}")
            if result.get('sample_location'):
                print(f"📍 Приклад локації: {result['sample_location']}")
            print(f"🔗 URL: {result['url'][:70]}...")
        else:
            print(f"❌ Помилка для району '{district}'")
            print(f"⚠️  Помилка: {result['error']}")
            print(f"🔗 URL: {result['url']}")
        
        # Затримка між запитами
        if i < len(districts):
            delay = 3
            print(f"\n⏸️  Затримка {delay} секунд...")
            time.sleep(delay)
    
    # Підсумкова статистика
    print("\n\n" + "="*80)
    print("📊 ПІДСУМКОВА СТАТИСТИКА")
    print("="*80)
    
    success_count = sum(1 for r in results if r['status'] == 'success')
    error_count = sum(1 for r in results if r['status'] == 'error')
    total_listings = sum(r['count'] for r in results if r['status'] == 'success')
    
    print(f"✅ Успішно перевірено: {success_count}/{len(districts)}")
    print(f"❌ Помилок: {error_count}/{len(districts)}")
    print(f"📋 Всього знайдено оголошень: {total_listings}")
    
    if success_count > 0:
        print(f"\n✅ Райони з оголошеннями:")
        for r in sorted([r for r in results if r['status'] == 'success' and r['count'] > 0], 
                       key=lambda x: x['count'], reverse=True):
            print(f"   • {r['district']:15} - {r['count']:3} оголошень")
    
    empty_districts = [r for r in results if r['status'] == 'success' and r['count'] == 0]
    if empty_districts:
        print(f"\n⚠️  Райони без оголошень (назва вірна, але немає результатів):")
        for r in empty_districts:
            print(f"   • {r['district']}")
    
    if error_count > 0:
        print(f"\n❌ Райони з помилками (можливо неправильна назва):")
        for r in [r for r in results if r['status'] == 'error']:
            print(f"   • {r['district']:15} - {r['error']}")
    
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

