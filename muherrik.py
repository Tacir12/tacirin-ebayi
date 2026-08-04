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
# CUSTOM CSS — ARXA FON VƏ DİZAYN TƏNZİMLƏMƏSİ
# ==========================================
st.markdown("""
    <style>
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }
    [data-testid="stSidebar"] {
        background-color: #1e1b4b;
    }
    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }
    .stTextInput>div>div>input, .stNumberInput>div>div>input {
        background-color: #1e293b;
        color: #ffffff;
        border: 1px solid #334155;
    }
    .stButton>button {
        background: linear-gradient(90deg, #6366f1 0%, #4f46e5 100%);
        color: white;
        border: none;
        font-weight: bold;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# ADVANCED ALIEXPRESS SCRAPER FUNCTION
# ==========================================
def extract_aliexpress_data(product_url):
    # AliExpress bloklamasını keçmək üçün real brauzer User-Agent-i
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Connection": "keep-alive"
    }
    
    try:
        session = requests.Session()
        response = session.get(product_url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return {"error": f"Səhifəyə daxil olmaq olmadı. Xəta kodu: {response.status_code}"}
        
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        
        # 1. Başlığı tapmaq (Çoxmərhələli axtarış)
        title = None
        
        # A) Meta etiketlərdən
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title = og_title.get("content")
        
        # B) HTML h1 elementindən
        if not title:
            h1_tag = soup.find("h1")
            if h1_tag:
                title = h1_tag.get_text().strip()
                
        # C) Script daxilindəki JSON parametrindən
        if not title or "AliExpress" in title:
            match_title = re.search(r'"subject":"([^"]+)"', html)
            if match_title:
                title = match_title.group(1)

        if not title:
            title = soup.title.string.strip() if soup.title else "Başlıq tapılmadı"

        # AliExpress lazımsız şəkilçi sözləri təmizləyirik
        title = re.sub(r' - AliExpress.*', '', title)

        # 2. HD Şəkilləri tapmaq (Regex vasitəsilə CDN linklərini çəkirik)
        images = []
        
        # CDN şəkil keçidlərini axtarırıq (ae01.alicdn.com)
        img_matches = re.findall(r'https://ae01\.alicdn\.com/kf/[A-Za-z0-9_\-]+\.(?:jpg|png)', html)
        
        for img in img_matches:
            # Şəklin ölçü parametrlərini təmizləyib orijinal HD versiyasını alırıq
            clean_img = img.split('_')[0] if '_' in img else img
            if clean_img not in images and not clean_img.endswith(".png"): # Simgələri kənarlaşdırmaq üçün
                images.append(clean_img)

        # Əgər əsas şəkil linki meta tag-də varsa, ilk sıraya qoyuruq
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            main_img = og_image.get("content").split('_')[0]
            if main_img not in images:
                images.insert(0, main_img)

        if not title and not images:
            return {"error": "AliExpress məlumatların oxunmasına icazə vermədi (Anti-bot bloklaması)."}

        return {
            "status": "success",
            "title": title,
            "images": images[:8]  # İlk 8 əsas HD şəkil
        }

    except Exception as e:
        return {"error": f"Xəta baş verdi: {str(e)}"}

# ==========================================
# AUTO-DS STİLİNDƏ SOL MENYU (SIDEBAR)
# ==========================================
with st.sidebar:
    st.title("🛍️ Tacirin eBayi")
    st.write("---")
    
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
            with st.spinner("Məhsul mühərriklə oxunur..."):
                data = extract_aliexpress_data(url)
                
                if "error" in data or not data.get("title"):
                    st.error("Məhsul məlumatları avtomatik çəkilə bilmədi. Standart başlıq istifadə olunur.")
                    item_id = url.split("item/")[-1].split(".html")[0] if "item/" in url else "Product"
                    title = f"New Trending Product High Quality Item {item_id[:10]}"
                    img_url = ""
                else:
                    title = data["title"]
                    img_url = data["images"][0] if data["images"] else ""

                description_html = f"""
                <h2>{title}</h2>
                <p>Original Product Link: {url}</p>
                <p>Fast Shipping & Top Quality Guaranteed.</p>
                """
                
                ebay_data = {
                    "Action": ["Draft"],
                    "Title": [title[:80]],
                    "Description": [description_html],
                    "Price": [selling_price],
                    "Quantity": [10],
                    "Format": ["FixedPrice"],
                    "Duration": ["GTC"],
                    "Location": ["China"],
                    "ConditionID": ["1000"],
                    "PicURL": [img_url]
                }
                
                df = pd.DataFrame(ebay_data)
                
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False)
                
                st.success("Məhsul uğurla hazırlandı!")
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
    st.title("🕷️ Mühərrik — AliExpress Məlumatı Çəkən Panel")
    st.write("Bu panel AliExpress linkindən məhsulun həqiqi adını və HD şəkillərini avtomatik çəkir.")

    url_scraper = st.text_input("🔗 AliExpress Məhsul Linkini Daxil Edin:", placeholder="https://www.aliexpress.com/item/...")

    if st.button("🔍 Məlumatları Çək", type="primary"):
        if not url_scraper:
            st.warning("Zəhmət olmasa link daxil edin!")
        else:
            with st.spinner("AliExpress səhifəsi təhlil olunur..."):
                data = extract_aliexpress_data(url_scraper)
                
                if "error" in data:
                    st.error(data["error"])
                else:
                    if data["title"] == "Başlıq tapılmadı" and not data["images"]:
                        st.warning("AliExpress bloklamasına görə bu linkdən məlumat çəkilə bilmədi. Fərqli məhsul linki ilə yoxlayın.")
                    else:
                        st.success("Məlumatlar uğurla çəkildi!")
                        st.subheader("📌 Məhsulun Orijinal Adı:")
                        st.write(data["title"])
                        
                        st.subheader("🖼️ Məhsulun HD Şəkilləri:")
                        if data["images"]:
                            cols = st.columns(4)
                            for idx, img_link in enumerate(data["images"]):
                                with cols[idx % 4]:
                                    st.image(img_link, use_column_width=True)
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
