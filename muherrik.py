import json
import re
import requests
from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd
import io

# Səhifə konfiqurasiyası
st.set_page_config(page_title="Tacirin eBayi", page_icon="🛍️", layout="wide")

# ==========================================
# AUTO-DS STİLİNDƏ SOL MENYU (SIDEBAR)
# ==========================================
with st.sidebar:
    st.title("🛍️ Tacirin eBayi")
    st.write("---")
    
    # Menyu seçimləri
    menu = st.radio(
        "Menyu:",
        [
            "➕ Ürün Ekle (Məhsul Əlavə Et)",
            "🕷️ AliExpress Scraper Test",
            "📋 Taslaklar (Qaralamalar)",
            "⚙️ Ayarlar və Təlimat"
        ]
    )
    
    st.write("---")
    st.info("💡 Telefonla daxil olarkən sol yuxarıdakı **`>`** oxuna basaraq menyunu aça bilərsiniz.")

# ==========================================
# BÖLMƏ 1: MƏHSUL ƏLAVƏ ET VƏ CSV GENERATORU
# ==========================================
if menu == "➕ Ürün Ekle (Məhsul Əlavə Et)":
    st.title("🛍️ Tacirin eBayi — Dropshipping Optimizasiya və CSV Paneli")
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
                item_id = url.split("item/")[-1].split(".html")[0] if "item/" in url else "Product"
                title = f"New Trending Product High Quality Item {item_id[:10]}"
                
                description_html = f"""
                <h2>High Quality Product from AliExpress</h2>
                <p>Original Product Link: {url}</p>
                <p>Fast Shipping & Top Quality Guaranteed.</p>
                """
                
                st.success("Məhsul uğurla hazırlandı!")
                
                ebay_data = {
                    "Action": ["Draft"],
                    "Title": [title[:80]],
                    "Description": [description_html],
                    "Price": [selling_price],
                    "Quantity": [10],
                    "Format": ["FixedPrice"],
                    "Duration": ["GTC"],
                    "Location": ["China"],
                    "ConditionID": ["1000"]
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

# ==========================================
# BÖLMƏ 2: ALIEXPRESS SCRAPER TEST
# ==========================================
elif menu == "🕷️ AliExpress Scraper Test":
    st.title("🕷️ AliExpress Məhsul Məlumatı Və Şəkil Çəkən Mühərrik")
    st.write("Bu panel AliExpress linkindən məhsulun həqiqi adını, HD şəkillərini avtomatik çəkir.")

    url_scraper = st.text_input("🔗 AliExpress Məhsul Linkini Daxil Edin:", placeholder="https://www.aliexpress.com/item/...")

    def extract_aliexpress_data(product_url):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        
        try:
            response = requests.get(product_url, headers=headers, timeout=12)
            if response.status_code != 200:
                return {"error": f"Səhifəyə daxil olmaq olmadı. Xəta kodu: {response.status_code}"}
            
            html = response.text
            soup = BeautifulSoup(html, "html.parser")
            
            og_title = soup.find("meta", property="og:title")
            title = og_title.get("content", "") if og_title else (soup.title.string if soup.title else "Başlıq tapılmadı")

            images = []
            og_image = soup.find("meta", property="og:image")
            if og_image and og_image.get("content"):
                images.append(og_image.get("content"))
                
            img_matches = re.findall(r'https://ae01\.alicdn\.com/kf/[^"\'\s_]+(?:\.jpg|\.png)', html)
            for img in img_matches:
                clean_img = img.split('_')[0] if '_' in img else img
                if clean_img not in images:
                    images.append(clean_img)

            return {
                "status": "success",
                "title": title,
                "images": images[:8]
            }

        except Exception as e:
            return {"error": str(e)}

    if st.button("🔍 Məlumatları Çək", type="primary"):
        if not url_scraper:
            st.warning("Zəhmət olmasa link daxil edin!")
        else:
            with st.spinner("AliExpress-dən məlumatlar yüklənir..."):
                data = extract_aliexpress_data(url_scraper)
                
                if "error" in data:
                    st.error(data["error"])
                else:
                    st.success("Məlumatlar uğurla çəkildi!")
                    st.subheader("📌 Məhsulun Orijinal Adı:")
                    st.write(data["title"])
                    
                    st.subheader("🖼️ Məhsulun HD Şəkilləri:")
                    if data["images"]:
                        cols = st.columns(4)
                        for idx, img_url in enumerate(data["images"]):
                            with cols[idx % 4]:
                                st.image(img_url, use_column_width=True)
                    else:
                        st.info("Şəkil tapılmadı.")

# ==========================================
# BÖLMƏ 3 & 4: TASLAKLAR VƏ AYARLAR
# ==========================================
elif menu == "📋 Taslaklar (Qaralamalar)":
    st.title("📋 Qaralamalar Paneli")
    st.write("Hazırladığın məhsul siyahıları burada saxlanılacaq.")

elif menu == "⚙️ Ayarlar və Təlimat":
    st.title("⚙️ Tənzimləmələr")
    st.markdown("""
    1. CSV faylını proqramdan endir.
    2. **[ebay.com/sh/reports/uploads](https://www.ebay.com/sh/reports/uploads)** bölməsinə keç.
    3. Faylı yüklə, məhsul dərhal **Drafts** bölməsinə düşəcək.
    """)
