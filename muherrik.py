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
# SCRAPERAPI İLƏ ALIEXPRESS MÜHƏRRİKİ
# ==========================================
SCRAPER_API_KEY = "d3ab337034b045efc43041d0281f2c4b"
EBAY_OAUTH_TOKEN = st.secrets.get("EBAY_OAUTH_TOKEN", "")

def extract_aliexpress_data(product_url):
    item_id_match = re.search(r'item/(\d+)\.html', product_url)
    if not item_id_match:
        item_id_match = re.search(r'(\d{10,})', product_url)
        
    if item_id_match:
        clean_url = f"https://www.aliexpress.com/item/{item_id_match.group(1)}.html"
    else:
        clean_url = product_url.split('?')[0].replace("aliexpress.us", "aliexpress.com")
    
    payload = {
        'api_key': SCRAPER_API_KEY,
        'url': clean_url
    }
    
    try:
        response = requests.get('http://api.scraperapi.com', params=payload, timeout=60)
        
        if response.status_code != 200:
            return {"error": f"API Xətası: {response.status_code}. Məlumat alınamadı."}
            
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        
        # 1. Başlıq tapmaq
        title = None
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title = og_title.get("content")
            
        if not title:
            title_match = re.search(r'"subject":"([^"]+)"', html)
            if title_match:
                title = title_match.group(1)

        if not title:
            h1 = soup.find("h1")
            if h1:
                title = h1.get_text().strip()

        title = re.sub(r' - AliExpress.*', '', title) if title else "Başlıq tapılmadı"

        # 2. HD Şəkilləri tapmaq
        images = []
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            main_img = og_image.get("content").split('_')[0]
            if not main_img.startswith('http'):
                main_img = 'https:' + main_img
            images.append(main_img)
            
        img_matches = re.findall(r'(?:https?:)?//ae01\.alicdn\.com/kf/[A-Za-z0-9_\-]+\.(?:jpg|png|webp)', html)
        
        for img in img_matches:
            full_img_url = img if img.startswith('http') else 'https:' + img
            clean_img = full_img_url.split('_')[0]
            if clean_img not in images and not clean_img.endswith(".png"):
                images.append(clean_img)

        return {
            "status": "success",
            "title": title,
            "images": images[:8]
        }

    except Exception as e:
        return {"error": f"Xəta baş verdi: {str(e)}"}

def optimize_ebay_title(raw_title):
    clean_title = re.sub(r'[^\w\s\-\.\,\/]', '', raw_title)
    words = clean_title.split()
    optimized = ""
    for word in words:
        if len(optimized + " " + word) <= 80:
            optimized += (" " if optimized else "") + word
        else:
            break
    return optimized if optimized else raw_title[:80]

def build_official_ebay_csv(title, description, price, pic_urls):
    """eBay Reports / File Exchange standartlarına 100% uyğun CSV generasiya edir"""
    headers = [
        "*Action(SiteID=US|PT=1|Format=FixedPrice)",
        "CustomLabel",
        "*Category",
        "*Title",
        "Subtitle",
        "*Relationship",
        "*RelationshipDetails",
        "*P:UPC",
        "*P:ISBN",
        "*P:EAN",
        "*P:EPID",
        "StartPrice",
        "*Quantity",
        "*Format",
        "*Duration",
        "PicURL",
        "Description",
        "*Location",
        "ShippingService-1:Option",
        "ShippingService-1:Cost",
        "*DispatchTimeMax",
        "*ReturnsAcceptedOption",
        "RefundOption",
        "ReturnsWithinOption",
        "ShippingCostPaidByOption"
    ]
    
    data_row = [
        "Draft",  # Action
        f"TACIR-{int(re.sub(r'\D', '', title)[:8] or 100000)}",  # CustomLabel (SKU)
        "1",  # Category (Sistem avtomatik seçəcək)
        title[:80],  # Title
        "",  # Subtitle
        "",  # Relationship
        "",  # RelationshipDetails
        "Does not apply",  # UPC
        "Does not apply",  # ISBN
        "Does not apply",  # EAN
        "",  # EPID
        str(price),  # StartPrice
        "10",  # Quantity
        "FixedPrice",  # Format
        "GTC",  # Duration
        pic_urls,  # PicURL
        description,  # Description
        "China",  # Location
        "StandardShipping",  # Shipping Option
        "0.00",  # Shipping Cost
        "3",  # DispatchTimeMax
        "ReturnsAccepted",  # Returns
        "MoneyBack",  # RefundOption
        "Days_30",  # ReturnsWithinOption
        "Buyer"  # ShippingCostPaidByOption
    ]
    
    df = pd.DataFrame([data_row], columns=headers)
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    return csv_buffer.getvalue()

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
# BÖLMƏ 1: MƏHSUL ƏLAVƏ ET VƏ CSV PANELSİ
# ==========================================
if menu == "➕ Ürün Ekle (Məhsul Əlavə Et)":
    st.title("🛍️ Tacirin eBayi — Dropshipping Optimizasiya Paneli")
    st.write("AliExpress məhsul linkini daxil edin, qiyməti təyin edin və rəsmi eBay CSV faylını endirin.")

    col1, col2 = st.columns([2, 1])

    with col1:
        url = st.text_input("🔗 Məhsul Linki (URL):", placeholder="https://www.aliexpress.com/item/...")

    with col2:
        cost_price = st.number_input("💰 Alış Qiyməti ($):", min_value=0.0, value=10.0, step=0.5)
        margin = st.number_input("📈 Qazanc Faizi (%):", min_value=0.0, value=30.0, step=5.0)

    selling_price = round(cost_price * (1 + margin / 100), 2)
    st.info(f"💡 Tövsiyə olunan eBay Satış Qiyməti: **${selling_price}**")

    st.write("---")

    if st.button("🚀 Rəsmi eBay CSV Faylını Hazırla və Endir", type="primary"):
        if not url:
            st.warning("Zəhmət olmasa məhsul linkini daxil edin!")
        else:
            with st.spinner("Məhsul oxunur və Rəsmi eBay CSV-si hazırlanır..."):
                data = extract_aliexpress_data(url)
                
                if "error" in data or not data.get("title"):
                    st.error("Məhsul məlumatı çəkilə bilmədi.")
                else:
                    raw_title = data.get("title", "Product")
                    opt_title = optimize_ebay_title(raw_title)
                    pic_urls = "|".join(data.get("images", []))
                    
                    description_html = f"<h2>{opt_title}</h2><p>High Quality Product - Fast Shipping</p>"
                    
                    csv_data = build_official_ebay_csv(opt_title, description_html, selling_price, pic_urls)
                    
                    st.success("Rəsmi eBay şablonuna uyğun CSV uğurla yaradıldı!")
                    st.download_button(
                        label="📥 ebay_official_template.csv Faylını Endir",
                        data=csv_data,
                        file_name="ebay_official_template.csv",
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
            with st.spinner("AliExpress oxunur (bir neçə saniyə çəkə bilər)..."):
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
                        for idx, img_link in enumerate(data["images"]):
                            with cols[idx % 4]:
                                try:
                                    st.image(img_link, use_container_width=True)
                                except Exception:
                                    pass
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
