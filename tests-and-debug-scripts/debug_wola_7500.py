#!/usr/bin/env python3
"""
Детальний дебаг для оголошення з Wola на 7500 zł
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


def test_wola_without_filters():
    """Тест Wola без фільтрів"""
    base_url = "https://www.olx.pl/nieruchomosci/mieszkania/wynajem/warszawa/q-wola/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7',
        'DNT': '1',
        'Connection': 'keep-alive',
    }
    
    print("🔍 ТЕСТ WOLA БЕЗ ФІЛЬТРІВ")
    print("="*80)
    print(f"URL: {base_url}")
    
    try:
        response = requests.get(base_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        cards = soup.find_all('div', {'data-cy': 'l-card'})
        
        print(f"📊 Знайдено карток: {len(cards)}")
        
        # Шукаємо оголошення з ціною близькою до 7500
        target_listings = []
        
        for i, card in enumerate(cards, 1):
            # Ціна
            price_elem = card.find('p', {'data-testid': 'ad-price'})
            if not price_elem:
                price_elem = card.find('span', class_=lambda x: x and 'price' in x.lower())
            
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                
                # Перевіряємо чи є 7500 в ціні
                if '7500' in price_text or '7 500' in price_text:
                    # Заголовок
                    title_elem = card.find('h4')
                    if not title_elem:
                        title_elem = card.find('h6')
                    
                    title = title_elem.get_text(strip=True) if title_elem else 'No title'
                    
                    # Локація
                    location_elem = card.find('p', {'data-testid': 'location-date'})
                    location = location_elem.get_text(strip=True) if location_elem else 'No location'
                    
                    # URL
                    link_elem = card.find('a', href=True)
                    url = link_elem['href'] if link_elem else 'No URL'
                    if url and not url.startswith('http'):
                        url = 'https://www.olx.pl' + url
                    
                    target_listings.append({
                        'position': i,
                        'title': title,
                        'price': price_text,
                        'location': location,
                        'url': url
                    })
        
        print(f"\n🎯 Знайдено оголошень з ціною ~7500 zł: {len(target_listings)}")
        
        for listing in target_listings:
            print(f"\n{listing['position']}. {listing['title']}")
            print(f"   💰 Ціна:     {listing['price']}")
            print(f"   📍 Локація:  {listing['location']}")
            print(f"   🔗 URL:      {listing['url'][:80]}...")
        
        # Також покажемо всі ціни для аналізу
        print(f"\n💰 ВСІ ЦІНИ В РЕЗУЛЬТАТАХ:")
        print("-" * 50)
        all_prices = []
        for card in cards:
            price_elem = card.find('p', {'data-testid': 'ad-price'})
            if not price_elem:
                price_elem = card.find('span', class_=lambda x: x and 'price' in x.lower())
            
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                all_prices.append(price_text)
        
        # Сортуємо ціни
        unique_prices = list(set(all_prices))
        unique_prices.sort()
        
        for price in unique_prices:
            count = all_prices.count(price)
            print(f"   {price} - {count} оголошень")
        
        return len(target_listings) > 0
        
    except Exception as e:
        print(f"❌ Помилка: {e}")
        return False


def test_wola_with_current_filters():
    """Тест Wola з поточними фільтрами"""
    base_url = "https://www.olx.pl/nieruchomosci/mieszkania/wynajem/warszawa/q-wola/"
    
    params = []
    
    # Поточні фільтри з .env
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
    
    price_to = os.getenv('PRICE_TO', '8000')
    if price_to:
        params.append(f"search[filter_float_price:to]={price_to}")
    
    listing_type = os.getenv('LISTING_TYPE', 'private')
    if listing_type:
        params.append(f"search[private_business]={listing_type}")
    
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
    
    print(f"\n🔍 ТЕСТ WOLA З ПОТОЧНИМИ ФІЛЬТРАМИ")
    print("="*80)
    print(f"URL: {search_url}")
    print(f"Фільтри: {', '.join(params)}")
    
    try:
        response = requests.get(search_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        cards = soup.find_all('div', {'data-cy': 'l-card'})
        
        print(f"📊 Знайдено карток з фільтрами: {len(cards)}")
        
        # Шукаємо оголошення з ціною близькою до 7500
        target_listings = []
        
        for i, card in enumerate(cards, 1):
            # Ціна
            price_elem = card.find('p', {'data-testid': 'ad-price'})
            if not price_elem:
                price_elem = card.find('span', class_=lambda x: x and 'price' in x.lower())
            
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                
                # Перевіряємо чи є 7500 в ціні
                if '7500' in price_text or '7 500' in price_text:
                    # Заголовок
                    title_elem = card.find('h4')
                    if not title_elem:
                        title_elem = card.find('h6')
                    
                    title = title_elem.get_text(strip=True) if title_elem else 'No title'
                    
                    # Локація
                    location_elem = card.find('p', {'data-testid': 'location-date'})
                    location = location_elem.get_text(strip=True) if location_elem else 'No location'
                    
                    # URL
                    link_elem = card.find('a', href=True)
                    url = link_elem['href'] if link_elem else 'No URL'
                    if url and not url.startswith('http'):
                        url = 'https://www.olx.pl' + url
                    
                    target_listings.append({
                        'position': i,
                        'title': title,
                        'price': price_text,
                        'location': location,
                        'url': url
                    })
        
        print(f"\n🎯 Знайдено оголошень з ціною ~7500 zł (з фільтрами): {len(target_listings)}")
        
        for listing in target_listings:
            print(f"\n{listing['position']}. {listing['title']}")
            print(f"   💰 Ціна:     {listing['price']}")
            print(f"   📍 Локація:  {listing['location']}")
            print(f"   🔗 URL:      {listing['url'][:80]}...")
        
        return len(target_listings) > 0
        
    except Exception as e:
        print(f"❌ Помилка: {e}")
        return False


def main():
    """Головна функція"""
    print("="*80)
    print("🧪 ДЕТАЛЬНИЙ ДЕБАГ ОГОЛОШЕННЯ З WOLA 7500 ZŁ")
    print("="*80)
    print(f"⏰ Час запуску: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Поточні фільтри
    print(f"\n📋 Поточні фільтри:")
    print(f"   Кімнати:        {os.getenv('ROOMS', 'three')}")
    print(f"   Ціна:           {os.getenv('PRICE_FROM', '4000')} - {os.getenv('PRICE_TO', '8000')} PLN")
    print(f"   Меблі:          {os.getenv('FURNITURE', 'yes')}")
    print(f"   Тварини:        {os.getenv('PETS', 'Tak')}")
    print(f"   Тип оголошення: {os.getenv('LISTING_TYPE', 'private')}")
    
    # Тест 1: Без фільтрів
    found_without_filters = test_wola_without_filters()
    
    # Затримка
    time.sleep(3)
    
    # Тест 2: З фільтрами
    found_with_filters = test_wola_with_current_filters()
    
    # Висновки
    print(f"\n\n" + "="*80)
    print("📊 ВИСНОВКИ")
    print("="*80)
    
    if found_without_filters and not found_with_filters:
        print("❌ ПРОБЛЕМА ЗНАЙДЕНА!")
        print("   Оголошення з ціною 7500 zł є БЕЗ фільтрів")
        print("   Але ЗНИКАЄ з фільтрами")
        print("   🔍 Можливі причини:")
        print("      - Фільтр по меблях (furniture=yes)")
        print("      - Фільтр по тваринах (pets=Tak)")
        print("      - Фільтр по типі оголошення (private)")
    elif found_without_filters and found_with_filters:
        print("✅ Оголошення знайдено в обох тестах")
        print("   Проблема може бути в парсингу або відправці в Slack")
    elif not found_without_filters:
        print("⚠️  Оголошення не знайдено навіть без фільтрів")
        print("   Можливо оголошення вже видалено або змінилося")
    else:
        print("🤔 Неочікуваний результат")
    
    print("\n" + "="*80)
    print("🏁 ДЕБАГ ЗАВЕРШЕНО")
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
