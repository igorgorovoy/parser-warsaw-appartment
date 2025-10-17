#!/usr/bin/env python3
"""
Тестовий скрипт для перевірки фільтрів парсерів
"""

import os
from dotenv import load_dotenv

def test_filters():
    """Тестуємо фільтри парсерів"""
    
    load_dotenv()
    
    print("🧪 ТЕСТУВАННЯ ФІЛЬТРІВ ПАРСЕРІВ")
    print("=" * 60)
    
    # Тестуємо OLX фільтрацію
    print("🔍 OLX Фільтрація:")
    
    test_locations_olx = [
        "Warszawa, Wola - Dzisiaj o 16:09",
        "Warszawa, Ursynow - Dzisiaj o 16:09", 
        "Warszawa, Kabaty - Dzisiaj o 16:09",
        "Sosnowiec, Centrum - Dzisiaj o 16:09",  # Не Варшава
        "Krakow, Stare Miasto - Dzisiaj o 16:09",  # Не Варшава
        "Warszawa, Mokotow - Dzisiaj o 16:09",  # Не в списку районів
    ]
    
    district_name = os.getenv('DISTRICT_NAME', '')
    filter_districts = [d.strip() for d in district_name.split(',') if d.strip()]
    
    for location in test_locations_olx:
        location_lower = location.lower()
        
        # Перевірка на Варшаву
        is_warsaw = 'warszawa' in location_lower or 'warsaw' in location_lower
        
        # Перевірка на район
        district_match = False
        if ',' in location_lower:
            parts = location_lower.split(',')
            if len(parts) >= 2:
                district_part = parts[1].strip().split(' - ')[0]
                district_match = any(district.lower() in district_part for district in filter_districts)
        
        # Результат
        if not is_warsaw:
            result = "❌ Не Варшава"
        elif not district_match:
            result = "⏭️  Не в списку районів"
        else:
            result = "✅ Підходить"
        
        print(f"   {location}: {result}")
    
    print()
    
    # Тестуємо Otodom фільтрацію
    print("🔍 Otodom Фільтрація:")
    
    test_districts_otodom = [
        "Wola, Warszawa",
        "Ursynow, Warszawa",
        "Kabaty, Warszawa", 
        "Sosnowiec, Slaskie",  # Не Варшава
        "Krakow, Malopolskie",  # Не Варшава
        "Mokotow, Warszawa",  # Не в списку районів
    ]
    
    otodom_districts = os.getenv('OTODOM_DISTRICT', '')
    expected_districts = [d.strip() for d in otodom_districts.split(',') if d.strip()]
    
    for district in test_districts_otodom:
        district_lower = district.lower()
        
        # Перевірка на Варшаву
        is_warsaw = 'warszawa' in district_lower or 'warsaw' in district_lower
        
        # Перевірка на район
        district_match = any(exp_district.lower() in district_lower for exp_district in expected_districts)
        
        # Результат
        if not is_warsaw:
            result = "❌ Не Варшава"
        elif not district_match:
            result = "⏭️  Не в списку районів"
        else:
            result = "✅ Підходить"
        
        print(f"   {district}: {result}")
    
    print()
    print("=" * 60)
    print("🏁 ТЕСТУВАННЯ ЗАВЕРШЕНО")
    print()
    print("💡 Очікуваний результат:")
    print("   - Тільки оголошення з Варшави")
    print("   - Тільки з дозволених районів")
    print("   - Неповідомлення з інших міст (Sosnowiec, Kraków)")

if __name__ == '__main__':
    test_filters()
