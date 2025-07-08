import asyncio
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.models import SearchRequest, SearchResponse
from app.search_engines import get_search_urls
from app.scraper import fetch_prices
import traceback

# --- START OF FIX ---
# This is the crucial part for Windows compatibility.
# It sets an asyncio policy that allows subprocesses, which Playwright needs.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
# --- END OF FIX ---

app = FastAPI(title="Price Comparison Tool")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Price Comparison Tool API", "endpoints": ["/search", "/docs"]}

@app.post("/search", response_model=SearchResponse)
async def search_prices(request: SearchRequest):
    try:
        # Get search URLs for the country
        search_urls = await get_search_urls(request.country, request.query)
        print(f"Search URLs: {search_urls}")

        # Fetch prices from all sources
        results = await fetch_prices(request.country, request.query, search_urls)
        print(f"Found {len(results)} results")

        if not results:
            # Return empty results instead of 404
            return SearchResponse(
                results=[],
                query=request.query,
                country=request.country
            )

        return SearchResponse(
            results=results,
            query=request.query,
            country=request.country
        )
    except Exception as e:
        print(f"Error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)