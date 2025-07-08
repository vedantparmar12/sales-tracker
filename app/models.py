from pydantic import BaseModel
from typing import List, Optional

class SearchRequest(BaseModel):
    country: str
    query: str

class ProductResult(BaseModel):
    link: str
    price: str
    currency: str
    productName: str
    source: Optional[str] = None
    availability: Optional[str] = None

class SearchResponse(BaseModel):
    results: List[ProductResult]
    query: str
    country: str