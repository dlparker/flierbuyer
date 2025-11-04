# src/flierbuyer/scrape_yachtworld.py
from playwright.sync_api import sync_playwright
import json, re, time
from hashlib import md5

def scrape_yachtworld(model_query: str):
    base = "https://www.yachtworld.com"
    url = f"{base}/boats-for-sale/make-corsair/model-{model_query}/"
    print(f"Scraping → {url}")

    listings = []

    with sync_playwright() as p:
        # Launch with stealth
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1920, "height": 1080},
            java_script_enabled=True,
            bypass_csp=True,
        )

        # Stealth: hide automation
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => false});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            window.chrome = { runtime: {}, app: {}, loadTimes: () => {} };
        """)

        page = context.new_page()

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=90000)
            page.wait_for_timeout(7000)  # Let JS + Cloudflare run
            page.wait_for_selector("a.grid-listing-link", timeout=30000)
        except Exception as e:
            print(f"Page load failed: {e}")
            browser.close()
            return []

        cards = page.query_selector_all("a.grid-listing-link")
        print(f"Found {len(cards)} card elements")

        for card in cards:
            try:
                link = card.get_attribute("href")
                if link and link.startswith("/"): link = base + link

                title_elem = card.query_selector("h2")
                title = title_elem.inner_text().strip() if title_elem else ""
                if not re.search(r"F-?27|F-?28", title, re.I): continue

                year = int(re.search(r"\b(19|20)\d{2}\b", title).group(0))

                price_elem = card.query_selector("p[class*='listingPrice']")
                price = None
                if price_elem:
                    p = price_elem.inner_text().replace("US$", "").replace("$", "").replace(",", "")
                    if p.replace(".", "").isdigit():
                        price = float(p)

                loc_elem = card.query_selector("p:has-text('|')")
                location = loc_elem.inner_text().split("|")[-1].strip() if loc_elem else ""

                # Detail page
                page2 = context.new_page()
                page2.goto(link, wait_until="domcontentloaded", timeout=60000)
                page2.wait_for_timeout(3000)

                desc_elem = page2.query_selector("div.description, div.details")
                desc = desc_elem.inner_text().lower() if desc_elem else ""
                has_head = any(w in desc for w in ["head", "toilet", "marine head"])
                trailer = "trailer" in desc
                cc = any(w in desc for w in ["center cockpit", "cc"])

                boat_id = md5((link + str(year)).encode()).hexdigest()[:10]
                model = "F27" if "27" in model_query else "F28"

                listings.append({
                    "boat_id": boat_id, "url": link, "model": model, "year": year,
                    "location": location, "price": price,
                    "trailer": "Yes" if trailer else "No",
                    "has_head": "yes" if has_head else "no",
                    "extended_tongue": None,
                    "features": json.dumps({"cc": cc}),
                    "special": "CC" if cc else None,
                    "source_site": "yachtworld.com",
                })

                page2.close()
            except Exception as e:
                print(f"Card parse error: {e}")
                continue

        browser.close()

    print(f"Found {len(listings)} {model_query.upper()} listings")
    return listings
