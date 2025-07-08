import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="Price Comparison Tool",
    page_icon="🛒",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .price-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    .best-price {
        background-color: #d4edda;
        border: 2px solid #28a745;
    }
    .price-highlight {
        font-size: 24px;
        font-weight: bold;
        color: #28a745;
    }
    .savings-badge {
        background-color: #ffc107;
        color: #000;
        padding: 5px 10px;
        border-radius: 20px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.title("🛒 Advanced Price Comparison Tool")
st.markdown("Find the best prices across multiple websites worldwide")

# Sidebar for advanced options
with st.sidebar:
    st.header("⚙️ Settings")
    
    result_limit = st.slider(
        "Max results to display",
        min_value=3,
        max_value=25,
        value=10,
        help="Number of results to show"
    )
    
    show_analytics = st.checkbox("Show price analytics", value=True)
    show_raw_data = st.checkbox("Show raw data", value=False)
    
    st.markdown("---")
    st.header("📊 Search History")
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []
    
    if st.session_state.search_history:
        for item in st.session_state.search_history[-5:]:
            st.text(f"• {item['query']} ({item['country']})")
    else:
        st.text("No searches yet")

# Extended country list
COUNTRIES = {
    "🇺🇸 United States": "US",
    "🇮🇳 India": "IN",
    "🇬🇧 United Kingdom": "UK",
    "🇨🇦 Canada": "CA",
    "🇦🇺 Australia": "AU",
    "🇩🇪 Germany": "DE",
    "🇫🇷 France": "FR",
    "🇯🇵 Japan": "JP",
    "🇨🇳 China": "CN",
    "🇧🇷 Brazil": "BR",
    "🇲🇽 Mexico": "MX",
    "🇪🇸 Spain": "ES",
    "🇮🇹 Italy": "IT",
    "🇳🇱 Netherlands": "NL",
    "🇸🇪 Sweden": "SE",
    "🇸🇬 Singapore": "SG",
    "🇦🇪 UAE": "AE",
    "🇸🇦 Saudi Arabia": "SA",
    "🇿🇦 South Africa": "ZA",
    "🇰🇷 South Korea": "KR"
}

# Main search interface
col1, col2, col3 = st.columns([2, 3, 1])

with col1:
    selected_country_name = st.selectbox(
        "Select Country",
        options=COUNTRIES.keys(),
        help="Choose your shopping location"
    )
    country_code = COUNTRIES[selected_country_name]

with col2:
    query = st.text_input(
        "Product Search",
        placeholder="e.g., iPhone 16 Pro 128GB, Samsung Galaxy S24, Sony WH-1000XM5",
        help="Enter the product you want to search for"
    )

with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    search_button = st.button("🔍 Search", type="primary", use_container_width=True)

# Popular searches
st.markdown("**Popular searches:** ")
popular_searches = ["iPhone 16 Pro", "MacBook Air M2", "iPad Air", "AirPods Pro", "Samsung Galaxy S24"]
cols = st.columns(len(popular_searches))
for idx, (col, search) in enumerate(zip(cols, popular_searches)):
    with col:
        if st.button(search, key=f"popular_{idx}"):
            query = search

# Search execution
if search_button or query:
    if query:
        # Add to search history
        st.session_state.search_history.append({
            'query': query,
            'country': country_code,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        
        with st.spinner(f"🔍 Searching for '{query}' in {selected_country_name}..."):
            try:
                response = requests.post(
                    "http://127.0.0.1:8000/search",
                    json={"country": country_code, "query": query},
                    params={"limit": result_limit}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data['results']
                    
                    if results:
                        st.success(f"✅ Found {len(results)} results!")
                        
                        # Price analytics
                        if show_analytics and len(results) > 1:
                            prices = [float(r['price']) for r in results]
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("🏆 Best Price", f"{results[0]['currency']} {min(prices):.2f}")
                            with col2:
                                st.metric("📊 Average Price", f"{results[0]['currency']} {sum(prices)/len(prices):.2f}")
                            with col3:
                                st.metric("📈 Highest Price", f"{results[0]['currency']} {max(prices):.2f}")
                            with col4:
                                savings = max(prices) - min(prices)
                                st.metric("💰 Max Savings", f"{results[0]['currency']} {savings:.2f}")
                        
                        st.markdown("---")
                        
                        # Results display
                        st.subheader("🛍️ Price Comparison Results")
                        
                        for idx, product in enumerate(results):
                            is_best_price = idx == 0
                            
                            # Create expandable card for each result
                            with st.expander(
                                f"{'🏆 ' if is_best_price else ''}{product['productName'][:80]}... - "
                                f"{product['currency']} {product['price']}",
                                expanded=is_best_price
                            ):
                                col1, col2 = st.columns([3, 1])
                                
                                with col1:
                                    st.markdown(f"**Product:** {product['productName']}")
                                    st.markdown(f"**Price:** `{product['currency']} {product['price']}`")
                                    st.markdown(f"**Source:** {product.get('source', 'Unknown')}")
                                    if product.get('availability'):
                                        st.markdown(f"**Availability:** {product['availability']}")
                                    
                                    if is_best_price:
                                        st.markdown("🏆 **BEST PRICE**")
                                
                                with col2:
                                    st.link_button(
                                        "🛒 Visit Store",
                                        product['link'],
                                        use_container_width=True
                                    )
                        
                        # Export options
                        st.markdown("---")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Convert to DataFrame for export
                            df = pd.DataFrame(results)
                            csv = df.to_csv(index=False)
                            st.download_button(
                                label="📥 Download Results (CSV)",
                                data=csv,
                                file_name=f"price_comparison_{query.replace(' ', '_')}_{country_code}.csv",
                                mime="text/csv"
                            )
                        
                        with col2:
                            # JSON export
                            json_data = json.dumps(results, indent=2)
                            st.download_button(
                                label="📥 Download Results (JSON)",
                                data=json_data,
                                file_name=f"price_comparison_{query.replace(' ', '_')}_{country_code}.json",
                                mime="application/json"
                            )
                        
                        # Raw data view
                        if show_raw_data:
                            st.markdown("---")
                            st.subheader("📊 Raw Data")
                            st.dataframe(df, use_container_width=True)
                        
                    else:
                        st.warning("🔍 No results found. Try adjusting your search query.")
                        st.info("Tips:\n- Try simpler product names\n- Remove specific model numbers\n- Check spelling")
                        
                else:
                    st.error(f"❌ Server error: {response.status_code}")
                    st.json(response.json())
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to the API server. Make sure it's running on port 8000.")
            except Exception as e:
                st.error(f"❌ An error occurred: {str(e)}")
    else:
        st.warning("⚠️ Please enter a product to search for.")

# Footer
st.markdown("---")
with st.expander("ℹ️ About this tool"):
    st.markdown("""
    This price comparison tool searches across multiple e-commerce websites to find the best prices for products.
    
    **Features:**
    - 🌍 Supports 20+ countries
    - 🛒 Searches major e-commerce platforms
    - 📊 Price analytics and comparisons
    - 💾 Export results in CSV or JSON format
    - 🔄 Real-time price fetching
    
    **Note:** Prices are fetched in real-time and may vary. Some websites may block automated requests.
    """)

# API status check
with st.sidebar:
    st.markdown("---")
    if st.button("🔧 Check API Status"):
        try:
            health_response = requests.get("http://127.0.0.1:8000/health")
            if health_response.status_code == 200:
                st.success("✅ API is running")
            else:
                st.error("❌ API is not responding properly")
        except:
            st.error("❌ Cannot connect to API")
