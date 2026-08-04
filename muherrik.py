import json
import re
import requests
from bs4 import BeautifulSoup
import streamlit as st

st.set_page_config(page_title="AliExpress Scraper Test", page_icon="🕷️", layout="wide")

st.title("🕷️ AliExpress Məhsul Məlumatı Və Şəkil Çəkən Mühərrik")
st.write("Bu panel AliExpress linkindən məhsulun həqiqi adını, HD şəkillərini və variantlarını avtomatik çəkir.")

url = st.text_input("🔗 AliExpress Məhsul Linkini Daxil Edin:", placeholder="https://www.aliexpress.com/item/...")

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
        
        # 1. Başlıq
        og_title = soup.find("meta", property="og:title")
        title = og_title.get("content", "") if og_title else (soup.title.string if soup.title else "Başlıq tapılmadı")

        # 2. HD Şəkillər
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
            "images": images[:8]  # İlk 8 HD şəkil
        }

    except Exception as e:
        return {"error": str(e)}

if st.button("🔍 Məlumatları Çək", type="primary"):
    if not url:
        st.warning("Zəhmət olmasa link daxil edin!")
    else:
        with st.spinner("AliExpress-dən məlumatlar yüklənir..."):
            data = extract_aliexpress_data(url)
            
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
