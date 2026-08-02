import json
import os
import requests
import pandas as pd
import streamlit as st
from bs4 import BeautifulSoup
import google.generativeai as genai

# 🔑 API Açarın:
API_KEY = "AQ.Ab8RN6LrmbukPOCEBXldBcVeLcY-4I18mx25iWzhAXrwjeo6Jw"
genai.configure(api_key=API_KEY)

EXCEL_FAYL_ADI = "ebay_mehsullar.xlsx"

# Səhifə Ayarları (Saytın Adı Burada Dəyişdirildi)
st.set_page_config(page_title="Tacirin eBayi", page_icon="🛍️", layout="wide")

st.title("🛍️ Tacirin eBayi")
st.write("Süni İntellekt vasitəsilə məhsul məlumatlarını eBay üçün optimizasiya edin və bazaya əlavə edin.")

def mehsul_melumatlarini_cek(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        basliq = ""
        if soup.find('h1'):
            basliq = soup.find('h1').text.strip()
        elif soup.title:
            basliq = soup.title.text.strip()

        tesvir_metni = ""
        paragraphs = soup.find_all('p')
        for p in paragraphs[:5]:
            if len(p.text.strip()) > 20:
                tesvir_metni += p.text.strip() + " "

        return {
            "basliq": basliq if basliq else "Məhsul Başlığı",
            "tesvir": tesvir_metni if tesvir_metni else "Məhsul haqqında ətraflı məlumat daxil edilməyib."
        }
    except Exception as e:
        st.error(f"Linkdən məlumat çəkilərkən xəta oldu: {e}")
        return None

def ebay_si_muherriki(xam_basliq, xam_tesvir, xam_qiymet, qazanc_faizi):
    son_qiymet = round(xam_qiymet * (1 + qazanc_faizi / 100), 2)

    prompt = f"""
    Sən peşəkar e-ticarət mütəxəssisisən. Məhsul məlumatlarını eBay üçün optimizasiya et.

    MƏHSUL MƏLUMATLARI:
    - Orijinal Başlıq: {xam_basliq}
    - Orijinal Təsvir: {xam_tesvir}

    TƏLƏBLƏR:
    1. "ebay_title": Maksimum 80 simvol olsun, əsas açar sözləri əhatə etsin.
    2. "ebay_description_html": Məhsulun üstünlüklərini göstərən təmiz HTML formatlı təsvir yaz.

    YALNIZ bu JSON formatında cavab ver:
    {{
        "ebay_title": "...",
        "ebay_description_html": "..."
    }}
    """

    model = genai.GenerativeModel(
        model_name='models/gemini-flash-latest',
        generation_config={"response_mime_type": "application/json"}
    )
    
    response = model.generate_content(prompt)
    si_cavab = json.loads(response.text)

    return {
        "ebay_title": si_cavab["ebay_title"],
        "orijinal_qiymet": xam_qiymet,
        "satis_qiymeti": son_qiymet,
        "qazanc_faizi": qazanc_faizi,
        "ebay_description_html": si_cavab["ebay_description_html"]
    }

def excele_yaz(yeni_data):
    df_new = pd.DataFrame([yeni_data])
    if os.path.exists(EXCEL_FAYL_ADI):
        df_old = pd.read_excel(EXCEL_FAYL_ADI)
        df_final = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df_final = df_new
    df_final.to_excel(EXCEL_FAYL_ADI, index=False)

# FORM
col1, col2 = st.columns([2, 1])

with col1:
    url = st.text_input("🔗 Məhsul Linki (URL):", placeholder="https://www.aliexpress.com/item/...")

with col2:
    alis_qiymeti = st.number_input("💰 Alış Qiyməti ($):", min_value=0.1, value=10.0, step=0.5)
    qazanc_faizi = st.number_input("📈 Qazanc Faizi (%):", min_value=1.0, value=30.0, step=1.0)

# DÜYMƏ VƏ NƏTİCƏLƏR
if st.button("🚀 Məhsulu Optimizasiya Et", type="primary"):
    if not url:
        st.warning("Zəhmət olmasa məhsul linkini daxil edin!")
    else:
        with st.spinner("Məlumatlar çəkilir və Sİ tərəfindən optimizasiya olunur..."):
            cekilen_data = mehsul_melumatlarini_cek(url)
            
            if cekilen_data:
                netice = ebay_si_muherriki(
                    cekilen_data["basliq"], 
                    cekilen_data["tesvir"], 
                    alis_qiymeti, 
                    qazanc_faizi
                )

                excel_data = {
                    "Məhsul Linki": url,
                    "eBay Başlıq": netice["ebay_title"],
                    "Alış Qiyməti ($)": netice["orijinal_qiymet"],
                    "Satış Qiyməti ($)": netice["satis_qiymeti"],
                    "Mənfəət (%)": netice["qazanc_faizi"],
                    "HTML Description": netice["ebay_description_html"]
                }
                excele_yaz(excel_data)

                st.success("✅ Optimizasiya tamamlandı və Excel faylına yadda saxlanıldı!")
                
                # Səliqəli Nəticə Bölməsi
                st.subheader("📌 Optimizasiya Edilmiş eBay Başlığı")
                st.code(netice["ebay_title"], language="text")

                st.subheader("💰 Qiymət Hesablanması")
                st.info(f"Alış Qiyməti: ${netice['orijinal_qiymet']}  ➔  Satış Qiyməti: ${netice['satis_qiymeti']}  (Mənfəət: %{netice['qazanc_faizi']})")

                st.subheader("📝 Hazır HTML Təsvir (Description)")
                st.code(netice["ebay_description_html"], language="html")

# CƏDVƏL BAZASI
st.divider()
st.subheader("📊 Saxlanılmış Məhsullar BAZASI (Excel)")

if os.path.exists(EXCEL_FAYL_ADI):
    df = pd.read_excel(EXCEL_FAYL_ADI)
    st.dataframe(df, use_container_width=True)
else:
    st.write("Hələ ki saxlanılmış məhsul yoxdur.")
