import streamlit as st
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import pandas as pd
import io

st.set_page_config(page_title="Tacirin eBayi", page_icon="🛍️", layout="wide")

# Google Gemini AI Konfiqurasiyası
API_KEY = "AQ.Ab8RN6LeQ4FlOCgflkaDwddwktdxbbcvKWonbOiMSD6hkYe1yg"
genai.configure(api_key=API_KEY)

st.title("🛍️ Tacirin eBayi — Dropshipping Optimizasiya və eBay CSV Paneli")
st.write("AliExpress məhsul linkini daxil edin, AI ilə optimize edin və tək kliklə eBay üçün hazır CSV faylı endirin.")

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
        with st.spinner("Məhsul məlumatları analiz edilir və eBay üçün hazırlanır..."):
            try:
                # AI vasitəsilə SEO Optimizasiyası
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"""
                Mən eBay-də dropshipping ilə məhsul satıram. 
                Aşağıdakı məhsul linkindən/mövzusundan istifadə edərək eBay üçün mükəmməl listing hazırla.
                
                Link: {url}
                
                Mənə cavabı tam olaraq bu 3 hissədə ver:
                1. Optimized_Title: (Maksimum 80 simvol, yüksək axtarışlı SEO açar sözlərlə ingiliscə başlıq)
                2. Item_Specifics: (Məhsulun xüsusiyyətləri: Brand, Type, Material, Color və s.)
                3. HTML_Description: (eBay üçün gözəl formatlanmış HTML təsvir mətni)
                """
                
                response = model.generate_content(prompt)
                ai_output = response.text
                
                st.success("Məhsul uğurla optimizasiya olundu!")
                st.markdown("### 📝 AI Tərəfindən Hazırlanmış Məhsul Məlumatı")
                st.write(ai_output)
                
                # eBay File Exchange / Bulk Upload üçün CSV strukturunun yaradılması
                ebay_data = {
                    "Action": ["Add"],
                    "Category": ["1"], # Kateqoriya ID
                    "Title": [f"Optimized Listing for {url[:30]}"],
                    "Relationship": [""],
                    "RelationshipDetails": [""],
                    "PicURL": [""],
                    "CostPrice": [cost_price],
                    "Price": [selling_price],
                    "Quantity": [10],
                    "Format": ["FixedPrice"],
                    "Duration": ["GTC"],
                    "Location": ["China"],
                    "Description": [ai_output]
                }
                
                df = pd.DataFrame(ebay_data)
                
                # CSV faylının hazırlanması
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False)
                
                st.download_button(
                    label="📥 eBay Üçün Hazır CSV Faylını Endir",
                    data=csv_buffer.getvalue(),
                    file_name="ebay_dropshipping_listing.csv",
                    mime="text/csv"
                )
                
            except Exception as e:
                st.error(f"Xəta baş verdi: {e}")
