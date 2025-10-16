#!/usr/bin/env python3
"""
Тестовий скрипт для перевірки заголовків Otodom
"""

import requests
from bs4 import BeautifulSoup

# Тестуємо базову URL Otodom з новими заголовками
test_url = "https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie/mazowieckie/warszawa?priceMin=4000&priceMax=6000&roomsNumber=%5B3%5D"

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
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

print("🔍 Тестуємо з'єднання з Otodom...")
print(f"URL: {test_url}")
print()

try:
    response = requests.get(test_url, headers=headers, timeout=30)
    print(f"✅ Статус код: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Успішно отримано відповідь!")
        
        # Перевіряємо чи є контент
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Шукаємо оголошення
        listing_links = soup.find_all('a', {'data-cy': 'listing-item-link'})
        print(f"📋 Знайдено оголошень: {len(listing_links)}")
        
        if len(listing_links) > 0:
            print("\n✅ УСПІХ! Otodom тепер працює з новими заголовками!")
            print("\nПерші 3 оголошення:")
            for i, link in enumerate(listing_links[:3], 1):
                title_elem = link.find('p', {'data-cy': 'listing-item-title'})
                if title_elem:
                    print(f"  {i}. {title_elem.get_text(strip=True)}")
        else:
            print("⚠️  Не знайдено оголошень, але з'єднання працює")
    else:
        print(f"❌ Помилка: статус код {response.status_code}")
        
except requests.exceptions.HTTPError as e:
    print(f"❌ HTTP помилка: {e}")
except requests.exceptions.RequestException as e:
    print(f"❌ Помилка запиту: {e}")
except Exception as e:
    print(f"❌ Несподівана помилка: {e}")

