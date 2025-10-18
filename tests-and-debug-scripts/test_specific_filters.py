#!/usr/bin/env python3
"""
Тест конкретних фільтрів для знаходження який блокує оголошення 7500 zł
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


def test_filter_combination(filters_dict, description):
    """Тест конкретної комбінації фільтрів"""
    base_url = "https://www.olx.pl/nieruchomosci/mieszkania/wynajem/warszawa/q-wola/"
    
    params = []
    for key, value in filters_dict.items():
        if value:
            params.append(f"search[{key}]={value}")
    
    if params:
        search_url = base_url + '?' + '&'.join(params)
    else:
        search_url = base_url
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7',
        'DNT': '1',
        'Connection': 'keep-alive',
    }
    
    print(f"\n🔍 {description}")
    print("-" * 60)
    print(f"Фільтри: {', '.join(params) if params else 'Немає'}")
    
    try:
        response = requests.get(search_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        cards = soup.find_all('div', {'data-cy': 'l-card'})
        
        # Шукаємо оголошення з ціною 7500
        found_7500 = False
        for card in cards:
            price_elem = card.find('p', {'data-testid': 'ad-price'})
            if not price_elem:
                price_elem = card.find('span', class_=lambda x: x and 'price' in x.lower())
            
            if price_elem and ('7500' in price_elem.get_text(strip=True) or '7 500' in price_elem.get_text(strip=True)):
                found_7500 = True
                break
        
        result = "✅ ЗНАЙДЕНО" if found_7500 else "❌ НЕ ЗНАЙДЕНО"
        print(f"📊 Карток: {len(cards)}, Оголошення 7500 zł: {result}")
        
        return found_7500, len(cards)
        
    except Exception as e:
        print(f"❌ Помилка: {e}")
        return False, 0


def main():
    """Головна функція"""
    print("="*80)
    print("🧪 ТЕСТ КОНКРЕТНИХ ФІЛЬТРІВ ДЛЯ ОГОЛОШЕННЯ 7500 ZŁ")
    print("="*80)
    print(f"⏰ Час запуску: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Тести різних комбінацій фільтрів
    tests = [
        ({}, "БЕЗ ФІЛЬТРІВ"),
        ({"filter_float_price:from": "4000", "filter_float_price:to": "8000"}, "ТІЛЬКИ ЦІНА 4000-8000"),
        ({"filter_enum_rooms[0]": "three"}, "ТІЛЬКИ 3 КІМНАТИ"),
        ({"filter_enum_furniture[0]": "yes"}, "ТІЛЬКИ МЕБЛІ"),
        ({"filter_enum_pets[0]": "Tak"}, "ТІЛЬКИ ТВАРИНИ"),
        ({"private_business": "private"}, "ТІЛЬКИ ПРИВАТНІ"),
        ({"filter_float_price:from": "4000", "filter_float_price:to": "8000", "filter_enum_rooms[0]": "three"}, "ЦІНА + 3 КІМНАТИ"),
        ({"filter_float_price:from": "4000", "filter_float_price:to": "8000", "filter_enum_rooms[0]": "three", "filter_enum_furniture[0]": "yes"}, "ЦІНА + 3 КІМНАТИ + МЕБЛІ"),
        ({"filter_float_price:from": "4000", "filter_float_price:to": "8000", "filter_enum_rooms[0]": "three", "filter_enum_pets[0]": "Tak"}, "ЦІНА + 3 КІМНАТИ + ТВАРИНИ"),
        ({"filter_float_price:from": "4000", "filter_float_price:to": "8000", "filter_enum_rooms[0]": "three", "private_business": "private"}, "ЦІНА + 3 КІМНАТИ + ПРИВАТНІ"),
        ({"filter_float_price:from": "4000", "filter_float_price:to": "8000", "filter_enum_rooms[0]": "three", "filter_enum_furniture[0]": "yes", "filter_enum_pets[0]": "Tak"}, "ЦІНА + 3 КІМНАТИ + МЕБЛІ + ТВАРИНИ"),
        ({"filter_float_price:from": "4000", "filter_float_price:to": "8000", "filter_enum_rooms[0]": "three", "filter_enum_furniture[0]": "yes", "filter_enum_pets[0]": "Tak", "private_business": "private"}, "ВСІ ФІЛЬТРИ (поточні налаштування)"),
    ]
    
    results = []
    
    for filters, description in tests:
        found, count = test_filter_combination(filters, description)
        results.append((description, found, count))
        
        # Затримка між запитами
        time.sleep(2)
    
    # Аналіз результатів
    print(f"\n\n" + "="*80)
    print("📊 АНАЛІЗ РЕЗУЛЬТАТІВ")
    print("="*80)
    
    print(f"{'Тест':<50} {'7500 zł':<12} {'Карток'}")
    print("-" * 80)
    
    for description, found, count in results:
        status = "✅" if found else "❌"
        print(f"{description:<50} {status:<12} {count}")
    
    # Знаходимо де зникає оголошення
    print(f"\n🔍 АНАЛІЗ:")
    
    # Знаходимо перший тест де зникає оголошення
    for i, (description, found, count) in enumerate(results):
        if not found and i > 0:  # Не перший тест (без фільтрів)
            prev_found, prev_count = results[i-1][1], results[i-1][2]
            if prev_found:
                print(f"❌ Оголошення зникає при додаванні фільтра: {description}")
                break
    
    # Перевіряємо чи є проблема з конкретними фільтрами
    furniture_test = next((r for r in results if "МЕБЛІ" in r[0] and "ЦІНА" not in r[0]), None)
    pets_test = next((r for r in results if "ТВАРИНИ" in r[0] and "ЦІНА" not in r[0]), None)
    private_test = next((r for r in results if "ПРИВАТНІ" in r[0] and "ЦІНА" not in r[0]), None)
    
    if furniture_test and not furniture_test[1]:
        print(f"❌ Проблема з фільтром МЕБЛІ")
    if pets_test and not pets_test[1]:
        print(f"❌ Проблема з фільтром ТВАРИНИ")
    if private_test and not private_test[1]:
        print(f"❌ Проблема з фільтром ПРИВАТНІ")
    
    print(f"\n💡 РЕКОМЕНДАЦІЇ:")
    print(f"   1. Перевірте оголошення 7500 zł вручну на OLX")
    print(f"   2. Переконайтеся чи воно має меблі/дозволяє тварин/є приватним")
    print(f"   3. Розгляньте послаблення фільтрів для кращого покриття")
    
    print("\n" + "="*80)
    print("🏁 ТЕСТ ЗАВЕРШЕНО")
    print("="*80)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Перервано користувачем")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Критична помилка: {e}")
        sys.exit(1)
