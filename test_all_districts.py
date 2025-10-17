#!/usr/bin/env python3
"""
Детальний тест фільтрації районів для OLX і Otodom
"""

import os
from dotenv import load_dotenv

def test_all_districts():
    """Тестуємо всі райони в обох парсерах"""
    
    load_dotenv()
    
    print("🧪 ДЕТАЛЬНИЙ ТЕСТ ФІЛЬТРАЦІЇ РАЙОНІВ")
    print("=" * 70)
    
    # Отримуємо налаштування
    district_name = os.getenv('DISTRICT_NAME', '')
    otodom_district = os.getenv('OTODOM_DISTRICT', '')
    
    print(f"📋 Налаштування:")
    print(f"   DISTRICT_NAME: {district_name}")
    print(f"   OTODOM_DISTRICT: {otodom_district}")
    print()
    
    # Парсимо райони
    olx_districts = [d.strip() for d in district_name.split(',') if d.strip()]
    otodom_districts = [d.strip() for d in otodom_district.split(',') if d.strip()]
    
    print(f"📍 Райони для OLX: {olx_districts}")
    print(f"📍 Райони для Otodom: {otodom_districts}")
    print()
    
    # Тестуємо кожен район окремо
    print("🔍 ТЕСТУВАННЯ КОЖНОГО РАЙОНУ:")
    print("-" * 70)
    
    # Тестові локації для кожного району
    test_cases = [
        ("wola", "Warszawa, Wola - Dzisiaj o 16:09", "Wola, Warszawa"),
        ("ursynow", "Warszawa, Ursynow - Dzisiaj o 16:09", "Ursynow, Warszawa"),
        ("kabaty", "Warszawa, Kabaty - Dzisiaj o 16:09", "Kabaty, Warszawa"),
        ("natolin", "Warszawa, Natolin - Dzisiaj o 16:09", "Natolin, Warszawa"),
        ("imielin", "Warszawa, Imielin - Dzisiaj o 16:09", "Imielin, Warszawa"),
        ("stoklosy", "Warszawa, Stoklosy - Dzisiaj o 16:09", "Stoklosy, Warszawa"),
    ]
    
    for district_key, olx_location, otodom_location in test_cases:
        print(f"\n🏘️  Район: {district_key.upper()}")
        
        # Тестуємо OLX
        olx_location_lower = olx_location.lower()
        olx_is_warsaw = 'warszawa' in olx_location_lower or 'warsaw' in olx_location_lower
        
        olx_district_match = False
        if ',' in olx_location_lower:
            parts = olx_location_lower.split(',')
            if len(parts) >= 2:
                district_part = parts[1].strip().split(' - ')[0]
                olx_district_match = any(d.lower() in district_part for d in olx_districts)
        
        olx_result = "✅" if (olx_is_warsaw and olx_district_match) else "❌"
        
        # Тестуємо Otodom
        otodom_location_lower = otodom_location.lower()
        otodom_is_warsaw = 'warszawa' in otodom_location_lower or 'warsaw' in otodom_location_lower
        otodom_district_match = any(d.lower() in otodom_location_lower for d in otodom_districts)
        
        otodom_result = "✅" if (otodom_is_warsaw and otodom_district_match) else "❌"
        
        print(f"   OLX:    {olx_location} → {olx_result}")
        print(f"   Otodom: {otodom_location} → {otodom_result}")
        
        # Перевіряємо чи район в налаштуваннях
        in_olx_config = district_key in olx_districts
        in_otodom_config = district_key in otodom_districts
        
        print(f"   В налаштуваннях: OLX {'✅' if in_olx_config else '❌'} | Otodom {'✅' if in_otodom_config else '❌'}")
    
    print("\n" + "=" * 70)
    
    # Тестуємо негативні випадки
    print("🚫 ТЕСТУВАННЯ НЕГАТИВНИХ ВИПАДКІВ:")
    print("-" * 70)
    
    negative_cases = [
        ("Sosnowiec, Centrum - Dzisiaj o 16:09", "Sosnowiec, Slaskie"),
        ("Krakow, Stare Miasto - Dzisiaj o 16:09", "Krakow, Malopolskie"),
        ("Warszawa, Mokotow - Dzisiaj o 16:09", "Mokotow, Warszawa"),
        ("Warszawa, Srodmiescie - Dzisiaj o 16:09", "Srodmiescie, Warszawa"),
    ]
    
    for olx_neg, otodom_neg in negative_cases:
        print(f"\n❌ Негативний тест:")
        
        # OLX негативний тест
        olx_neg_lower = olx_neg.lower()
        olx_neg_is_warsaw = 'warszawa' in olx_neg_lower or 'warsaw' in olx_neg_lower
        olx_neg_district_match = False
        if ',' in olx_neg_lower:
            parts = olx_neg_lower.split(',')
            if len(parts) >= 2:
                district_part = parts[1].strip().split(' - ')[0]
                olx_neg_district_match = any(d.lower() in district_part for d in olx_districts)
        
        olx_neg_result = "⏭️" if not (olx_neg_is_warsaw and olx_neg_district_match) else "❌ ПРОБЛЕМА!"
        
        # Otodom негативний тест
        otodom_neg_lower = otodom_neg.lower()
        otodom_neg_is_warsaw = 'warszawa' in otodom_neg_lower or 'warsaw' in otodom_neg_lower
        otodom_neg_district_match = any(d.lower() in otodom_neg_lower for d in otodom_districts)
        
        otodom_neg_result = "⏭️" if not (otodom_neg_is_warsaw and otodom_neg_district_match) else "❌ ПРОБЛЕМА!"
        
        print(f"   OLX:    {olx_neg} → {olx_neg_result}")
        print(f"   Otodom: {otodom_neg} → {otodom_neg_result}")
    
    print("\n" + "=" * 70)
    print("🏁 ТЕСТУВАННЯ ЗАВЕРШЕНО")
    print()
    print("💡 Очікуваний результат:")
    print("   ✅ Всі райони з налаштувань повинні проходити фільтр")
    print("   ⏭️  Негативні випадки повинні відфільтровуватися")

if __name__ == '__main__':
    test_all_districts()
