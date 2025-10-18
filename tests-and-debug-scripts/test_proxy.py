#!/usr/bin/env python3
"""
Скрипт для тестування проксі-з'єднання з Otodom
"""

import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Завантажуємо змінні оточення
load_dotenv()

def test_connection(use_proxy=False):
    """Тестує з'єднання з Otodom з/без проксі"""
    
    test_url = "https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie/mazowieckie/warszawa?priceMin=4000&priceMax=6000&roomsNumber=%5B3%5D"
    
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
    
    proxies = None
    if use_proxy:
        proxy_url = os.getenv('PROXY_URL')
        if not proxy_url:
            print("❌ PROXY_URL не встановлено в .env файлі")
            return False
        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        print(f"🔐 Використання проксі: {proxy_url.split('@')[-1] if '@' in proxy_url else proxy_url}")
    else:
        print("🌐 Пряме з'єднання (без проксі)")
    
    print(f"🔍 Тестування з'єднання з Otodom...")
    print(f"URL: {test_url}")
    print()
    
    try:
        # Створюємо сесію
        session = requests.Session()
        if proxies:
            session.proxies.update(proxies)
        
        # Спочатку відвідуємо головну сторінку
        print("1️⃣  Відвідування головної сторінки для отримання cookies...")
        home_response = session.get('https://www.otodom.pl/', headers=headers, timeout=30)
        print(f"   Статус: {home_response.status_code}")
        print(f"   Cookies: {len(session.cookies)} шт.")
        
        if home_response.status_code != 200:
            print(f"❌ Помилка при відвідуванні головної сторінки: {home_response.status_code}")
            return False
        
        # Затримка
        import time
        time.sleep(2)
        
        # Запит до сторінки пошуку
        print("\n2️⃣  Запит до сторінки пошуку...")
        search_headers = headers.copy()
        search_headers['Referer'] = 'https://www.otodom.pl/'
        search_headers['Sec-Fetch-Site'] = 'same-origin'
        
        response = session.get(test_url, headers=search_headers, timeout=30)
        print(f"   Статус: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Успішно отримано відповідь!")
            
            # Перевіряємо контент
            soup = BeautifulSoup(response.content, 'html.parser')
            listing_links = soup.find_all('a', {'data-cy': 'listing-item-link'})
            print(f"   📋 Знайдено оголошень: {len(listing_links)}")
            
            if len(listing_links) > 0:
                print("\n✅ УСПІХ! З'єднання працює!")
                print("\nПерші 3 оголошення:")
                for i, link in enumerate(listing_links[:3], 1):
                    title_elem = link.find('p', {'data-cy': 'listing-item-title'})
                    if title_elem:
                        print(f"  {i}. {title_elem.get_text(strip=True)}")
                return True
            else:
                print("⚠️  Не знайдено оголошень, але з'єднання працює")
                print("Можливо, сторінка завантажилася некоректно")
                # Зберігаємо HTML для аналізу
                with open('debug_proxy_test.html', 'w', encoding='utf-8') as f:
                    f.write(soup.prettify())
                print("💾 HTML збережено у debug_proxy_test.html")
                return False
        elif response.status_code == 403:
            print(f"❌ Помилка 403 Forbidden - доступ заборонено")
            print("Можливі причини:")
            print("  - IP адреса заблокована")
            print("  - Проксі не працює")
            print("  - Потрібен інший проксі-сервер")
            return False
        else:
            print(f"❌ Помилка: статус код {response.status_code}")
            return False
            
    except requests.exceptions.ProxyError as e:
        print(f"❌ Помилка проксі: {e}")
        print("Перевірте:")
        print("  - Правильність URL проксі")
        print("  - Чи працює проксі-сервер")
        print("  - Чи правильні логін/пароль (якщо потрібні)")
        return False
    except requests.exceptions.Timeout as e:
        print(f"❌ Таймаут: {e}")
        print("Проксі занадто повільний або недоступний")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Помилка запиту: {e}")
        return False
    except Exception as e:
        print(f"❌ Несподівана помилка: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_ip():
    """Перевіряє поточну IP адресу"""
    print("\n" + "="*60)
    print("Перевірка IP адреси")
    print("="*60)
    
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=10)
        ip_data = response.json()
        print(f"📍 Ваша IP адреса: {ip_data['ip']}")
        
        # Перевіряємо геолокацію
        geo_response = requests.get(f"https://ipapi.co/{ip_data['ip']}/json/", timeout=10)
        geo_data = geo_response.json()
        print(f"📍 Країна: {geo_data.get('country_name', 'Unknown')}")
        print(f"📍 Місто: {geo_data.get('city', 'Unknown')}")
        print(f"📍 ISP: {geo_data.get('org', 'Unknown')}")
        
    except Exception as e:
        print(f"⚠️  Не вдалося визначити IP: {e}")


if __name__ == '__main__':
    print("="*60)
    print("🧪 ТЕСТ З'ЄДНАННЯ З OTODOM")
    print("="*60)
    
    # Перевіряємо поточну IP
    check_ip()
    
    # Тест без проксі
    print("\n" + "="*60)
    print("ТЕСТ #1: Пряме з'єднання (без проксі)")
    print("="*60)
    direct_success = test_connection(use_proxy=False)
    
    # Тест з проксі (якщо вказано)
    proxy_url = os.getenv('PROXY_URL')
    if proxy_url:
        print("\n" + "="*60)
        print("ТЕСТ #2: З'єднання через проксі")
        print("="*60)
        proxy_success = test_connection(use_proxy=True)
        
        # Підсумок
        print("\n" + "="*60)
        print("ПІДСУМОК")
        print("="*60)
        print(f"Пряме з'єднання: {'✅ Працює' if direct_success else '❌ Не працює'}")
        print(f"Через проксі:    {'✅ Працює' if proxy_success else '❌ Не працює'}")
        
        if not direct_success and proxy_success:
            print("\n💡 РЕКОМЕНДАЦІЯ: Використовуйте проксі для цього сервера")
        elif direct_success and not proxy_success:
            print("\n💡 РЕКОМЕНДАЦІЯ: Проксі не потрібен, пряме з'єднання працює")
        elif direct_success and proxy_success:
            print("\n💡 РЕКОМЕНДАЦІЯ: Обидва варіанти працюють, проксі не обов'язковий")
        else:
            print("\n❌ УВАГА: Обидва варіанти не працюють!")
            print("Спробуйте:")
            print("  1. Інший проксі-сервер")
            print("  2. VPN з польським IP")
            print("  3. Збільшити затримки між запитами")
    else:
        print("\n💡 PROXY_URL не встановлено. Для тестування з проксі додайте в .env:")
        print("   PROXY_URL=http://your-proxy:port")

