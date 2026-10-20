from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import time
import re


def main():
    base_url = "https://ek.ua/ua/list/157/"
    all_offers = []

    print("Починаємо збір даних про монітори з ek.ua (Playwright + BeautifulSoup)...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()

        for page_num in range(5):
            url = base_url if page_num == 0 else f"{base_url}{page_num}/"
            print(f"Парсинг сторінки {page_num + 1}: {url}")

            try:
                page.goto(url, timeout=60000, wait_until="domcontentloaded")
                time.sleep(3)

                page.wait_for_selector('.model-short-div', timeout=15000)

                html_content = page.content()
                soup = BeautifulSoup(html_content, 'html.parser')

                items = soup.select('.model-short-div')

                products_data = []
                for item in items:
                    title_elem = item.select_one('.model-short-title')
                    if title_elem:
                        model_name = title_elem.get_text(strip=True)
                        href = title_elem.get('href')

                        desc_elem = item.select_one('.m-s-f2')
                        description = desc_elem.get_text(strip=True) if desc_elem else "Немає опису"

                        if href:
                            full_url = href if href.startswith('http') else f"https://ek.ua{href}"
                            products_data.append({
                                "url": full_url,
                                "model": model_name,
                                "description": description
                            })

            except Exception as e:
                print(f"Помилка на сторінці каталогу {url}: {e}")
                continue
            for product in products_data[:5]:
                try:
                    page.goto(product["url"], timeout=60000, wait_until="domcontentloaded")
                    time.sleep(2)

                    prod_html = page.content()
                    prod_soup = BeautifulSoup(prod_html, 'html.parser')
                    shop_rows = prod_soup.select('.where-buy-table tr, .where-buy-row')

                    for row in shop_rows:
                        shop_elem = row.select_one('.it-shop, .shop-title')
                        if not shop_elem:
                            continue
                        shop_name = shop_elem.get_text(strip=True)

                        price_elem = row.select_one('.where-buy-price, .shop-price')
                        price_text = price_elem.get_text(strip=True) if price_elem else ""

                        price_match = re.sub(r'[^0-9]', '', price_text)

                        if price_match and shop_name:
                            offer = {
                                "model": product["model"],
                                "description": product["description"],
                                "city": "Київ",
                                "shop": shop_name,
                                "price": int(price_match)
                            }
                            all_offers.append(offer)

                except Exception as e:
                    print(f"Помилка парсингу товару {product['url']}: {e}")
                    continue

        browser.close()

    output_filename = "monitors_ek_playwright_fixed.json"
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(all_offers, f, ensure_ascii=False, indent=4)

    print(f"Збір даних завершено. Збережено {len(all_offers)} пропозицій у файл {output_filename}")


if __name__ == '__main__':
    main()