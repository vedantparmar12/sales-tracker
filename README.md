# Enhanced Price Comparison Tool v2.0

A powerful, generic price comparison tool that fetches product prices from multiple websites across 20+ countries.

## 🚀 Key Improvements

### 1. **Enhanced Search Coverage**
- **Multiple search strategies**: Google Shopping + Regular Search + Direct E-commerce URLs
- **Country-specific search**: Uses localized Google domains and shopping sites
- **Smart deduplication**: Prevents duplicate results from the same domain
- **Expanded country support**: Now supports 20+ countries worldwide

### 2. **Advanced Scraping Capabilities**
- **Multiple extraction methods**:
  - JSON-LD structured data
  - Open Graph and meta tags
  - Site-specific patterns (Amazon, etc.)
  - Generic HTML pattern matching
- **Improved price extraction**: Regex patterns for various currency formats
- **Better product matching**: Enhanced similarity scoring with weighted keywords
- **Rotating user agents**: Avoids detection and blocks
- **Extended timeouts**: Better handling of slow sites

### 3. **Robust Error Handling**
- **Retry logic**: Automatic retries for failed requests
- **Graceful degradation**: Continues even if some sites fail
- **Detailed logging**: Track which sites succeed/fail
- **HTTP error handling**: Specific handling for 403, 404, timeout errors

### 4. **Enhanced API Features**
- **Configurable result limits**: Control number of results (1-50)
- **Batch search endpoint**: Search multiple products at once
- **Health check endpoint**: Monitor API status
- **Better validation**: Country code validation with helpful errors

### 5. **Improved UI/UX**
- **20+ country support**: Extended country selection
- **Price analytics**: Show best, average, highest prices and potential savings
- **Export functionality**: Download results as CSV or JSON
- **Search history**: Track recent searches
- **Popular searches**: Quick access to common products
- **Better visual design**: Cards, badges, and highlights for best prices

## 📋 Supported Countries

- 🇺🇸 United States (US)
- 🇮🇳 India (IN)
- 🇬🇧 United Kingdom (UK)
- 🇨🇦 Canada (CA)
- 🇦🇺 Australia (AU)
- 🇩🇪 Germany (DE)
- 🇫🇷 France (FR)
- 🇯🇵 Japan (JP)
- 🇨🇳 China (CN)
- 🇧🇷 Brazil (BR)
- 🇲🇽 Mexico (MX)
- 🇪🇸 Spain (ES)
- 🇮🇹 Italy (IT)
- 🇳🇱 Netherlands (NL)
- 🇸🇪 Sweden (SE)
- 🇸🇬 Singapore (SG)
- 🇦🇪 UAE (AE)
- 🇸🇦 Saudi Arabia (SA)
- 🇿🇦 South Africa (ZA)
- 🇰🇷 South Korea (KR)

## 🛠️ Installation & Setup

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Set up environment variables**:
Create a `.env` file:
```
SERPAPI_API_KEY=your_serpapi_api_key_here
```

3. **Run the API server**:
```bash
python run.py
```

4. **Run the Streamlit UI** (in a new terminal):
```bash
streamlit run streamlit_app.py
```

## 📡 API Endpoints

### Search for Products
```http
POST /search
Content-Type: application/json

{
  "country": "US",
  "query": "iPhone 16 Pro 128GB"
}

# Optional query parameters:
?limit=10  # Number of results (1-50)
```

### Batch Search
```http
POST /batch-search
Content-Type: application/json

[
  {"country": "US", "query": "iPhone 16 Pro"},
  {"country": "IN", "query": "Samsung Galaxy S24"}
]
```

### Health Check
```http
GET /health
```

## 🔧 How It Works

1. **Search Phase**:
   - Queries Google Shopping for product listings
   - Falls back to regular Google search with shopping keywords
   - Adds known e-commerce sites for the country

2. **Scraping Phase**:
   - Attempts multiple extraction methods per site
   - Validates product relevance using similarity scoring
   - Extracts price, currency, and product details

3. **Results Processing**:
   - Deduplicates similar products
   - Sorts by price (ascending)
   - Returns structured JSON response

## 📊 Example Output

```json
[
  {
    "link": "https://www.amazon.com/...",
    "price": "799.99",
    "currency": "USD",
    "productName": "Apple iPhone 16 Pro 128GB",
    "source": "Amazon",
    "availability": "In Stock"
  },
  {
    "link": "https://www.bestbuy.com/...",
    "price": "849.99",
    "currency": "USD",
    "productName": "iPhone 16 Pro - 128GB",
    "source": "Best Buy",
    "availability": "Available"
  }
]
```

## 🚨 Common Issues & Solutions

### Few Results Returned
- **Cause**: Many e-commerce sites block automated requests
- **Solution**: The tool now uses multiple strategies to maximize results

### Timeout Errors
- **Cause**: Slow website response
- **Solution**: Increased timeout to 30 seconds, considers using proxy services

### Wrong Products Matched
- **Cause**: Generic search terms
- **Solution**: Use specific product names with model numbers

## 🔮 Future Enhancements

1. **Proxy rotation**: Bypass rate limits and blocks
2. **Headless browser**: Handle JavaScript-rendered sites
3. **Price history**: Track price changes over time
4. **Price alerts**: Notify when prices drop
5. **More countries**: Expand to 50+ countries
6. **Category filters**: Filter by product category
7. **Review scores**: Include product ratings

## 📄 License

MIT License - feel free to use and modify!

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📞 Support

For issues or questions:
- Check the API logs for detailed error messages
- Ensure SerpAPI key is valid and has remaining credits
- Verify the API server is running on port 8000
