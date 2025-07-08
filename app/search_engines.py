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

# --- START OF CHANGES ---

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
    "CN": "China"
}

# Currency mapping remains the same
CURRENCY_MAP = {
    "US": "USD", "IN": "INR", "UK": "GBP", "CA": "CAD",
    "AU": "AUD", "DE": "EUR", "FR": "EUR", "JP": "JPY", "CN": "CNY"
}

# --- END OF CHANGES ---

async def get_search_urls(country: str, query: str) -> List[Dict[str, str]]:
    """
    Get a list of shopping URLs for a given product query and country
    using the Google Search API.
    """
    # Look up the full country name, default to "United States" if not found
    location_name = COUNTRY_NAMES.get(country, "United States")

    search_params = {
        "q": f"{query} buy online",
        "location": location_name, # Use the full location name here
        "api_key": SERPAPI_API_KEY
    }

    search = GoogleSearch(search_params)
    results = search.get_dict()

    if "error" in results:
        print("="*50)
        print(f"🔴 ERROR FROM SERPAPI: {results['error']}")
        print("="*50)
        return []

    print("✅ SerpApi results received:")
    print(json.dumps(results.get('organic_results', 'No organic results found'), indent=2))

    shopping_urls = []
    if "organic_results" in results:
        for result in results["organic_results"][:10]:
            shopping_urls.append({
                "name": result.get("source", "Unknown"),
                "url": result.get("link")
            })

    return shopping_urls

def get_currency(country: str) -> str:
    return CURRENCY_MAP.get(country.upper(), "USD")