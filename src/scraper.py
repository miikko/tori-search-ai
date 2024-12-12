from playwright.sync_api import sync_playwright
import random
from datetime import datetime

def scrape_listings(listings_url, limit=0, skip_listing_urls=set()):
    if limit == 0:
        return [], []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(user_agent=f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        page.set_default_timeout(10000)
        urls = _scrape_listing_urls(page, listings_url, limit, skip_listing_urls)
        listings = []
        bad_listings = []
        for url in urls:
            try:
                listings.append(_scrape_listing(page, url))
            except Exception as e:
                bad_listings.append({
                    "url": url,
                    "error": str(e)
                })
        browser.close()
    return listings, bad_listings

def _scrape_listing_urls(page, listings_url, limit=0, skip_listing_urls=set()):
    page.goto(listings_url)
    urls = set()
    page_num = 1
    while len(urls) < limit:
        links_selector = 'div.sf-result-list > article a'
        try:
            page.wait_for_selector(links_selector, timeout=1000)
        except Exception:
            print(f"Ran out of listings after {page_num-1} pages")
            break
        urls_on_page = page.eval_on_selector_all(links_selector, '(elems) => elems.map(e => e.href)')
        urls.update(url for url in urls_on_page if url not in skip_listing_urls)
        page_num += 1
        page.goto(f"{listings_url}&page={page_num}")
    return list(urls)[:limit]

def _scrape_listing(page, url):
    page.goto(url)
    page.wait_for_timeout(random.uniform(0, 1000))
    business_listing = page.locator('div[data-testid="sexy-sidebar"]').is_visible() # :D
    listing = {"url": url, "last_checked": datetime.now().isoformat()}
    listing["title"] = page.locator('h1[data-testid="object-title"]').inner_text()
    listing["about"] = page.locator('section[data-testid="description"]').inner_text()
    price_selector = 'div.mt-24.pb-16 > span.h2' if business_listing else '#tjt-create-offer-button > section > div.mb-24 > p'
    price_str = page.locator(price_selector).inner_text()
    listing["price"] = int(price_str.split()[0])
    listing["address"] = page.locator('span[data-testid="object-address"]').inner_text()
    if business_listing:
        attributeNames = page.locator('dl > div > dt').all_inner_texts()
        attributeValues = page.locator('dl > div > dd').all_inner_texts()
        listing["attributes"] = {name: value for (name, value) in zip(attributeNames, attributeValues)}
    else:
        attributes = page.locator('section[aria-label="Lisätietoja"] > span').all_inner_texts()
        listing["attributes"] = {attr.split(":")[0]: attr.split(":")[1].strip() for attr in attributes}
    imgs = page.locator('ul[data-image] > li > img').all()
    listing["image_urls"] = [img.get_attribute('srcset').split(" ")[0] for img in imgs]
    return listing
