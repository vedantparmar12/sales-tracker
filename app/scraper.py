import asyncio
import httpx
from bs4 import BeautifulSoup
import json
import re
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse

from app.models import ProductResult
from app.search_engines import get_currency

# Rotate user agents to avoid detection
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
]

def get_headers(user_agent_index: int = 0) -> dict:
    """Get headers with rotating user agent."""
    return {
        'User-Agent': USER_AGENTS[user_agent_index % len(USER_AGENTS)],
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }

def extract_price_from_text(text: str) -> Optional[Tuple[str, str]]:
    """Extract price and currency from text using regex patterns."""
    if not text:
        return None
    
    # Common currency symbols and codes
    currency_patterns = {
        '$': 'USD', '₹': 'INR', '£': 'GBP', '€': 'EUR', '¥': 'JPY', 
        'C$': 'CAD', 'A$': 'AUD', '元': 'CNY', 'USD': 'USD', 'INR': 'INR'
    }
    
    # Price patterns to match
    patterns = [
        r'(?:(?:US\s*)?[$]|USD)\s*([0-9,]+(?:\.[0-9]{2})?)',  # $999.99 or USD 999.99
        r'(?:₹|Rs\.?|INR)\s*([0-9,]+(?:\.[0-9]{2})?)',        # ₹999 or Rs.999
        r'(?:£|GBP)\s*([0-9,]+(?:\.[0-9]{2})?)',               # £999.99
        r'(?:€|EUR)\s*([0-9,]+(?:\.[0-9]{2})?)',               # €999.99
        r'([0-9,]+(?:\.[0-9]{2})?)\s*(?:USD|EUR|GBP|INR|JPY|CAD|AUD|CNY)',  # 999.99 USD
        r'\b([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?)\b',     # Generic number pattern
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            price = match.group(1).replace(',', '')
            # Determine currency
            for symbol, code in currency_patterns.items():
                if symbol in text:
                    return (price, code)
            # Default to USD if no currency found
            return (price, 'USD')
    
    return None

def get_product_similarity(query: str, product_name: str) -> float:
    """Enhanced similarity calculation."""
    if not product_name:
        return 0.0
    
    query_lower = query.lower()
    product_lower = product_name.lower()
    
    # Direct substring match gets high score
    if query_lower in product_lower:
        return 1.0
    
    # Token-based matching
    query_tokens = set(query_lower.split())
    product_tokens = set(product_lower.split())
    
    if not query_tokens:
        return 0.0
    
    # Count matching tokens
    matches = len(query_tokens.intersection(product_tokens))
    
    # Check for important tokens (numbers, model names)
    important_tokens = [t for t in query_tokens if any(c.isdigit() for c in t)]
    important_matches = sum(1 for t in important_tokens if t in product_lower)
    
    # Calculate score
    base_score = matches / len(query_tokens)
    importance_bonus = important_matches * 0.3
    
    return min(base_score + importance_bonus, 1.0)

async def extract_from_json_ld(soup: BeautifulSoup, url: str) -> Optional[dict]:
    """Extract product data from JSON-LD structured data."""
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
                    return {
                        "link": data.get('url', url),
                        "price": str(price),
                        "currency": offers.get('priceCurrency', 'USD'),
                        "productName": data.get('name', '').strip(),
                        "availability": offers.get('availability', '')
                    }
        except (json.JSONDecodeError, TypeError, IndexError):
            continue
    return None

async def extract_from_meta_tags(soup: BeautifulSoup, url: str) -> Optional[dict]:
    """Extract product info from meta tags (Open Graph, Twitter Cards)."""
    product_name = None
    price = None
    currency = None
    
    # Try Open Graph tags
    og_title = soup.find('meta', property='og:title')
    if og_title:
        product_name = og_title.get('content', '')
    
    # Try product:price:amount
    price_meta = soup.find('meta', property='product:price:amount')
    if price_meta:
        price = price_meta.get('content', '')
    
    # Try product:price:currency
    currency_meta = soup.find('meta', property='product:price:currency')
    if currency_meta:
        currency = currency_meta.get('content', '')
    
    # Try twitter:data tags
    if not price:
        for i in range(1, 3):
            label = soup.find('meta', {'name': f'twitter:label{i}'})
            if label and 'price' in label.get('content', '').lower():
                data = soup.find('meta', {'name': f'twitter:data{i}'})
                if data:
                    price_data = extract_price_from_text(data.get('content', ''))
                    if price_data:
                        price, currency = price_data
                        break
    
    if product_name and price:
        return {
            "link": url,
            "price": price,
            "currency": currency or 'USD',
            "productName": product_name
        }
    
    return None

async def extract_from_html_patterns(soup: BeautifulSoup, url: str, query: str) -> Optional[dict]:
    """Extract product info using common HTML patterns."""
    product_data = {}
    
    # Extract product name
    name_selectors = [
        'h1', 
        '[class*="product-title"]', '[class*="product-name"]', '[class*="item-title"]',
        '[itemprop="name"]', '[data-testid*="product-title"]', '.product_title',
        '#productTitle', '.product-name', '.item-name'
    ]
    
    for selector in name_selectors:
        element = soup.select_one(selector)
        if element:
            text = element.get_text(strip=True)
            if text and len(text) > 5:
                product_data['productName'] = text
                break
    
    # Extract price
    price_selectors = [
        '[class*="price"]', '[class*="Price"]', '[class*="cost"]',
        '[itemprop="price"]', '[data-price]', '.price', '.Price',
        'span[class*="price"]', 'div[class*="price"]', '.product-price',
        '[data-testid*="price"]', '.priceView-customer-price-number'
    ]
    
    price_found = None
    currency_found = None
    
    for selector in price_selectors:
        elements = soup.select(selector)
        for element in elements:
            text = element.get_text(strip=True)
            price_data = extract_price_from_text(text)
            if price_data:
                price_found, currency_found = price_data
                break
        if price_found:
            break
    
    # Also check data attributes
    if not price_found:
        for element in soup.find_all(attrs={'data-price': True}):
            price_found = element.get('data-price', '')
            if price_found:
                break
    
    if price_found:
        product_data['price'] = price_found
        product_data['currency'] = currency_found or 'USD'
    
    # Only return if we have both name and price
    if product_data.get('productName') and product_data.get('price'):
        product_data['link'] = url
        return product_data
    
    return None

async def extract_amazon_data(soup: BeautifulSoup, url: str) -> Optional[dict]:
    """Special handling for Amazon pages."""
    product_data = {}
    
    # Amazon-specific selectors
    title = soup.select_one('#productTitle, [data-hook="product-link"], .product-title')
    if title:
        product_data['productName'] = title.get_text(strip=True)
    
    # Price extraction for Amazon
    price_selectors = [
        '.a-price-whole', '.a-price.a-text-price.a-size-medium',
        '[data-a-color="price"] .a-offscreen', '.a-price-range',
        '#priceblock_dealprice', '#priceblock_ourprice'
    ]
    
    for selector in price_selectors:
        element = soup.select_one(selector)
        if element:
            text = element.get_text(strip=True)
            price_match = re.search(r'[\d,]+\.?\d*', text)
            if price_match:
                product_data['price'] = price_match.group().replace(',', '')
                product_data['currency'] = 'USD'  # Default, should be determined by country
                break
    
    if product_data.get('productName') and product_data.get('price'):
        product_data['link'] = url
        return product_data
    
    return None

async def scrape_site(client: httpx.AsyncClient, url: str, query: str, site_name: str, country: str, index: int) -> Optional[ProductResult]:
    """Enhanced scraping with multiple extraction methods."""
    try:
        print(f"-> Scraping {site_name} (attempt {index + 1})...")
        
        # Special headers for specific sites
        headers = get_headers(index)
        domain = urlparse(url).netloc.lower()
        
        if 'amazon' in domain:
            headers['Referer'] = 'https://www.amazon.com/'
        elif 'bestbuy' in domain:
            headers['Referer'] = 'https://www.bestbuy.com/'
        
        response = await client.get(
            url, 
            headers=headers,
            follow_redirects=True, 
            timeout=30.0
        )
        
        if response.status_code != 200:
            print(f"❌ HTTP Error for {site_name}: Status {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, 'lxml')
        
        # Try multiple extraction methods
        product_data = None
        
        # 1. Try JSON-LD first (most reliable)
        product_data = await extract_from_json_ld(soup, url)
        
        # 2. Try meta tags
        if not product_data:
            product_data = await extract_from_meta_tags(soup, url)
        
        # 3. Try Amazon-specific extraction
        if not product_data and 'amazon' in domain:
            product_data = await extract_amazon_data(soup, url)
        
        # 4. Try generic HTML patterns
        if not product_data:
            product_data = await extract_from_html_patterns(soup, url, query)
        
        # Validate and create result
        if product_data:
            similarity = get_product_similarity(query, product_data.get('productName', ''))
            print(f"   Found: {product_data.get('productName', 'Unknown')[:50]}... (similarity: {similarity:.2f})")
            
            if similarity >= 0.3:  # Lower threshold for better coverage
                # Ensure all required fields
                product_data['currency'] = product_data.get('currency') or get_currency(country)
                product_data['source'] = site_name
                
                return ProductResult(**product_data)
        
        print(f"   No relevant product found on {site_name}.")
        return None
        
    except httpx.TimeoutException:
        print(f"❌ Timeout error scraping {site_name}.")
        return None
    except Exception as e:
        print(f"❌ Error scraping {site_name}: {str(e)}")
        return None

async def fetch_prices(country: str, query: str, search_urls: List[Dict[str, str]]) -> List[ProductResult]:
    """Enhanced price fetching with retry logic and better extraction."""
    print(f"\n--- Starting enhanced price fetch for '{query}' in {country} ---")
    
    # Create multiple clients with different settings
    async with httpx.AsyncClient(verify=False) as client:
        tasks = []
        for i, item in enumerate(search_urls):
            # Create task with index for user agent rotation
            task = scrape_site(client, item['url'], query, item['name'], country, i)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
    
    # Filter valid results
    valid_results = [res for res in results if res]
    print(f"\n--- Found {len(valid_results)} valid prices ---")
    
    # Remove duplicates
    unique_results = []
    seen = set()
    for result in valid_results:
        # Create a key based on normalized product name and price
        key = (
            ''.join(result.productName.lower().split())[:30], 
            float(result.price)
        )
        if key not in seen:
            unique_results.append(result)
            seen.add(key)
    
    # Sort by price
    unique_results.sort(key=lambda x: float(x.price))
    
    # Return top results
    return unique_results[:25]
