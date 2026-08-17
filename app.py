import streamlit as st
from PIL import Image
import io
import os
from google import genai
from google.genai import types

st.set_page_config(
    page_title="Gemini AI Mockup Studio",
    page_icon="🖼️",
    layout="wide"
)

st.title("🖼️ Gemini Otomatik Mockup Üretici")
st.write("Tablonuzun stilini ve içeriğini koruyarak **Google Gemini** altyapısıyla otomatik mockup'lar oluşturun.")

# ---------------------------------------------------------
# GEMINI API ANAHTARI (Streamlit Secrets Üzerinden Çekilir)
# ---------------------------------------------------------
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    st.error("API Anahtarı bulunamadı! Lütfen Streamlit Cloud ayarlarından Secrets kısmına ekleyin.")
    st.stop()

# 4 Farklı İç Mekan Konsepti
PROMPTS = {
    "1. Modern Minimalist Salon": "A high quality photo of a luxury modern minimalist living room wall with this framed art piece hanging on the wall. Soft natural sunlight, elegant interior design.",
    "2. İskandinav Çalışma Alanı": "A high quality photo of a cozy Scandinavian study room wall with this framed art piece hanging above a wooden desk with indoor plants.",
    "3. Boho Style Yatak Odası": "A high quality photo of a boho-chic bedroom interior wall with this framed art piece hanging above the bed, warm textures, pampas grass.",
    "4. Sanat Galerisi Koridoru": "A high quality photo of a modern art gallery corridor wall with this framed art piece illuminated by gallery spotlights."
}

# Görsel Yükleme Alanı
uploaded_file = st.file_uploader("Tablo Görselinizi Yükleyin (PNG, JPG)", type=["png", "jpg", "jpeg"])

if uploaded_file:
    raw_img = Image.open(uploaded_file)
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.image(raw_img, caption="Orijinal Tablonuz", use_container_width=True)
    
    with col_right:
        st.markdown("### ⚙️ Mockup Seçenekleri")
        frame_style = st.selectbox(
            "Çerçeve Stili", 
            ["Siyah Ahşap Çerçeve (Black Wooden Frame)", "Doğal Ahşap Çerçeve (Natural Oak Frame)", "Beyaz Çerçeve (White Frame)", "Çerçevesiz Kanvas (Thin Canvas)"]
        )
        
        generate_btn = st.button("✨ 4 Mockup'ı Otomatik Üret", type="primary", use_container_width=True)

    if generate_btn:
        st.markdown("---")
        st.markdown("### ⏳ Gemini Odaları Oluşturuyor...")
        progress_bar = st.progress(0)
        
        generated_images = {}
        
        for idx, (style_name, room_prompt) in enumerate(PROMPTS.items()):
            full_prompt = (
                f"Place this exact artwork image inside a {frame_style} and render it naturally mounted on the wall in this room: {room_prompt}. "
                f"Do not alter the colors, details, or drawing inside the artwork."
            )
            
            try:
                # Güncel Gemini Multimodal Visual Modeli
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[raw_img, full_prompt]
                )
                
                # Görsel yanıtı kontrolü
                if hasattr(response, 'candidates') and response.candidates:
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                            img = Image.open(io.BytesIO(part.inline_data.data))
                            generated_images[style_name] = img
                            break

            except Exception as e:
                # İkinci yedek model denemesi (Fallback)
                try:
                    response = client.models.generate_content(
                        model='gemini-1.5-flash',
                        contents=[raw_img, full_prompt]
                    )
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                            img = Image.open(io.BytesIO(part.inline_data.data))
                            generated_images[style_name] = img
                            break
                except Exception as ex:
                    st.error(f"{style_name} üretilirken bir hata oluştu: {str(ex)}")
            
            progress_bar.progress((idx + 1) / len(PROMPTS))

        if generated_images:
            st.success("✅ Tüm Gemini Mockup'ları Başarıyla Üretildi!")
            tabs = st.tabs(list(generated_images.keys()))
            for tab, (style_name, img) in zip(tabs, generated_images.items()):
                with tab:
                    st.image(img, caption=style_name, use_container_width=True)
        elif generate_btn:
            st.warning("Görsel üretilemedi. Lütfen tekrar deneyin.")
