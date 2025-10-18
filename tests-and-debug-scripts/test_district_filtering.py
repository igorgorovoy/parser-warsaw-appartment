#!/usr/bin/env python3
"""
Тестовий скрипт для перевірки фільтрації районів
"""

import os
from dotenv import load_dotenv

def test_district_filtering():
    """Тестуємо фільтрацію районів"""
    
    load_dotenv()
    
    print("🧪 ТЕСТУВАННЯ ФІЛЬТРАЦІЇ РАЙОНІВ")
    print("=" * 60)
    
    # Перевіряємо налаштування
    district_name = os.getenv('DISTRICT_NAME', '')
    otodom_district = os.getenv('OTODOM_DISTRICT', '')
    
    print(f"📋 Поточні налаштування:")
    print(f"   DISTRICT_NAME: {district_name}")
    print(f"   OTODOM_DISTRICT: {otodom_district}")
    
    # Парсимо райони
    olx_districts = [d.strip() for d in district_name.split(',') if d.strip()]
    otodom_districts = [d.strip() for d in otodom_district.split(',') if d.strip()]
    
    print(f"\n📍 Райони для OLX: {olx_districts}")
    print(f"📍 Райони для Otodom: {otodom_districts}")
    
    # Перевіряємо чи включені райони Ursynów
    ursynow_areas = ['ursynow', 'kabaty', 'natolin', 'imielin', 'stoklosy']
    
    print(f"\n🏘️  Перевірка районів Ursynów:")
    for area in ursynow_areas:
        in_olx = area in olx_districts
        in_otodom = area in otodom_districts
        status_olx = "✅" if in_olx else "❌"
        status_otodom = "✅" if in_otodom else "❌"
        print(f"   {area.capitalize()}: OLX {status_olx} | Otodom {status_otodom}")
    
    # Тестуємо логіку фільтрації
    print(f"\n🔍 Тестування логіки фільтрації:")
    
    test_locations = [
        "Wola, Warszawa",
        "Ursynow, Warszawa", 
        "Kabaty, Warszawa",
        "Natolin, Warszawa",
        "Imielin, Warszawa",
        "Stoklosy, Warszawa",
        "Mokotow, Warszawa",
        "Srodmiescie, Warszawa"
    ]
    
    for location in test_locations:
        location_lower = location.lower()
        
        # Тестуємо OLX фільтрацію
        olx_match = False
        for district in olx_districts:
            if district.lower() in location_lower:
                olx_match = True
                break
        
        # Тестуємо Otodom фільтрацію  
        otodom_match = False
        for district in otodom_districts:
            if district.lower() in location_lower:
                otodom_match = True
                break
        
        olx_status = "✅" if olx_match else "⏭️"
        otodom_status = "✅" if otodom_match else "⏭️"
        
        print(f"   {location}: OLX {olx_status} | Otodom {otodom_status}")
    
    print("\n" + "=" * 60)
    print("🏁 ТЕСТУВАННЯ ЗАВЕРШЕНО")

if __name__ == '__main__':
    test_district_filtering()
