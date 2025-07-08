import asyncio
import httpx
from bs4 import BeautifulSoup
import json
from typing import List, Dict, Optional

from app.models import ProductResult
from app.search_engines import get_currency

# More sophisticated headers to mimic a real browser visit
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.google.com/',
    'DNT': '1',
    'Upgrade-Insecure-Requests': '1',
}

def get_product_similarity(query: str, product_name: str) -> float:
    """Calculates a similarity score to ensure product relevance."""
    if not product_name:
        return 0.0
    query_tokens = set(query.lower().split())
    product_tokens = set(product_name.lower().split())
    if not product_tokens:
        return 0.0
    intersection = len(query_tokens.intersection(product_tokens))
    # Give more weight to matching the query terms
    return intersection / len(query_tokens)

async def extract_from_json_ld(soup: BeautifulSoup, url: str) -> Optional[dict]:
    """Extracts product data from JSON-LD structured data, which is the most reliable source."""
    scripts = soup.find_all('script', type='application/ld+json')
    for script in scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, list):
                data = data[0] if data else None
            
            if data and data.get('@type') == 'Product':
                offers = data.get('offers', {})
                if isinstance(offers, list):
                    offers = offers[0] if offers else {}

                price = offers.get('price') or offers.get('lowPrice')
                if price:
                    # FIX: Return a complete dictionary ready for the Pydantic model
                    return {
                        "link": data.get('url', url),
                        "price": str(price),
                        "currency": offers.get('priceCurrency'),
                        "productName": data.get('name', '').strip()
                    }
        except (json.JSONDecodeError, TypeError, IndexError):
            continue
    return None

async def scrape_site(client: httpx.AsyncClient, url: str, query: str, site_name: str, country: str) -> Optional[ProductResult]:
    """Scrapes a single website for product information using httpx."""
    try:
        print(f"-> Scraping {site_name}...")
        response = await client.get(url, follow_redirects=True, timeout=20.0) # Increased timeout
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'lxml')
        structured_data = await extract_from_json_ld(soup, url)
        
        if structured_data and get_product_similarity(query, structured_data['productName']) >= 0.5:
            # FIX: Ensure currency is set if not found in structured data, then create the ProductResult
            if not structured_data.get('currency'):
                structured_data['currency'] = get_currency(country)
            
            return ProductResult(**structured_data, source=site_name)
            
        print(f"-> No relevant product found on {site_name}.")
        return None
        
    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP Error for {site_name}: Status {e.response.status_code}")
        return None
    except httpx.TimeoutException:
        print(f"❌ Timeout error scraping {site_name}.")
        return None
    except Exception as e:
        print(f"❌ Unexpected error for {site_name}: {e}")
        return None

async def fetch_prices(country: str, query: str, search_urls: List[Dict[str, str]]) -> List[ProductResult]:
    """Manages all scraping tasks and returns the collected results."""
    print(f"\n--- Starting to fetch prices for '{query}' in {country} ---")
    async with httpx.AsyncClient(headers=HEADERS, verify=False) as client: # Added verify=False for flexibility
        tasks = [scrape_site(client, item['url'], query, item['name'], country) for item in search_urls]
        results = await asyncio.gather(*tasks)

    valid_results = [res for res in results if res]
    print(f"--- Finished fetching. Found {len(valid_results)} valid prices. ---")
    
    unique_results = []
    seen = set()
    for result in valid_results:
        key = (result.productName.lower().strip(), result.price)
        if key not in seen:
            unique_results.append(result)
            seen.add(key)
            
    unique_results.sort(key=lambda x: float(x.price))
    return unique_results[:25]