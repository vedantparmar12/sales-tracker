from typing import Dict, List
from serpapi import GoogleSearch
import os
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

SERPAPI_API_KEY = os.environ.get("SERPAPI_API_KEY")

if not SERPAPI_API_KEY:
    raise ValueError("SERPAPI_API_KEY not found. Please set it in your .env file or as an environment variable.")

# Dictionary to map country codes to the names SerpApi expects
COUNTRY_NAMES = {
    "US": "United States",
    "IN": "India",
    "UK": "United Kingdom",
    "CA": "Canada",
    "AU": "Australia",
    "DE": "Germany",
    "FR": "France",
    "JP": "Japan",
    "CN": "China",
    "BR": "Brazil",
    "MX": "Mexico",
    "ES": "Spain",
    "IT": "Italy",
    "NL": "Netherlands",
    "SE": "Sweden",
    "SG": "Singapore",
    "AE": "United Arab Emirates",
    "SA": "Saudi Arabia",
    "ZA": "South Africa",
    "KR": "South Korea"
}

# Currency mapping
CURRENCY_MAP = {
    "US": "USD", "IN": "INR", "UK": "GBP", "CA": "CAD",
    "AU": "AUD", "DE": "EUR", "FR": "EUR", "JP": "JPY", 
    "CN": "CNY", "BR": "BRL", "MX": "MXN", "ES": "EUR",
    "IT": "EUR", "NL": "EUR", "SE": "SEK", "SG": "SGD",
    "AE": "AED", "SA": "SAR", "ZA": "ZAR", "KR": "KRW"
}

# Google domains by country for better localization
GOOGLE_DOMAINS = {
    "US": "google.com", "IN": "google.co.in", "UK": "google.co.uk",
    "CA": "google.ca", "AU": "google.com.au", "DE": "google.de",
    "FR": "google.fr", "JP": "google.co.jp", "CN": "google.com.hk",
    "BR": "google.com.br", "MX": "google.com.mx", "ES": "google.es",
    "IT": "google.it", "NL": "google.nl", "SE": "google.se",
    "SG": "google.com.sg", "AE": "google.ae", "SA": "google.com.sa",
    "ZA": "google.co.za", "KR": "google.co.kr"
}

async def get_search_urls(country: str, query: str) -> List[Dict[str, str]]:
    """
    Enhanced search to get more shopping results using multiple strategies.
    """
    all_urls = []
    seen_domains = set()
    
    # Strategy 1: Google Shopping Search
    shopping_urls = await search_google_shopping(country, query)
    for url_data in shopping_urls:
        domain = url_data['url'].split('/')[2].lower()
        if domain not in seen_domains:
            all_urls.append(url_data)
            seen_domains.add(domain)
    
    # Strategy 2: Regular Google Search with shopping intent
    if len(all_urls) < 10:
        regular_urls = await search_google_regular(country, query)
        for url_data in regular_urls:
            domain = url_data['url'].split('/')[2].lower()
            if domain not in seen_domains:
                all_urls.append(url_data)
                seen_domains.add(domain)
    
    # Strategy 3: Add known e-commerce sites for the country
    if len(all_urls) < 15:
        ecommerce_urls = get_known_ecommerce_sites(country, query)
        for url_data in ecommerce_urls:
            domain = url_data['url'].split('/')[2].lower()
            if domain not in seen_domains:
                all_urls.append(url_data)
                seen_domains.add(domain)
    
    print(f"\n✅ Total URLs found: {len(all_urls)}")
    return all_urls[:20]  # Return top 20 URLs

async def search_google_shopping(country: str, query: str) -> List[Dict[str, str]]:
    """Search using Google Shopping."""
    location_name = COUNTRY_NAMES.get(country, "United States")
    google_domain = GOOGLE_DOMAINS.get(country, "google.com")
    
    search_params = {
        "q": query,
        "tbm": "shop",  # Google Shopping
        "location": location_name,
        "google_domain": google_domain,
        "api_key": SERPAPI_API_KEY,
        "num": 20
    }
    
    try:
        search = GoogleSearch(search_params)
        results = search.get_dict()
        
        shopping_urls = []
        if "shopping_results" in results:
            for result in results["shopping_results"][:15]:
                if "link" in result:
                    shopping_urls.append({
                        "name": result.get("source", "Unknown"),
                        "url": result["link"]
                    })
        
        print(f"✅ Google Shopping found {len(shopping_urls)} results")
        return shopping_urls
    except Exception as e:
        print(f"❌ Google Shopping search error: {e}")
        return []

async def search_google_regular(country: str, query: str) -> List[Dict[str, str]]:
    """Regular Google search with shopping keywords."""
    location_name = COUNTRY_NAMES.get(country, "United States")
    google_domain = GOOGLE_DOMAINS.get(country, "google.com")
    
    # Add shopping-related keywords
    enhanced_query = f"{query} buy online price shopping"
    
    search_params = {
        "q": enhanced_query,
        "location": location_name,
        "google_domain": google_domain,
        "api_key": SERPAPI_API_KEY,
        "num": 30
    }
    
    try:
        search = GoogleSearch(search_params)
        results = search.get_dict()
        
        shopping_urls = []
        if "organic_results" in results:
            for result in results["organic_results"]:
                # Filter for e-commerce sites
                if is_ecommerce_result(result):
                    shopping_urls.append({
                        "name": result.get("source", extract_site_name(result.get("link", ""))),
                        "url": result.get("link")
                    })
        
        print(f"✅ Regular search found {len(shopping_urls)} shopping results")
        return shopping_urls
    except Exception as e:
        print(f"❌ Regular search error: {e}")
        return []

