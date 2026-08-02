import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Tacirin eBayi", page_icon="🛍️", layout="wide")

st.title("🛍️ Tacirin eBayi — Dropshipping Optimizasiya və eBay CSV Paneli")
st.write("AliExpress məhsul linkini daxil edin və tək kliklə eBay üçün hazır CSV faylı endirin.")

col1, col2 = st.columns([2, 1])

with col1:
    url = st.text_input("🔗 Məhsul Linki (URL):", placeholder="https://www.aliexpress.com/item/...")

with col2:
    cost_price = st.number_input("💰 Alış Qiyməti ($):", min_value=0.0, value=10.0, step=0.5)
    margin = st.number_input("📈 Qazanc Faizi (%):", min_value=0.0, value=30.0, step=5.0)

selling_price = round(cost_price * (1 + margin / 100), 2)
st.info(f"💡 Tövsiyə olunan eBay Satış Qiyməti: **${selling_price}**")

if st.button("🚀 Məhsulu Optimizasiya Et və CSV Hazırla", type="primary"):
    if not url:
        st.warning("Zəhmət olmasa məhsul linkini daxil edin!")
    else:
        with st.spinner("Məhsul eBay üçün hazırlanır..."):
            
            # Linkdən təmiz ad çıxarılması
            item_id = url.split("item/")[-1].split(".html")[0] if "item/" in url else "Product"
            title = f"New Trending Product - High Quality Item {item_id[:10]}"
            
            description_html = f"""
            <h2>High Quality Product from AliExpress</h2>
            <p>Original Product Link: {url}</p>
            <p>Fast Shipping & Top Quality Guaranteed.</p>
            """
            
            st.success("Məhsul uğurla hazırlandı!")
            st.markdown("### 📝 Məhsul Məlumatı")
            st.write(f"**Başlıq:** {title}")
            st.write(f"**Satış Qiyməti:** ${selling_price}")
            
            # eBay Bulk Upload üçün CSV
            ebay_data = {
                "Action": ["Add"],
                "Category": ["1"],
                "Title": [title[:80]],
                "Relationship": [""],
                "RelationshipDetails": [""],
                "PicURL": [""],
                "CostPrice": [cost_price],
                "Price": [selling_price],
                "Quantity": [10],
                "Format": ["FixedPrice"],
                "Duration": ["GTC"],
                "Location": ["China"],
                "Description": [description_html]
            }
            
            df = pd.DataFrame(ebay_data)
            
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            
            st.download_button(
                label="📥 eBay Üçün Hazır CSV Faylını Endir",
                data=csv_buffer.getvalue(),
                file_name="ebay_dropshipping_listing.csv",
                mime="text/csv"
            )
