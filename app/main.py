import asyncio
import sys
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from app.models import SearchRequest, SearchResponse
from app.search_engines import get_search_urls
from app.scraper import fetch_prices
import traceback
from typing import Optional

# Windows compatibility fix
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

app = FastAPI(
    title="Price Comparison Tool",
    description="Fetch product prices from multiple websites across different countries",
    version="2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Price Comparison Tool API v2.0",
        "endpoints": [
            "/search - Search for product prices",
            "/docs - API documentation",
            "/health - Health check"
        ],
        "supported_countries": [
            "US", "IN", "UK", "CA", "AU", "DE", "FR", "JP", "CN",
            "BR", "MX", "ES", "IT", "NL", "SE", "SG", "AE", "SA", "ZA", "KR"
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/search", response_model=SearchResponse)
async def search_prices(
    request: SearchRequest,
    limit: Optional[int] = Query(default=10, ge=1, le=50, description="Number of results to return")
):
    """
    Search for product prices across multiple websites.
    
    - **country**: Country code (e.g., US, IN, UK)
    - **query**: Product search query
    - **limit**: Maximum number of results to return (default: 10, max: 50)
    """
    try:
        print(f"\n{'='*60}")
        print(f"New search request: '{request.query}' in {request.country}")
        print(f"{'='*60}")
        
        # Validate country code
        valid_countries = ["US", "IN", "UK", "CA", "AU", "DE", "FR", "JP", "CN", 
                          "BR", "MX", "ES", "IT", "NL", "SE", "SG", "AE", "SA", "ZA", "KR"]
        if request.country not in valid_countries:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid country code. Supported: {', '.join(valid_countries)}"
            )
        
        # Get search URLs with retry logic
        max_retries = 2
        search_urls = []
        
        for attempt in range(max_retries):
            try:
                search_urls = await get_search_urls(request.country, request.query)
                if search_urls:
                    break
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(1)
        
        if not search_urls:
            print("No search URLs found")
            return SearchResponse(
                results=[],
                query=request.query,
                country=request.country
            )
        
        print(f"Found {len(search_urls)} URLs to scrape")
        
        # Fetch prices from all sources
        results = await fetch_prices(request.country, request.query, search_urls)
        
        # Apply limit
        limited_results = results[:limit]
        
        print(f"\nReturning {len(limited_results)} results (from {len(results)} total)")
        
        # Log summary
        if limited_results:
            prices = [float(r.price) for r in limited_results]
            print(f"Price range: {min(prices):.2f} - {max(prices):.2f}")
            print(f"Sources: {', '.join(set(r.source for r in limited_results))}")
        
        return SearchResponse(
            results=limited_results,
            query=request.query,
            country=request.country
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/search", response_model=SearchResponse)
async def search_prices_get(
    country: str = Query(..., description="Country code (e.g., US, IN, UK)"),
    query: str = Query(..., description="Product search query"),
    limit: Optional[int] = Query(default=10, ge=1, le=50, description="Number of results to return")
):
    """
    Alternative GET endpoint for searching product prices.
    """
    request = SearchRequest(country=country, query=query)
    return await search_prices(request, limit)

@app.post("/batch-search")
async def batch_search_prices(
    queries: list[SearchRequest],
    limit: Optional[int] = Query(default=10, ge=1, le=50)
):
    """
    Search for multiple products at once.
    """
    results = []
    for query in queries[:5]:  # Limit to 5 queries per batch
        try:
            result = await search_prices(query, limit)
            results.append(result)
        except Exception as e:
            results.append({
                "error": str(e),
                "query": query.query,
                "country": query.country
            })
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
