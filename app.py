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

st.title("🖼️ Gemini Tabanlı Yapay Zeka Mockup Üretici")
st.write("Tablonuzun stilini ve içeriğini koruyarak **Google Gemini / Imagen** altyapısıyla ücretsiz mockup'lar oluşturun.")

# Sol Menü - Ücretsiz Google API Key
st.sidebar.header("🔑 Google AI Bağlantısı")
api_key = st.sidebar.text_input(
    "Gemini API Key", 
    type="password", 
    help="aistudio.google.com adresinden tamamen ücretsiz alabilirsiniz."
)

if not api_key:
    st.info("💡 Başlamak için lütfen sol menüye **Google Gemini API Key**'inizi girin (Ücretsizdir).")
    st.stop()

# Client Bağlantısı
client = genai.Client(api_key=api_key)

# 4 Farklı İç Mekan Konsepti
PROMPTS = {
    "1. Modern Minimalist Salon": "A photo of a luxury modern minimalist living room wall with a framed art piece hanging. Soft natural sunlight, elegant decor.",
    "2. İskandinav Çalışma Alanı": "A photo of a cozy Scandinavian study room wall with a framed art piece hanging above a wooden desk with plants.",
    "3. Boho Style Yatak Odası": "A photo of a boho-chic bedroom interior wall with a framed art piece hanging above the bed, warm textures.",
    "4. Sanat Galerisi Koridoru": "A photo of a modern art gallery wall with a framed art piece illuminated by gallery spotlights."
}

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
        
        generate_btn = st.button("✨ Gemini ile 4 Mockup Üret", type="primary", use_container_width=True)

    if generate_btn:
        st.markdown("---")
        st.markdown("### ⏳ Gemini Odaları Oluşturuyor...")
        progress_bar = st.progress(0)
        
        generated_images = {}
        
        for idx, (style_name, room_prompt) in enumerate(PROMPTS.items()):
            full_prompt = (
                f"Place this input artwork image inside a {frame_style} and mount it seamlessly on the wall in this room: {room_prompt}. "
                f"Keep the exact artwork details, colors, and perspective intact inside the frame without changing the drawing."
            )
            
            try:
                # Gemini Imagen görsel üretimi / düzenlemesi
                result = client.models.generate_images(
                    model='imagen-3.0-generate-002',
                    prompt=full_prompt,
                    config=types.GenerateImagesConfig(
                        number_of_images=1,
                        aspect_ratio="4:3",
                        output_mime_type="image/jpeg"
                    )
                )
                
                for generated_image in result.generated_images:
                    image = Image.open(io.BytesIO(generated_image.image.image_bytes))
                    generated_images[style_name] = image

            except Exception as e:
                st.error(f"{style_name} üretilirken bir hata oluştu: {str(e)}")
            
            progress_bar.progress((idx + 1) / len(PROMPTS))

        if generated_images:
            st.success("✅ Tüm Gemini Mockup'ları Üretildi!")
            tabs = st.tabs(list(generated_images.keys()))
            for tab, (style_name, img) in zip(tabs, generated_images.items()):
                with tab:
                    st.image(img, caption=style_name, use_container_width=True)
