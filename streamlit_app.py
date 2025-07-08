import streamlit as st
import requests
import json

st.set_page_config(layout="wide")

st.title("🛒 Price Comparison Tool")

# --- START OF CHANGES ---

# Use a dictionary for country selection for clarity
COUNTRIES = {
    "United States": "US",
    "India": "IN",
    "United Kingdom": "UK",
    "Canada": "CA",
    "Australia": "AU",
    "Germany": "DE",
    "France": "FR",
    "Japan": "JP",
    "China": "CN"
}

col1, col2 = st.columns(2)

with col1:
    # Let the user select the full country name
    selected_country_name = st.selectbox(
        "Country",
        options=COUNTRIES.keys(), # Show full names in the dropdown
        help="Select the country you're shopping from."
    )
    # Get the corresponding country code to send to the API
    country_code = COUNTRIES[selected_country_name]

# --- END OF CHANGES ---

with col2:
    query = st.text_input("Product Query", placeholder="e.g. iPhone 16 Pro, 128GB")

if st.button("Search Prices", type="primary"):
    if query:
        with st.spinner("Searching for the best prices... this may take a moment."):
            try:
                response = requests.post(
                    "http://127.0.0.1:8000/search",
                    # Send the country_code to the backend
                    json={"country": country_code, "query": query}
                )

                if response.status_code == 200:
                    data = response.json()

                    if data['results']:
                        st.success(f"Found {len(data['results'])} results!")

                        for idx, product in enumerate(data['results']):
                            with st.expander(f"{product['productName'][:60]}... - {product['currency']} {product['price']}"):
                                st.markdown(f"**Price:** `{product['currency']} {product['price']}`")
                                st.markdown(f"**Source:** `{product.get('source', 'Unknown')}`")
                                st.markdown(f"**Link:** [Click to view]({product['link']})")
                    else:
                        st.warning("No results found. Try refining your search query or check the server logs for errors.")
                else:
                    st.error("Failed to fetch results. Please try again later.")

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
    else:
        st.warning("Please enter a product query to begin.")

with st.sidebar:
    st.header("Example Queries")
    st.code('{"country": "US", "query": "iPhone 16 Pro, 128GB"}')
    st.code('{"country": "IN", "query": "boAt Airdopes 311 Pro"}')