def is_ecommerce_result(result: dict) -> bool:
    """Check if a search result is likely an e-commerce site."""
    url = result.get("link", "").lower()
    title = result.get("title", "").lower()
    snippet = result.get("snippet", "").lower()
    
    # E-commerce indicators
    ecommerce_indicators = [
        "buy", "shop", "price", "sale", "deal", "offer", "$", "₹", "£", "€",
        "cart", "checkout", "shipping", "delivery", "stock", "available"
    ]
    
    # Check URL patterns
    ecommerce_domains = [
        "amazon", "ebay", "walmart", "bestbuy", "target", "newegg",
        "aliexpress", "flipkart", "myntra", "snapdeal", "shopee",
        "lazada", "zalando", "otto", "cdiscount", "fnac", "rakuten"
    ]
    
    # Check if URL contains e-commerce domain
    for domain in ecommerce_domains:
        if domain in url:
            return True
    
    # Check for e-commerce indicators in title or snippet
    indicator_count = sum(1 for indicator in ecommerce_indicators 
                         if indicator in title or indicator in snippet)
    
    return indicator_count >= 2

def get_known_ecommerce_sites(country: str, query: str) -> List[Dict[str, str]]:
    """Get direct URLs for known e-commerce sites by country."""
    # Country-specific e-commerce sites
    ecommerce_sites = {
        "US": [
            {"name": "Amazon", "domain": "amazon.com"},
            {"name": "Walmart", "domain": "walmart.com"},
            {"name": "Best Buy", "domain": "bestbuy.com"},
            {"name": "Target", "domain": "target.com"},
            {"name": "Newegg", "domain": "newegg.com"},
            {"name": "Costco", "domain": "costco.com"},
            {"name": "Home Depot", "domain": "homedepot.com"}
        ],
        "IN": [
            {"name": "Amazon India", "domain": "amazon.in"},
            {"name": "Flipkart", "domain": "flipkart.com"},
            {"name": "Myntra", "domain": "myntra.com"},
            {"name": "Snapdeal", "domain": "snapdeal.com"},
            {"name": "Reliance Digital", "domain": "reliancedigital.in"},
            {"name": "Croma", "domain": "croma.com"},
            {"name": "Tata CLiQ", "domain": "tatacliq.com"}
        ],
        "UK": [
            {"name": "Amazon UK", "domain": "amazon.co.uk"},
            {"name": "Argos", "domain": "argos.co.uk"},
            {"name": "Currys", "domain": "currys.co.uk"},
            {"name": "John Lewis", "domain": "johnlewis.com"},
            {"name": "Very", "domain": "very.co.uk"},
            {"name": "AO", "domain": "ao.com"}
        ],
        "CA": [
            {"name": "Amazon Canada", "domain": "amazon.ca"},
            {"name": "Best Buy Canada", "domain": "bestbuy.ca"},
            {"name": "Walmart Canada", "domain": "walmart.ca"},
            {"name": "Canadian Tire", "domain": "canadiantire.ca"},
            {"name": "The Source", "domain": "thesource.ca"}
        ],
        "AU": [
            {"name": "Amazon Australia", "domain": "amazon.com.au"},
            {"name": "JB Hi-Fi", "domain": "jbhifi.com.au"},
            {"name": "Harvey Norman", "domain": "harveynorman.com.au"},
            {"name": "Kogan", "domain": "kogan.com"},
            {"name": "Officeworks", "domain": "officeworks.com.au"}
        ]
    }
    
    # Get sites for the country, default to US sites
    sites = ecommerce_sites.get(country, ecommerce_sites["US"])
    
    # Build search URLs
    urls = []
    search_query = query.replace(" ", "+")
    
    for site in sites[:7]:  # Limit to 7 sites
        if "amazon" in site["domain"]:
            url = f"https://www.{site['domain']}/s?k={search_query}"
        elif "flipkart" in site["domain"]:
            url = f"https://www.{site['domain']}/search?q={search_query}"
        elif "walmart" in site["domain"]:
            url = f"https://www.{site['domain']}/search?q={search_query}"
        elif "bestbuy" in site["domain"]:
            url = f"https://www.{site['domain']}/site/searchpage.jsp?st={search_query}"
        else:
            url = f"https://www.{site['domain']}/search?q={search_query}"
        
        urls.append({
            "name": site["name"],
            "url": url
        })
    
    return urls

def extract_site_name(url: str) -> str:
    """Extract a readable site name from URL."""
    try:
        domain = url.split('/')[2]
        # Remove www. and common TLDs
        domain = domain.replace('www.', '')
        name = domain.split('.')[0]
        # Capitalize first letter
        return name.capitalize()
    except:
        return "Unknown"

def get_currency(country: str) -> str:
    """Get currency code for a country."""
    return CURRENCY_MAP.get(country.upper(), "USD")
